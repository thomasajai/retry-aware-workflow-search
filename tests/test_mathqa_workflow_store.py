"""Offline migration, provenance, measurement, and execution identity checks."""

from contextlib import closing
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_batch as batch
import mathqa_workflow_store as store
from mathqa_verifier import extract_usable


def fingerprint(path, *, legacy_only=False):
    with closing(sqlite3.connect(path)) as c:
        tables = sorted(r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        if legacy_only:
            tables = [t for t in tables if not t.startswith("workflow_") and t != "schema_migrations"]
        return {t: c.execute(f'SELECT * FROM "{t}" ORDER BY rowid').fetchall() for t in tables}


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "test.sqlite3"

    def test_fresh_schema_and_noop_rerun(self):
        result = store.migrate(self.db)
        self.assertEqual(result["applied"], ["001_workflow.sql", "002_screening.sql", "003_transport.sql"])
        self.assertIsNone(result["backup_path"])
        before = fingerprint(self.db)
        self.assertEqual(store.migrate(self.db), {"applied": [], "backup_path": None})
        self.assertEqual(before, fingerprint(self.db))
        with closing(store.connect(self.db)) as c:
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(c.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_upgrade_backs_up_and_preserves_every_legacy_row(self):
        batch.initialize_database(self.db)
        questions = batch.load_questions(1)
        run = batch.create_run(questions, self.db)
        call = batch.create_call(run, questions[0]["id"], 1, batch.MODELS[0], {"model": batch.MODELS[0]}, database_path=self.db)
        batch.finish_call(call, status="failed", elapsed_seconds=0.2, error_type="SyntheticFailure", database_path=self.db)
        before = fingerprint(self.db)
        result = store.migrate(self.db)
        self.assertTrue(Path(result["backup_path"]).exists())
        self.assertEqual(before, fingerprint(result["backup_path"]))
        self.assertEqual(before, fingerprint(self.db, legacy_only=True))
        self.assertEqual(len(list((self.db.parent / "backups").glob("*.sqlite3"))), 1)
        store.migrate(self.db)
        self.assertEqual(len(list((self.db.parent / "backups").glob("*.sqlite3"))), 1)

    def test_changed_applied_migration_is_rejected(self):
        store.migrate(self.db)
        copied = Path(self.directory.name) / "migrations"
        shutil.copytree(store.MIGRATIONS, copied)
        with (copied / "001_workflow.sql").open("a") as f:
            f.write("\n-- changed\n")
        before = fingerprint(self.db)
        with self.assertRaisesRegex(ValueError, "changed"):
            store.migrate(self.db, migration_dir=copied)
        self.assertEqual(before, fingerprint(self.db))

    def test_invalid_migration_rolls_back_all_workflow_schema_changes(self):
        batch.initialize_database(self.db)
        before = fingerprint(self.db)
        copied = Path(self.directory.name) / "migrations"
        shutil.copytree(store.MIGRATIONS, copied)
        (copied / "004_broken.sql").write_text("CREATE TABLE not_committed (id INTEGER);\nINVALID SQL;\n", encoding="utf-8")
        with self.assertRaises(sqlite3.Error):
            store.migrate(self.db, migration_dir=copied)
        self.assertEqual(before, fingerprint(self.db))


class StorageTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.db = Path(directory.name) / "test.sqlite3"
        store.migrate(self.db)
        self.run = store.create_run("sequence_evaluation", "dataset.json", "checksum", ["q"], {}, database_path=self.db)
        self.snapshot = {"solver_sequence": ["m1", "m2", "m3"], "verifier": {"model": "v", "temperature": 0}}
        self.config = store.create_config(self.run, "sequence", self.snapshot, database_path=self.db)
        self.question = {"id": "q", "problem": "6 times 7?", "options": "a) 40, b) 42", "correct": "b", "Rationale": "OFFLINE_ONLY"}

    def execution(self, *, config=None, repetition=1):
        return store.create_execution(self.run, config or self.config, self.question, repetition=repetition, database_path=self.db)

    def source(self, execution, position=1, *, usable=True):
        attempt = store.create_attempt(execution, position, f"m{position}", database_path=self.db)
        call = store.create_call(attempt, "solver", f"m{position}", {"model": f"m{position}"}, database_path=self.db)
        answer = '{"calculation":"6*7=42","option":"b","value":"42"}' if usable else "unparseable"
        store.finish_call(call, status="completed", elapsed_seconds=0.1,
                          payload={"choices": [{"message": {"content": answer}, "finish_reason": "stop"}]}, database_path=self.db)
        store.record_usability(attempt, extract_usable(answer, "json-v1"), database_path=self.db)
        return attempt, call

    def verify(self, attempt, accepted=True):
        call = store.create_call(attempt, "verifier", "v", {"model": "v"}, database_path=self.db)
        store.finish_call(call, status="completed", elapsed_seconds=0.2,
                          payload={"choices": [{"message": {"content": json.dumps({"accepted": accepted})}, "finish_reason": "stop"}]}, database_path=self.db)
        store.record_verification(attempt, "accept" if accepted else "reject", database_path=self.db)
        return call

    def test_configuration_identity_repetitions_and_frozen_snapshot(self):
        original = deepcopy(self.snapshot)
        self.snapshot["verifier"]["temperature"] = 0.9
        other = store.create_config(self.run, "other-sequence", original, database_path=self.db)
        first, second = self.execution(), self.execution(config=other)
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, self.execution(repetition=2))
        with self.assertRaises(sqlite3.IntegrityError):
            self.execution()
        with closing(store.connect(self.db)) as c:
            snapshot = c.execute("SELECT snapshot_json,snapshot_sha256 FROM workflow_configs WHERE config_id=?", (self.config,)).fetchone()
            self.assertEqual(json.loads(snapshot[0]), original)
            self.assertEqual(hashlib.sha256(snapshot[0].encode()).hexdigest(), snapshot[1])
            runtime = c.execute("SELECT question_json FROM workflow_executions WHERE execution_id=?", (first,)).fetchone()[0]
            self.assertNotIn("OFFLINE_ONLY", runtime)
            self.assertEqual(set(json.loads(runtime)), {"id", "problem", "options"})

    def test_cross_run_config_and_unselected_question_are_rejected(self):
        other = store.create_run("sequence_evaluation", "x", "checksum", ["q"], {}, database_path=self.db)
        with self.assertRaises(sqlite3.IntegrityError):
            store.create_execution(other, self.config, self.question, database_path=self.db)
        with self.assertRaises(ValueError):
            store.create_execution(self.run, self.config, {**self.question, "id": "unselected"}, database_path=self.db)

    def test_call_links_measurements_missing_cost_and_credentials(self):
        execution = self.execution()
        attempt = store.create_attempt(execution, 1, "m1", database_path=self.db)
        request = {"model": "m1", "headers": {"Authorization": "Bearer private"}, "api_key": "private", "nested": ["sk-or-v1-fake_test_secret"]}
        call = store.create_call(attempt, "solver", "m1", request, database_path=self.db)
        with self.assertRaises(sqlite3.IntegrityError):
            store.create_call(attempt, "solver", "m1", request, database_path=self.db)
        store.finish_call(call, status="failed", elapsed_seconds=0.4, error_message="sk-or-v1-fake_test_secret", database_path=self.db)
        with self.assertRaises(ValueError):
            store.finish_call(call, status="failed", elapsed_seconds=0.5, database_path=self.db)
        with closing(store.connect(self.db)) as c:
            row = dict(c.execute("SELECT * FROM workflow_calls WHERE call_id=?", (call,)).fetchone())
            self.assertNotIn("private", row["request_json"])
            self.assertNotIn("fake_test_secret", row["request_json"] + row["error_message"])
            self.assertIsNone(row["cost_usd"])
            self.assertIsNone(row["input_tokens"])
        self.assertEqual(store.cost_summary(self.run, database_path=self.db), [
            {"role": "solver", "requests": 1, "known_cost_usd": 0, "unknown_cost_calls": 1}])

    def test_reasoning_tokens_are_preserved_without_double_counting_cost(self):
        execution = self.execution()
        attempt = store.create_attempt(execution, 1, "m1", database_path=self.db)
        call = store.create_call(attempt, "solver", "m1", {}, database_path=self.db)
        store.finish_call(call, status="completed", elapsed_seconds=0.4,
                          payload={"provider": "test", "usage": {"prompt_tokens": 20, "completion_tokens": 15,
                          "completion_tokens_details": {"reasoning_tokens": 10}, "cost": 0.002}}, database_path=self.db)
        with closing(store.connect(self.db)) as c:
            row = c.execute("SELECT output_tokens,reasoning_tokens,provider,cost_usd FROM workflow_calls WHERE call_id=?", (call,)).fetchone()
            self.assertEqual(tuple(row), (15, 10, "test", 0.002))

    def test_unusable_source_skips_verifier_and_positions_are_bounded(self):
        execution = self.execution()
        with self.assertRaises(ValueError):
            store.create_attempt(execution, 2, "m2", database_path=self.db)
        for position in range(1, 4):
            attempt, _ = self.source(execution, position, usable=False)
            with self.assertRaises(ValueError):
                store.create_call(attempt, "verifier", "v", {}, database_path=self.db)
        with self.assertRaises(sqlite3.IntegrityError):
            store.create_attempt(execution, 4, "m4", database_path=self.db)
        store.finish_execution(execution, "exhausted", "unusable", 0.3, database_path=self.db)
        store.record_grade(execution, "v1", "checksum", "independent key", option_correct=True, workflow_score=0, database_path=self.db)
        with self.assertRaises(ValueError):
            store.record_grade(execution, "v2", "checksum", "key", option_correct=True, workflow_score=1, database_path=self.db)

    def test_acceptance_is_separate_from_key_and_reasoning_grades(self):
        execution = self.execution()
        attempt, _ = self.source(execution)
        self.verify(attempt)
        store.finish_execution(execution, "accepted", "verifier accepted", 0.3, accepted_attempt_id=attempt, database_path=self.db)
        store.record_grade(execution, "option-v1", "checksum", "dataset key", option_correct=False, workflow_score=0, database_path=self.db)
        store.record_grade(execution, "review-v1", "checksum", "independent review", attempt_id=attempt,
                           reasoning_valid=False, reviewer="test reviewer", database_path=self.db)
        with self.assertRaises(ValueError):
            store.create_attempt(execution, 2, "m2", database_path=self.db)
        with self.assertRaises(ValueError):
            store.record_grade(execution, "bad", "wrong-checksum", "key", workflow_score=0, database_path=self.db)
        with self.assertRaises(ValueError):
            store.record_grade(execution, "unattributed", "checksum", "review", reasoning_valid=True, database_path=self.db)

    def test_malformed_verifier_is_not_a_valid_rejection_or_acceptance(self):
        execution = self.execution()
        attempt, _ = self.source(execution)
        call = store.create_call(attempt, "verifier", "v", {}, database_path=self.db)
        with self.assertRaises(ValueError):
            store.record_verification(attempt, "accept", database_path=self.db)
        store.finish_call(call, status="completed", elapsed_seconds=0.1,
                          payload={"choices": [{"message": {"content": '{"accepted":"false"}'}, "finish_reason": "stop"}]}, database_path=self.db)
        with self.assertRaises(ValueError):
            store.record_verification(attempt, "reject", database_path=self.db)
        store.record_verification(attempt, "invalid", database_path=self.db)

    def test_historical_sources_match_question_model_and_are_not_new_spend(self):
        questions = batch.load_questions(1)
        old_run = batch.create_run(questions, self.db)
        historical = batch.create_call(old_run, questions[0]["id"], 1, "m1", {}, database_path=self.db)
        batch.finish_call(historical, status="completed", elapsed_seconds=1, response_payload={
            "choices": [{"message": {"content": '{"calculation":"6*7=42","option":"b","value":"42"}'}, "finish_reason": "stop"}],
            "usage": {"cost": 9}}, database_path=self.db)
        q = {**self.question, "id": questions[0]["id"]}
        run = store.create_run("verifier_screen", "x", "checksum", [q["id"]], {}, database_path=self.db)
        config = store.create_config(run, "v", {}, database_path=self.db)
        execution = store.create_execution(run, config, q, database_path=self.db)
        with self.assertRaises(ValueError):
            store.create_attempt(execution, 1, "wrong-model", historical_solver_call_id=historical, database_path=self.db)
        attempt = store.create_attempt(execution, 1, "m1", historical_solver_call_id=historical, database_path=self.db)
        with self.assertRaises(ValueError):
            store.create_call(attempt, "solver", "m1", {}, database_path=self.db)
        self.assertEqual(store.cost_summary(run, database_path=self.db), [])


if __name__ == "__main__":
    unittest.main()
