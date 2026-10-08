"""Offline screening controls with disposable databases and mocked HTTP only."""

from contextlib import closing, redirect_stderr
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_batch as batch
import mathqa_verifier_preflight as preflight
import mathqa_verifier_screen as screen
import mathqa_verifier_trials as trials
import mathqa_workflow_store as store
from mathqa_verifier import profile


class ScreeningTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.db = self.root / "test.sqlite3"
        self.dataset = self.root / "dataset.json"
        self.review_path = self.root / "reviews.json"
        records = json.loads(batch.DATASET_PATH.read_text(encoding="utf-8"))[:1]
        records[0]["Rationale"] = "SECRET_REFERENCE_MUST_NOT_LEAK"
        self.dataset.write_text(json.dumps(records), encoding="utf-8")
        batch.initialize_database(self.db)
        q = {"id": records[0]["id"], "problem": records[0]["Problem"], "options": records[0]["options"]}
        with patch.object(batch, "DATASET_PATH", self.dataset), patch.object(batch, "PROJECT_ROOT", self.root):
            self.source = batch.create_run([q], self.db)
        reviews = []
        for index, model in enumerate(batch.MODELS):
            option = records[0]["correct"]
            calculation = "30*29=870" if index == 2 else "30*29=380"
            answer = json.dumps({"calculation": calculation, "option": option, "value": "870"})
            call = batch.create_call(self.source, q["id"], 1, model, {"model": model}, database_path=self.db)
            batch.finish_call(call, status="completed", elapsed_seconds=1, response_payload={
                "choices": [{"message": {"content": answer}, "finish_reason": "stop"}], "usage": {"cost": 9}},
                database_path=self.db)
            reviews.append({"source_call_id": call, "question_id": q["id"], "solver_model": model,
                "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(), "labels": {
                    "option_correct": True, "reasoning_valid": index == 2, "expected_accept": index == 2},
                "annotation_uncertainty": False, "review": {"reviewer": "offline test reviewer", "explanation": "Test-only labels."}})
        batch.set_run_status(self.source, "running", self.db)
        batch.set_run_status(self.source, "completed", self.db)
        self.review = {"source_run_id": self.source, "dataset_sha256": hashlib.sha256(self.dataset.read_bytes()).hexdigest(), "reviews": reviews}
        self.review_path.write_text(json.dumps(self.review), encoding="utf-8")
        for target, name, value in ((trials, "PROJECT_ROOT", self.root), (screen, "NATURAL_REVIEW", self.review_path)):
            p = patch.object(target, name, value)
            p.start()
            self.addCleanup(p.stop)
        p = profile("flashlite25")
        endpoint = {"tag": "google-ai-studio", "provider_name": "Google AI Studio", "status": 0,
            "max_completion_tokens": 4096, "supported_parameters": ["temperature", "max_tokens", "reasoning", "response_format"],
            "pricing": {"prompt": "0.0000001", "completion": "0.0000004", "internal_reasoning": "0.0000004"}}
        self.metadata = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(), "models": {
            p["model"]: {"source_url": "https://openrouter.ai/api/v1/models/" + p["model"] + "/endpoints",
                         "data": {"id": p["model"], "endpoints": [endpoint]}}}}
        self.plan = self.prepare()

    def prepare(self, **kwargs):
        preview = trials.preview_saved(self.source, database_path=self.db, questions=1, candidates=["flashlite25"], include_reviewed=True)
        return screen.prepare_plan(preview, self.metadata, self.review, **kwargs)

    def payload(self, accepted=True, cost=0.00001, **updates):
        result = {"id": "test", "model": profile("flashlite25")["model"], "provider": "Google AI Studio",
            "choices": [{"message": {"content": json.dumps({"accepted": accepted})}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 300, "completion_tokens": 20, "completion_tokens_details": {"reasoning_tokens": 5}, "cost": cost}}
        result.update(updates)
        return result

    def run_mock(self, payloads, **kwargs):
        requests = []
        def respond(request):
            requests.append(json.loads(request.content))
            value = payloads(len(requests)) if callable(payloads) else payloads
            if isinstance(value, BaseException):
                raise value
            return httpx.Response(200, json=value)
        with httpx.Client(transport=httpx.MockTransport(respond)) as client:
            report = screen.run_screen(self.plan, database_path=self.db, budget_usd=kwargs.pop("budget_usd", 0.05),
                max_requests=kwargs.pop("max_requests", 12), api_key="sk-or-v1-test_secret", client=client, **kwargs)
        return report, requests

    def test_preparation_is_read_only_and_requests_do_not_leak_labels(self):
        before = self.db.read_bytes()
        with patch("httpx.Client.send", side_effect=AssertionError("No network")), patch("urllib.request.urlopen", side_effect=AssertionError("No network")):
            plan = self.prepare()
        self.assertEqual(before, self.db.read_bytes())
        self.assertEqual(len(plan["entries"]), 12)
        for entry in plan["entries"]:
            user = json.loads(entry["request"]["messages"][1]["content"])
            self.assertEqual(set(user), {"question", "options", "solver_proposal"})
            self.assertNotIn("SECRET_REFERENCE", json.dumps(entry["request"]))
            self.assertNotIn("test reviewer", json.dumps(entry["request"]))
            self.assertFalse(entry["request"]["provider"]["allow_fallbacks"])
            self.assertEqual(entry["request"]["provider"]["max_price"], {"prompt": 0.1, "completion": 0.4, "request": 0})

    def test_serial_execution_preserves_billing_and_separate_quality(self):
        report, requests = self.run_mock(self.payload())
        self.assertEqual(report["status"], "completed")
        self.assertEqual(len(requests), 12)
        self.assertEqual(report["costs"][0]["requests"], 12)
        self.assertAlmostEqual(report["costs"][0]["known_cost_usd"], 0.00012)
        natural = next(row for row in report["quality"] if row["group"] == "natural")
        self.assertEqual((natural["false_acceptances"], natural["invalid_solution_denominator"]), (2, 2))
        self.assertEqual(natural["accepted_wrong_options"], 0)  # lucky options still invalid reasoning
        synthetic = next(row for row in report["quality"] if row["group"] == "synthetic")
        self.assertEqual(synthetic["unknown_label_valid_verdicts"], 1)
        with closing(store.connect(self.db)) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM workflow_calls WHERE role='solver'").fetchone()[0], 0)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM workflow_attempts WHERE offline_source_json IS NOT NULL").fetchone()[0], 9)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM workflow_grades WHERE workflow_score IS NOT NULL").fetchone()[0], 0)
            self.assertEqual(c.execute("SELECT output_tokens,reasoning_tokens FROM workflow_calls LIMIT 1").fetchone()[:], (20, 5))
            serialized = json.dumps([tuple(r) for r in c.execute("SELECT * FROM workflow_calls")])
            self.assertNotIn("test_secret", serialized)

    def test_unknown_cost_stops_after_one_and_remains_unknown(self):
        report, requests = self.run_mock(self.payload(cost=None))
        self.assertEqual((len(requests), report["stop_reason"]), (1, "unknown_cost"))
        self.assertEqual(report["costs"][0]["unknown_cost_calls"], 1)

    def test_bad_measurements_are_retained_without_counting_as_zero(self):
        report, requests = self.run_mock(self.payload(usage={"cost": "0.001", "prompt_tokens": -1, "completion_tokens": True}))
        self.assertEqual((len(requests), report["stop_reason"]), (1, "unknown_cost"))
        with closing(store.connect(self.db)) as c:
            row = c.execute("SELECT response_json,input_tokens,output_tokens,cost_usd FROM workflow_calls").fetchone()
        self.assertEqual(json.loads(row[0])["usage"]["cost"], "0.001")
        self.assertEqual(row[1:], (None, None, None))

    def test_budgets_reserve_before_request_and_limit_request_count(self):
        report, requests = self.run_mock(self.payload(), budget_usd=0.00000001)
        self.assertEqual((requests, report["status"], report["stop_reason"]), ([], "budget_stopped", "spending_limit"))
        self.assertEqual(report["costs"], [])

    def test_max_requests_and_same_plan_rerun_guard(self):
        report, requests = self.run_mock(self.payload(), max_requests=2)
        self.assertEqual((len(requests), report["stop_reason"]), (2, "request_limit"))
        with self.assertRaisesRegex(ValueError, "already has a run"):
            self.run_mock(self.payload())

    def test_reported_cost_over_reservation_stops_scheduling(self):
        report, requests = self.run_mock(self.payload(cost=0.02))
        self.assertEqual((len(requests), report["stop_reason"]), (1, "reservation_exceeded"))
        self.assertEqual(report["costs"][0]["known_cost_usd"], 0.02)

    def test_token_overrun_stops_even_with_small_cost(self):
        payload = self.payload()
        payload["usage"]["completion_tokens"] = 257
        report, requests = self.run_mock(payload)
        self.assertEqual((len(requests), report["stop_reason"]), (1, "reservation_exceeded"))

    def test_provider_drift_stops_scheduling(self):
        report, requests = self.run_mock(self.payload(provider="Unexpected"))
        self.assertEqual((len(requests), report["stop_reason"]), (1, "provider_or_model_mismatch"))
        self.assertEqual(report["quality"][0]["valid_verdicts"], 0)

    def test_reasoning_cost_is_counted_once_and_prices_use_million_units(self):
        entry = self.plan["entries"][0]
        cost = preflight.request_cost(entry["request"], entry["endpoint"], input_tokens=1000, output_tokens=100)
        self.assertEqual(str(cost), "0.0001400")
        self.assertEqual(entry["request"]["provider"]["max_price"]["completion"], 0.4)

    def test_inconsistent_reasoning_measurements_stop(self):
        payload = self.payload()
        payload["usage"]["completion_tokens_details"]["reasoning_tokens"] = 21
        report, requests = self.run_mock(payload)
        self.assertEqual((len(requests), report["stop_reason"]), (1, "inconsistent_reasoning_usage"))

    def test_malformed_verdicts_are_errors_not_rejections(self):
        payload = self.payload(choices=[{"message": {"content": '{"accepted": "false"}'}, "finish_reason": "stop"}])
        report, requests = self.run_mock(payload, max_requests=1)
        natural = report["quality"][0]
        self.assertEqual(natural["technical_or_format_errors"], 1)
        self.assertEqual(natural["invalid_solution_denominator"], 0)
        self.assertEqual(natural["false_rejections"], 0)

    def test_transport_failure_and_interrupt_never_retry(self):
        report, requests = self.run_mock(httpx.ReadTimeout("test"))
        self.assertEqual((len(requests), report["stop_reason"]), (1, "unknown_cost"))
        self.assertEqual(report["quality"][0]["technical_or_format_errors"], 1)

    def test_interrupt_is_durable_and_stops(self):
        report, requests = self.run_mock(KeyboardInterrupt())
        self.assertEqual((len(requests), report["status"]), (1, "interrupted"))
        self.assertEqual(report["costs"][0]["unknown_cost_calls"], 1)
        with closing(store.connect(self.db)) as c:
            self.assertEqual(c.execute("SELECT status FROM workflow_calls").fetchone()[0], "interrupted")

    def test_stale_metadata_and_changed_prompt_are_rejected_before_calls(self):
        stale = deepcopy(self.metadata)
        stale["fetched_at_utc"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        preview = trials.preview_saved(self.source, database_path=self.db, questions=1, candidates=["flashlite25"], include_reviewed=True)
        old = screen.prepare_plan(preview, stale, self.review)
        with self.assertRaisesRegex(ValueError, "24-hour"):
            screen.validate_plan(old, self.db)
        edited = deepcopy(self.plan)
        edited["entries"][0]["request"]["messages"][1]["content"] += " LEAKED KEY"
        edited["sha256"] = screen.digest({k: v for k, v in edited.items() if k != "sha256"})
        with self.assertRaisesRegex(ValueError, "changed"):
            screen.validate_plan(edited, self.db)

    def test_changed_source_review_and_missing_controls_block_preflight(self):
        changed = deepcopy(self.review)
        changed["reviews"][0]["answer_sha256"] = "bad"
        preview = trials.preview_saved(self.source, database_path=self.db, questions=1, candidates=["flashlite25"])
        with self.assertRaisesRegex(ValueError, "changed"):
            screen.prepare_plan(preview, self.metadata, changed)
        metadata = deepcopy(self.metadata)
        metadata["models"][profile("flashlite25")["model"]]["data"]["endpoints"][0]["supported_parameters"] = ["max_tokens"]
        with self.assertRaisesRegex(ValueError, "controls"):
            preflight.select_endpoint(metadata, "flashlite25")

    def test_caps_required_and_no_key_read_on_offline_cli(self):
        with patch.object(sys, "argv", ["screen", "--run", "--plan", "unused.json"]), redirect_stderr(io.StringIO()), patch.object(screen, "load_dotenv", side_effect=AssertionError("No key read")):
            with self.assertRaises(SystemExit):
                screen.main()
        for bad in (0, float("nan"), float("inf"), -1, True):
            with self.assertRaises(ValueError):
                self.run_mock(self.payload(), budget_usd=bad)
        with closing(sqlite3.connect(self.db)) as c:
            self.assertIsNone(c.execute("SELECT name FROM sqlite_master WHERE name='workflow_runs'").fetchone())

    def test_offline_fixture_source_cannot_be_duplicated_as_solver_call(self):
        store.migrate(self.db)
        run = store.create_run("verifier_screen", self.dataset, self.review["dataset_sha256"], ["fixture"], {}, database_path=self.db)
        config = store.create_config(run, "test", {}, database_path=self.db)
        execution = store.create_execution(run, config, {"id": "fixture", "problem": "1+1?", "options": "a)2"}, database_path=self.db)
        attempt = store.create_attempt(execution, 1, "offline/synthetic", offline_source={"status": "completed", "finish_reason": "stop"}, database_path=self.db)
        with self.assertRaises(ValueError):
            store.create_call(attempt, "solver", "offline/synthetic", {}, database_path=self.db)
        with closing(store.connect(self.db)) as c, c:
            source_call = self.review["reviews"][0]["source_call_id"]
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("UPDATE workflow_attempts SET historical_solver_call_id=? WHERE attempt_id=?", (source_call, attempt))


if __name__ == "__main__":
    unittest.main()
