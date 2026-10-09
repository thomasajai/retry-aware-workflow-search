"""UCB-E decisions, Random pairing, oracle isolation and reusable saved overlays."""

from dataclasses import replace
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_search as search
import mathqa_vinelm as vine
from test_mathqa_vinelm import SEQUENCES, tiny_dataset


def documented_fixture():
    dataset = tiny_dataset()
    source = {**dataset.source, "database_sha256": "fixture", "run_id": "fixture",
              "dataset_sha256": "fixture", "plan_sha256": "fixture", "grader_version": "fixture",
              "question_count": len(dataset.questions), "configuration_count": len(dataset.sequences)}
    return replace(dataset, source=source)


class MatrixUCBTests(unittest.TestCase):
    def test_explores_every_configuration_before_repeating_one(self):
        s = search.PairSearch(SEQUENCES, ("q1", "q2", "q3"), strategy="agentopt", seed=11)
        first = []
        for _ in SEQUENCES:
            pair = s.next_pair()
            first.append(pair[1])
            s.observe(pair, 1)
        self.assertEqual(len(set(first)), len(SEQUENCES))
        self.assertEqual(first, s.priority)

    def test_ucb_sampling_and_empirical_recommendation_have_different_targets(self):
        questions = tuple(f"q{i:02}" for i in range(20))
        s = search.PairSearch(SEQUENCES, questions, strategy="agentopt", seed=0)
        leader, uncertain = SEQUENCES[:2]
        for sequence in SEQUENCES[2:]:
            s.observe((questions[0], sequence), 0)
        for i in range(10):
            s.observe((questions[i], leader), int(i < 8))
        s.observe((questions[0], uncertain), 1)
        s.observe((questions[1], uncertain), 0)
        self.assertAlmostEqual(s.bound(leader), .8 + math.sqrt(1 / 10))
        self.assertAlmostEqual(s.bound(uncertain), .5 + math.sqrt(1 / 2))
        self.assertEqual(s.next_pair()[1], uncertain)
        self.assertEqual(s.recommend(), (leader, .8))

    def test_completed_configuration_is_excluded_from_sampling_but_can_win(self):
        s = search.PairSearch(SEQUENCES, ("q1",), strategy="agentopt", seed=5)
        champion = s.priority[0]
        s.observe(("q1", champion), 1)
        self.assertEqual(s.bound(champion), -math.inf)
        self.assertNotEqual(s.next_pair()[1], champion)
        self.assertEqual(s.recommend(), (champion, 1))

    def test_unobserved_configurations_cannot_win_empirical_recommendation(self):
        s = search.PairSearch(SEQUENCES, ("q1", "q2"), strategy="agentopt", seed=3)
        self.assertIsNone(s.recommend()[1])
        sampled = s.priority[-1]
        s.observe(("q1", sampled), 0)
        self.assertEqual(s.recommend(), (sampled, 0))

    def test_invalid_weights_scores_and_duplicate_pairs_fail(self):
        for weight in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                search.PairSearch(SEQUENCES, ("q",), strategy="agentopt", exploration=weight)
        s = search.PairSearch(SEQUENCES, ("q",), strategy="agentopt")
        pair = s.next_pair()
        with self.assertRaises(ValueError):
            s.observe(pair, .5)
        s.observe(pair, 1)
        with self.assertRaises(ValueError):
            s.observe(pair, 1)


class ReplayTests(unittest.TestCase):
    def test_random_and_vinelm_use_identical_pairs_and_cumulative_costs(self):
        dataset = tiny_dataset()
        for seed in (0, 7, 33):
            random_run = search.simulate(dataset, strategy="random", seed=seed)
            vine_run = vine.simulate(dataset, seed=seed, smoothing=False)
            for random_point, vine_point in zip(random_run["history"], vine_run["history"]):
                for key in ("queried_question", "queried_configuration", "cost_cents"):
                    self.assertEqual(random_point[key], vine_point[key])

    def test_replays_ignore_hidden_oracle_values_and_costs_for_decisions(self):
        dataset = tiny_dataset()
        changed = replace(dataset, accuracy={s: 1 - a for s, a in dataset.accuracy.items()},
                          observations={pair: replace(o, cost_usd=Decimal("10"))
                                        for pair, o in dataset.observations.items()})
        for strategy in search.VERSIONS:
            a = search.simulate(dataset, strategy=strategy, seed=9)
            b = search.simulate(changed, strategy=strategy, seed=9)
            for first, second in zip(a["history"], b["history"]):
                for key in ("queried_question", "queried_configuration", "recommendation", "estimated_accuracy"):
                    self.assertEqual(first[key], second[key])
            self.assertNotEqual(a["history"][-1]["gap_pp"], b["history"][-1]["gap_pp"])

    def test_coverage_reproducibility_actual_costs_full_grid_optimum_and_no_network(self):
        dataset = tiny_dataset()
        for strategy in search.VERSIONS:
            with patch.object(socket, "socket", side_effect=AssertionError("Network prohibited")):
                run = search.simulate(dataset, strategy=strategy, seed=8)
            self.assertEqual(run, search.simulate(dataset, strategy=strategy, seed=8))
            pairs = {(p["queried_question"], p["queried_configuration"]) for p in run["history"][1:]}
            self.assertEqual(len(pairs), len(dataset.observations))
            self.assertEqual(Decimal(run["history"][-1]["cost_cents"]), Decimal("3.6"))
            self.assertEqual(run["history"][-1]["gap_pp"], 0)
            self.assertTrue(all(counts["observations"] == len(dataset.questions)
                                for counts in run["configuration_counts"].values()))

    def test_empty_replay_and_invalid_observation_limits(self):
        for strategy in search.VERSIONS:
            run = search.simulate(tiny_dataset(), strategy=strategy, max_pairs=0)
            self.assertEqual(len(run["history"]), 1)
            for n in (-1, 25):
                with self.assertRaises(ValueError):
                    search.simulate(tiny_dataset(), strategy=strategy, max_pairs=n)


class SavedComparisonTests(unittest.TestCase):
    def test_comparison_uses_only_saved_values_and_preserves_input_files(self):
        dataset = documented_fixture()
        results = [vine.experiment(dataset, seeds=3, smoothing=False),
                   search.experiment(dataset, strategy="agentopt", seeds=3),
                   search.experiment(dataset, strategy="random", seeds=3)]
        with tempfile.TemporaryDirectory() as folder:
            files = []
            for label, result in zip(("vinelm", "agentopt", "random"), results):
                output = Path(folder) / f"{label}.json"
                vine.save_outputs(result, output)
                files.append(output)
            checksums = [hashlib.sha256(p.read_bytes()).hexdigest() for p in files]
            with patch.object(vine, "load_dataset", side_effect=AssertionError("No database reads")), patch.object(
                    search, "simulate", side_effect=AssertionError("No search reruns")):
                comparison = search.save_comparison(files, Path(folder) / "comparison.json")
            self.assertEqual(checksums, [hashlib.sha256(p.read_bytes()).hexdigest() for p in files])
            self.assertEqual(len(comparison["series"]), 3)
            budgets = [[p["cost_cents"] for p in series["curve"]] for series in comparison["series"]]
            self.assertEqual(budgets[0], budgets[1])
            self.assertEqual(budgets[1], budgets[2])
            self.assertEqual(comparison["series"][0]["curve"][0]["mean_gap_pp"], results[0]["curve"][0]["mean_gap_pp"])
            self.assertEqual(len((Path(folder) / "comparison.csv").read_text().splitlines()), 364)
            with self.assertRaises(ValueError):
                search.save_comparison(files, files[0])

    def test_different_sources_seeds_limits_and_duplicate_strategies_are_rejected(self):
        dataset = documented_fixture()
        result = search.experiment(dataset, strategy="random", seeds=2)
        bad_source = {**result, "source": {**result["source"], "database_sha256": "other"}}
        with self.assertRaisesRegex(ValueError, "datasets"):
            search.assert_compatible([result, bad_source])
        with self.assertRaisesRegex(ValueError, "seed"):
            search.assert_compatible([result, search.experiment(dataset, strategy="agentopt", seeds=2, first_seed=1)])
        with self.assertRaisesRegex(ValueError, "limits"):
            search.assert_compatible([result, search.experiment(dataset, strategy="agentopt", seeds=2, max_pairs=5)])
        with tempfile.TemporaryDirectory() as folder:
            path = vine.save_outputs(result, Path(folder) / "random.json")
            with self.assertRaisesRegex(ValueError, "distinct strategies"):
                search.save_comparison([path, path], Path(folder) / "comparison.json")

    def test_explicit_budget_grid_never_looks_ahead_or_extrapolates(self):
        runs = [{"history": [{"cost_cents": "0", "gap_pp": 10},
                             {"cost_cents": "2", "gap_pp": 0}]}]
        curve = vine.aggregate(runs, budgets=[Decimal(0), Decimal("1.99"), Decimal(2)])
        self.assertEqual([p["mean_gap_pp"] for p in curve], [10, 10, 0])
        for budgets in ([Decimal(3)], [Decimal(-1)], [Decimal(2), Decimal(1)]):
            with self.assertRaises(ValueError):
                vine.aggregate(runs, budgets=budgets)

    def test_version_and_snapshot_provenance(self):
        spec = vine.SPECIFICATION.read_text(encoding="utf-8")
        for strategy, version in search.VERSIONS.items():
            self.assertIn(version, spec)
            result = search.experiment(documented_fixture(), strategy=strategy, seeds=1, max_pairs=3)
            with tempfile.TemporaryDirectory() as folder:
                output = search.save_result(result, Path(folder) / "result.json")
                self.assertEqual(hashlib.sha256(output.with_suffix(".spec.md").read_bytes()).hexdigest(),
                                 result["specification"]["sha256"])
                self.assertEqual(hashlib.sha256(output.with_suffix(".implementation.py").read_bytes()).hexdigest(),
                                 result["implementation_sha256"])
                self.assertEqual(hashlib.sha256(output.with_suffix(".shared-implementation.py").read_bytes()).hexdigest(),
                                 result["shared_implementation_sha256"])


if __name__ == "__main__":
    unittest.main()
