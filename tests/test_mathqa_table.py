"""Check HTML export ordering, answer preservation, and read-only database access."""

import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_batch as batch
import mathqa_table as table


class ParsedTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.tags = []
        self.cell = None
        self.tables = {}
        self.current_table = None

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "table":
            self.current_table = dict(attrs)["id"]
            self.tables[self.current_table] = []
        elif tag == "tr":
            self.rows.append([])
            self.tables[self.current_table].append(self.rows[-1])
        elif tag in ("td", "th"):
            self.cell = {"tag": tag, "attrs": dict(attrs), "text": ""}

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.rows[-1].append(self.cell)
            self.cell = None


class TableExportTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.database_path = self.directory / "runs.sqlite3"
        self.output_path = self.directory / "table.html"
        batch.initialize_database(self.database_path)
        self.questions = batch.load_questions()
        self.questions[0], self.questions[1] = self.questions[1], self.questions[0]
        self.models = list(reversed(batch.MODELS))
        configs = batch.default_model_configs()
        self.run_id = batch.create_run(self.questions, self.database_path,
                                       model_configs={model: configs[model] for model in self.models})

    def save_answer(self, row, model_index, answer, *, status="completed", attempt=1):
        call_id = batch.create_call(
            self.run_id, self.questions[row - 1]["id"], row, self.models[model_index], {},
            attempt_number=attempt, database_path=self.database_path,
        )
        batch.finish_call(
            call_id, status=status, elapsed_seconds=1.0,
            response_payload={"choices": [{"message": {"content": answer}}]},
            database_path=self.database_path,
        )

    def database_snapshot(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            return list(connection.iterdump())

    def test_order_shape_escaping_missing_cells_and_latest_attempt(self):
        malicious_text = "<script>alert('x')</script> & <b>text</b>\nsecond line"
        self.save_answer(1, 0, "Earlier answer")
        self.save_answer(1, 0, "Latest partial answer", status="failed", attempt=2)
        self.save_answer(1, 1, malicious_text)
        self.save_answer(2, 2, "Interrupted partial", status="interrupted")
        before = self.database_snapshot()
        result = table.export_table(
            self.run_id, database_path=self.database_path, output_path=self.output_path
        )
        self.assertEqual(result, self.output_path)
        self.assertEqual(self.database_snapshot(), before)
        document = result.read_text(encoding="utf-8")
        parsed = ParsedTable()
        parsed.feed(document)
        self.assertEqual(list(parsed.tables), ["final-answers", "scores", "accuracy"])
        answers = parsed.tables["final-answers"]
        scores = parsed.tables["scores"]
        self.assertEqual(len(answers), 51)
        self.assertEqual(len(scores), 51)
        self.assertEqual(len(parsed.tables["accuracy"]), 4)
        self.assertEqual([cell["text"] for cell in answers[0][1:]], self.models)
        self.assertEqual(sum(cell["tag"] == "td" for row in answers for cell in row), 150)
        self.assertTrue(all(len(row) == 4 for row in answers))
        self.assertTrue(all(cell["text"] == "Ungraded" for row in scores[1:] for cell in row[1:]))
        for row, question in zip(answers[1:], self.questions):
            self.assertTrue(row[0]["text"].endswith(question["id"]))
        self.assertIn("Latest partial answer", answers[1][1]["text"])
        self.assertEqual(answers[1][1]["attrs"]["class"], "failed")
        self.assertIn(malicious_text, answers[1][2]["text"])
        self.assertIn("[No answer text saved]", answers[1][3]["text"])
        self.assertIn("Interrupted partial", answers[2][3]["text"])
        self.assertEqual(answers[2][3]["attrs"]["class"], "unfinished")
        self.assertEqual(parsed.tags.count("details"), 150)
        self.assertNotIn("script", parsed.tags)
        self.assertNotIn("b", parsed.tags)
        self.assertIn("white-space: pre-wrap", document)
        self.assertNotIn("Earlier answer", document)

    def test_run_selection_isolation_and_default_filename(self):
        self.save_answer(1, 0, "Selected run only")
        other_run = batch.create_run(self.questions, self.database_path)
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute("UPDATE runs SET created_at_utc = ? WHERE run_id = ?", ("2026-10-01T00:00:00+00:00", self.run_id))
                connection.execute("UPDATE runs SET created_at_utc = ? WHERE run_id = ?", ("2026-10-02T00:00:00+00:00", other_run))
        selected = table.export_table(self.run_id, database_path=self.database_path, output_path=self.output_path)
        self.assertIn("Selected run only", selected.read_text(encoding="utf-8"))
        with patch.object(table, "OUTPUT_DIRECTORY", self.directory / "exports"):
            latest = table.export_table(database_path=self.database_path)
        self.assertEqual(latest.name, f"mathqa_{other_run}.html")
        self.assertIn(other_run, latest.read_text(encoding="utf-8"))
        self.assertNotIn("Selected run only", latest.read_text(encoding="utf-8"))

    def test_missing_database_unknown_run_and_overwrite_protection(self):
        missing_path = self.directory / "missing.sqlite3"
        with self.assertRaises(sqlite3.OperationalError):
            table.export_table(database_path=missing_path, output_path=self.output_path)
        self.assertFalse(missing_path.exists())
        with self.assertRaises(ValueError):
            table.export_table("unknown-run", database_path=self.database_path, output_path=self.output_path)
        self.assertFalse(self.output_path.exists())
        before = self.database_snapshot()
        with self.assertRaises(ValueError):
            table.export_table(self.run_id, database_path=self.database_path, output_path=self.database_path)
        self.assertEqual(self.database_snapshot(), before)

    def test_unmigrated_database_exports_as_ungraded_without_creating_tables(self):
        self.save_answer(1, 0, "Legacy reply")
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            for name in ("call_gradings", "model_gradings", "run_gradings", "call_validations"):
                connection.execute(f"DROP TABLE {name}")
        before = self.database_snapshot()
        path = table.export_table(self.run_id, database_path=self.database_path, output_path=self.output_path)
        document = path.read_text(encoding="utf-8")
        self.assertIn("Legacy reply", document)
        self.assertIn("Ungraded; no complete batch grading saved", document)
        self.assertNotIn("Fully graded", document)
        self.assertEqual(before, self.database_snapshot())


if __name__ == "__main__":
    unittest.main()
