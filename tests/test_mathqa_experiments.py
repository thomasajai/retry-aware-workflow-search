"""Formatting experiment tests: mocked HTTP and temporary databases only."""

from contextlib import closing, redirect_stdout, redirect_stderr
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
import mathqa_experiments as experiments
from mathqa_response import validate_answer


OPTIONS = "a ) 40 , b ) 42 , c ) 44 , d ) 46 , e ) none of these"
VALID_FIELDS = {"calculation": "6*7=42", "option": "b", "value": "42"}


class ResponseContractTests(unittest.TestCase):
    def test_accepts_line_and_json_without_grading_math(self):
        for contract, answer in (
            ("line-v1", " 6*7=42; b) 42\n"),
            ("json-v1", json.dumps(VALID_FIELDS, indent=2)),
            ("line-v1", "6*7=40; a) 40"),  # Incorrect math is still valid format.
            ("line-v1", "gcd(1345,775)=5; e) none of these"),
        ):
            with self.subTest(answer=answer):
                result = validate_answer(answer, contract, OPTIONS)
                self.assertTrue(result["valid"], result["errors"])

    def test_rejects_nonempty_noncompliant_answers(self):
        invalid_lines = [
            "The answer is b", "<calculation>; b) 42", "6*7=42; B) 42",
            "6*7=42; b) 42\nExplanation", "We multiply 6 and 7; b) 42",
            "6*7=42; b) 44", "6*7=42; b) <option value>", "x" * 161 + "; b) 42",
        ]
        invalid_json = [
            None, "", "[]", "null", '```json\n' + json.dumps(VALID_FIELDS) + '\n```',
            json.dumps(VALID_FIELDS) + " trailing explanation",
            '{"calculation":"6*7=42","option":"a","option":"b","value":"42"}',
            json.dumps({**VALID_FIELDS, "value": 42}),
            json.dumps({**VALID_FIELDS, "option": "bc"}),
            json.dumps({**VALID_FIELDS, "extra": "commentary"}),
            json.dumps({"option": "b", "value": "42"}),
            json.dumps({**VALID_FIELDS, "calculation": "6*7=42\nexplanation"}),
        ]
        for contract, answers in (("line-v1", invalid_lines), ("json-v1", invalid_json)):
            for answer in answers:
                with self.subTest(contract=contract, answer=answer):
                    result = validate_answer(answer, contract, OPTIONS)
                    self.assertFalse(result["valid"])
                    self.assertTrue(result["errors"])
        bad_fields = {**VALID_FIELDS, "value": 42}
        self.assertEqual(validate_answer(json.dumps(bad_fields), "json-v1", OPTIONS)["parsed_fields"], bad_fields)


class ExperimentConfigurationTests(unittest.TestCase):
    def test_controls_variants_and_no_answer_key_in_prompts(self):
        first = batch.load_questions(1)[0]
        for alias in experiments.MODEL_SETTINGS:
            for variant in experiments.EXPERIMENTS[:3]:
                model, config = experiments.experiment_config(alias, variant)
                body = config["body_settings"]
                self.assertEqual(model, experiments.MODEL_SETTINGS[alias]["model"])
                self.assertFalse(body["provider"]["allow_fallbacks"])
                self.assertTrue(body["provider"]["require_parameters"])
                self.assertEqual(len(body["provider"]["only"]), 1)
                self.assertEqual(body["max_tokens"], 256)
                self.assertEqual("response_format" in body, variant == "json-schema")
                self.assertEqual("reasoning" in body, alias != "qwen25")
                if alias != "qwen25":
                    self.assertEqual(body["reasoning"], {"enabled": False})
                prompt = config["prompt_template"].format(**first)
                self.assertIn("6*7=42", prompt)
                self.assertNotIn("30*29=870", prompt)
                self.assertNotIn("Rationale", prompt)
                self.assertNotIn("correct", prompt)
        _, config = experiments.experiment_config("qwen3", "line-no-think")
        self.assertTrue(config["prompt_template"].endswith("/no_think"))
        config["body_settings"]["provider"]["only"].clear()
        self.assertTrue(experiments.experiment_config("qwen3", "line-no-think")[1]["body_settings"]["provider"]["only"])
        with self.assertRaises(ValueError):
            experiments.experiment_config("deepseek", "line-no-think")

    def test_preview_and_list_never_call_api_or_change_database(self):
        for argv, expected in (
            (["--list"], None),
            (["--model", "qwen25"], "json-prompt"),
            (["--model", "qwen3"], "json-schema-no-think"),
            (["--model", "deepseek"], "json-prompt"),
            (["--model", "qwen25", "--experiment", "json-schema"], "json-schema"),
        ):
            with patch.object(sys, "argv", ["mathqa_experiments.py", *argv]), \
                    patch.object(batch, "initialize_database") as initialize, \
                    patch.object(batch, "create_run") as create, \
                    patch.object(batch, "run_batch") as runner, redirect_stdout(io.StringIO()) as output:
                self.assertEqual(experiments.main(), 0)
                initialize.assert_not_called()
                create.assert_not_called()
                runner.assert_not_called()
                if "--model" in argv:
                    self.assertIn("Planned calls: 5", output.getvalue())
                    self.assertIn("Preview only", output.getvalue())
                    self.assertIn(f"experiment: {expected}", output.getvalue())
        for argv in (["--run"], ["--list", "--run"], ["--model", "qwen25", "--questions", "0"]):
            with patch.object(sys, "argv", ["mathqa_experiments.py", *argv]), \
                    redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                experiments.main()


class SavedTrialTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_path = Path(directory.name) / "trial.sqlite3"
        batch.initialize_database(self.database_path)
        self.questions = batch.load_questions(5)
        self.model, self.config = experiments.experiment_config("qwen3", "json-schema-no-think")
        self.run_id = batch.create_run(self.questions, self.database_path, model_configs={self.model: self.config})

    def rows(self, query):
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query)]

    async def test_saved_settings_raw_preservation_and_separate_outcomes(self):
        sent = []
        raw_bodies = {}
        async def handler(request):
            body = json.loads(request.content)
            sent.append(body)
            index = len(sent) - 1
            self.assertEqual(body["provider"]["only"], ["siliconflow/fp8"])
            self.assertEqual(body["temperature"], 0.7)
            self.assertEqual(body["response_format"]["type"], "json_schema")
            self.assertTrue(body["messages"][0]["content"].endswith("/no_think"))
            if index == 3:
                raise httpx.ReadTimeout("Mock timeout", request=request)
            option_value = self.questions[index]["options"].split("a ) ")[1].split(" , b")[0]
            answer = json.dumps({"calculation": "1+1=2", "option": "a", "value": option_value})
            if index == 1:
                answer = "Here is a long explanation."
            if index == 4:
                answer = None
            payload = {"provider": "SiliconFlow", "choices": [{"finish_reason": "length" if index == 2 else "stop",
                        "message": {"content": answer}}], "usage": {"cost": 0.001}}
            if index in (0, 1):
                payload["usage"]["completion_tokens_details"] = {"reasoning_tokens": 4 if index == 0 else 0}
            raw = json.dumps(payload, indent=3)
            raw_bodies[self.questions[index]["id"]] = raw
            return httpx.Response(200, text=raw)

        # Execution uses the saved configuration, even if live defaults change.
        with patch.dict(experiments.MODEL_SETTINGS, {}, clear=True), redirect_stdout(io.StringIO()):
            status = await batch.run_batch(self.run_id, self.questions, "fake-key", database_path=self.database_path,
                                           transport=httpx.MockTransport(handler))
        self.assertEqual(status, "completed_with_errors")
        self.assertEqual(len(sent), 5)  # No retries.
        report = experiments.build_report(self.run_id, self.database_path)
        summary = report["summaries"][0]
        self.assertEqual(summary["generation_completed"], 2)
        self.assertEqual(summary["generation_failed"], 3)
        self.assertEqual(summary["invalid_completed_responses"], 1)
        self.assertEqual(summary["format_successes"], 1)
        self.assertEqual(summary["format_success_rate"], 1 / 5)
        self.assertEqual(summary["calls_without_reported_cost"], 1)
        self.assertAlmostEqual(summary["reported_cost_usd"], 0.004)
        self.assertEqual([call["reasoning_tokens"] for call in report["calls"]], [4, 0, None, None, None])
        self.assertTrue(report["calls"][2]["format_valid"])  # Valid text, truncated generation.
        for call in self.rows("SELECT * FROM calls"):
            if call["question_id"] in raw_bodies:
                raw = raw_bodies[call["question_id"]]
                self.assertEqual(call["response_body_text"], raw)
                self.assertEqual(json.loads(call["response_json"]), json.loads(raw))
                self.assertEqual(call["answer_text"], json.loads(raw)["choices"][0]["message"]["content"])
        self.assertEqual(len(self.rows("SELECT * FROM call_validations")), 5)

    def test_additive_migration_keeps_legacy_records_and_export_readable(self):
        legacy_id = batch.create_run(self.questions, self.database_path)
        call_id = batch.create_call(legacy_id, self.questions[0]["id"], 1, batch.MODELS[0], {}, database_path=self.database_path)
        batch.finish_call(call_id, status="completed", elapsed_seconds=1, response_payload={"choices": [{"message": {"content": "Old answer"}}]}, database_path=self.database_path)
        latest_id = batch.create_call(legacy_id, self.questions[0]["id"], 1, batch.MODELS[0], {}, attempt_number=2, database_path=self.database_path)
        batch.finish_call(latest_id, status="failed", elapsed_seconds=1, response_payload={"choices": [{"message": {"content": "Latest old answer"}}]}, database_path=self.database_path)
        before = self.rows("SELECT * FROM calls")
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute("DROP TABLE call_validations")
        report = experiments.build_report(legacy_id, self.database_path)
        self.assertEqual(report["summaries"][0]["missing_calls"], 4)
        self.assertEqual(len(report["calls"]), 1)
        self.assertEqual(report["calls"][0]["answer_text"], "Latest old answer")
        self.assertIsNone(report["calls"][0]["format_valid"])
        with closing(sqlite3.connect(self.database_path)) as connection:
            self.assertIsNone(connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'call_validations'").fetchone())
        batch.initialize_database(self.database_path)
        batch.initialize_database(self.database_path)
        self.assertEqual(before, self.rows("SELECT * FROM calls"))
        self.assertEqual(self.rows("SELECT * FROM call_validations"), [])
        output = experiments.export_table(legacy_id, database_path=self.database_path, output_path=self.database_path.parent / "old.html")
        self.assertIn("Latest old answer", output.read_text(encoding="utf-8"))
        report = experiments.build_report(legacy_id, self.database_path)
        self.assertEqual(report["summaries"][0]["selected_questions"], 5)
        self.assertEqual(report["summaries"][0]["missing_calls"], 4)
        self.assertEqual(report["summaries"][0]["validation_missing"], 1)
        self.assertIsNone(report["calls"][0]["format_valid"])


if __name__ == "__main__":
    unittest.main()
