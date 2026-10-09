"""Finite-population DP, synchronized phases, oracle isolation and cost matching."""

from bisect import bisect_right
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

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_bandits as bandits
import mathqa_search as search
import mathqa_vinelm as vine
from test_mathqa_vinelm import SEQUENCES, tiny_dataset
from test_mathqa_search import documented_fixture


class GittinsTests(unittest.TestCase):
    def test_convolution_matches_independent_direct_piecewise_linear_integral(self):
        grid = np.linspace(-2, 2, 65)
        values = np.maximum(grid - .17, 0)
        slopes = np.diff(values) / (grid[1] - grid[0])
        changes = np.diff(np.r_[0., slopes, 1.])
        expected = []
        for x in grid:
            terms = []
            for location, delta in zip(grid, changes):
                z = (x - location) / .23
                ei = (x - location) * .5 * math.erfc(-z / math.sqrt(2))
                ei += .23 * math.exp(-z * z / 2) / math.sqrt(2 * math.pi)
                terms.append(delta * ei)
            expected.append(values[0] + sum(terms))
        np.testing.assert_allclose(bandits.convolve_m_diff(values, .23, grid), expected, atol=2e-13)

    def test_one_step_root_matches_analytic_gaussian_expected_improvement(self):
        # With one remaining observation Q(s)=GaussianEI(s,sigma)-charge.
        roots = bandits.finite_roots(1, transition_charge=.01, grid_points=4097)
        sigma = (1 + .25 / .04) * .04 / math.sqrt(.04 + .25)
        left, right = -5 * sigma, 5 * sigma
        for _ in range(80):
            mid = (left + right) / 2
            z = mid / sigma
            q = mid * .5 * math.erfc(-z / math.sqrt(2))
            q += sigma * math.exp(-z * z / 2) / math.sqrt(2 * math.pi) - .01
            if q < 0:
                left = mid
            else:
                right = mid
        dx = (10 * sigma + .0101) / 4096
        self.assertLess(abs(roots[0] - (left + right) / 2), 2 * dx)
        self.assertEqual(roots[-1], 0)

    def test_finite_target_counts_observed_scores_and_completed_variance_is_zero(self):
        s = bandits.Gittins(SEQUENCES[:1], ("q1", "q2", "q3"))
        pair = s.next_pair()
        s.observe(pair, 1)
        latent_v = 1 / (1 / .04 + 1 / .25)
        latent_mean = latent_v * (.5 / .04 + 1 / .25)
        mean, var = s.moments(SEQUENCES[0])
        self.assertAlmostEqual(mean, (1 + 2 * latent_mean) / 3)
        self.assertAlmostEqual(var, (4 * latent_v + 2 * .25) / 9)
        for score in (0, 1):
            s.observe(s.next_pair(), score)
        self.assertEqual(s.moments(SEQUENCES[0]), (2 / 3, 0))
        self.assertEqual(s.indices()[SEQUENCES[0]], 2 / 3)
        self.assertIsNone(s.next_pair())

    def test_finite_variance_drop_matches_dp_transition_variance(self):
        n = 20
        for t in range(n):
            v = 1 / (1 / .04 + t / .25)
            v_next = 1 / (1 / .04 + (t + 1) / .25)
            remaining = n - t
            var_now = (remaining ** 2 * v + remaining * .25) / n ** 2
            var_next = ((remaining - 1) ** 2 * v_next + (remaining - 1) * .25) / n ** 2
            sigma = (1 + .25 / (n * .04)) * v / math.sqrt(v + .25)
            self.assertAlmostEqual(var_now - var_next, sigma ** 2)

    def test_continues_after_natural_stopping_and_completed_arms_remain_recommendable(self):
        run = bandits.simulate(tiny_dataset(), strategy="gittins", seed=2)
        self.assertEqual(run["history"][-1]["step"], 24)
        self.assertEqual(run["history"][-1]["gap_pp"], 0)
        self.assertIsNotNone(run["natural_stop_step"])
        self.assertLessEqual(run["natural_stop_step"], 24)

    def test_grid_refinement_stabilizes_exploration_bonus(self):
        coarse = bandits.finite_roots(20)
        fine = bandits.finite_roots(20, grid_points=4097)
        np.testing.assert_allclose(coarse, fine, atol=.003)
        self.assertTrue(all(coarse[:-1] < 0))

    def test_invalid_priors_charges_and_grids_fail(self):
        for kwargs in ({"prior_variance": 0}, {"noise_variance": -1},
                       {"transition_charge": float("nan")}, {"grid_points": 100}):
            with self.assertRaises(ValueError):
                bandits.Gittins(SEQUENCES, ("q1", "q2"), **kwargs)
        with self.assertRaises(ValueError):
            bandits.Gittins(SEQUENCES, ("q",), prior_mean=2)


class SySRsTests(unittest.TestCase):
    def test_reference_schedule_and_small_population_reallocation(self):
        self.assertEqual(bandits.sysrs_schedule(54, 27, 20).tolist(),
                         [0] + [1] * 20 + [2] * 4 + [3, 4])
        self.assertEqual(bandits.sysrs_schedule(540, 27, 20).tolist(), [0] + [20] * 26)

    def test_shared_question_and_no_elimination_until_entire_phase_finishes(self):
        sequences = tuple((str(i),) for i in range(27))
        s = bandits.SySRs(sequences, tuple(f"q{i}" for i in range(20)), seed=7)
        pairs = []
        for i in range(27):
            pair = s.next_pair()
            pairs.append(pair)
            self.assertEqual(len(s.active), 27)
            self.assertEqual(s.eliminations, [])
            s.observe(pair, int(i < 10))
        self.assertEqual(len({q for q, _ in pairs}), 1)
        self.assertEqual(len({seq for _, seq in pairs}), 27)
        s.next_pair()
        self.assertGreater(len(s.eliminations), 0)
        self.assertTrue(all(e["step"] == 27 for e in s.eliminations))

    def test_partial_round_hard_pair_budget_does_not_overshoot(self):
        s = bandits.SySRs(tuple((str(i),) for i in range(27)), tuple(f"q{i}" for i in range(20)),
                          planned_budget=216)
        while (pair := s.next_pair()) is not None:
            s.observe(pair, 1)
        self.assertEqual(len(s.seen), 216)
        self.assertEqual(s.stop_reason, "planned_budget_reached")

    def test_eliminated_configurations_are_not_queried_again(self):
        run = bandits.simulate(tiny_dataset(), strategy="sysrs", seed=2, planned_budget=16)
        for event in run["eliminations"]:
            name = "-".join(event["configuration"])
            later = [p for p in run["history"] if p["step"] > event["step"]]
            self.assertTrue(all(p["queried_configuration"] != name for p in later))
        self.assertLessEqual(run["history"][-1]["step"], 16)

    def test_completed_single_configuration_stops_without_eliminating_it(self):
        s = bandits.SySRs(SEQUENCES[:1], ("q1", "q2"), planned_budget=2)
        for _ in range(2):
            s.observe(s.next_pair(), 1)
        self.assertIsNone(s.next_pair())
        self.assertEqual(s.recommend(), (SEQUENCES[0], 1))

    def test_budget_is_prespecified_and_smaller_horizon_changes_schedule(self):
        self.assertNotEqual(bandits.sysrs_schedule(54, 27, 20).tolist(),
                            bandits.sysrs_schedule(108, 27, 20).tolist())
        for budget in (0, 8, 25):
            with self.assertRaises(ValueError):
                bandits.SySRs(SEQUENCES, ("q1", "q2", "q3"), planned_budget=budget)


class OfflineReplayTests(unittest.TestCase):
    def test_no_network_hidden_accuracy_or_costs_affect_decisions(self):
        dataset = tiny_dataset()
        changed = replace(dataset, accuracy={s: 1 - a for s, a in dataset.accuracy.items()},
                          observations={p: replace(o, cost_usd=Decimal(10)) for p, o in dataset.observations.items()})
        for strategy in bandits.VERSIONS:
            with patch.object(socket, "socket", side_effect=AssertionError("No network")):
                original = bandits.simulate(dataset, strategy=strategy, seed=4)
                alternative = bandits.simulate(changed, strategy=strategy, seed=4)
            self.assertEqual(len(original["history"]), len(alternative["history"]))
            for a, b in zip(original["history"], alternative["history"]):
                for key in ("queried_question", "queried_configuration", "recommendation", "estimated_accuracy"):
                    self.assertEqual(a[key], b[key])
            self.assertNotEqual(original["history"][-1]["cost_cents"], alternative["history"][-1]["cost_cents"])

    def test_recorded_costs_reconcile_and_pending_queries_are_enforced(self):
        dataset = tiny_dataset()
        for strategy in bandits.VERSIONS:
            run = bandits.simulate(dataset, strategy=strategy, seed=3)
            queries = [p for p in run["history"] if p["queried_question"] is not None]
            self.assertEqual(len(queries), run["history"][-1]["step"])
            pairs = [(p["queried_question"], tuple(p["queried_configuration"].split("-"))) for p in queries]
            self.assertEqual(len(pairs), len(set(pairs)))
            expected = sum((dataset.observations[p].cost_usd for p in pairs), Decimal(0)) * 100
            self.assertEqual(Decimal(run["history"][-1]["cost_cents"]), expected)
        for cls in (bandits.Gittins, bandits.SySRs):
            policy = cls(SEQUENCES, dataset.questions)
            pair = policy.next_pair()
            with self.assertRaises(ValueError):
                policy.next_pair()
            with self.assertRaises(ValueError):
                policy.observe(pair, .5)
            policy.observe(pair, 1)
            with self.assertRaises(ValueError):
                policy.observe(pair, 1)

    def test_snapshots_and_seed_reproducibility(self):
        for strategy in bandits.VERSIONS:
            result = bandits.experiment(documented_fixture(), strategy=strategy, seeds=2)
            self.assertEqual(result["runs"][0], bandits.simulate(documented_fixture(), strategy=strategy))
            with tempfile.TemporaryDirectory() as folder:
                output = bandits.save_result(result, Path(folder) / "result.json")
                self.assertEqual(hashlib.sha256(output.with_suffix(".implementation.py").read_bytes()).hexdigest(),
                                 result["implementation_sha256"])
                self.assertEqual(hashlib.sha256(output.with_suffix(".spec.md").read_bytes()).hexdigest(),
                                 result["specification"]["sha256"])
            self.assertIn(bandits.VERSIONS[strategy], vine.SPECIFICATION.read_text())


class ComparisonTests(unittest.TestCase):
    def make_files(self, folder):
        dataset = documented_fixture()
        results = [vine.experiment(dataset, seeds=2, smoothing=False),
                   search.experiment(dataset, strategy="agentopt", seeds=2),
                   search.experiment(dataset, strategy="random", seeds=2),
                   bandits.experiment(dataset, strategy="gittins", seeds=2)]
        files = [vine.save_outputs(r, Path(folder) / f"{i}.json") for i, r in enumerate(results)]
        return dataset, results, files

    def test_extended_overlay_accepts_natural_stop_and_never_extends_its_domain(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset, _, files = self.make_files(folder)
            result = bandits.experiment(dataset, strategy="sysrs", seeds=2)
            files.append(vine.save_outputs(result, Path(folder) / "sysrs.json"))
            comparison = bandits.save_extended_comparison(files, Path(folder) / "extended.json")
            self.assertEqual(len(comparison["series"]), 5)
            self.assertEqual(comparison["series"][-1]["curve"], vine.aggregate(result["runs"]))
            with self.assertRaises(ValueError):
                bandits.save_extended_comparison(files, files[0])

    def test_budget_matching_uses_per_seed_spend_not_average_spend_or_future_outcomes(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset, results, files = self.make_files(folder)
            horizons = [bandits.experiment(dataset, strategy="sysrs", seeds=2, planned_budget=n) for n in (12, 24)]
            with patch.object(vine, "load_dataset", side_effect=AssertionError("No database reads")):
                c = bandits.save_budget_matched_comparison(files, horizons, Path(folder) / "matched.json")
            for i, horizon in enumerate(horizons, start=1):
                caps = [Decimal(r["history"][-1]["cost_cents"]) for r in horizon["runs"]]
                self.assertEqual(Decimal(c["series"][0]["curve"][i]["cost_cents"]), sum(caps) / len(caps))
                for series, result in zip(c["series"], results):
                    gaps = []
                    for run, cap in zip(result["runs"], caps):
                        costs = [Decimal(p["cost_cents"]) for p in run["history"]]
                        gaps.append(run["history"][bisect_right(costs, cap) - 1]["gap_pp"])
                    self.assertEqual(series["curve"][i]["mean_gap_pp"], sum(gaps) / len(gaps))
            self.assertEqual(len(c["series"]), 5)
            for point, horizon in zip(c["series"][-1]["curve"][1:], horizons):
                self.assertEqual(point["mean_gap_pp"], sum(r["history"][-1]["gap_pp"] for r in horizon["runs"]) / 2)
            with self.assertRaises(ValueError):
                bandits.save_budget_matched_comparison(files, horizons[::-1], Path(folder) / "bad.json")

    def test_horizon_source_mismatch_and_missing_budget_coverage_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset, results, files = self.make_files(folder)
            horizon = bandits.experiment(dataset, strategy="sysrs", seeds=2, planned_budget=24)
            wrong_file = vine.save_outputs(results[0], Path(folder) / "wrong.json")
            with self.assertRaisesRegex(ValueError, "provenance"):
                bandits.save_budget_matched_comparison(files, [horizon], Path(folder) / "matched.json",
                                                      horizon_files=[wrong_file])
            partial = search.experiment(dataset, strategy="random", seeds=2, max_pairs=2)
            path = vine.save_outputs(partial, Path(folder) / "partial.json")
            with self.assertRaisesRegex(ValueError, "extrapolation"):
                bandits.save_budget_matched_comparison([path], [horizon], Path(folder) / "unsupported.json")

    def test_portable_export_preserves_sources_and_original_baseline_files(self):
        with tempfile.TemporaryDirectory() as folder:
            output_dir, portable = Path(folder) / "full", Path(folder) / "portable"
            output_dir.mkdir()
            portable.mkdir()
            sentinel = portable / "vinelm-adapted.csv"
            sentinel.write_bytes(b"original baseline")
            dataset, results, files = self.make_files(output_dir)
            vine.save_outputs(results[-1], output_dir / "gittins.json")
            horizons = [bandits.experiment(dataset, strategy="sysrs", seeds=2, planned_budget=n) for n in (12, 24)]
            sysrs_file = vine.save_outputs(horizons[0], output_dir / "sysrs.json")
            bandits.save_extended_comparison([*files, sysrs_file], output_dir / "search-comparison-extended.json")
            bandits.save_budget_matched_comparison(files, horizons, output_dir / "search-comparison-budget-matched.json")
            bandits.save_budget_summary(horizons, output_dir / "sysrs-budget-sweep.json")
            before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output_dir.glob("*.*")}
            paths = bandits.export_portable(output_dir, portable)
            self.assertEqual(len(paths), 8)
            self.assertEqual(sentinel.read_bytes(), b"original baseline")
            self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output_dir.glob("*.*")})
            payload = json.loads((portable / "search-comparison-budget-matched.json").read_text())
            self.assertEqual(payload["source"]["database"], "data/experiments/mathqa_runs.sqlite3")
            self.assertEqual(payload["plotter"]["path"], "scripts/mathqa_search_plot.py")
            self.assertEqual((portable / "gittins.csv").read_bytes(), (output_dir / "gittins.csv").read_bytes())


if __name__ == "__main__":
    unittest.main()
