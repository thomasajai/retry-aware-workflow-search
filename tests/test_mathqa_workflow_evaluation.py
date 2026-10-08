"""Evaluation design/metrics checks using disposable storage and simulated calls."""

from collections import Counter
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import mathqa_workflow_evaluation as evaluation
import mathqa_workflow_pilot as pilot
import mathqa_workflow as workflow
import mathqa_workflow_store as store


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db = self.root/"db.sqlite3"
        self.dataset = self.root/"dataset.json"
        self.records = json.loads(pilot.DATASET_PATH.read_bytes())
        for r in self.records:
            r["Rationale"] = "SECRET_DATASET_REASONING"
        self.dataset.write_text(json.dumps(self.records),encoding="utf-8")
        sample = workflow.configuration(pilot.SEQUENCES[0])
        models = {}
        for p in sample["solvers"]+[sample["verifier"]]:
            settings = p.get("body_settings",p.get("settings"))
            models[p["model"]] = {"data":{"id":p["model"],"endpoints":[{
                "tag":settings["provider"]["only"][0],"provider_name":"Offline fixture","status":0,
                "pricing":{"prompt":"0.0000001","completion":"0.0000004"},"max_completion_tokens":4096,
                "supported_parameters":["temperature","max_tokens","reasoning","response_format","top_p","top_k"]}]}}
        self.metadata = {"fetched_at_utc":datetime.now(timezone.utc).isoformat(),"models":models,
            "catalog":{"models":{sample["verifier"]["model"]:{"id":sample["verifier"]["model"],
            "supported_parameters":["reasoning"],"reasoning":{"mandatory":False}}}}}
        self.exposure = {"as_of_utc":datetime.now(timezone.utc).isoformat(),"database":str(self.db),
            "legacy_question_ids":[r["id"] for r in self.records[:100]],"workflow_question_ids":list(pilot.QUESTION_IDS)}
        self.plan = evaluation.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset)
        self.sent = []

    def response(self, request, *, unknown=False, accept=True):
        body = json.loads(request.content)
        self.sent.append(body)
        if body["messages"][0]["role"]=="system":
            answer = {"accepted":accept}
        else:
            record = next(r for r in self.records if r["Problem"] in body["messages"][0]["content"])
            answer = {"calculation":"controlled simulation","option":record["correct"],"value":"controlled"}
        return httpx.Response(200,json={"model":body["model"],"provider":"Offline fixture","id":"mock",
            "choices":[{"message":{"content":json.dumps(answer)},"finish_reason":"stop"}],
            "usage":{"prompt_tokens":100,"completion_tokens":20,"completion_tokens_details":{"reasoning_tokens":0},
                     "cost":None if unknown else .00001}})

    def run_mock(self, *, max_requests=3, handler=None, budget=None):
        with httpx.Client(transport=httpx.MockTransport(handler or self.response)) as client:
            return evaluation.run_evaluation(self.plan,database_path=self.db,api_key="mock_secret",client=client,
                max_requests=max_requests,budget_usd=budget or self.plan["execution_policy"]["maximum_budget_usd"])

    def test_frozen_selection_full_cross_product_and_equal_initial_model_exposure(self):
        with patch("httpx.Client.send",side_effect=AssertionError("No generation")):
            evaluation.validate_plan(self.plan)
        self.assertFalse(self.db.exists())
        self.assertEqual((len(self.plan["questions"]),len(self.plan["configurations"]),len(self.plan["schedule"])),(20,27,540))
        self.assertEqual(self.plan["cost_preview"]["maximum_calls"],3240)
        self.assertEqual(self.plan["cost_preview"]["expected_calls"],2160)
        self.assertEqual(sum(r["maximum_calls"] for r in self.plan["cost_preview"]["breakdown"]),3240)
        ids = [q["id"] for q in self.plan["questions"]]
        self.assertFalse(set(ids)&set(pilot.QUESTION_IDS))
        self.assertFalse(set(ids)&set(self.plan["split"]["reserved_held_out_ids"]))
        for q in ids:
            items = [r for r in self.plan["schedule"] if r["question_id"]==q]
            self.assertEqual(len({r["configuration"] for r in items}),27)
            self.assertEqual(Counter(self.plan["configurations"][r["configuration"]]["solver_sequence"][0] for r in items),
                             {"qwen25":9,"qwen3":9,"deepseek":9})
        same = evaluation.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset,created_at=self.plan["created_at_utc"])
        self.assertEqual(self.plan,same)

    def test_split_rejects_recorded_held_out_exposure_and_invalid_datasets(self):
        exposure = deepcopy(self.exposure)
        exposure["workflow_question_ids"].append(self.records[100]["id"])
        with self.assertRaisesRegex(ValueError,"exposure"):
            evaluation.prepare_plan(self.metadata,exposure,dataset_path=self.dataset)
        self.records[-1]["id"] = self.records[0]["id"]
        self.dataset.write_text(json.dumps(self.records),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"unique"):
            evaluation.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset)

    def test_readonly_exposure_inventory_does_not_modify_database(self):
        store.migrate(self.db)
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        snapshot = evaluation.exposure_snapshot(self.db)
        self.assertEqual(snapshot["legacy_question_ids"],[])
        self.assertEqual(before,hashlib.sha256(self.db.read_bytes()).hexdigest())

    def test_partial_run_has_no_ranking_or_imputed_config_scores(self):
        report = self.run_mock()
        self.assertEqual((report["new_requests"],report["scored_executions"]),(3,1))
        self.assertFalse(report["complete_coverage"])
        self.assertIsNone(report["ranking"])
        self.assertIsNone(report["accuracy_cost_frontier"])
        self.assertEqual(len(report["configurations"]),27)
        self.assertEqual(sum(r["scored"] for r in report["configurations"]),1)
        self.assertTrue(all(r["mean_cost_usd_per_planned_execution"] is None for r in report["configurations"]))
        self.assertEqual(sum(r["scored_first_slot_calls"] for r in report["one_attempt_baselines"]),1)
        for request in self.sent:
            self.assertNotIn("SECRET_DATASET_REASONING",json.dumps(request))
            self.assertEqual(request["provider"]["max_price"],self.plan["price_limits"][request["model"]])

    def test_complete_summary_baselines_and_paired_question_intervals_without_extra_calls(self):
        # Persist complete controlled observations directly: analysis must not call HTTP.
        store.migrate(self.db)
        run = store.create_run("sequence_evaluation",str(self.dataset),self.plan["dataset"]["sha256"],
            [q["id"] for q in self.plan["questions"]],{"plan":self.plan},database_path=self.db,
            budget_usd=self.plan["execution_policy"]["maximum_budget_usd"],max_requests=3240,plan_sha256=self.plan["sha256"])
        ids = {name:store.create_config(run,name,c,database_path=self.db) for name,c in self.plan["configurations"].items()}
        from mathqa_workflow_grading import grade_execution
        records = {r["id"]:r for r in self.records}
        with closing(store.connect(self.db)) as c,c:
            c.execute("UPDATE workflow_runs SET started_at_utc=? WHERE run_id=?",(store.now(),run))
        for item in self.plan["schedule"]:
            config = self.plan["configurations"][item["configuration"]]
            q = next(q for q in self.plan["questions"] if q["id"]==item["question_id"])
            execution = store.create_execution(run,ids[item["configuration"]],q,database_path=self.db)
            model = config["solvers"][0]["model"]
            attempt = store.create_attempt(execution,1,model,database_path=self.db)
            call = store.create_call(attempt,"solver",model,workflow.solver_request(config["solvers"][0],q),database_path=self.db)
            # Qwen2.5 is intentionally wrong to make paired metrics nontrivial.
            correct = records[q["id"]]["correct"]
            option = next(o for o in "abcde" if o!=correct) if config["solver_sequence"][0]=="qwen25" else correct
            fields = {"calculation":"controlled simulation","option":option,"value":"controlled"}
            payload = {"model":model,"provider":"Offline fixture","choices":[{"message":{"content":json.dumps(fields)},"finish_reason":"stop"}],
                "usage":{"prompt_tokens":100,"completion_tokens":20,"cost":.00001}}
            store.finish_call(call,status="completed",payload=payload,elapsed_seconds=1,database_path=self.db)
            store.record_usability(attempt,{"usable":True,"fields":fields,"diagnostics":{}},database_path=self.db)
            verifier = store.create_call(attempt,"verifier",config["verifier"]["model"],{},database_path=self.db)
            verdict = {"model":config["verifier"]["model"],"provider":"Offline fixture",
                "choices":[{"message":{"content":'{"accepted":true}'},"finish_reason":"stop"}],
                "usage":{"prompt_tokens":100,"completion_tokens":20,"cost":.00001}}
            store.finish_call(verifier,status="completed",payload=verdict,elapsed_seconds=1,database_path=self.db)
            store.record_verification(attempt,"accept",database_path=self.db)
            store.finish_execution(execution,"accepted","controlled",1,accepted_attempt_id=attempt,database_path=self.db)
            grade_execution(execution,database_path=self.db)
        with closing(store.connect(self.db)) as c,c:
            c.execute("UPDATE workflow_runs SET status='completed',finished_at_utc=? WHERE run_id=?",(store.now(),run))
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        with patch("httpx.Client.send",side_effect=AssertionError("No extra baseline calls")):
            report = evaluation.evaluation_summary(run,database_path=self.db)
        self.assertEqual(before,hashlib.sha256(self.db.read_bytes()).hexdigest())
        self.assertTrue(report["complete_coverage"])
        self.assertEqual(report["score_total"],360)
        self.assertEqual(len(report["ranking"]),27)
        self.assertEqual(len(report["accuracy_cost_frontier"]),18)
        top_interval = report["ranking"][0]["answer_accuracy_wilson_95_interval"]
        self.assertLess(top_interval[0],1)
        self.assertAlmostEqual(top_interval[1],1)
        self.assertEqual({r["raw_solver_accuracy"] for r in report["one_attempt_baselines"]},{0,1})
        self.assertTrue(all(r["scored_first_slot_calls"]==180 for r in report["one_attempt_baselines"]))
        self.assertEqual(len(report["paired_differences"]),27)
        wrong = next(r for r in report["paired_differences"] if r["configuration"]=="qwen25-qwen25-qwen25")
        self.assertEqual(wrong["question_bootstrap_95_interval"],[1,1])

    def test_unknown_cost_duplicate_plan_budget_and_request_guards(self):
        report = self.run_mock(handler=lambda r:self.response(r,unknown=True))
        self.assertEqual((report["new_requests"],report["unknown_cost_calls"]),(1,1))
        self.assertIsNone(report["ranking"])
        with self.assertRaisesRegex(ValueError,"already has a run"):
            self.run_mock()
        self.assertEqual(len(self.sent),1)
        with self.assertRaisesRegex(ValueError,"scope"):
            self.run_mock(max_requests=3241)
        with self.assertRaisesRegex(ValueError,"scope"):
            self.run_mock(budget=self.plan["execution_policy"]["maximum_budget_usd"]+.01)

    def test_upstream_429_without_usage_exports_partial_report_with_null_fields(self):
        def overloaded(request):
            self.sent.append(json.loads(request.content))
            return httpx.Response(429,json={"error":{"code":429,"message":"Provider returned error",
                "metadata":{"provider_error_code":"engine_overloaded","limit_source":"upstream_provider_shared_pool"}}})
        report = self.run_mock(handler=overloaded)
        self.assertEqual((report["status"],report["stop_reason"],report["new_requests"]),("budget_stopped","unknown_cost",1))
        self.assertEqual(report["known_new_cost_usd"],"0")
        self.assertEqual(report["unknown_cost_calls"],1)
        self.assertEqual(report["repeat_option_value_after_retry"],{"usable_retries":0,"repeats_of_any_prior_answer":0})
        self.assertIsNone(report["ranking"])
        with closing(store.connect(self.db)) as c:
            row = c.execute('SELECT usable,parsed_fields_json FROM workflow_attempts').fetchone()
        self.assertEqual(row["usable"],0)
        self.assertEqual(row["parsed_fields_json"],"null")

    def test_live_adapter_recovery_repeated_answers_and_distinct_verified_baseline(self):
        # Smaller disposable plan exercises all 27 triples and actual mocked graph calls.
        with patch.object(evaluation,"QUESTION_COUNT",1):
            self.plan = evaluation.prepare_plan(self.metadata,self.exposure,dataset_path=self.dataset)
            report = self.run_mock(max_requests=162,handler=lambda r:self.response(r,accept=len(self.sent)%4==3))
        self.assertTrue(report["complete_coverage"])
        self.assertEqual((report["score_total"],report["new_requests"]),(27,108))
        self.assertEqual(report["recovery_after_first_rejection"],{"finished_executions":27,"correct_final":27})
        self.assertEqual(report["repeat_option_value_after_retry"],{"usable_retries":27,"repeats_of_any_prior_answer":27})
        self.assertTrue(all(r["raw_solver_accuracy"]==1 and r["one_attempt_verified_accuracy"]==0 for r in report["one_attempt_baselines"]))
        self.assertTrue(all(r["mean_one_attempt_verified_cost_usd"]==.00002 for r in report["one_attempt_baselines"]))

    def test_tampered_schedule_sources_stale_prices_and_dataset_changes_rejected(self):
        for kind in ("schedule","code","age"):
            plan = deepcopy(self.plan)
            if kind=="schedule":
                plan["schedule"].pop()
            elif kind=="code":
                plan["code_sha256"]["mathqa_workflow_evaluation.py"]="wrong"
            else:
                plan["metadata"]["fetched_at_utc"]="2026-01-01T00:00:00+00:00"
            plan["sha256"] = pilot.digest({k:v for k,v in plan.items() if k!="sha256"})
            with self.assertRaises(ValueError):
                evaluation.validate_plan(plan)
        self.dataset.write_bytes(self.dataset.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"changed"):
            evaluation.validate_plan(self.plan)

    def test_held_out_exposure_changed_since_preparation_blocks_before_calls(self):
        store.migrate(self.db)
        run = store.create_run("sequence_evaluation",str(self.dataset),self.plan["dataset"]["sha256"],[self.records[100]["id"]],{},database_path=self.db)
        config = store.create_config(run,"prior",{},database_path=self.db)
        r = self.records[100]
        store.create_execution(run,config,{"id":r["id"],"problem":r["Problem"],"options":r["options"]},database_path=self.db)
        with self.assertRaisesRegex(ValueError,"exposure changed"):
            self.run_mock()
        self.assertEqual(self.sent,[])


if __name__=="__main__":
    unittest.main()
