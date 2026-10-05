"""Focused answer grading checks; saved fixtures and mocked HTTP only."""

import asyncio
from contextlib import closing, redirect_stdout
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
import mathqa_grading as grading


QUESTION = {"correct": "b", "parsed_options": dict(zip("abcde", ["40", "42", "44", "46", "48"]))}


class ExtractionTests(unittest.TestCase):
    def grade(self, answer, *, status="completed", finish="stop", contract="json-v1"):
        return grading.grade_answer({"answer_text": answer, "status": status, "finish_reason": finish}, contract, QUESTION)

    def test_option_alone_controls_score_and_value_conflict_is_separate(self):
        for fields, score, conflict in (
            ({"calculation": "This is prose", "option": "b", "value": "42"}, 1, False),
            ({"option": "a", "value": "40"}, 0, False),
            ({"option": "b", "value": "44"}, 1, True),
            ({"option": "b"}, 1, None),
            ({"option": "b", "value": 42}, 1, None),
        ):
            with self.subTest(fields=fields):
                result = self.grade(json.dumps(fields))
                self.assertEqual(result["score"], score)
                self.assertTrue(result["gradable"])
                self.assertEqual(result["value_conflict"], conflict)

    def test_missing_malformed_ambiguous_options_are_zero_without_repair(self):
        for answer in (None, "", "The answer is b", "{}", "[]", '{"option":"b"',
                       '{"option":"a","option":"b","value":"42"}',
                       '{"option":["a","b"]}', '{"option":"B"}', '{"option":"none"}',
                       '{"option":" b "}', '```json\n{"option":"b"}\n```',
                       '{"option":"b"} trailing'):
            with self.subTest(answer=answer):
                result = self.grade(answer)
                self.assertEqual(result["score"], 0)
                self.assertFalse(result["gradable"])
                self.assertTrue(result["diagnostics"]["errors"])

    def test_line_extraction_ignores_calculation_format_but_rejects_ambiguity(self):
        for answer in ("some prose; x=6; b ) 42", "<calculation>;b) 42", "; b) 42"):
            result = self.grade(answer, contract="line-v1")
            self.assertEqual(result["score"], 1)
            self.assertEqual(result["returned_value"], "42")
        for answer in ("x; a) 40; b) 42", "x; b) 42 or c) 44", "b) 42", "x; b) 42\nextra", "x; B) 42"):
            self.assertFalse(self.grade(answer, contract="line-v1")["gradable"])

    def test_failed_and_truncated_generations_ignore_even_complete_final_fields(self):
        answer = '{"option":"b","value":"42"}'
        for status, finish in (("failed", "stop"), ("failed", "length"), ("completed", "length"), ("completed", "error")):
            result = self.grade(answer, status=status, finish=finish)
            self.assertEqual(result["score"], 0)
            self.assertFalse(result["gradable"])
            self.assertEqual(result["option_letter"], "b")


class SavedGradingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / "runs.sqlite3"
        batch.initialize_database(self.database)
        self.questions = batch.load_questions(4)
        # A fourth model exercises integration without any hard-coded model list.
        configs = batch.default_model_configs()
        configs["example/additional"] = next(iter(configs.values()))
        self.models = list(configs)
        self.run_id = batch.create_run(self.questions, self.database, model_configs=configs)
        self.records = json.loads(batch.DATASET_PATH.read_text(encoding="utf-8"))[:4]

    def rows(self, sql, parameters=()):
        with closing(sqlite3.connect(self.database)) as c:
            c.row_factory = sqlite3.Row
            return [dict(row) for row in c.execute(sql, parameters)]

    async def execute(self):
        entered = 0
        async def handler(request):
            nonlocal entered
            entered += 1
            index = (entered - 1) % 4
            # No grading results may exist even while the last model is running.
            self.assertEqual(self.rows("SELECT * FROM call_gradings"), [])
            await asyncio.sleep(0)
            q = self.records[index]
            option = q["correct"] if index in (0, 3) else next(x for x in "abcde" if x != q["correct"])
            answer = json.dumps({"calculation": "invalid calculation prose", "option": option,
                                 "value": q["parsed_options"][option]})
            if index == 2:
                answer = '{"option":"none","value":"none"}'
            return httpx.Response(200, json={"choices": [{"message": {"content": answer},
                                  "finish_reason": "length" if index == 3 else "stop"}]})
        with redirect_stdout(io.StringIO()) as output:
            await batch.run_batch(self.run_id, self.questions, "fake-key", database_path=self.database,
                                  transport=httpx.MockTransport(handler))
        self.assertEqual(entered, 16)
        return output.getvalue()

    async def test_post_batch_grading_denominator_and_original_preservation(self):
        output = await self.execute()
        summaries = self.rows("SELECT * FROM model_gradings")
        self.assertEqual(len(summaries), 4)
        for s in summaries:
            self.assertEqual((s["correct_count"], s["denominator"], s["accuracy_percent"]), (1, 4, 25))
            self.assertEqual(s["generation_failures"], 1)
            self.assertEqual(s["ungradable_completed"], 1)
            self.assertEqual(s["format_invalid_completed"], 3)
        self.assertIn("1/4 correct (25.00%)", output)
        original = self.rows("SELECT * FROM calls")
        validations = self.rows("SELECT * FROM call_validations")
        grading.grade_run(self.run_id, self.database)
        self.assertEqual(original, self.rows("SELECT * FROM calls"))
        self.assertEqual(validations, self.rows("SELECT * FROM call_validations"))
        self.assertEqual(len(self.rows("SELECT * FROM call_gradings")), 16)
        import mathqa_table
        from test_mathqa_table import ParsedTable
        before = self.rows("SELECT * FROM call_gradings")
        path = mathqa_table.export_table(self.run_id, database_path=self.database,
                                        output_path=self.database.parent / "report.html")
        parsed = ParsedTable()
        parsed.feed(path.read_text(encoding="utf-8"))
        self.assertEqual(list(parsed.tables), ["final-answers", "scores", "accuracy"])
        for row, score in zip(parsed.tables["scores"][1:], (1, 0, 0, 0)):
            self.assertEqual([cell["text"] for cell in row[1:]], [str(score)] * 4)
        for row in parsed.tables["accuracy"][1:]:
            self.assertEqual([cell["text"] for cell in row[1:4]], ["1", "4", "25.00%"])
        for cell in parsed.tables["final-answers"][1][1:]:
            self.assertIn(f"{self.records[0]['correct']})", cell["text"])
            self.assertIn("format: invalid", cell["text"])
            self.assertIn("invalid calculation prose", cell["text"])
        self.assertEqual(before, self.rows("SELECT * FROM call_gradings"))

    async def test_checksum_refuses_grading_and_incomplete_runs_are_not_graded(self):
        for status in ("prepared", "running", "interrupted"):
            with closing(sqlite3.connect(self.database)) as c, c:
                c.execute("UPDATE runs SET status = ?", (status,))
            with self.assertRaisesRegex(ValueError, "finished batch"):
                grading.grade_run(self.run_id, self.database)
        with closing(sqlite3.connect(self.database)) as c, c:
            c.execute("UPDATE runs SET status='completed', finished_at_utc='now'")
        with self.assertRaisesRegex(ValueError, "planned attempts"):
            grading.grade_run(self.run_id, self.database)
        self.assertEqual(self.rows("SELECT * FROM run_gradings"), [])
        with closing(sqlite3.connect(self.database)) as c, c:
            c.execute("UPDATE runs SET status='prepared', finished_at_utc=NULL")
        # Allow execution but prevent the automatic grader for this corruption check.
        with patch.object(batch, "grade_run", return_value=[]):
            await self.execute()
        # A terminal run label is insufficient when even one planned call is unfinished.
        call = self.rows("SELECT * FROM calls LIMIT 1")[0]
        with closing(sqlite3.connect(self.database)) as c, c:
            c.execute("UPDATE calls SET status='running' WHERE call_id=?", (call["call_id"],))
        with self.assertRaisesRegex(ValueError, "planned attempts"):
            grading.grade_run(self.run_id, self.database)
        self.assertEqual(self.rows("SELECT * FROM run_gradings"), [])
        with closing(sqlite3.connect(self.database)) as c, c:
            c.execute("UPDATE calls SET status=? WHERE call_id=?", (call["status"], call["call_id"]))
        with closing(sqlite3.connect(self.database)) as c, c:
            c.execute("UPDATE runs SET dataset_sha256 = 'wrong'")
        with self.assertRaisesRegex(ValueError, "checksum"):
            grading.grade_run(self.run_id, self.database)
        self.assertEqual(self.rows("SELECT * FROM call_gradings"), [])


if __name__ == "__main__":
    unittest.main()
