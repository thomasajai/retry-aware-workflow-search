"""Offline scheduler checks: temporary SQLite databases and simulated HTTP only."""

import asyncio
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_batch as batch


class BatchSchedulerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.database_path = Path(temporary_directory.name) / "runs.sqlite3"
        batch.initialize_database(self.database_path)
        self.questions = batch.load_questions()
        self.models = list(batch.MODELS)
        self.run_id = batch.create_run(self.questions, self.database_path)
        self.api_key = "fake-key-for-offline-tests"
        self.prompts = {
            batch.build_prompt(question): row
            for row, question in enumerate(self.questions, start=1)
        }

    def calls(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute("SELECT * FROM calls")]

    def run_record(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            return dict(connection.execute("SELECT * FROM runs").fetchone())

    async def execute(self, handler):
        with redirect_stdout(io.StringIO()):
            return await batch.run_batch(
                self.run_id, self.questions, self.api_key,
                database_path=self.database_path,
                transport=httpx.MockTransport(handler),
            )

    @staticmethod
    def success(row):
        return httpx.Response(200, json={
            "choices": [{"message": {"content": f"answer {row}"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001},
        })

    async def test_concurrency_model_order_and_expected_failures(self):
        active = 0
        peak = 0
        request_order = []
        finish_order = []

        async def handler(request):
            nonlocal active, peak
            body = json.loads(request.content)
            model = body["model"]
            row = self.prompts[body["messages"][0]["content"]]
            model_index = self.models.index(model)
            # Every preceding model must have all 50 final records already saved.
            saved = self.calls()
            for previous_model in self.models[:model_index]:
                previous_calls = [item for item in saved if item["requested_model"] == previous_model]
                self.assertEqual(len(previous_calls), 50)
                self.assertTrue(all(item["status"] in ("completed", "failed") for item in previous_calls))
            current = [item for item in saved if item["requested_model"] == model and item["row_number"] == row]
            self.assertEqual(len(current), 1)
            self.assertEqual(current[0]["status"], "running")
            self.assertEqual(self.run_record()["status"], "running")
            active += 1
            peak = max(peak, active)
            self.assertLessEqual(active, 5)
            request_order.append(model)
            try:
                # Force the first question to finish after later questions.
                await asyncio.sleep(0.025 if row == 1 else 0.001)
                if model_index == 0 and row == 7:
                    return httpx.Response(429, json={"error": {"message": "Rate limited"}})
                if model_index == 1 and row == 19:
                    raise httpx.ReadTimeout("Simulated timeout", request=request)
                if model_index == 2 and row == 3:
                    return httpx.Response(200, json={
                        "choices": [{"message": {"content": "partial"}, "finish_reason": "length"}],
                        "usage": {"cost": 0.002},
                    })
                return self.success(row)
            finally:
                finish_order.append((model, row))
                active -= 1

        status = await self.execute(handler)
        self.assertEqual(status, "completed_with_errors")
        self.assertEqual(peak, 5)
        self.assertEqual(request_order, [model for model in self.models for _ in range(50)])
        self.assertNotEqual([row for model, row in finish_order if model == self.models[0]], list(range(1, 51)))
        saved = self.calls()
        self.assertEqual(len(saved), 150)
        self.assertEqual(sum(item["status"] == "failed" for item in saved), 3)
        self.assertEqual(sum(item["status"] == "completed" for item in saved), 147)
        for model in self.models:
            model_calls = [item for item in saved if item["requested_model"] == model]
            self.assertEqual({item["row_number"] for item in model_calls}, set(range(1, 51)))
            self.assertEqual({item["question_id"] for item in model_calls}, {q["id"] for q in self.questions})
        self.assertTrue(all(item["attempt_number"] == 1 for item in saved))
        self.assertEqual(self.run_record()["status"], status)
        self.assertIsNotNone(self.run_record()["started_at_utc"])
        self.assertIsNotNone(self.run_record()["finished_at_utc"])

    async def test_saved_settings_and_no_reexecution(self):
        requests = 0

        async def handler(request):
            nonlocal requests
            requests += 1
            body = json.loads(request.content)
            self.assertIn(body["model"], self.models)
            self.assertEqual(body["max_tokens"], 1024)
            row = self.prompts[body["messages"][0]["content"]]
            return self.success(row)

        with patch.object(batch, "MODELS", []), patch.object(batch, "MAX_CONCURRENT_REQUESTS", 1), \
                patch.object(batch, "MAX_OUTPUT_TOKENS", 1), patch.object(batch, "PROMPT_TEMPLATE", "changed"):
            self.assertEqual(await self.execute(handler), "completed")
        self.assertEqual(requests, 150)
        with self.assertRaises(ValueError):
            await self.execute(handler)
        self.assertEqual(requests, 150)
        self.assertEqual(len(self.calls()), 150)

    async def test_cancellation_saves_active_calls_and_stops_models(self):
        all_started = asyncio.Event()
        entered = 0

        async def handler(request):
            nonlocal entered
            entered += 1
            if entered == 5:
                all_started.set()
            await asyncio.Future()

        task = asyncio.create_task(self.execute(handler))
        await asyncio.wait_for(all_started.wait(), timeout=5)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        saved = self.calls()
        self.assertEqual(len(saved), 5)
        self.assertTrue(all(item["status"] == "interrupted" for item in saved))
        self.assertEqual({item["requested_model"] for item in saved}, {self.models[0]})
        self.assertEqual(self.run_record()["status"], "interrupted")
        self.assertIsNotNone(self.run_record()["finished_at_utc"])

    async def test_unexpected_error_cancels_other_tasks(self):
        all_started = asyncio.Event()
        entered = 0

        async def handler(request):
            nonlocal entered
            entered += 1
            body = json.loads(request.content)
            row = self.prompts[body["messages"][0]["content"]]
            if entered >= 5:
                all_started.set()
            await all_started.wait()
            if row == 1:
                raise RuntimeError("Simulated unexpected transport failure")
            await asyncio.Future()

        with self.assertRaises(ExceptionGroup):
            await self.execute(handler)
        saved = self.calls()
        self.assertGreaterEqual(len(saved), 5)
        self.assertEqual(sum(item["status"] == "failed" for item in saved), 1)
        self.assertTrue(all(item["status"] in ("failed", "interrupted") for item in saved))
        self.assertEqual({item["requested_model"] for item in saved}, {self.models[0]})
        self.assertEqual(self.run_record()["status"], "interrupted")

    async def test_invalid_setup_never_sends_requests(self):
        async def handler(request):
            self.fail("Invalid setup must not send an HTTP request")

        with self.assertRaises(ValueError):
            await batch.run_batch(
                self.run_id, list(reversed(self.questions)), self.api_key,
                database_path=self.database_path, transport=httpx.MockTransport(handler),
            )
        with self.assertRaises(ValueError):
            await batch.run_batch(self.run_id, self.questions, "", database_path=self.database_path)
        changed_dataset = self.database_path.parent / "changed.json"
        changed_dataset.write_text("[]", encoding="utf-8")
        with patch.object(batch, "DATASET_PATH", changed_dataset), self.assertRaises(ValueError):
            await self.execute(handler)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.run_record()["status"], "prepared")
        self.assertIsNone(self.run_record()["started_at_utc"])


class QuestionCountTests(unittest.TestCase):
    def test_loader_defaults_prefix_and_bounds(self):
        default_questions = batch.load_questions()
        self.assertEqual(len(default_questions), 50)
        self.assertEqual(batch.load_questions(1), default_questions[:1])
        self.assertEqual(set(batch.load_questions(1)[0]), {"id", "problem", "options"})
        for count in (0, -1, 201):
            with self.subTest(count=count), self.assertRaises(ValueError):
                batch.load_questions(count)

    def test_cli_one_question_reaches_runner_and_invalid_counts_stop_early(self):
        with patch.object(sys, "argv", ["mathqa_batch.py", "--run", "--questions", "1"]), \
                patch.object(batch, "load_dotenv"), patch.object(batch.os, "getenv", return_value="fake-test-key"), \
                patch.object(batch, "initialize_database"), patch.object(batch, "create_run", return_value="test-run") as create, \
                patch.object(batch, "run_batch", new_callable=AsyncMock, return_value="completed") as runner, \
                patch.object(batch, "export_table", return_value=Path("test.html")), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(batch.main(), 0)
            self.assertEqual(len(create.call_args.args[0]), 1)
            self.assertEqual(len(runner.await_args.args[1]), 1)
            self.assertIn("Planned API calls: 3", output.getvalue())

        for count in ("0", "-1", "201", "not-an-integer"):
            with self.subTest(count=count), \
                    patch.object(sys, "argv", ["mathqa_batch.py", "--run", "--questions", count]), \
                    patch.object(batch, "initialize_database") as initialize, \
                    patch.object(batch, "create_run") as create, redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as error:
                batch.main()
            self.assertEqual(error.exception.code, 2)
            initialize.assert_not_called()
            create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
