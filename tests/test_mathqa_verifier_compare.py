"""Paired comparisons, immutable baselines, and paid-call reuse; mocked HTTP only."""

from contextlib import closing
from copy import deepcopy
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_verifier as verifier
import mathqa_verifier_compare as compare
import mathqa_verifier_screen as screen
import mathqa_verifier_trials as trials
import mathqa_workflow_store as store
import test_mathqa_verifier_screen as fixtures


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        # Reuse the disposable-source fixture, without inheriting/repeating its
        # tests or touching the production database.
        self.prepare = fixtures.ScreeningTests.prepare.__get__(self)
        self.payload = fixtures.ScreeningTests.payload.__get__(self)
        fixtures.ScreeningTests.setUp(self)
        self.baseline_plan = self.plan
        report, _ = fixtures.ScreeningTests.run_mock(self, self.payload())
        self.pilot = report["run_id"]
        template = next(iter(self.metadata["models"].values()))
        self.metadata["models"] = {}
        reasoning_models = {}
        for base in verifier.VERIFIER_PROFILES:
            p = verifier.profile(base)
            data = deepcopy(template)
            data["data"]["id"] = p["model"]
            endpoint = data["data"]["endpoints"][0]
            endpoint["tag"] = p["settings"]["provider"]["only"][0]
            endpoint["provider_name"] = "DeepInfra" if base == "deepseek" else "Google AI Studio"
            self.metadata["models"][p["model"]] = data
            reasoning_models[p["model"]] = {"id": p["model"], "supported_parameters": ["reasoning"],
                "reasoning": {"mandatory": False, "supported_efforts": ["minimal", "low"]}}
        self.reasoning_metadata = {"fetched_at_utc": store.now(), "models": reasoning_models}
        self.plan = self.comparison()

    def comparison(self):
        preview = trials.preview_saved(self.source, database_path=self.db, questions=1, candidates=compare.candidates())
        return compare.prepare_comparison(preview, self.metadata, self.review, self.reasoning_metadata,
            database_path=self.db, pilot_run_id=self.pilot, created_at="2026-10-07T00:00:00+00:00")

    def run_comparison(self, *, fail=False, cap=24, fail_at=None):
        requests = []
        def respond(request):
            body = json.loads(request.content)
            requests.append(body)
            proposed = json.loads(body["messages"][1]["content"])["solver_proposal"]
            baseline = body["messages"][0]["content"] == verifier.VERIFIER_PROMPT
            payload = self.payload(accepted=baseline or proposed["calculation"] == "30*29=870", model=body["model"],
                provider="DeepInfra" if body["model"].startswith("deepseek/") else "Google AI Studio")
            if fail or len(requests) == fail_at:
                payload["choices"][0]["finish_reason"] = "length"
            return httpx.Response(200, json=payload)
        with httpx.Client(transport=httpx.MockTransport(respond)) as client:
            report = screen.run_screen(self.plan, database_path=self.db, budget_usd=0.05, max_requests=cap,
                api_key="sk-or-v1-mock_secret", client=client)
        return report, requests

    def test_baseline_snapshots_and_old_plan_validation_are_unchanged(self):
        for base in verifier.VERIFIER_PROFILES:
            self.assertEqual(verifier.profile(base), verifier.VERIFIER_PROFILES[base])
        screen.validate_plan(self.baseline_plan, self.db)

    def test_prompt_only_changes_prompt_and_reasoning_arm_changes_allowance(self):
        q = {"problem": "6*7?", "options": "a)42", "correct": "MUST_NOT_LEAK"}
        fields = {"calculation": "6*7=42", "option": "a", "value": "42", "review": "MUST_NOT_LEAK"}
        for base in verifier.VERIFIER_PROFILES:
            original = verifier.build_request(base, q, fields)
            recompute = verifier.build_request(base + "__recompute", q, fields)
            reasoning = verifier.build_request(base + "__reasoning", q, fields)
            normalized = deepcopy(recompute)
            normalized["messages"][0] = original["messages"][0]
            self.assertEqual(normalized, original)
            self.assertEqual(reasoning["messages"], recompute["messages"])
            self.assertGreater(reasoning["max_tokens"], original["max_tokens"])
            self.assertNotEqual(reasoning["reasoning"], original["reasoning"])
            self.assertNotIn("MUST_NOT_LEAK", json.dumps(reasoning))
            reasoning["provider"]["only"].append("MUTATED")
            self.assertNotIn("MUTATED", verifier.profile(base)["settings"]["provider"]["only"])
        self.assertEqual(verifier.profile("flashlite25__reasoning")["settings"]["reasoning"], {"max_tokens": 512})
        self.assertEqual(verifier.profile("flashlite31__reasoning")["settings"]["reasoning"], {"effort": "low"})
        self.assertEqual(verifier.profile("deepseek__reasoning")["settings"]["reasoning"], {"enabled": True})

    def test_preparation_is_read_only_and_only_exact_requests_are_reused(self):
        before = self.db.read_bytes()
        with patch("httpx.Client.send", side_effect=AssertionError("No network")):
            plan = self.comparison()
            screen.validate_plan(plan, self.db)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(plan["comparison"]["planned_observations"], 27)
        self.assertEqual(plan["comparison"]["reused_observations"], 3)
        self.assertEqual(len(plan["entries"]), 24)
        self.assertTrue(all(e["entry"]["candidate"] == "flashlite25" for e in plan["reused_entries"]))
        self.assertEqual(sum(r["calls"] for r in plan["cost_preview"]["breakdown"]), 24)
        self.assertTrue(all(e["evaluation_group"] == "regression" for e in plan["entries"]))
        self.assertEqual(plan, self.comparison())  # recorded scheduling seed

    def test_changed_request_not_reused_and_changed_verdict_is_not_trusted(self):
        with closing(store.connect(self.db)) as c, c:
            row = c.execute("SELECT call_id,request_json FROM workflow_calls LIMIT 1").fetchone()
            request = json.loads(row["request_json"])
            request["max_tokens"] += 1
            c.execute("UPDATE workflow_calls SET request_json=? WHERE call_id=?", (json.dumps(request), row["call_id"]))
        self.assertEqual(len(self.comparison()["reused_entries"]), 2)
        with closing(store.connect(self.db)) as c, c:
            c.execute("UPDATE workflow_attempts SET verification_status='reject' WHERE verifier_call_id=?", (row["call_id"],))
        with self.assertRaisesRegex(ValueError, "differs"):
            self.comparison()

    def test_cache_drift_blocks_execution_before_new_requests(self):
        with closing(store.connect(self.db)) as c, c:
            cid = self.plan["reused_entries"][0]["call_id"]
            row = c.execute("SELECT response_json FROM workflow_calls WHERE call_id=?", (cid,)).fetchone()
            payload = json.loads(row[0])
            payload["id"] = "changed-response"
            c.execute("UPDATE workflow_calls SET response_json=? WHERE call_id=?", (json.dumps(payload), cid))
        with self.assertRaisesRegex(ValueError, "changed"):
            self.run_comparison()
        with closing(store.connect(self.db)) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM workflow_runs").fetchone()[0], 1)

    def test_new_calls_exclude_reused_cost_and_produce_paired_counts(self):
        report, requests = self.run_comparison()
        self.assertEqual((report["status"], len(requests)), ("completed", 24))
        self.assertAlmostEqual(report["costs"][0]["known_cost_usd"], 0.00024)
        rows = report["comparison"]["quality"]
        baseline = next(r for r in rows if r["candidate"] == "flashlite25" and r["arm"] == "baseline")
        self.assertEqual((baseline["new_calls"], baseline["reused"], baseline["new_known_cost_usd"]), (0, 3, 0))
        pair = next(r for r in report["comparison"]["paired_changes"] if r["candidate"] == "flashlite25" and r["arm"] == "recompute" and r["reference_arm"] == "baseline" and r["evaluation_group"] == "regression")
        self.assertEqual((pair["improved"], pair["both_correct"], pair["worsened"]), (2, 1, 0))
        with closing(store.connect(self.db)) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM workflow_calls").fetchone()[0], 36)  # 12 original + 24 new
            self.assertEqual(c.execute("SELECT COUNT(*) FROM workflow_calls WHERE role='solver'").fetchone()[0], 0)

    def test_truncation_stops_for_review_without_retry(self):
        report, requests = self.run_comparison(fail=True)
        self.assertEqual((len(requests), report["stop_reason"]), (1, "verifier_error_review_settings"))
        self.assertEqual(report["comparison"]["design"]["new_requests"], 24)
        self.assertTrue(any(r["unpaired_or_error"] for r in report["comparison"]["paired_changes"]))

    def test_partial_report_keeps_planned_and_reused_coverage_visible(self):
        report, requests = self.run_comparison(cap=1)
        self.assertEqual((len(requests), report["stop_reason"]), (1, "request_limit"))
        rows = report["comparison"]["quality"]
        self.assertEqual(sum(r["planned"] for r in rows), 27)
        self.assertEqual(sum(r["observed"] for r in rows), 4)
        self.assertEqual(sum(r["reused"] for r in rows), 3)

    def test_reasoning_capability_and_reuse_provenance_are_checked(self):
        missing = deepcopy(self.reasoning_metadata)
        missing["models"][verifier.profile("flashlite31")["model"]]["reasoning"]["supported_efforts"] = ["minimal"]
        with self.assertRaisesRegex(ValueError, "effort"):
            compare.check_reasoning_metadata(missing)
        changed = deepcopy(self.review)
        changed["reviews"][0]["review"]["explanation"] = "Changed label provenance"
        preview = trials.preview_saved(self.source, database_path=self.db, questions=1, candidates=compare.candidates())
        with self.assertRaisesRegex(ValueError, "labels differ"):
            compare.prepare_comparison(preview, self.metadata, changed, self.reasoning_metadata, database_path=self.db, pilot_run_id=self.pilot)

    def test_unknown_labels_are_excluded_and_expansion_stays_separate(self):
        plan = deepcopy(self.plan)
        # Pure reporting check: one case is an uncertain expansion example.
        # Both arms retain the same label; every new verdict is observed.
        cid = plan["reused_entries"][0]["entry"]["case_id"]
        entries = plan["entries"] + [r["entry"] for r in plan["reused_entries"]]
        for entry in entries:
            if entry["case_id"] == cid:
                entry["evaluation_group"] = "expansion"
                entry["labels"]["expected_accept"] = None
        rows = [{"candidate": e["candidate"], "diagnostics_json": json.dumps({"case_id": e["case_id"]}),
                 "verification_status": "accept", "cost_usd": 0.00001} for e in plan["entries"]]
        report = compare.comparison_summary(plan, rows)
        self.assertTrue(any(r["evaluation_group"] == "regression" for r in report["quality"]))
        self.assertTrue(any(r["evaluation_group"] == "expansion" for r in report["quality"]))
        expansion = [r for r in report["paired_changes"] if r["evaluation_group"] == "expansion"]
        self.assertTrue(all(r["paired_labeled_verdicts"] == 0 and r["unknown_label_pairs"] == 1 for r in expansion))

    def test_stale_reasoning_metadata_blocks_live_execution(self):
        plan = deepcopy(self.plan)
        plan["reasoning_metadata"]["fetched_at_utc"] = "2026-01-01T00:00:00+00:00"
        plan["sha256"] = screen.digest({k: v for k, v in plan.items() if k != "sha256"})
        with self.assertRaisesRegex(ValueError, "reasoning metadata"):
            screen.validate_plan(plan, self.db)

    def amendment(self, reuse_ids, excluded=None):
        excluded = ["deepseek__reasoning"] if excluded is None else excluded
        preview = trials.preview_saved(self.source, database_path=self.db, questions=1,
                                       candidates=compare.candidates(excluded))
        return compare.prepare_comparison(preview, self.metadata, self.review, self.reasoning_metadata,
            database_path=self.db, reuse_run_ids=reuse_ids, excluded_candidates=excluded)

    def test_stopped_source_reuses_only_valid_finished_calls_and_runs_remaining(self):
        stopped, _ = self.run_comparison(fail_at=3)
        before = self.db.read_bytes()
        plan = self.amendment([self.pilot, stopped["run_id"]])
        screen.validate_plan(plan, self.db)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(plan["version"], "verifier-comparison-plan-v2")
        self.assertEqual(plan["comparison"]["planned_observations"], 24)
        with closing(store.connect(self.db)) as c:
            successful = {r[0] for r in c.execute("SELECT w.call_id FROM workflow_calls w "
                "JOIN workflow_attempts a USING(attempt_id) JOIN workflow_executions e USING(execution_id) "
                "JOIN workflow_configs f USING(config_id) WHERE e.run_id=? AND w.status='completed' "
                "AND f.name!='deepseek__reasoning'", (stopped["run_id"],))}
        reused_from_stopped = {r["call_id"] for r in plan["reused_entries"] if r["run_id"] == stopped["run_id"]}
        self.assertEqual(successful, reused_from_stopped)
        self.assertEqual(len(plan["entries"]) + len(plan["reused_entries"]), 24)
        self.assertNotIn("deepseek__reasoning", plan["profiles"])
        self.assertTrue(all(e["candidate"] != "deepseek__reasoning" for e in plan["entries"]))
        self.plan = plan
        result, requests = self.run_comparison()
        self.assertEqual((result["status"], len(requests)), ("completed", len(plan["entries"])))
        self.assertAlmostEqual(result["costs"][0]["known_cost_usd"], len(requests) * 0.00001)
        self.assertEqual(sum(r["reused"] for r in result["comparison"]["quality"]), len(plan["reused_entries"]))
        self.assertFalse(any(r["candidate"] == "deepseek" and r["arm"] == "reasoning"
                             for r in result["comparison"]["paired_changes"]))

    def test_false_acceptances_are_reused_without_outcome_selection(self):
        plan = self.amendment([self.pilot])
        wrong = [r for r in plan["reused_entries"] if r["entry"]["labels"]["expected_accept"] is False]
        self.assertEqual(len(wrong), 2)
        self.assertTrue(all(r["verdict"] == "accept" for r in wrong))

    def test_active_or_unfinished_source_is_rejected(self):
        stopped, _ = self.run_comparison(cap=2)
        with closing(store.connect(self.db)) as c, c:
            c.execute("UPDATE workflow_runs SET status='running' WHERE run_id=?", (stopped["run_id"],))
        with self.assertRaisesRegex(ValueError, "finished"):
            self.amendment([self.pilot, stopped["run_id"]])
        with closing(store.connect(self.db)) as c, c:
            c.execute("UPDATE workflow_runs SET status='budget_stopped' WHERE run_id=?", (stopped["run_id"],))
            c.execute("UPDATE workflow_calls SET finished_at_utc=NULL WHERE call_id=(SELECT call_id FROM workflow_calls LIMIT 1)")
        with self.assertRaisesRegex(ValueError, "unfinished"):
            self.amendment([self.pilot, stopped["run_id"]])

    def test_duplicate_sources_and_ambiguous_judgments_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            self.amendment([self.pilot, self.pilot])
        self.plan = self.prepare(created_at="2026-10-07T00:01:00+00:00")
        repeated, _ = fixtures.ScreeningTests.run_mock(self, self.payload())
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            self.amendment([self.pilot, repeated["run_id"]])

    def test_partial_reuse_drift_blocks_before_new_paid_calls(self):
        stopped, _ = self.run_comparison(cap=2)
        plan = self.amendment([self.pilot, stopped["run_id"]])
        reused = next(r for r in plan["reused_entries"] if r["run_id"] == stopped["run_id"])
        with closing(store.connect(self.db)) as c, c:
            c.execute("UPDATE workflow_calls SET cost_usd=0.00002 WHERE call_id=?", (reused["call_id"],))
        self.plan = plan
        with self.assertRaisesRegex(ValueError, "changed"):
            self.run_comparison()

    def test_inconsistent_measurements_are_not_reused(self):
        stopped, _ = self.run_comparison(cap=2)
        plan = self.amendment([self.pilot, stopped["run_id"]])
        reused = next(r for r in plan["reused_entries"] if r["run_id"] == stopped["run_id"])
        with closing(store.connect(self.db)) as c, c:
            c.execute("UPDATE workflow_calls SET reasoning_tokens=output_tokens+1 WHERE call_id=?", (reused["call_id"],))
        amended = self.amendment([self.pilot, stopped["run_id"]])
        self.assertNotIn(reused["call_id"], {r["call_id"] for r in amended["reused_entries"]})
        self.assertEqual(len(amended["entries"]), len(plan["entries"]) + 1)
        with closing(store.connect(self.db)) as c, c:
            c.execute("UPDATE workflow_calls SET reasoning_tokens=0,input_tokens=1000000 WHERE call_id=?", (reused["call_id"],))
        self.assertNotIn(reused["call_id"], {r["call_id"] for r in self.amendment([self.pilot, stopped["run_id"]])["reused_entries"]})

    def test_selected_reasoning_profiles_only_require_their_capabilities(self):
        del self.reasoning_metadata["models"][verifier.profile("deepseek")["model"]]
        screen.validate_plan(self.amendment([self.pilot]), self.db)
        with self.assertRaises(KeyError):
            self.comparison()
        with self.assertRaisesRegex(ValueError, "unique declared"):
            compare.candidates(["unknown"])


if __name__ == "__main__":
    unittest.main()
