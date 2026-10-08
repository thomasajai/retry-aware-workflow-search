"""Offline aggregation and safe HTML export; no credentials or paid adapters."""

from decimal import Decimal
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_workflow_trie as trie


def execution(eid, sequence, score, position, status="accepted", question="q"):
    return dict(execution_id=eid, sequence=sequence, question_id=question,
                score=score, accepted_position=position, status=status, elapsed_seconds=2)


def attempt(aid, eid, position, correct=1, accepted=False):
    return dict(attempt_id=aid, execution_id=eid, position=position, has_grade=True,
                option_correct=correct, verification_status="accept" if accepted else "reject")


def call(aid, role, cost, finish=None):
    return dict(attempt_id=aid, role=role, cost_usd=cost, finish_reason=finish,
                input_tokens=10, output_tokens=20, reasoning_tokens=5, elapsed_seconds=.5)


class TrieMetricsTests(unittest.TestCase):
    def setUp(self):
        # Same first solver, independently paid calls; one branch accepts early,
        # the other recovers at position 2. Position 3 is never called.
        self.executions = [execution("e1", ["a", "b", "a"], 1, 1),
                           execution("e2", ["a", "b", "b"], 1, 2)]
        self.schedule = [dict(sequence=e["sequence"], question_id="q") for e in self.executions]
        self.attempts = [attempt("a1", "e1", 1, accepted=True), attempt("a2", "e2", 1, correct=0),
                         attempt("a3", "e2", 2, accepted=True)]
        self.calls = [call("a1", "solver", ".01"), call("a1", "verifier", ".02"),
                      call("a2", "solver", ".03"), call("a2", "verifier", ".04"),
                      call("a3", "solver", ".05"), call("a3", "verifier", ".06")]

    def metrics(self, prefix, **kwargs):
        return trie.prefix_metrics(prefix, self.executions, self.attempts, self.calls, self.schedule, **kwargs)

    def test_shared_prefix_counts_fresh_calls_and_accuracy_through_position(self):
        first = self.metrics(["a"])
        self.assertEqual(Decimal(first["cost_usd"]), Decimal(".10"))
        self.assertEqual(Decimal(first["mean_cost_usd"]), Decimal(".05"))
        self.assertEqual(first["requests"], 4)
        self.assertEqual(first["through_accuracy"], .5)
        self.assertEqual(first["final_accuracy"], 1)
        second = self.metrics(["a", "b"])
        self.assertEqual(Decimal(second["cost_usd"]), Decimal(".21"))
        self.assertEqual(second["slot_reached"], 1)
        self.assertEqual(second["planned"], 2)
        self.assertEqual(second["through_accuracy"], 1)

    def test_uncalled_leaf_keeps_actual_early_acceptance_cost(self):
        leaf = self.metrics(["a", "b", "a"])
        self.assertEqual(leaf["slot_reached"], 0)
        self.assertEqual(leaf["slot_requests"], 0)
        self.assertEqual(Decimal(leaf["cost_usd"]), Decimal(".03"))
        self.assertEqual(leaf["final_accuracy"], 1)
        leaf_sum = sum(Decimal(self.metrics(e["sequence"])["cost_usd"]) for e in self.executions)
        self.assertEqual(leaf_sum, Decimal(self.metrics([])["cost_usd"]))

    def test_truncation_is_paid_and_exhaustion_is_incorrect(self):
        self.executions[1].update(score=0, status="exhausted", accepted_position=None)
        self.attempts.append(attempt("a4", "e2", 3, correct=None))
        self.calls.append(call("a4", "solver", ".07", finish="length"))
        leaf = self.metrics(["a", "b", "b"])
        self.assertEqual(Decimal(leaf["cost_usd"]), Decimal(".25"))
        self.assertEqual(leaf["truncations"], 1)
        self.assertEqual(leaf["slot_requests"], 1)
        self.assertEqual(leaf["slot_verifier_cost_usd"], "0")
        self.assertEqual(leaf["final_accuracy"], 0)

    def test_unknown_billing_and_incomplete_grades_are_preserved(self):
        self.executions[1].update(score=None, status="billing_unresolved", accepted_position=None)
        self.calls[-1]["cost_usd"] = None
        self.schedule.append(dict(sequence=["a", "b", "b"], question_id="q2"))
        metric = self.metrics(["a", "b"])
        self.assertFalse(metric["complete"])
        self.assertEqual(metric["unknown_cost_calls"], 1)
        self.assertEqual(metric["graded"], 1)
        self.assertEqual(metric["planned"], 3)
        self.assertEqual(metric["final_accuracy"], 1)  # Completed-only, not 1/3.
        q2 = self.metrics(["a", "b"], question_id="q2")
        self.assertIsNone(q2["final_accuracy"])
        self.assertEqual(q2["requests"], 0)
        self.assertFalse(q2["complete"])


class TrieExportTests(unittest.TestCase):
    def test_embedded_content_cannot_close_json_script(self):
        payload = {"question": '</script><script>alert("x")</script>&\u2028'}
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "tree.html"
            with patch.object(trie, "load_run", return_value=payload):
                trie.export_trie(output_path=output)
            html = output.read_text(encoding="utf-8")
            match = re.search(r'<script id="run-data" type="application/json">(.*?)</script>', html, re.S)
            self.assertEqual(json.loads(match[1]), payload)
            self.assertNotIn("<script>", match[1])
            self.assertIn("\\u003c", match[1])

    def test_cannot_overwrite_template(self):
        with patch.object(trie, "load_run", return_value={}):
            with self.assertRaisesRegex(ValueError, "distinct"):
                trie.export_trie(output_path=trie.TEMPLATE_PATH)

    def test_missing_read_only_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "missing.sqlite3"
            with self.assertRaises(trie.sqlite3.OperationalError):
                trie.load_run(database_path=db)
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
