"""Frozen pilot and live adapter checks; disposable databases and mocked HTTP."""

from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import mathqa_workflow_pilot as pilot
import mathqa_workflow as workflow
import mathqa_workflow_store as store


class PilotTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.db = self.root/"test.sqlite3"
        self.dataset = self.root/"dataset.json"
        records = json.loads(pilot.DATASET_PATH.read_text(encoding="utf-8"))
        selected = [r for r in records if r["id"] in pilot.QUESTION_IDS]
        for r in selected:
            r["Rationale"] = "SECRET_REFERENCE_MUST_NOT_LEAK"
        self.dataset.write_text(json.dumps(selected),encoding="utf-8")
        self.key = {r["Problem"]:r["correct"] for r in selected}
        self.questions = {r["Problem"]:r for r in selected}
        config = workflow.configuration(pilot.SEQUENCES[0])
        models = {}
        for p in config["solvers"]+[config["verifier"]]:
            settings = p.get("body_settings",p.get("settings"))
            models[p["model"]] = {"data":{"id":p["model"],"endpoints":[{
                "tag":settings["provider"]["only"][0],"provider_name":"Offline fixture","status":0,
                "pricing":{"prompt":"0.0000001","completion":"0.0000004"},"max_completion_tokens":4096,
                "supported_parameters":["temperature","max_tokens","reasoning","response_format","top_p","top_k"]}]}}
        self.metadata = {"fetched_at_utc":datetime.now(timezone.utc).isoformat(),"models":models,
            "catalog":{"models":{config["verifier"]["model"]:{"id":config["verifier"]["model"],
            "supported_parameters":["reasoning"],"reasoning":{"mandatory":False}}}}}
        self.plan = pilot.prepare_plan(self.metadata,dataset_path=self.dataset)
        self.sent = []

    def response(self, request, *, accept=True, invalid=False, truncated=False, unknown=False, wrong=False):
        body = json.loads(request.content)
        self.sent.append(body)
        verifier = body["messages"][0]["role"] == "system"
        if verifier:
            content = {"accepted":"true"} if invalid else {"accepted":accept}
        else:
            problem = next(q for q in self.key if q in body["messages"][0]["content"])
            option = self.key[problem]
            if wrong:
                option = next(o for o in "abcde" if o!=option)
            content = {"calculation":"controlled test-only calculation","option":option,"value":"controlled"}
        payload = {"model":body["model"],"provider":"Offline fixture","id":"offline-test",
            "choices":[{"message":{"content":json.dumps(content)},"finish_reason":"length" if truncated else "stop"}],
            "usage":{"prompt_tokens":100,"completion_tokens":20,"completion_tokens_details":{"reasoning_tokens":0},"cost":None if unknown else 0.00001}}
        return httpx.Response(200,json=payload)

    def run_mock(self, *, handler=None, budget=0.04, count=36):
        with httpx.Client(transport=httpx.MockTransport(handler or self.response)) as client:
            return pilot.run_pilot(self.plan,database_path=self.db,budget_usd=budget,max_requests=count,
                                   api_key="sk-or-v1-mock_secret",client=client)

    def test_preparation_is_read_only_frozen_and_has_six_balanced_executions(self):
        with patch("httpx.Client.send",side_effect=AssertionError("No paid call")):
            plan = pilot.prepare_plan(self.metadata,dataset_path=self.dataset,created_at=self.plan["created_at_utc"])
            pilot.validate_plan(plan)
        self.assertFalse(self.db.exists())
        self.assertEqual(plan,self.plan)
        self.assertEqual(len(plan["schedule"]),6)
        self.assertEqual(plan["cost_preview"]["maximum_calls"],36)
        self.assertEqual(sum(r["maximum_calls"] for r in plan["cost_preview"]["breakdown"]),36)
        self.metadata["models"].clear()
        pilot.validate_plan(plan)

    def test_all_first_acceptances_have_complete_grades_costs_and_actual_price_ceilings(self):
        report = self.run_mock()
        self.assertEqual((report["status"],report["new_requests"],report["score_total"]),("completed",12,6))
        self.assertTrue(report["complete_coverage"])
        self.assertEqual(report["known_new_cost_usd"],"0.00012")
        self.assertEqual(report["accuracy_completed_only"],1)
        self.assertEqual({r["model"] for r in report["costs"] if r["role"]=="solver"},
                         {p["model"] for p in self.plan["configurations"][next(iter(self.plan["configurations"]))]["solvers"]})
        for body in self.sent:
            self.assertEqual(body["provider"]["max_price"],self.plan["price_limits"][body["model"]])
            self.assertFalse(body["provider"]["allow_fallbacks"])
            self.assertNotIn("SECRET_REFERENCE",json.dumps(body))
        with closing(store.connect(self.db)) as c:
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(),[])
            encoded = json.dumps([tuple(r) for r in c.execute("SELECT * FROM workflow_calls")])
            self.assertNotIn("mock_secret",encoded)

    def test_rejections_reach_three_slots_without_feedback_and_stop_at_36_calls(self):
        report = self.run_mock(handler=lambda r:self.response(r,accept=False))
        self.assertEqual((report["status"],report["new_requests"],report["score_total"]),("completed",36,0))
        self.assertTrue(report["complete_coverage"])
        self.assertEqual(report["verification_statuses"],{"reject":18})
        self.assertTrue(all(v==3 for v in report["attempts_per_execution"].values()))
        for body in self.sent:
            if body["messages"][0]["role"]=="user":
                self.assertNotIn('"accepted"',json.dumps(body))

    def test_known_technical_verifier_errors_advance_but_are_not_mathematical_rejections(self):
        report = self.run_mock(handler=lambda r:self.response(r,invalid=True))
        self.assertEqual((report["status"],report["score_total"]),("completed_with_errors",0))
        self.assertEqual(report["verification_statuses"],{"invalid":18})

    def test_wrong_accepted_answers_have_independent_score_zero(self):
        report = self.run_mock(handler=lambda r:self.response(r,wrong=True))
        self.assertEqual((report["new_requests"],report["score_total"]),(12,0))
        self.assertTrue(all(r["status"]=="accepted" for r in report["executions"]))

    def test_budget_and_request_stops_report_partial_coverage_without_imputed_scores(self):
        report = self.run_mock(count=1)
        self.assertEqual((report["status"],report["new_requests"],report["scored_executions"]),("budget_stopped",1,0))
        self.assertFalse(report["complete_coverage"])
        self.assertIsNone(report["accuracy_completed_only"])

    def test_unknown_billing_stops_entire_pilot_after_one_call(self):
        report = self.run_mock(handler=lambda r:self.response(r,unknown=True))
        self.assertEqual((report["stop_reason"],report["new_requests"],report["unknown_cost_calls"]),("unknown_cost",1,1))
        self.assertEqual(report["known_new_cost_usd"],"0")

    def test_malformed_http_json_is_preserved_and_never_counted_as_free(self):
        def broken(request):
            self.sent.append(json.loads(request.content))
            return httpx.Response(200,text='{"usage":{"cost":NaN}}')
        report = self.run_mock(handler=broken)
        self.assertEqual((report["new_requests"],report["stop_reason"]),(1,"unknown_cost"))
        with closing(store.connect(self.db)) as c:
            response = json.loads(c.execute("SELECT response_json FROM workflow_calls").fetchone()[0])
        self.assertIn("NaN",response["error"]["raw_response"])

    def test_duplicate_plan_is_rejected_before_another_paid_request(self):
        self.run_mock()
        before = len(self.sent)
        with self.assertRaisesRegex(ValueError,"already has a run"):
            self.run_mock()
        self.assertEqual(len(self.sent),before)

    def test_stale_metadata_tampered_schedule_and_source_drift_block_execution(self):
        for kind in ("age","schedule","code"):
            with self.subTest(kind=kind):
                plan = deepcopy(self.plan)
                if kind=="age":
                    plan["metadata"]["fetched_at_utc"]="2026-01-01T00:00:00+00:00"
                elif kind=="schedule":
                    plan["schedule"][0]["repetition"]=2
                else:
                    plan["code_sha256"]["mathqa_workflow.py"]="tampered"
                plan["sha256"]=pilot.digest({k:v for k,v in plan.items() if k!="sha256"})
                with self.assertRaises(ValueError):
                    pilot.validate_plan(plan)
        self.dataset.write_bytes(self.dataset.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"changed"):
            pilot.validate_plan(self.plan)

    def test_endpoint_capabilities_prices_and_missing_key_are_validated(self):
        metadata = deepcopy(self.metadata)
        model = next(iter(metadata["models"]))
        metadata["models"][model]["data"]["endpoints"][0]["supported_parameters"]=[]
        with self.assertRaisesRegex(ValueError,"controls"):
            pilot.prepare_plan(metadata,dataset_path=self.dataset)
        with httpx.Client(transport=httpx.MockTransport(self.response)) as client:
            with self.assertRaisesRegex(ValueError,"API key"):
                pilot.run_pilot(self.plan,database_path=self.db,budget_usd=.04,max_requests=36,api_key="",client=client)
            with self.assertRaisesRegex(ValueError,"scope"):
                pilot.run_pilot(self.plan,database_path=self.db,budget_usd=.04,max_requests=37,api_key="mock",client=client)
            with self.assertRaisesRegex(ValueError,"scope"):
                pilot.run_pilot(self.plan,database_path=self.db,budget_usd=.041,max_requests=36,api_key="mock",client=client)
        self.assertFalse(self.db.exists())


if __name__=="__main__":
    unittest.main()
