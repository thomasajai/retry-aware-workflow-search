"""Provider changes, ceiling-priced budgets and mathematical retries, offline."""
from copy import deepcopy
from decimal import Decimal
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
        cases = [{"status":-2},{"supported_parameters":["max_tokens","temperature"]},
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


if __name__ == "__main__":
    unittest.main()
