"""Read-only saved-answer previews: no network, migrations, or paid runner."""

from contextlib import closing, redirect_stdout, redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_batch as batch
import mathqa_verifier_trials as trials


class PreviewTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.db = Path(directory.name) / "legacy.sqlite3"
        self.dataset = Path(directory.name) / "dataset.json"
        self.records = deepcopy(json.loads(batch.DATASET_PATH.read_text(encoding="utf-8"))[:2])
        for record in self.records:
            record["Rationale"] = "REFERENCE_RATIONALE_MUST_NOT_LEAK"
        self.dataset.write_text(json.dumps(self.records), encoding="utf-8")
        questions = [{"id": r["id"], "problem": r["Problem"], "options": r["options"]} for r in self.records]
        batch.initialize_database(self.db)
        root_patch = patch.object(trials, "PROJECT_ROOT", self.dataset.parent)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        with patch.object(batch, "DATASET_PATH", self.dataset), patch.object(batch, "PROJECT_ROOT", self.dataset.parent):
            self.run = batch.create_run(questions, self.db)
        for qi, (question, record) in enumerate(zip(questions, self.records)):
            for mi, model in enumerate(batch.MODELS):
                fields = {"calculation": "Six groups of seven give 6*7=42.", "option": record["correct"],
                          "value": record["parsed_options"][record["correct"]]}
                if qi == 1 and mi == 0:
                    fields["option"] = "none"
                elif qi == 1 and mi == 1:
                    fields["option"] = next(x for x in "abcde" if x != record["correct"])
                answer = json.dumps(fields)
                call = batch.create_call(self.run, question["id"], qi + 1, model, {"model": model}, database_path=self.db)
                failed = qi == 1 and mi == 2
                payload = {"choices": [{"message": {"content": answer}, "finish_reason": "length" if failed else "stop"}]}
                if not failed:
                    payload["usage"] = {"cost": 1}
                batch.finish_call(call, status="failed" if failed else "completed", elapsed_seconds=0.1,
                                  response_payload=payload, response_contract="json-v1", options=question["options"], database_path=self.db)
        batch.set_run_status(self.run, "running", self.db)
        batch.set_run_status(self.run, "completed_with_errors", self.db)

    def preview(self, **kwargs):
        return trials.preview_saved(self.run, database_path=self.db, questions=2, **kwargs)

    def test_preview_has_no_network_or_database_changes_and_counts_only_usable(self):
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        with patch("httpx.Client.send", side_effect=AssertionError("Network forbidden")), patch("httpx.AsyncClient.send", side_effect=AssertionError("Network forbidden")):
            report = self.preview()
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).hexdigest())
        self.assertFalse(report["paid_execution_available"])
        self.assertEqual(report["summary"]["source_attempts"], 6)
        self.assertEqual(report["summary"]["usable_source_answers"], 4)
        self.assertEqual(report["summary"]["unusable_source_answers"], 2)
        self.assertEqual(report["summary"]["natural_max_requests"], 12)
        self.assertEqual(report["summary"]["new_cost_usd"], 0)
        self.assertEqual(report["summary"]["historical_known_solver_cost_usd"], 5)
        self.assertEqual(report["summary"]["historical_unknown_cost_calls"], 1)
        self.assertTrue(all(c["estimated_cost_usd"] is None for c in report["cost_preview"]))
        with closing(sqlite3.connect(self.db)) as c:
            self.assertIsNone(c.execute("SELECT name FROM sqlite_master WHERE name='workflow_runs'").fetchone())

    def test_labels_never_enter_proposed_requests_and_diagnostics_are_separate(self):
        report = self.preview(include_reviewed=True)
        self.assertEqual(report["summary"]["reviewed_diagnostic_cases"], 12)
        self.assertEqual(report["summary"]["diagnostic_max_requests"], 27)
        for source in report["natural_answers"] + report["reviewed_diagnostics"]:
            if not source["usability"]["usable"]:
                self.assertEqual(source["requests"], {})
            for request in source["requests"].values():
                serialized = json.dumps(request)
                self.assertNotIn("REFERENCE_RATIONALE_MUST_NOT_LEAK", serialized)
                supplied = json.loads(request["messages"][1]["content"])
                self.assertEqual(set(supplied), {"question", "options", "solver_proposal"})
        self.assertTrue(all(s["offline_labels"]["reasoning_valid"] is None for s in report["natural_answers"]))

    def test_candidate_subset_and_selection_errors(self):
        report = self.preview(candidates=["deepseek"])
        self.assertEqual(report["summary"]["natural_max_requests"], 4)
        for candidates in ([], ["deepseek", "deepseek"], ["unknown"]):
            with self.assertRaises(ValueError):
                self.preview(candidates=candidates)
        with self.assertRaises(ValueError):
            trials.preview_saved(self.run, database_path=self.db, questions=3)
        with self.assertRaises(ValueError):
            trials.preview_saved(self.run, database_path=self.db, questions=0)

    def test_checksum_and_unfinished_source_guards(self):
        with closing(sqlite3.connect(self.db)) as c, c:
            c.execute("UPDATE runs SET status='interrupted' WHERE run_id=?", (self.run,))
        with self.assertRaisesRegex(ValueError, "finished"):
            self.preview()
        with closing(sqlite3.connect(self.db)) as c, c:
            c.execute("UPDATE runs SET status='completed_with_errors' WHERE run_id=?", (self.run,))
        self.dataset.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.preview()

    def test_missing_source_pair_is_not_silently_omitted(self):
        with closing(sqlite3.connect(self.db)) as c, c:
            call_id = c.execute("SELECT call_id FROM calls WHERE run_id=? LIMIT 1", (self.run,)).fetchone()[0]
            c.execute("DELETE FROM calls WHERE call_id=?", (call_id,))
        with self.assertRaisesRegex(ValueError, "Missing source call"):
            self.preview()

    def test_cli_cannot_run_paid_requests_and_output_cannot_overwrite_source(self):
        with patch.object(sys, "argv", ["preview", "--run"]), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                trials.main()
        self.assertEqual(raised.exception.code, 2)
        before = self.db.read_bytes()
        args = ["preview", "--source-run", self.run, "--questions", "2", "--database", str(self.db), "--output", str(self.db)]
        with patch.object(sys, "argv", args), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                trials.main()
        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(before, self.db.read_bytes())
        output = self.db.parent / "preview.json"
        with patch.object(sys, "argv", args[:-1] + [str(output)]), redirect_stdout(io.StringIO()):
            self.assertEqual(trials.main(), 0)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["summary"]["new_requests_made"], 0)


if __name__ == "__main__":
    unittest.main()
