"""Offline HTTP simulations of bounded 429 recovery and honest billing."""
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.utils import format_datetime
import json
from pathlib import Path
import sys
import tempfile
import unittest

import httpx

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import mathqa_workflow_availability as availability
import mathqa_workflow_evaluation as evaluation
import mathqa_workflow_pilot as pilot
import mathqa_workflow_store as store
import mathqa_workflow as workflow
from mathqa_transport import upstream_429, retry_delay


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.db = self.root/"db.sqlite3"
        self.dataset = self.root/"dataset.json"
        self.records = json.loads(pilot.DATASET_PATH.read_bytes())
        for r in self.records:
            r["Rationale"]="SECRET_KEY_ONLY_REASONING"
        self.dataset.write_text(json.dumps(self.records),encoding="utf-8")
        config = workflow.configuration(["deepseek"]*3,deepseek_provider="venice",rate_limit_retries=True)
        models = {}
        for p in [config["solvers"][0],config["verifier"]]:
            settings = p.get("body_settings",p.get("settings"))
            models[p["model"]] = {"data":{"id":p["model"],"endpoints":[{"tag":settings["provider"]["only"][0],
                "provider_name":"Fixture DeepSeek" if "deepseek" in p["model"] else "Fixture Gemini","status":0,
                "pricing":{"prompt":"0.00000026829","completion":"0.00000039024"},
                "max_completion_tokens":4096,"supported_parameters":["temperature","max_tokens","reasoning","response_format"]}]}}
        self.metadata = {"fetched_at_utc":datetime.now(timezone.utc).isoformat(),"models":models,
            "catalog":{"models":{config["verifier"]["model"]:{"id":config["verifier"]["model"],
                "reasoning":{"mandatory":False},"supported_parameters":["reasoning"]}}}}
        self.exposure = {"legacy_question_ids":[],"workflow_question_ids":list(pilot.QUESTION_IDS)}
        self.plan = availability.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset)
        self.sent,self.waits = [],[]

    def response(self,request,*,error=False,headers=None,known=False,wrong=False,unknown=False):
        body = json.loads(request.content)
        self.sent.append(body)
        provider = self.plan["endpoints"][body["model"]]["provider_name"]
        if error:
            payload = {"error":{"code":429,"metadata":{"limit_source":"upstream_provider_shared_pool",
                "provider_name":provider,"headers":{"Retry-After":"30"},"retry_after_seconds":30}}}
            if known:
                payload["usage"]={"cost":0,"prompt_tokens":0,"completion_tokens":0}
            return httpx.Response(429,json=payload,headers=headers)
        if body["messages"][0]["role"]=="system":
            answer = {"accepted":True}
        else:
            record = next(r for r in self.records if r["Problem"] in body["messages"][0]["content"])
            answer = {"calculation":"simulation","option":"a" if wrong else record["correct"],"value":"simulation"}
        return httpx.Response(200,json={"model":body["model"],"provider":provider,"id":"mock",
            "choices":[{"message":{"content":json.dumps(answer)},"finish_reason":"stop"}],
            "usage":{"prompt_tokens":100,"completion_tokens":20,"cost":None if unknown else .00001,
                "completion_tokens_details":{"reasoning_tokens":0}}})

    def run_mock(self,handler=None,*,budget=None,requests=None,waiter=None):
        with httpx.Client(transport=httpx.MockTransport(handler or self.response)) as client:
            return availability.run_check(self.plan,database_path=self.db,budget_usd=budget or self.plan["execution_policy"]["maximum_budget_usd"],
                max_requests=requests or 38,api_key="mock_secret",client=client,waiter=waiter or self.waits.append)

    def rows(self,table):
        with closing(store.connect(self.db)) as c:
            return [dict(r) for r in c.execute('SELECT * FROM "'+table+'" ORDER BY rowid')]

    def test_preparation_is_offline_frozen_small_scope_and_opt_in(self):
        availability.validate_plan(self.plan)
        self.assertFalse(self.db.exists())
        self.assertEqual((len(self.plan["questions"]),len(self.plan["schedule"])),(2,6))
        self.assertEqual(self.plan["cost_preview"]["maximum_calls"],38)
        self.assertEqual(self.plan["cost_preview"]["maximum_logical_calls"],36)
        self.assertEqual(self.plan["cost_preview"]["maximum_retry_requests"],2)
        self.assertNotIn("transport_policy",workflow.configuration(["deepseek"]*3,deepseek_provider="venice"))
        changed = deepcopy(self.plan)
        changed["configurations"]["deepseek-deepseek-deepseek"]["transport_policy"]["max_retries_per_call"]=20
        changed["sha256"]=pilot.digest({k:v for k,v in changed.items() if k!="sha256"})
        with self.assertRaises(ValueError):
            availability.validate_plan(changed)

    def test_solver_recovers_without_consuming_math_slot_or_losing_unknown_cost(self):
        report = self.run_mock(lambda r:self.response(r,error=len(self.sent)==0))
        self.assertTrue(report["complete_coverage"])
        self.assertEqual((report["scored_executions"],report["score_total"],report["new_requests"]),(6,6,13))
        self.assertEqual(report["transport_retry_requests"],1)
        self.assertEqual(report["unknown_cost_calls"],1)
        self.assertEqual(Decimal(report["known_new_cost_usd"]),Decimal(".00012"))
        self.assertEqual(self.waits,[30])
        self.assertEqual(self.sent[0],self.sent[1])
        attempts = self.rows("workflow_attempts")
        self.assertEqual(len(attempts),6)
        self.assertTrue(all(a["position"]==1 for a in attempts))
        physical = self.rows("workflow_transport_calls")
        self.assertIsNone(physical[0]["cost_usd"])
        self.assertEqual(physical[0]["held_cost_usd"],physical[0]["cost_reservation_usd"])
        self.assertEqual(Decimal(report["accounted_exposure_usd"]),Decimal(report["known_new_cost_usd"])+Decimal(report["held_unknown_cost_usd"]))
        self.assertNotIn("SECRET_KEY_ONLY_REASONING",json.dumps(self.sent))

    def test_two_transport_retries_keep_same_request_and_hold_both_unknowns(self):
        report = self.run_mock(lambda r:self.response(r,error=len(self.sent)<2))
        self.assertEqual(self.waits,[30,60])
        self.assertEqual(self.sent[:3],[self.sent[0]]*3)
        self.assertEqual((report["new_requests"],report["unknown_cost_calls"],report["transport_retry_requests"]),(14,2,2))
        self.assertTrue(report["complete_coverage"])

    def test_physical_requests_are_durable_and_mathematical_retry_remains_separate(self):
        def respond(request):
            with closing(store.connect(self.db)) as c:
                active = c.execute("SELECT request_json FROM workflow_transport_calls WHERE status='running'").fetchall()
            self.assertEqual(len(active),1)
            self.assertEqual(json.loads(active[0][0]),json.loads(request.content))
            index = len(self.sent)
            response = self.response(request,error=index==0)
            if index==2:
                payload = response.json()
                payload["choices"][0]["message"]["content"]='{"accepted":false}'
                return httpx.Response(200,json=payload)
            return response
        report = self.run_mock(respond)
        self.assertEqual((report["new_requests"],report["transport_retry_requests"]),(15,1))
        self.assertTrue(report["complete_coverage"])
        first = report["executions"][0]["execution_id"]
        positions = [a["position"] for a in self.rows("workflow_attempts") if a["execution_id"]==first]
        self.assertEqual(positions,[1,2])
        self.assertEqual(self.sent[0],self.sent[1])
        self.assertEqual(self.sent[1],self.sent[3])

    def test_verifier_retry_does_not_call_solver_again(self):
        report = self.run_mock(lambda r:self.response(r,error=len(self.sent)==1))
        self.assertEqual(self.sent[1],self.sent[2])
        self.assertEqual((report["new_requests"],report["unknown_cost_calls"]),(13,1))
        self.assertTrue(report["complete_coverage"])
        self.assertEqual(report["cooldowns"][0]["role"],"verifier")

    def test_known_zero_cost_429_remains_known_without_a_hold(self):
        report = self.run_mock(lambda r:self.response(r,error=len(self.sent)==0,known=True))
        self.assertEqual(report["unknown_cost_calls"],0)
        self.assertEqual(report["held_unknown_cost_usd"],"0")
        self.assertEqual(report["new_requests"],13)

    def test_exhausted_429s_are_incomplete_not_three_mathematical_failures(self):
        report = self.run_mock(lambda r:self.response(r,error=True))
        self.assertEqual((report["new_requests"],report["unknown_cost_calls"]),(3,3))
        self.assertEqual(report["scored_executions"],0)
        self.assertEqual(len(self.rows("workflow_attempts")),1)
        self.assertEqual(len(self.rows("workflow_grades")),0)
        self.assertEqual(report["stop_reason"],"rate_limit_retry_limit")
        self.assertEqual(self.waits,[30,60])

    def test_retry_limit_is_shared_across_entire_run(self):
        report = self.run_mock(lambda r:self.response(r,error=len(self.sent) in (0,3,6)))
        self.assertEqual((report["new_requests"],report["scored_executions"]),(7,2))
        self.assertEqual(self.waits,[30,30])
        self.assertEqual(report["stop_reason"],"rate_limit_retry_limit")

    def test_request_and_spending_limits_checked_before_wait_or_retry(self):
        report = self.run_mock(lambda r:self.response(r,error=True),requests=1)
        self.assertEqual((report["new_requests"],self.waits),(1,[]))
        self.assertEqual(report["stop_reason"],"request_limit")
        self.setUp()
        model = "deepseek/deepseek-v3.2"
        config = self.plan["configurations"]["deepseek-deepseek-deepseek"]
        request = workflow.solver_request(config["solvers"][0],self.plan["questions"][0])
        request["provider"]["max_price"]=self.plan["price_limits"][model]
        from mathqa_verifier_preflight import request_cost
        reserve = request_cost(request,self.plan["endpoints"][model])
        report = self.run_mock(lambda r:self.response(r,error=True),budget=float(reserve*Decimal("1.5")))
        self.assertEqual((report["new_requests"],self.waits),(1,[]))
        self.assertEqual(report["stop_reason"],"spending_limit")

    def test_invalid_or_excessive_retry_after_never_shortened(self):
        for value in ("120","NaN","-1","garbage"):
            with self.subTest(value=value):
                self.setUp()
                report = self.run_mock(lambda r:self.response(r,error=True,headers={"Retry-After":value}))
                self.assertEqual((report["new_requests"],self.waits),(1,[]))
                self.assertEqual(report["stop_reason"],"rate_limit_cooldown_limit_or_invalid")

    def test_cancel_during_cooldown_preserves_one_physical_request(self):
        def cancel(_):
            raise KeyboardInterrupt
        report = self.run_mock(lambda r:self.response(r,error=True),waiter=cancel)
        self.assertEqual((report["status"],report["new_requests"],report["scored_executions"]),("interrupted",1,0))
        self.assertEqual(report["stop_reason"],"cancelled_during_cooldown")

    def test_timeout_and_unknown_success_billing_are_not_retried(self):
        def timeout(request):
            self.sent.append(json.loads(request.content))
            raise httpx.ReadTimeout("simulated timeout",request=request)
        report = self.run_mock(timeout)
        self.assertEqual((report["new_requests"],self.waits),(1,[]))
        self.assertEqual(report["stop_reason"],"unknown_cost")
        self.setUp()
        report = self.run_mock(lambda r:self.response(r,unknown=True))
        self.assertEqual((report["new_requests"],self.waits),(1,[]))
        self.assertEqual(report["stop_reason"],"unknown_cost")

    def test_unknown_allowance_cap_and_profile_tampering_are_rejected(self):
        metadata = deepcopy(self.metadata)
        metadata["models"]["deepseek/deepseek-v3.2"]["data"]["endpoints"][0]["pricing"]["prompt"]="0.000002"
        self.plan = availability.prepare_plan(metadata,self.exposure,dataset_path=self.dataset)
        report = self.run_mock(lambda r:self.response(r,error=True))
        self.assertEqual((report["stop_reason"],report["new_requests"],self.waits),("unknown_429_allowance_limit",1,[]))
        with closing(store.connect(self.db)) as c:
            run = c.execute("SELECT run_id FROM workflow_runs").fetchone()[0]
        config = deepcopy(self.plan["configurations"]["deepseek-deepseek-deepseek"])
        config["transport_policy"]["max_unknown_reservation_usd"]="1"
        cid = store.create_config(run,"tampered",config,database_path=self.db)
        with self.assertRaisesRegex(ValueError,"trusted"):
            workflow.Runner(run,cid,config,database_path=self.db,sender=lambda r:None,reservations=lambda r:.001,
                providers={},limits=workflow.Limits(self.plan["execution_policy"]["maximum_budget_usd"],38))

    def test_migration_and_plan_drift_duplicate_run_and_wrong_option_grading(self):
        changed = deepcopy(self.plan)
        changed["migration_sha256"]["003_transport.sql"]="changed"
        changed["sha256"]=pilot.digest({k:v for k,v in changed.items() if k!="sha256"})
        with self.assertRaises(ValueError):
            availability.validate_plan(changed)
        report = self.run_mock(lambda r:self.response(r,wrong=True))
        # Acceptance still does not establish correctness after transport recovery.
        self.assertTrue(report["complete_coverage"])
        self.assertLess(report["score_total"],6)
        count = len(self.sent)
        with self.assertRaisesRegex(ValueError,"already has a run"):
            self.run_mock()
        self.assertEqual(len(self.sent),count)


class RetryProtocolTests(unittest.TestCase):
    def test_only_empty_pinned_upstream_errors_are_eligible(self):
        good = {"error":{"code":429,"metadata":{"provider_name":"Venice","limit_source":"upstream_provider_shared_pool"}}}
        self.assertTrue(upstream_429(429,good,"Venice","deepseek/model"))
        for status,payload in [(503,good),(402,good),(429,{**good,"id":"gen"}),(429,{**good,"choices":[{}]}),
                (429,{**good,"usage":{"cost":.01}}),(429,{**good,"usage":{"cost":None}}),
                (429,{**good,"model":"other"})]:
            self.assertFalse(upstream_429(status,payload,"Venice","deepseek/model"))
        self.assertFalse(upstream_429(429,good,"Other","deepseek/model"))
        good["error"]["metadata"]["limit_source"]="openrouter_key_limit"
        self.assertFalse(upstream_429(429,good,"Venice","deepseek/model"))

    def test_retry_after_http_date_and_longest_source(self):
        instant = datetime.now(timezone.utc).replace(microsecond=0)
        payload = {"error":{"metadata":{"headers":{"Retry-After":"35"}}}}
        self.assertEqual(retry_delay(payload,{"Retry-After":format_datetime(instant+timedelta(seconds=40))},1,now=instant),40)
        self.assertEqual(retry_delay(payload,{},2,now=instant),60)


if __name__=="__main__":
    unittest.main()
