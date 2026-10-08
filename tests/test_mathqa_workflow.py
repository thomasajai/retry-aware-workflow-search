"""Controlled LangGraph routing, durable records, grading, and spend gates."""

from contextlib import closing
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_models as models
import mathqa_workflow as workflow
from mathqa_workflow_demo import run_demo
from mathqa_workflow_grading import grade_execution
import mathqa_workflow_store as store


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.db = self.root / "test.sqlite3"
        self.dataset = self.root / "dataset.json"
        self.question = {"id": "q", "problem": "6 times 7?", "options": "a)40, b)42, c)44, d)46, e)48",
                         "correct": "b", "Rationale": "OFFLINE_KEY_ONLY", "feedback": "PRIOR_FEEDBACK_MUST_NOT_LEAK"}
        self.dataset.write_text(json.dumps([{"id": "q", "Problem": "6 times 7?", "options": self.question["options"],
                                           "correct": "b", "Rationale": "OFFLINE_KEY_ONLY"}]), encoding="utf-8")
        store.migrate(self.db)
        self.config = workflow.configuration(["qwen25"]*3)
        self.limits = workflow.Limits(0.1, 6)
        self.run = store.create_run("sequence_evaluation", self.dataset, hashlib.sha256(self.dataset.read_bytes()).hexdigest(),
            ["q"], {"mode": "offline_test"}, budget_usd=0.1, max_requests=6, database_path=self.db)
        self.cid = store.create_config(self.run, "sequence", self.config, database_path=self.db)
        self.steps, self.sent = [], []
        self.reserve = 0.001

    def solver(self, option="b", calculation="6*7=42", **updates):
        return {"role": "solver", "content": json.dumps({"calculation": calculation, "option": option, "value": "42"}), **updates}

    def verifier(self, accepted=True, **updates):
        return {"role": "verifier", "content": json.dumps({"accepted": accepted}), **updates}

    def sender(self, request):
        self.sent.append(request)
        step = self.steps.pop(0)
        actual_role = "verifier" if request["messages"][0]["role"] == "system" else "solver"
        self.assertEqual(step["role"], actual_role)
        if step.get("exception"):
            raise step["exception"]
        payload = {"model": step.get("model", request["model"]), "provider": step.get("provider", "Offline fixture"), "id": "offline-test",
            "choices": [{"message": {"content": step["content"]}, "finish_reason": step.get("finish_reason", "stop")}],
            "usage": {"prompt_tokens": step.get("input_tokens", 100), "completion_tokens": step.get("output_tokens", 20),
                      "completion_tokens_details": {"reasoning_tokens": step.get("reasoning_tokens", 0)}, "cost": step.get("cost", 0.0001)}}
        return step.get("http_status", 200), payload

    def runner(self, sender=None):
        return workflow.Runner(self.run, self.cid, self.config, database_path=self.db, sender=sender or self.sender,
            reservations=lambda _: self.reserve,
            providers={p["model"]: "Offline fixture" for p in self.config["solvers"] + [self.config["verifier"]]}, limits=self.limits)

    def execute(self, *, repetition=1, sender=None):
        return self.runner(sender).execute(self.question, repetition=repetition)

    def rows(self, table):
        with closing(store.connect(self.db)) as c:
            return [dict(r) for r in c.execute('SELECT * FROM "' + table + '" ORDER BY rowid')]

    def set_limits(self, budget, requests):
        self.limits = workflow.Limits(budget, requests)
        with closing(store.connect(self.db)) as c, c:
            c.execute("UPDATE workflow_runs SET budget_usd=?,max_requests=? WHERE run_id=?", (budget, requests, self.run))

    def test_acceptance_at_each_position_skips_unreached_calls(self):
        for position in (1, 2, 3):
            with self.subTest(position=position):
                # Separate runs keep the run-wide request count independent.
                if position > 1:
                    self.setUp()
                self.steps = [step for i in range(position) for step in (self.solver(), self.verifier(i == position-1))]
                outcome = self.execute()
                self.assertEqual(outcome["status"], "accepted")
                self.assertEqual(len(self.sent), position*2)
                self.assertEqual(len(self.rows("workflow_attempts")), position)
                self.assertEqual(grade_execution(outcome["execution_id"], database_path=self.db)["workflow_score"], 1)
                self.assertEqual(sum(r["cost_usd"] for r in self.rows("workflow_calls")), position*0.0002)

    def test_three_rejections_score_zero_even_if_every_option_is_correct(self):
        self.steps = [step for _ in range(3) for step in (self.solver(), self.verifier(False))]
        outcome = self.execute()
        self.assertEqual(outcome["status"], "exhausted")
        self.assertIsNone(outcome["accepted_fields"])
        self.assertEqual(grade_execution(outcome["execution_id"], database_path=self.db)["workflow_score"], 0)
        self.assertTrue(all(r["option_correct"] == 1 for r in self.rows("workflow_grades") if r["attempt_id"]))

    def test_accepted_wrong_option_stops_but_scores_zero(self):
        self.steps = [self.solver(option="a", calculation="6*7=40"), self.verifier(True)]
        outcome = self.execute()
        self.assertEqual((outcome["status"], len(self.sent)), ("accepted", 2))
        self.assertEqual(grade_execution(outcome["execution_id"], database_path=self.db)["workflow_score"], 0)

    def test_option_accuracy_does_not_claim_reasoning_validity(self):
        self.steps = [self.solver(calculation="6*7=0"), self.verifier(True)]
        outcome = self.execute()
        self.assertEqual(grade_execution(outcome["execution_id"], database_path=self.db)["workflow_score"], 1)
        self.assertTrue(all(r["reasoning_valid"] is None for r in self.rows("workflow_grades")))

    def test_retries_have_identical_original_input_without_feedback_or_keys(self):
        self.steps = [step for i in range(3) for step in (self.solver(calculation=f"6*7={40+i}"), self.verifier(i==2))]
        self.execute()
        solver_requests = self.sent[::2]
        self.assertEqual(solver_requests, [solver_requests[0]]*3)
        for request in self.sent:
            encoded = json.dumps(request)
            self.assertNotIn("OFFLINE_KEY_ONLY", encoded)
            self.assertNotIn("PRIOR_FEEDBACK", encoded)
        for request in self.sent[1::2]:
            user = json.loads(request["messages"][1]["content"])
            self.assertEqual(set(user), {"question", "options", "solver_proposal"})
        self.assertNotIn('"correct"', self.rows("workflow_executions")[0]["question_json"])

    def test_each_slot_uses_the_configured_model_with_repetitions_allowed(self):
        self.config = workflow.configuration(["qwen25", "qwen3", "deepseek"])
        self.cid = store.create_config(self.run, "different_models", self.config, database_path=self.db)
        self.steps = [step for i in range(3) for step in (self.solver(), self.verifier(i==2))]
        self.execute()
        self.assertEqual([r["model"] for r in self.sent[::2]], [p["model"] for p in self.config["solvers"]])

    def test_unusable_answers_skip_verifier_and_do_not_reuse_old_state(self):
        self.steps = [self.solver(content="not an answer"), self.solver(content=""), self.solver(), self.verifier(True)]
        outcome = self.execute()
        self.assertEqual((outcome["status"], len(self.sent)), ("accepted", 4))
        self.assertEqual([r["verification_status"] for r in self.rows("workflow_attempts")], ["not_requested", "not_requested", "accept"])

    def test_cosmetic_format_does_not_reject_an_extractable_answer(self):
        self.steps = [self.solver(content='```json\n{"calculation":"' + 'Valid explanation '*30 + '","option":" B ","value":"42","extra":"cosmetic"}\n```'), self.verifier(True)]
        self.assertEqual(self.execute()["status"], "accepted")
        self.assertEqual(json.loads(self.sent[1]["messages"][1]["content"])["solver_proposal"]["option"], "b")

    def test_solver_truncation_consumes_slot_but_skips_verifier(self):
        self.steps = [self.solver(finish_reason="length"), self.solver(), self.verifier(True)]
        outcome = self.execute()
        self.assertEqual((outcome["status"], len(self.sent)), ("accepted", 3))
        self.assertEqual(self.rows("workflow_calls")[0]["error_type"], "IncompleteGeneration")

    def test_invalid_verdict_and_truncation_are_distinct_from_rejection(self):
        self.steps = [self.solver(), self.verifier(content='{"accepted":"true"}'),
                      self.solver(), self.verifier(finish_reason="length"), self.solver(), self.verifier(False)]
        outcome = self.execute()
        self.assertEqual(outcome["status"], "failed")
        self.assertEqual([r["verification_status"] for r in self.rows("workflow_attempts")], ["invalid", "error", "reject"])
        self.assertEqual(grade_execution(outcome["execution_id"], database_path=self.db)["workflow_score"], 0)

    def test_all_unusable_answers_finish_without_verifier_or_fourth_slot(self):
        self.steps = [self.solver(content="missing option")]*3
        outcome = self.execute()
        self.assertEqual((outcome["status"], len(self.sent)), ("exhausted", 3))
        self.assertEqual(grade_execution(outcome["execution_id"], database_path=self.db)["workflow_score"], 0)

    def test_zero_calls_when_reservation_cannot_fit_budget(self):
        self.set_limits(0.0001, 6)
        outcome = self.execute()
        self.assertEqual((outcome["status"], len(self.sent)), ("budget_stopped", 0))
        self.assertEqual(self.rows("workflow_attempts"), [])
        self.assertIsNone(grade_execution(outcome["execution_id"], database_path=self.db)["workflow_score"])

    def test_request_limit_between_solver_and_verifier_is_incomplete(self):
        self.set_limits(0.1, 1)
        self.steps = [self.solver()]
        outcome = self.execute()
        self.assertEqual((outcome["status"], outcome["terminal_reason"]), ("budget_stopped", "request_limit"))
        self.assertEqual(self.rows("workflow_attempts")[0]["verification_status"], "not_requested")
        self.assertIsNone(grade_execution(outcome["execution_id"], database_path=self.db)["workflow_score"])
        self.assertEqual(self.rows("workflow_grades"), [])

    def test_budget_is_shared_across_executions(self):
        self.set_limits(0.00115, 6)
        self.steps = [self.solver(), self.verifier(True)]
        self.assertEqual(self.execute()["status"], "accepted")
        second = self.execute(repetition=2)
        self.assertEqual((second["status"], second["terminal_reason"], len(self.sent)), ("budget_stopped", "spending_limit", 2))

    def test_unknown_cost_stops_scheduling_and_preserves_unknown(self):
        self.steps = [self.solver(cost=None)]
        outcome = self.execute()
        self.assertEqual((outcome["terminal_reason"], len(self.sent)), ("unknown_cost", 1))
        self.assertIsNone(self.rows("workflow_calls")[0]["cost_usd"])
        self.assertIsNone(grade_execution(outcome["execution_id"], database_path=self.db)["workflow_score"])
        with self.assertRaisesRegex(ValueError, "unfinished|terminal"):
            self.execute(repetition=2)

    def test_usage_and_routing_drift_stop_before_any_more_calls(self):
        for updates, reason in (({"reasoning_tokens": 21}, "inconsistent_reasoning_usage"),
                                ({"provider": "unexpected"}, "provider_or_model_mismatch"),
                                ({"model": "other"}, "provider_or_model_mismatch"),
                                ({"output_tokens": 513}, "reservation_exceeded"),
                                ({"input_tokens": 100000}, "reservation_exceeded"),
                                ({"cost": 0.002}, "reservation_exceeded"),
                                ({"input_tokens": None}, "unknown_token_usage")):
            with self.subTest(updates=updates):
                self.setUp()
                self.steps = [self.solver(**updates)]
                self.assertEqual(self.execute()["terminal_reason"], reason)
                self.assertEqual(len(self.sent), 1)

    def test_transport_failure_stops_on_unknown_billing_without_retry(self):
        self.steps = [self.solver(exception=httpx.ReadTimeout("do not log sk-or-v1-test_secret"))]
        outcome = self.execute()
        self.assertEqual((outcome["terminal_reason"], len(self.sent)), ("unknown_cost", 1))
        self.assertNotIn("test_secret", json.dumps(self.rows("workflow_calls")))

    def test_cancellation_and_unexpected_error_leave_durable_finished_call(self):
        self.steps = [self.solver(exception=KeyboardInterrupt())]
        self.assertEqual(self.execute()["status"], "interrupted")
        self.assertEqual(self.rows("workflow_calls")[0]["status"], "interrupted")
        self.setUp()
        self.steps = [self.solver(exception=RuntimeError("never log sk-or-v1-test_secret"))]
        with self.assertRaises(RuntimeError):
            self.execute()
        self.assertEqual(self.rows("workflow_executions")[0]["status"], "interrupted")
        self.assertEqual(self.rows("workflow_runs")[0]["status"], "interrupted")
        self.assertTrue(self.rows("workflow_calls")[0]["finished_at_utc"])
        self.assertNotIn("test_secret", json.dumps(self.rows("workflow_calls")))

    def test_grading_checks_dataset_identity_and_is_atomic_on_duplicate(self):
        self.steps = [self.solver(), self.verifier(True)]
        outcome = self.execute()
        original = self.dataset.read_bytes()
        self.dataset.write_bytes(original+b" ")
        with self.assertRaisesRegex(ValueError, "checksum"):
            grade_execution(outcome["execution_id"], database_path=self.db)
        self.assertEqual(self.rows("workflow_grades"), [])
        self.dataset.write_bytes(original)
        grade_execution(outcome["execution_id"], database_path=self.db)
        before = self.rows("workflow_grades")
        with self.assertRaises(sqlite3.IntegrityError):
            grade_execution(outcome["execution_id"], database_path=self.db)
        self.assertEqual(self.rows("workflow_grades"), before)

    def test_mock_http_adapter_integrates_request_response_storage(self):
        self.steps = [self.solver(), self.verifier(True)]
        def respond(request):
            status, payload = self.sender(json.loads(request.content))
            return httpx.Response(status, json=payload)
        with httpx.Client(transport=httpx.MockTransport(respond)) as client:
            def send(request):
                response = client.post("https://offline.example/controlled", json=request)
                return response.status_code, response.json()
            self.assertEqual(self.execute(sender=send)["status"], "accepted")
        self.assertEqual(len(self.rows("workflow_calls")), 2)
        with closing(store.connect(self.db)) as c:
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_twenty_seven_snapshots_and_legacy_defaults_are_preserved(self):
        before = deepcopy(models.default_model_configs())
        configs = workflow.configurations()
        self.assertEqual(len(configs), 27)
        self.assertEqual(len({tuple(c["solver_sequence"]) for c in configs}), 27)
        for config in configs:
            self.assertEqual(config["verifier_alias"], "flashlite25__reasoning")
            self.assertTrue(all(s["body_settings"]["temperature"] == 0.2 for s in config["solvers"]))
        configs[0]["solvers"][0]["body_settings"]["provider"]["only"].append("mutated")
        self.assertEqual(models.default_model_configs(), before)
        self.assertNotIn("mutated", configs[0]["solvers"][1]["body_settings"]["provider"]["only"])

    def test_limits_and_frozen_config_are_checked(self):
        for budget, count in ((0,6), (float("nan"),6), (float("inf"),6), (True,6), (.1,False), (.1,0)):
            with self.assertRaises(ValueError):
                workflow.Limits(budget, count)
        for sequence in (["qwen25"], ["qwen25","qwen3","unknown"]):
            with self.assertRaises(ValueError):
                workflow.configuration(sequence)
        self.config["verifier"]["settings"]["temperature"] = 0.5
        with self.assertRaisesRegex(ValueError, "trusted"):
            self.runner()


class DemoTests(unittest.TestCase):
    def test_offline_demo_has_reviewable_routes_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "demo"
            report = run_demo(output)
            self.assertEqual(report["new_generation_requests"], 0)
            self.assertEqual(report["actual_openrouter_cost_usd"], 0)
            self.assertEqual([r["mock_calls"] for r in report["results"]], [2,6,6,2])
            self.assertEqual([r["grade"]["workflow_score"] for r in report["results"]], [1,1,0,0])
            self.assertTrue((output / "report.json").exists())
            with self.assertRaisesRegex(ValueError, "new output"):
                run_demo(output)


if __name__ == "__main__":
    unittest.main()
