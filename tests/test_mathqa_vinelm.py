"""Search semantics, isolation, frozen-grid reconciliation and admission checks."""

from dataclasses import replace
from contextlib import closing
from decimal import Decimal
import hashlib
from itertools import product
import json
from pathlib import Path
import shutil
import socket
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_vinelm as vine

try:
    import numpy
except ImportError:
    numpy = None

SEQUENCES = tuple(product(("a", "b"), repeat=3))


def observation(question="q", sequence=("a", "b", "a"), outcomes=("correct_accept",), cost="0.001"):
    return vine.Observation(question, sequence, outcomes, Decimal(cost))


def tiny_dataset():
    questions = ("q1", "q2", "q3")
    observations = {(q, s): observation(q, s, ("correct_accept",) if s[0] == "a" else ("incorrect_stop",),
                                        cost="0.001" if s[0] == "a" else "0.002")
                    for q, s in product(questions, SEQUENCES)}
    return vine.Dataset(SEQUENCES, questions, observations, {s: int(s[0] == "a") for s in SEQUENCES},
                        {s: "-".join(s) for s in SEQUENCES}, {"database": str(vine.DATABASE)})


class EstimatorTests(unittest.TestCase):
    def estimator(self):
        return vine.VineLMEstimator(SEQUENCES, smoothing=False)

    def test_wrong_accept_stops_and_is_not_continuation(self):
        e = self.estimator()
        e.observe(observation(outcomes=("incorrect_stop",)))
        success, continuation = e.rates(("a",))
        self.assertAlmostEqual(success, .2)
        self.assertAlmostEqual(continuation, .2)
        self.assertNotAlmostEqual(continuation, 1 - success)
        self.assertNotIn(("a", "b"), e.counts)
        self.assertNotIn(("a", "b", "a"), e.counts)

    def test_late_correct_accept_updates_only_reached_prefixes(self):
        e = self.estimator()
        e.observe(observation(outcomes=("continue", "correct_accept")))
        self.assertEqual(dict(e.counts), {("a",): [0, 1, 0], ("a", "b"): [1, 0, 0]})
        self.assertNotIn(("a", "b", "a"), e.counts)

    def test_decomposition_accounts_for_three_disjoint_success_events(self):
        e = self.estimator()
        e.observe(observation("q1", outcomes=("correct_accept",)))
        e.observe(observation("q2", outcomes=("continue", "correct_accept")))
        e.observe(observation("q3", outcomes=("continue", "continue", "correct_accept")))
        # Depth-1 posterior (s,r)=(1.5/4.5,2.5/4.5); depth 2=(1.5/3.5,1.5/3.5);
        # depth 3 success=1.5/2. Evidence at shared prefixes is pooled.
        expected = 1.5 / 4.5 + 2.5 / 4.5 * (1.5 / 3.5) + 2.5 / 4.5 * (1.5 / 3.5) * .75
        self.assertAlmostEqual(e.estimates()[("a", "b", "a")], expected)
        self.assertTrue(all(0 <= v <= 1 for v in e.estimates().values()))

    def test_duplicate_and_invalid_observations_do_not_mutate_counts(self):
        e = self.estimator()
        o = observation()
        e.observe(o)
        before = {k: v.copy() for k, v in e.counts.items()}
        for invalid in (o, observation("q2", outcomes=("correct_accept", "continue")),
                        observation("q3", outcomes=("continue",))):
            with self.assertRaises(ValueError):
                e.observe(invalid)
        self.assertEqual(dict(e.counts), before)

    def test_positive_finite_pseudocount_required(self):
        for alpha in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                vine.VineLMEstimator(SEQUENCES, pseudocount=alpha)

    @unittest.skipIf(numpy is None, "Install profiling extra for SVD checks.")
    def test_svd_preserves_rank_one_matrix_and_handles_missing_columns(self):
        parents = sorted({s[:2] for s in SEQUENCES})
        rates = {p + (m,): (i + 1) / 4 * (.5 if m == "a" else 1)
                 for i, p in enumerate(parents) for m in ("a", "b")}
        projected = vine.rank_one_rates(rates, SEQUENCES)
        for p, value in rates.items():
            self.assertAlmostEqual(projected[p], value)
        missing = vine.rank_one_rates({("a", "a", "a"): .4}, SEQUENCES)
        for p in parents:
            self.assertAlmostEqual(missing[p + ("a",)], .4)
            self.assertAlmostEqual(missing[p + ("b",)], .5)
        self.assertTrue(all(0 <= v <= 1 for v in missing.values()))


class SimulationTests(unittest.TestCase):
    def test_hidden_oracle_accuracy_never_changes_sampling_or_recommendation(self):
        dataset = tiny_dataset()
        changed_oracle = replace(dataset, accuracy={s: 1 - a for s, a in dataset.accuracy.items()})
        first = vine.simulate(dataset, seed=7, smoothing=False)
        second = vine.simulate(changed_oracle, seed=7, smoothing=False)
        for a, b in zip(first["history"], second["history"]):
            for field in ("queried_question", "queried_configuration", "recommendation", "estimated_accuracy", "cost_cents"):
                self.assertEqual(a[field], b[field])
        self.assertNotEqual(first["history"][-1]["gap_pp"], second["history"][-1]["gap_pp"])

    def test_unrevealed_costs_never_change_sampling_or_recommendation(self):
        dataset = tiny_dataset()
        changed_costs = replace(dataset, observations={key: replace(o, cost_usd=Decimal("10"))
                                                       for key, o in dataset.observations.items()})
        first = vine.simulate(dataset, seed=3, smoothing=False)
        second = vine.simulate(changed_costs, seed=3, smoothing=False)
        self.assertEqual([(p["queried_question"], p["queried_configuration"], p["recommendation"])
                          for p in first["history"]],
                         [(p["queried_question"], p["queried_configuration"], p["recommendation"])
                          for p in second["history"]])

    def test_exact_cost_pair_coverage_reproducibility_and_no_network(self):
        dataset = tiny_dataset()
        with patch.object(socket, "socket", side_effect=AssertionError("Network is out of scope")):
            run = vine.simulate(dataset, seed=9, smoothing=False)
        self.assertEqual(run, vine.simulate(dataset, seed=9, smoothing=False))
        pairs = {(p["queried_question"], p["queried_configuration"]) for p in run["history"][1:]}
        self.assertEqual(len(pairs), len(dataset.observations))
        self.assertEqual(Decimal(run["history"][-1]["cost_cents"]), Decimal("3.6"))
        changed_seed = vine.simulate(dataset, seed=10, smoothing=False)
        self.assertNotEqual(run["history"], changed_seed["history"])
        self.assertEqual(run["prefix_counts"], changed_seed["prefix_counts"])

    def test_budget_aggregation_uses_only_completed_observations(self):
        runs = [{"history": [{"cost_cents": "0", "gap_pp": 20},
                             {"cost_cents": "2", "gap_pp": 5},
                             {"cost_cents": "4", "gap_pp": 0}]},
                {"history": [{"cost_cents": "0", "gap_pp": 10},
                             {"cost_cents": "3", "gap_pp": 0},
                             {"cost_cents": "5", "gap_pp": 0}]}]
        curve = vine.aggregate(runs, points=5)
        self.assertEqual([p["mean_gap_pp"] for p in curve], [15, 15, 7.5, 2.5, 0])
        self.assertEqual(Decimal(curve[-1]["cost_cents"]), Decimal(4))
        self.assertEqual(curve[0]["p10_gap_pp"], 11)
        self.assertEqual(curve[0]["p90_gap_pp"], 19)

    def test_zero_pair_run_and_invalid_limits(self):
        result = vine.simulate(tiny_dataset(), max_pairs=0, smoothing=False)
        self.assertEqual(len(result["history"]), 1)
        self.assertEqual(result["history"][0]["cost_cents"], "0")
        for count in (-1, 25):
            with self.assertRaises(ValueError):
                vine.simulate(tiny_dataset(), max_pairs=count, smoothing=False)

    def test_specification_version_and_result_provenance(self):
        self.assertIn(vine.VERSION, vine.SPECIFICATION.read_text(encoding="utf-8"))
        result = vine.experiment(tiny_dataset(), seeds=2, max_pairs=3, smoothing=False)
        self.assertEqual(result["specification"]["sha256"], hashlib.sha256(vine.SPECIFICATION.read_bytes()).hexdigest())
        self.assertEqual(result["implementation_sha256"], hashlib.sha256(Path(vine.__file__).read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory() as folder:
            output = vine.save_outputs(result, Path(folder) / "result.json")
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)
            self.assertTrue(output.with_suffix(".csv").is_file())


class FrozenDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = hashlib.sha256(vine.DATABASE.read_bytes()).hexdigest()
        cls.dataset = vine.load_dataset()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(vine.DATABASE.read_bytes()).hexdigest() == cls.before

    def test_frozen_grid_accuracy_cost_and_early_stops(self):
        dataset = self.dataset
        self.assertEqual((len(dataset.questions), len(dataset.sequences), len(dataset.observations)), (20, 27, 540))
        self.assertEqual(max(dataset.accuracy.values()), .65)
        self.assertEqual(sum(v == .65 for v in dataset.accuracy.values()), 4)
        self.assertEqual(sum((o.cost_usd for o in dataset.observations.values()), Decimal(0)), Decimal("0.30118175983"))
        self.assertEqual(sum(len(o.outcomes) for o in dataset.observations.values()), 1132)
        self.assertEqual(sum(o.outcomes[-1] == "correct_accept" for o in dataset.observations.values()), 292)
        # 294 accepted executions: two terminate wrong rather than continue.
        self.assertEqual(sum(len(o.outcomes) < 3 and o.outcomes[-1] == "incorrect_stop"
                             for o in dataset.observations.values()), 2)

    def test_saved_rejected_correct_answers_and_truncations_continue(self):
        by_sequence_name = {name: seq for seq, name in self.dataset.names.items()}
        with closing(sqlite3.connect(vine.DATABASE.as_uri() + "?mode=ro", uri=True)) as c:
            rows = c.execute("SELECT e.question_id,f.name,a.position,a.verification_status,a.usable,g.option_correct "
                             "FROM workflow_attempts a JOIN workflow_executions e USING(execution_id) "
                             "JOIN workflow_configs f USING(config_id) JOIN workflow_grades g USING(attempt_id) "
                             "WHERE e.run_id=? AND g.grader_version=? AND a.position<3 "
                             "AND (a.usable=0 OR (a.verification_status='reject' AND g.option_correct=1))",
                             (vine.RUN_ID, vine.GRADER)).fetchall()
        self.assertTrue(any(row[-1] == 1 for row in rows))
        self.assertTrue(any(row[-2] == 0 for row in rows))
        for question, name, position, *_ in rows:
            self.assertEqual(self.dataset.observations[question, by_sequence_name[name]].outcomes[position - 1], "continue")

    def test_bad_billing_grades_grid_and_verification_are_rejected(self):
        changes = [
            ("UPDATE workflow_calls SET cost_usd=NULL WHERE call_id=(SELECT solver_call_id FROM workflow_attempts a "
             "JOIN workflow_executions e USING(execution_id) WHERE e.run_id=? LIMIT 1)", "billing"),
            ("DELETE FROM workflow_grades WHERE grade_id=(SELECT g.grade_id FROM workflow_grades g JOIN "
             "workflow_executions e USING(execution_id) WHERE e.run_id=? AND g.attempt_id IS NULL LIMIT 1)", "graded"),
            ("DELETE FROM workflow_executions WHERE execution_id=(SELECT execution_id FROM workflow_executions "
             "WHERE run_id=? LIMIT 1)", "grid"),
            ("UPDATE workflow_attempts SET verification_status='pending' WHERE attempt_id=(SELECT a.attempt_id "
             "FROM workflow_attempts a JOIN workflow_executions e USING(execution_id) WHERE e.run_id=? LIMIT 1)", "verification"),
        ]
        with tempfile.TemporaryDirectory() as folder:
            for sql, expected in changes:
                with self.subTest(expected=expected):
                    copy = Path(folder) / "fixture.sqlite3"
                    shutil.copyfile(vine.DATABASE, copy)
                    with closing(sqlite3.connect(copy)) as c, c:
                        c.execute(sql, (vine.RUN_ID,))
                    with self.assertRaisesRegex(ValueError, expected):
                        vine.load_dataset(copy)

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing.sqlite3"
            with self.assertRaises(FileNotFoundError):
                vine.load_dataset(missing)
            self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
