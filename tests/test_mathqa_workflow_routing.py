"""Provider changes, ceiling-priced budgets and mathematical retries, offline."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import unittest

import httpx

import test_mathqa_workflow_availability as fixtures
import test_mathqa_workflow_evaluation as evaluation_fixtures
from mathqa_models import MODEL_PROFILES, WORKFLOW_DEEPSEEK_PRICE_LIMITS
import mathqa_workflow as workflow
import mathqa_workflow_availability as availability
import mathqa_workflow_evaluation as evaluation
import mathqa_workflow_pilot as pilot
import mathqa_workflow_store as store
from mathqa_workflow_grading import grade_execution
from mathqa_verifier_preflight import request_cost

DEEPSEEK = MODEL_PROFILES["deepseek"].model


class RoutingTests(unittest.TestCase):
    def setUp(self):
        fixtures.AvailabilityTests.setUp(self)
        endpoints = self.metadata["models"][DEEPSEEK]["data"]["endpoints"]
        alternative = deepcopy(endpoints[0])
        alternative.update(tag="other", provider_name="Other provider")
        alternative["pricing"] = {"prompt":"0.00000056", "completion":"0.00000168"}
        endpoints.append(alternative)
        self.plan = availability.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset,deepseek_provider="auto")

    def response(self, request, **kwargs):
        response = fixtures.AvailabilityTests.response(self, request, **kwargs)
        body = json.loads(request.content)
        payload = response.json()
        if response.status_code == 200 and body["model"] == DEEPSEEK:
            # Provider changes across independent solver calls are legitimate.
            payload["provider"] = self.plan["endpoints"][DEEPSEEK]["provider_names"][(len(self.sent)//2)%2]
        return httpx.Response(response.status_code,json=payload)

    def run_mock(self, handler=None, *, budget=None, requests=36):
        with httpx.Client(transport=httpx.MockTransport(handler or self.response)) as client:
            return availability.run_check(self.plan,database_path=self.db,budget_usd=budget or self.plan["execution_policy"]["maximum_budget_usd"],
                max_requests=requests,api_key="mock_secret",client=client,waiter=lambda _:self.fail("No client cooldowns"))

    def rows(self, table):
        return fixtures.AvailabilityTests.rows(self,table)

    def test_provider_changes_are_logged_and_independently_graded(self):
        result = self.run_mock()
        self.assertEqual((result["new_requests"],result["scored_executions"],result["score_total"]),(12,6,6))
        solver_groups = [r for r in result["provider_costs"] if r["model"]==DEEPSEEK]
        self.assertEqual({r["provider"] for r in solver_groups},{"Fixture DeepSeek","Other provider"})
        self.assertEqual(sum(r["requests"] for r in solver_groups),6)
        self.assertEqual(sum(Decimal(r["known_cost_usd"]) for r in result["provider_costs"]),Decimal(result["known_new_cost_usd"]))
        self.assertEqual(result["transport_retry_requests"],0)
        for request in self.sent:
            if request["model"]==DEEPSEEK:
                self.assertNotIn("only",request["provider"])
                self.assertNotIn("order",request["provider"])
                self.assertTrue(request["provider"]["allow_fallbacks"])
                self.assertTrue(request["provider"]["require_parameters"])
                self.assertEqual(request["provider"]["max_price"],WORKFLOW_DEEPSEEK_PRICE_LIMITS)
            else:
                self.assertEqual(request["provider"]["only"],["google-ai-studio"])
                self.assertFalse(request["provider"]["allow_fallbacks"])

    def test_rejected_attempts_repeat_original_input_and_exhaustion_scores_zero(self):
        def reject(request):
            result = self.response(request)
            body = json.loads(request.content)
            if body["messages"][0]["role"]=="system":
                payload = result.json()
                payload["choices"][0]["message"]["content"]='{"accepted":false}'
                return httpx.Response(200,json=payload)
            return result
        result = self.run_mock(reject)
        self.assertEqual((result["new_requests"],result["scored_executions"],result["score_total"]),(36,6,0))
        for offset in range(0,36,6):
            self.assertEqual(self.sent[offset],self.sent[offset+2])
            self.assertEqual(self.sent[offset],self.sent[offset+4])
        self.assertNotIn("SECRET_KEY_ONLY_REASONING",json.dumps(self.sent))
        self.assertTrue(all(e["status"]=="exhausted" for e in result["executions"]))

    def test_approval_of_wrong_option_is_still_scored_incorrect(self):
        result = self.run_mock(lambda r:self.response(r,wrong=True))
        expected = sum(next(q for q in self.records if q["id"]==e["question_id"])["correct"]=="a" for e in result["executions"])
        self.assertEqual(result["score_total"],expected)
        self.assertTrue(all(e["status"]=="accepted" for e in result["executions"]))

    def test_unknown_429_stops_without_retry_or_mathematical_grade(self):
        result = self.run_mock(lambda r:self.response(r,error=True))
        self.assertEqual((result["new_requests"],result["unknown_cost_calls"],result["scored_executions"]),(1,1,0))
        self.assertEqual(result["stop_reason"],"unknown_cost")
        self.assertEqual(result["held_unknown_cost_usd"],"0")
        self.assertEqual(len(self.rows("workflow_attempts")),1)

    def test_unknown_success_cost_stops(self):
        result = self.run_mock(lambda r:self.response(r,unknown=True))
        self.assertEqual((result["new_requests"],result["scored_executions"]),(1,0))
        self.assertEqual(result["stop_reason"],"unknown_cost")

    def test_unexpected_provider_or_model_stops(self):
        for field,value in (("provider","Unreviewed provider"),("model","another/model")):
            with self.subTest(field=field):
                if self.db.exists():
                    self.setUp()
                def altered(request):
                    payload = self.response(request).json()
                    payload[field] = value
                    return httpx.Response(200,json=payload)
                result = self.run_mock(altered)
                self.assertEqual((result["new_requests"],result["scored_executions"]),(1,0))
                self.assertEqual(result["stop_reason"],"provider_or_model_mismatch")

    def test_known_gateway_failure_is_incomplete(self):
        def failed(request):
            payload = self.response(request).json()
            payload.pop("choices")
            payload["error"] = {"code":503}
            return httpx.Response(503,json=payload)
        result = self.run_mock(failed)
        self.assertEqual((result["new_requests"],result["scored_executions"]),(1,0))
        self.assertEqual(result["stop_reason"],"gateway_failure")

    def test_charge_above_token_price_ceiling_stops_even_below_reservation(self):
        def expensive(request):
            payload = self.response(request).json()
            payload["usage"]["cost"] = .0002
            return httpx.Response(200,json=payload)
        result = self.run_mock(expensive)
        self.assertEqual(result["stop_reason"],"price_ceiling_exceeded")
        self.assertEqual(result["new_requests"],1)

    def test_reservations_use_ceiling_and_budget_gate_precedes_http(self):
        profile = self.plan["configurations"]["deepseek-deepseek-deepseek"]["solvers"][0]
        request = workflow.solver_request(profile,self.plan["questions"][0])
        envelope = self.plan["endpoints"][DEEPSEEK]
        reserve = request_cost(request,envelope)
        cheapest = request_cost(request,envelope["eligible_endpoints"][0])
        self.assertGreater(reserve,cheapest)
        result = self.run_mock(budget=float(reserve/2))
        self.assertEqual((result["new_requests"],result["stop_reason"]),(0,"spending_limit"))
        self.assertFalse(self.sent)

    def test_preflight_excludes_ineligible_endpoints_and_fails_without_candidates(self):
        template = deepcopy(self.metadata["models"][DEEPSEEK]["data"]["endpoints"][0])
        cases = [{"status":None},{"supported_parameters":["max_tokens","temperature"]},
                 {"max_completion_tokens":256},{"pricing":{"prompt":"0.000001","completion":"0.000001"}},
                 {"pricing":{"prompt":"0.0000003","completion":"0.000002"}},
                 {"pricing":{"prompt":"0.0000003","completion":"0.000001","request":".001"}},
                 {"pricing":{"prompt":"NaN","completion":"0.000001"}},
                 {"pricing":{"prompt":"0.0000003","completion":"0.000001","internal_reasoning":"0.000003"}}]
        for changes in cases:
            with self.subTest(changes=changes):
                metadata = deepcopy(self.metadata)
                candidate = {**template,**changes,"tag":"ineligible","provider_name":"Ineligible"}
                data = metadata["models"][DEEPSEEK]["data"]
                data["endpoints"].append(candidate)
                plan = availability.prepare_plan(metadata,self.exposure,dataset_path=self.dataset,deepseek_provider="auto")
                self.assertNotIn("Ineligible",plan["endpoints"][DEEPSEEK]["provider_names"])
                data["endpoints"] = [candidate]
                with self.assertRaisesRegex(ValueError,"No active providers"):
                    availability.prepare_plan(metadata,self.exposure,dataset_path=self.dataset,deepseek_provider="auto")

    def test_known_compatible_provider_can_return_after_being_inactive(self):
        endpoints = self.metadata["models"][DEEPSEEK]["data"]["endpoints"]
        endpoints[1]["status"] = -2
        self.plan = availability.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset,deepseek_provider="auto")
        envelope = self.plan["endpoints"][DEEPSEEK]
        self.assertIn("Other provider",envelope["provider_names"])
        self.assertNotIn("Other provider",envelope["active_provider_names"])
        result = self.run_mock()
        self.assertTrue(result["complete_coverage"])
        self.assertTrue(any(r["provider"]=="Other provider" for r in result["provider_costs"]))
        endpoints[0]["status"] = -2
        with self.assertRaisesRegex(ValueError,"No active providers"):
            availability.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset,deepseek_provider="auto")

    def test_plan_freezes_routing_and_disables_client_retry_exception(self):
        availability.validate_plan(self.plan)
        self.assertEqual(self.plan["execution_policy"]["maximum_requests"],36)
        self.assertEqual(self.plan["cost_preview"]["maximum_retry_requests"],0)
        self.assertNotIn("transport_policy",self.plan["execution_policy"])
        with self.assertRaises(ValueError):
            workflow.configuration(["deepseek"]*3,deepseek_provider="auto",rate_limit_retries=True)
        changed = deepcopy(self.plan)
        changed["endpoints"][DEEPSEEK]["provider_names"].append("Unreviewed")
        changed["sha256"] = pilot.digest({k:v for k,v in changed.items() if k!="sha256"})
        with self.assertRaises(ValueError):
            availability.validate_plan(changed)

    def test_broad_plan_retains_27_sequences_and_original_question_selection(self):
        evaluation_fixtures.EvaluationTests.setUp(self)
        original_ids = [q["id"] for q in self.plan["questions"]]
        routed = evaluation.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset,deepseek_provider="auto")
        evaluation.validate_plan(routed)
        self.assertEqual(len(routed["configurations"]),27)
        self.assertEqual([q["id"] for q in routed["questions"]],original_ids)
        self.assertEqual(routed["execution_policy"]["maximum_requests"],3240)
        self.assertFalse(self.db.exists())

    def output_loop(self, handler, *, repetitions=1, requests=36):
        config = workflow.configuration(["deepseek"]*3,deepseek_provider="auto",solver_truncation_unusable=True)
        store.migrate(self.db)
        run = store.create_run("sequence_evaluation",self.dataset,hashlib.sha256(self.dataset.read_bytes()).hexdigest(),
            [q["id"] for q in self.plan["questions"]],{"mode":"offline-test"},
            database_path=self.db,budget_usd=.07,max_requests=requests)
        cid = store.create_config(run,"deepseek-deepseek-deepseek",config,database_path=self.db)
        def sender(body):
            response = handler(httpx.Request("POST","https://mock.invalid",json=body))
            return response.status_code,response.json()
        runner = workflow.Runner(run,cid,config,database_path=self.db,sender=sender,
            reservations=lambda r:request_cost(r,self.plan["endpoints"][r["model"]]),
            providers={m:e.get("provider_names",e["provider_name"]) for m,e in self.plan["endpoints"].items()},
            limits=workflow.Limits(.07,requests),price_limits=self.plan["price_limits"])
        outcomes=[]
        for rep in range(1,repetitions+1):
            result = runner.execute(self.plan["questions"][0],repetition=rep)
            if result["status"] in ("accepted","exhausted","failed"):
                result["grade"] = grade_execution(result["execution_id"],database_path=self.db)
            outcomes.append(result)
            if result["status"] in ("budget_stopped","interrupted"):
                break
        return outcomes

    def truncate(self, request, **kwargs):
        payload = self.response(request,**kwargs).json()
        payload["choices"][0]["finish_reason"] = "length"
        payload["choices"][0]["message"]["content"] = '{"calculation":"unfinished'
        payload["usage"]["completion_tokens"] = 512
        return httpx.Response(200,json=payload)

    def test_known_solver_truncation_consumes_one_slot_then_original_input_retry(self):
        result = self.output_loop(lambda r:self.truncate(r) if not self.sent else self.response(r))[0]
        self.assertEqual((result["status"],result["grade"]["workflow_score"],len(self.sent)),("accepted",1,3))
        self.assertEqual(self.sent[0],self.sent[1])
        attempts=self.rows("workflow_attempts")
        self.assertEqual([a["position"] for a in attempts],[1,2])
        self.assertEqual(attempts[0]["usable"],0)
        self.assertIsNone(attempts[0]["verifier_call_id"])
        calls=self.rows("workflow_calls")
        self.assertEqual((calls[0]["status"],calls[0]["finish_reason"]),("failed","length"))
        self.assertEqual(calls[0]["cost_usd"],.00001)
        self.assertEqual(calls[0]["answer_text"],'{"calculation":"unfinished')
        self.assertNotIn("SECRET_KEY_ONLY_REASONING",json.dumps(self.sent))

    def test_three_truncated_solver_outputs_score_zero_and_next_execution_runs(self):
        results=self.output_loop(self.truncate,repetitions=2)
        self.assertEqual([r["status"] for r in results],["exhausted","exhausted"])
        self.assertEqual([r["grade"]["workflow_score"] for r in results],[0,0])
        self.assertEqual(len(self.sent),6)
        self.assertTrue(all(r["role"]=="solver" for r in self.rows("workflow_calls")))
        self.assertTrue(all(r["usable"]==0 for r in self.rows("workflow_attempts")))
        self.assertEqual(self.sent,[self.sent[0]]*6)

    def test_unknown_cost_on_truncated_solver_still_stops(self):
        result=self.output_loop(lambda r:self.truncate(r,unknown=True))[0]
        self.assertEqual((result["status"],result["terminal_reason"],len(self.sent)),("budget_stopped","unknown_cost",1))
        self.assertNotIn("grade",result)

    def test_truncated_solver_does_not_bypass_identity_or_output_guards(self):
        for field,value,reason in (("model","wrong/model","provider_or_model_mismatch"),
                                   ("completion_tokens",513,"reservation_exceeded")):
            with self.subTest(field=field):
                if self.db.exists():
                    self.setUp()
                def altered(request):
                    payload=self.truncate(request).json()
                    if field=="model":
                        payload[field]=value
                    else:
                        payload["usage"][field]=value
                    return httpx.Response(200,json=payload)
                result=self.output_loop(altered)[0]
                self.assertEqual((result["terminal_reason"],len(self.sent)),(reason,1))

    def test_verifier_truncation_and_gateway_errors_still_stop(self):
        result=self.output_loop(lambda r:self.response(r) if not self.sent else self.truncate(r))[0]
        self.assertEqual((result["terminal_reason"],len(self.sent)),("gateway_failure",2))
        self.setUp()
        def failed(request):
            payload=self.truncate(request).json()
            payload["error"]={"code":503}
            return httpx.Response(503,json=payload)
        result=self.output_loop(failed)[0]
        self.assertEqual((result["terminal_reason"],len(self.sent)),("gateway_failure",1))

    def test_final_slot_truncation_after_two_rejections_scores_zero(self):
        def respond(request):
            if len(self.sent)==4:
                return self.truncate(request)
            payload=self.response(request).json()
            if json.loads(request.content)["messages"][0]["role"]=="system":
                payload["choices"][0]["message"]["content"]='{"accepted":false}'
            return httpx.Response(200,json=payload)
        result=self.output_loop(respond)[0]
        self.assertEqual((result["status"],result["grade"]["workflow_score"],len(self.sent)),("exhausted",0,5))
        self.assertEqual([a["position"] for a in self.rows("workflow_attempts")],[1,2,3])

    def test_truncation_still_consumes_budget_and_request_allowance(self):
        result=self.output_loop(self.truncate,requests=1)[0]
        self.assertEqual((result["terminal_reason"],len(self.sent)),("request_limit",1))
        self.assertEqual(self.rows("workflow_calls")[0]["cost_usd"],.00001)

    def test_v4_truncation_policy_preserved_and_v5_plan_frozen(self):
        result=self.run_mock(self.truncate)
        self.assertEqual(result["stop_reason"],"gateway_failure")
        evaluation_fixtures.EvaluationTests.setUp(self)
        new=evaluation.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset,deepseek_provider="auto",solver_truncation_unusable=True)
        evaluation.validate_plan(new)
        self.assertEqual(new["version"],"workflow-evaluation-plan-v5")
        self.assertTrue(all(c["version"]=="solver-verifier-config-v5" for c in new["configurations"].values()))
        self.assertEqual(new["questions"],self.plan["questions"])
        self.assertEqual(new["schedule"],self.plan["schedule"])
        changed=deepcopy(new)
        changed["solver_truncation_unusable"]=False
        changed["sha256"]=pilot.digest({k:v for k,v in changed.items() if k!="sha256"})
        with self.assertRaises(ValueError):
            evaluation.validate_plan(changed)


if __name__ == "__main__":
    unittest.main()
