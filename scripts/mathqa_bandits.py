"""Offline, equal-cost Gittins and synchronized successive rejects.

Only the frozen SQLite loader accesses saved results. Policies receive identities
and one queried binary score at a time; recorded monetary costs are evaluator-only.
Reference: QianJaneXie/BanditGittinsEval, a4992e22a48e781327efd5411fb7d0921ad5ab61.
The NumPy DP preserves the reference m-diff convolution and finite-row target.
See notes/workflow-search-experiment-spec.md for every adaptation.
"""

import argparse
from collections import deque
from decimal import Decimal
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import random
import sqlite3
import sys

import numpy as np

import mathqa_vinelm as vine
import mathqa_search as search

REFERENCE = {"repository": "https://github.com/QianJaneXie/BanditGittinsEval",
             "commit": "a4992e22a48e781327efd5411fb7d0921ad5ab61"}
VERSIONS = {"gittins": "gittins-equal-cost-finite-v1", "sysrs": "sysrs-synchronized-v1"}
DEFAULT_BUDGET_FRACTIONS = tuple(i / 10 for i in range(1, 11))


def default_sysrs_budget(n_arms, n_questions):
    """Reference 10% horizon, with enough cells to avoid zero-observation SR."""
    minimum = n_arms + 1 if n_arms > 1 else 1
    return max(minimum, round(.1 * n_arms * n_questions))


def gaussian_ei(x, sigma):
    """E[max(x + sigma Z, 0)], with the normal CDF evaluated via erfc."""
    x = np.asarray(x, dtype=np.float64)
    z = x / sigma
    cdf = np.fromiter((.5 * math.erfc(-float(v) / math.sqrt(2)) for v in z.flat),
                      dtype=np.float64, count=z.size).reshape(z.shape)
    return x * cdf + sigma * np.exp(-z * z / 2) / math.sqrt(2 * math.pi)


def convolve_m_diff(values, sigma, grid):
    """Reference piecewise-linear Gaussian expectation, using NumPy FFTs.

    Adapted from q_estimation.py, Copyright 2025 Qian Xie, Theo Brown,
    Ziv Scully, Alexander Terenin. MIT terms: references/BanditGittinsEval-NOTICE.md.
    Constant left and slope-one right extrapolation match the reference solver.
    """
    n = len(grid)
    dx = grid[1] - grid[0]
    slope_changes = np.diff(np.r_[0., np.diff(values) / dx, 1.])
    kernel = gaussian_ei((np.arange(2 * n - 1) - (n - 1)) * dx, sigma)
    length = 1 << (3 * n - 3).bit_length()
    convolution = np.fft.irfft(np.fft.rfft(slope_changes, length) *
                              np.fft.rfft(kernel, length), length)
    return values[0] + convolution[n - 1:2 * n - 1]


@lru_cache(maxsize=16)
def finite_roots(n_questions, prior_variance=.04, noise_variance=.25,
                 transition_charge=1e-4, grid_points=1025):
    """One shared root table: equal decision charges, unrelated to actual cents."""
    if n_questions < 1 or grid_points < 33 or grid_points % 2 == 0:
        raise ValueError("Require positive question count and odd grid size >=33.")
    if any(not math.isfinite(v) or v <= 0
           for v in (prior_variance, noise_variance, transition_charge)):
        raise ValueError("Prior variance, noise variance and decision charge must be positive and finite.")
    t = np.arange(n_questions)
    variance = 1 / (1 / prior_variance + t / noise_variance)
    scale = 1 + noise_variance / (n_questions * prior_variance)
    stds = scale * variance / np.sqrt(variance + noise_variance)
    bound = 5 * np.sqrt(np.sum(stds ** 2))
    grid = np.linspace(-bound, 1.01 * n_questions * transition_charge + bound, grid_points)
    values = grid.copy()  # Q_N(s) = s.
    roots = np.zeros(n_questions + 1)
    for stage in range(n_questions - 1, -1, -1):
        values = convolve_m_diff(np.maximum(values, 0), stds[stage], grid) - transition_charge
        if values[0] >= 0 or values[-1] < 0 or np.min(np.diff(values)) < -1e-9:
            raise ValueError("Gittins DP grid does not bracket a monotone root.")
        roots[stage] = grid[np.searchsorted(values, 0)]
    # Completed arms have exactly zero bonus, rather than a rounded terminal root.
    roots.setflags(write=False)
    return roots


class MatrixPolicy:
    """The policy has no dataset, oracle accuracy, or monetary cost reference."""

    def __init__(self, sequences, questions, seed):
        self.sequences, self.questions = tuple(sorted(sequences)), tuple(sorted(questions))
        if not self.sequences or not self.questions:
            raise ValueError("Require a nonempty grid.")
        self.priority = list(self.sequences)
        random.Random(seed + 1_000_003).shuffle(self.priority)
        self.rng = random.Random(seed)
        self.counts = {s: [0, 0] for s in self.sequences}
        self.seen = set()
        self.pending = None

    def observe(self, pair, score):
        if pair != self.pending or pair in self.seen or score not in (0, 1):
            raise ValueError("Require the pending unseen pair and a binary score.")
        self.seen.add(pair)
        self.counts[pair[1]][0] += score
        self.counts[pair[1]][1] += 1
        self.pending = None

    def choose_max(self, values):
        highest = max(values.values())
        return next(s for s in self.priority if s in values and
                    math.isclose(values[s], highest, rel_tol=0, abs_tol=1e-12))


class Gittins(MatrixPolicy):
    def __init__(self, sequences, questions, seed=0, *, prior_mean=.5,
                 prior_variance=.04, noise_variance=.25, transition_charge=1e-4,
                 grid_points=1025):
        super().__init__(sequences, questions, seed)
        if not math.isfinite(prior_mean) or not 0 <= prior_mean <= 1:
            raise ValueError("Prior mean must be in [0,1].")
        self.prior_mean, self.prior_variance = prior_mean, prior_variance
        self.noise_variance = noise_variance
        self.roots = finite_roots(len(self.questions), prior_variance, noise_variance,
                                  transition_charge, grid_points)
        self.natural_stop_step = None
        self.recommendation_stop_step = None

    def moments(self, sequence):
        successes, n = self.counts[sequence]
        remaining = len(self.questions) - n
        v = 1 / (1 / self.prior_variance + n / self.noise_variance)
        mu = v * (self.prior_mean / self.prior_variance + successes / self.noise_variance)
        mean = (successes + remaining * mu) / len(self.questions)
        variance = (remaining ** 2 * v + remaining * self.noise_variance) / len(self.questions) ** 2
        return mean, variance

    def indices(self):
        return {s: self.moments(s)[0] - self.roots[self.counts[s][1]] for s in self.sequences}

    def next_pair(self):
        if self.pending is not None:
            raise ValueError("Observe the pending pair first.")
        candidates = {s: value for s, value in self.indices().items()
                      if self.counts[s][1] < len(self.questions)}
        if not candidates:
            return None
        sequence = self.choose_max(candidates)
        question = self.rng.choice([q for q in self.questions if (q, sequence) not in self.seen])
        self.pending = question, sequence
        return self.pending

    def recommend(self):
        means = {s: self.moments(s)[0] for s in self.sequences}
        sequence = self.choose_max(means)
        return sequence, means[sequence]

    def observe(self, pair, score):
        super().observe(pair, score)
        scores = self.indices()
        best = self.choose_max(scores)
        if self.counts[best][1] == len(self.questions) and self.natural_stop_step is None:
            self.natural_stop_step = len(self.seen)
        unfinished = [v for s, v in scores.items() if self.counts[s][1] < len(self.questions)]
        if unfinished and max(unfinished) < self.recommend()[1] and self.recommendation_stop_step is None:
            self.recommendation_stop_step = len(self.seen)


def sysrs_schedule(planned_budget, n_arms, n_questions):
    """Reference SR schedule and late-round saturation reallocation.

    Adapted from src/sysrs_policy.py and upstream llm-bandits-sysrs Smart-SR.
    """
    if n_arms == 1:
        return np.array([0, min(n_questions, planned_budget)])
    logbar = .5 + sum(1 / j for j in range(2, n_arms + 1))
    phases = np.arange(1, n_arms)
    original = np.r_[0, np.ceil((planned_budget - n_arms) / logbar /
                                (n_arms + 1 - phases)).astype(int)]
    original = np.maximum.accumulate(original)
    current = original.astype(float)
    saturated = set()
    for _ in range(len(original)):
        newly = {t for t in range(1, len(original))
                 if t not in saturated and current[t] > n_questions}
        if not newly:
            break
        saturated.update(newly)
        weighted = sum((original[t] - original[t - 1]) * (n_arms - t + 1)
                       for t in range(1, len(original)) if t not in saturated)
        boundary = 0.
        for t in sorted(saturated):
            if t > 1 and t - 1 not in saturated:
                boundary += n_questions * (n_arms - t + 1)
                weighted -= original[t - 1] * (n_arms - t + 1)
        consecutive = n_questions * n_arms if 1 in saturated else 0
        if weighted == 0:
            break
        alpha = (planned_budget - consecutive - boundary) / weighted
        for t in range(1, len(original)):
            current[t] = n_questions if t in saturated else original[t] * alpha
    return np.maximum.accumulate(np.ceil(current).astype(int))


class SySRs(MatrixPolicy):
    def __init__(self, sequences, questions, seed=0, *, planned_budget=None):
        super().__init__(sequences, questions, seed)
        total = len(self.sequences) * len(self.questions)
        self.planned_budget = default_sysrs_budget(len(self.sequences), len(self.questions)) if planned_budget is None else planned_budget
        minimum = len(self.sequences) + 1 if len(self.sequences) > 1 else 1
        if not minimum <= self.planned_budget <= total:
            raise ValueError(f"SySRs planned budget must be between {minimum} and {total}.")
        self.schedule = sysrs_schedule(self.planned_budget, len(self.sequences), len(self.questions))
        self.elimination_rng = np.random.default_rng(seed)
        max_tasks = min(len(self.questions), int(self.schedule[-1]))
        self.shared_tasks = self.elimination_rng.choice(len(self.questions), size=max_tasks, replace=False)
        self.active = set(self.sequences)
        self.phase = 1
        self.cursor = 0
        self.phase_tasks = deque()
        self.round_pairs = deque()
        self.eliminations = []
        self.stop_reason = None
        self.refill()

    def refill(self):
        if len(self.active) <= 1 and len(self.sequences) > 1:
            self.stop_reason = "one_survivor"
            return
        if self.phase >= len(self.schedule):
            self.stop_reason = "schedule_finished"
            return
        extra = int(self.schedule[self.phase] - self.schedule[self.phase - 1])
        if extra <= 0:
            return
        if self.cursor >= len(self.shared_tasks):
            self.stop_reason = "shared_questions_exhausted"
            return
        end = min(self.cursor + extra, len(self.shared_tasks))
        self.phase_tasks.extend(int(c) for c in self.shared_tasks[self.cursor:end])
        self.cursor = end

    def eliminate(self):
        # The reference uses NumPy isclose defaults and random worst-arm ties.
        ordered = sorted(self.active)
        means = np.array([self.counts[s][0] / self.counts[s][1]
                          if self.counts[s][1] else -math.inf for s in ordered])
        candidates = np.flatnonzero(np.isclose(means, means.min()))
        worst = ordered[int(self.elimination_rng.choice(candidates))]
        self.active.remove(worst)
        self.eliminations.append({"step": len(self.seen), "phase": self.phase,
                                  "configuration": list(worst)})
        self.phase += 1
        self.refill()

    def next_pair(self):
        if self.pending is not None:
            raise ValueError("Observe the pending pair first.")
        if len(self.seen) >= self.planned_budget:
            self.stop_reason = "planned_budget_reached"
            return None
        while not self.round_pairs and self.stop_reason is None:
            if self.phase_tasks:
                q = self.questions[self.phase_tasks.popleft()]
                # Fixed seeded order serializes a native synchronized batch.
                self.round_pairs.extend((q, s) for s in self.priority if s in self.active)
            else:
                if len(self.sequences) == 1:
                    self.stop_reason = "shared_questions_exhausted"
                    return None
                self.eliminate()
        if self.stop_reason is not None:
            return None
        self.pending = self.round_pairs.popleft()
        return self.pending

    def recommend(self):
        means = {s: self.counts[s][0] / self.counts[s][1] for s in self.active if self.counts[s][1]}
        if not means:
            return next(s for s in self.priority if s in self.active), None
        sequence = self.choose_max(means)
        return sequence, means[sequence]


def simulate(dataset, *, strategy, seed=0, planned_budget=None, **gittins_settings):
    if strategy not in VERSIONS:
        raise ValueError("Choose gittins or sysrs.")
    policy = (Gittins(dataset.sequences, dataset.questions, seed, **gittins_settings)
              if strategy == "gittins" else SySRs(dataset.sequences, dataset.questions, seed,
                                                 planned_budget=planned_budget))
    cost, history = Decimal(0), []
    best = max(dataset.accuracy.values())

    def record(pair=None):
        choice, estimate = policy.recommend()
        accuracy = dataset.accuracy[choice]  # Evaluator-only, never supplied to policy.
        history.append({"step": len(policy.seen), "cost_cents": str(cost * 100),
                        "queried_question": pair[0] if pair else None,
                        "queried_configuration": dataset.names[pair[1]] if pair else None,
                        "recommendation": dataset.names[choice], "estimated_accuracy": estimate,
                        "full_dataset_accuracy": accuracy, "gap_pp": 100 * (best - accuracy),
                        **({"phase": policy.phase, "active_count": len(policy.active)}
                           if strategy == "sysrs" else {})})
    record()
    while True:
        pair = policy.next_pair()
        if pair is None:
            # The reference can eliminate through zero-pull phases at termination.
            # Save that final recommendation at the same spend without inventing a query.
            if policy.recommend()[0] != choice_from_history(dataset, history[-1]):
                record()
            break
        if policy.recommend()[0] != choice_from_history(dataset, history[-1]):
            record()  # Zero-cost elimination recommendation before the next paid query.
        observation = dataset.observations[pair]
        policy.observe(pair, int("correct_accept" in observation.outcomes))
        cost += observation.cost_usd
        record(pair)
    run = {"seed": seed, "history": history,
           "configuration_counts": {dataset.names[s]: {"correct": c[0], "observations": c[1]}
                                    for s, c in policy.counts.items()}}
    if strategy == "gittins":
        run.update(stop_reason="all_pairs_revealed", natural_stop_step=policy.natural_stop_step,
                   recommendation_stop_step=policy.recommendation_stop_step)
    else:
        run.update(stop_reason=policy.stop_reason, schedule=policy.schedule.tolist(),
                   shared_question_order=[policy.questions[int(i)] for i in policy.shared_tasks],
                   eliminations=policy.eliminations,
                   survivors=[dataset.names[s] for s in sorted(policy.active)])
    return run


def choice_from_history(dataset, point):
    return next(s for s, name in dataset.names.items() if name == point["recommendation"])


def experiment(dataset, *, strategy, seeds=100, first_seed=0, planned_budget=None, **kwargs):
    if seeds < 1:
        raise ValueError("Require at least one seed.")
    runs = [simulate(dataset, strategy=strategy, seed=seed, planned_budget=planned_budget, **kwargs)
            for seed in range(first_seed, first_seed + seeds)]
    total = len(dataset.observations)
    settings = {"seeds": seeds, "first_seed": first_seed, "max_pairs": total, "batch_size": 1,
                "cost_aware_selection": False, "cost_policy": "full recorded cost, evaluator-only",
                "ties": "fixed seeded random priority; SySRs elimination ties use NumPy isclose and random choice",
                "curve_semantics": "one fixed-horizon trajectory; truncate at minimum terminal spend across seeds",
                "limitations": ["fixed original keys and one saved execution per pair",
                                "seeded ties, RNG and float64 NumPy are replay adaptations"]}
    if strategy == "gittins":
        settings.update(prior_mean=kwargs.get("prior_mean", .5), prior_variance=kwargs.get("prior_variance", .04),
                        noise_variance=kwargs.get("noise_variance", .25),
                        transition_charge=kwargs.get("transition_charge", 1e-4),
                        grid_points=kwargs.get("grid_points", 1025), grid_sd_bound=5., grid_cost_margin=.01,
                        index_target="finite_population_mean", recommendation_std_penalty=0,
                        stopping="continue through full grid; natural stop retained as a diagnostic",
                        sampling="maximum unfinished finite-row Gittins index, uniform unseen question")
        settings["limitations"].append("Gaussian approximation to binary scores; fixed prior and numerical charge")
    else:
        settings.update(planned_budget=default_sysrs_budget(len(dataset.sequences), len(dataset.questions))
                        if planned_budget is None else planned_budget,
                        sampling="shared unseen question across active arms; successive rejects after full phases",
                        stopping="planned pair budget or natural schedule termination; no forced post-stop pulls",
                        recommendation="maximum raw mean among observed active configurations")
        settings["limitations"].append("budget-dependent schedule; trace is not a smaller-budget rerun")
    best = max(dataset.accuracy.values())
    return {"version": VERSIONS[strategy], "strategy": strategy, "source": dataset.source,
            "reference": REFERENCE, "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "shared_implementation_sha256": hashlib.sha256(Path(vine.__file__).read_bytes()).hexdigest(),
            "specification": {"path": str(vine.SPECIFICATION),
                              "sha256": hashlib.sha256(vine.SPECIFICATION.read_bytes()).hexdigest()},
            "python_version": sys.version, "dependencies": {"numpy": np.__version__},
            "settings": settings, "exhaustive": {"pairs": total,
                 "cost_cents": str(sum((o.cost_usd for o in dataset.observations.values()), Decimal(0)) * 100),
                 "accuracy": best, "optimal_configurations": [dataset.names[s] for s in dataset.sequences
                                                               if dataset.accuracy[s] == best]},
            "roots": Gittins(dataset.sequences, dataset.questions, **kwargs).roots.tolist()
                     if strategy == "gittins" else None,
            "curve": vine.aggregate(runs), "runs": runs}


def save_result(result, output):
    code = Path(__file__).read_bytes()
    spec, shared = vine.SPECIFICATION.read_bytes(), Path(vine.__file__).read_bytes()
    for data, expected in ((code, result["implementation_sha256"]),
                           (spec, result["specification"]["sha256"]),
                           (shared, result["shared_implementation_sha256"])):
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Source changed during experiment.")
    output = vine.save_outputs(result, output)
    output.with_suffix(".implementation.py").write_bytes(code)
    output.with_suffix(".spec.md").write_bytes(spec)
    output.with_suffix(".shared-implementation.py").write_bytes(shared)
    return output


def save_extended_comparison(files, output):
    """Preserve each strategy's supported domain; never extend stopped searches."""
    import csv
    files = [Path(f).resolve() for f in files]
    results = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    if not results:
        raise ValueError("Require saved results.")
    first = results[0]
    fields = ("database_sha256", "run_id", "dataset_sha256", "plan_sha256", "grader_version",
              "question_count", "configuration_count")
    for result in results[1:]:
        if any(result["source"][key] != first["source"][key] for key in fields) or result["exhaustive"] != first["exhaustive"]:
            raise ValueError("Cannot overlay different datasets or exhaustive references.")
        if [r["seed"] for r in result["runs"]] != [r["seed"] for r in first["runs"]]:
            raise ValueError("Cannot overlay different seed sets.")
        result_limit = result["settings"]["max_pairs"]
        first_limit = first["settings"]["max_pairs"]
        if (result["exhaustive"]["pairs"] if result_limit is None else result_limit) != (
                first["exhaustive"]["pairs"] if first_limit is None else first_limit):
            raise ValueError("Cannot overlay different observation limits.")
    labels = [r.get("strategy", "vinelm") for r in results]
    if len(labels) != len(set(labels)):
        raise ValueError("Require distinct strategies.")
    output = Path(output).resolve()
    if output.suffix != ".json" or output in files or output == Path(first["source"]["database"]).resolve():
        raise ValueError("Choose a comparison JSON distinct from its sources and database.")
    comparison = {"version": "workflow-search-comparison-v2", "source": first["source"],
                  "exhaustive": first["exhaustive"],
                  "aggregation": "per-strategy common-spend grid ending at minimum terminal spend; no extrapolation",
                  "series": []}
    rows = []
    for label, result, path in zip(labels, results, files):
        curve = vine.aggregate(result["runs"])
        series = {"strategy": label, "version": result["version"], "settings": result["settings"],
                  "result_path": str(path), "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "implementation_sha256": result["implementation_sha256"],
                  "specification_sha256": result["specification"]["sha256"],
                  "curve": curve}
        if "reference" in result:
            series["reference"] = result["reference"]
        comparison["series"].append(series)
        rows.extend({"strategy": label, **p} for p in curve)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(comparison, indent=2, allow_nan=False), encoding="utf-8")
    with output.with_suffix(".csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return comparison


def artifact_record(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def save_budget_matched_comparison(files, horizons, output, *, horizon_files=None):
    """Pair seed-specific spend caps with independently rerun SySRs horizons.

    Every other strategy is evaluated at the last completed observation affordable
    at that seed's SySRs terminal spend. The x coordinate is the mean of those caps,
    not a hypothetical concatenated SySRs search or average-gap interpolation.
    """
    from bisect import bisect_right
    import csv
    files = [Path(f).resolve() for f in files]
    results = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    if not results or not horizons:
        raise ValueError("Require comparison sources and independent SySRs horizon runs.")
    first = results[0]
    seeds = [r["seed"] for r in first["runs"]]
    fields = ("database_sha256", "run_id", "dataset_sha256", "plan_sha256", "grader_version",
              "question_count", "configuration_count")
    for result in [*results, *horizons]:
        if any(result["source"][key] != first["source"][key] for key in fields) or result["exhaustive"] != first["exhaustive"]:
            raise ValueError("Cannot compare different datasets or exhaustive references.")
        if [r["seed"] for r in result["runs"]] != seeds:
            raise ValueError("Cannot compare different seed sets.")
    if any(r.get("strategy") != "sysrs" for r in horizons):
        raise ValueError("Budget anchors must be independent SySRs experiments.")
    planned = [r["settings"]["planned_budget"] for r in horizons]
    if planned != sorted(set(planned)):
        raise ValueError("Require increasing distinct planned SySRs horizons.")
    horizon_sources = []
    if horizon_files is not None:
        if len(horizon_files) != len(horizons):
            raise ValueError("Require one source file per horizon.")
        for path, horizon in zip(horizon_files, horizons):
            if json.loads(Path(path).read_text(encoding="utf-8")) != horizon:
                raise ValueError("Horizon provenance file does not match the supplied result.")
            horizon_sources.append(artifact_record(path))
    labels = [r.get("strategy", "vinelm") for r in results]
    if "sysrs" in labels or len(labels) != len(set(labels)):
        raise ValueError("Supply distinct other strategies; SySRs is supplied by horizons.")
    output = Path(output).resolve()
    if output.suffix != ".json" or output in files or output == Path(first["source"]["database"]).resolve():
        raise ValueError("Choose a comparison JSON distinct from its sources and database.")
    comparison = {"version": "workflow-search-budget-matched-v1", "source": first["source"],
                  "exhaustive": first["exhaustive"], "series": [], "budget_anchors": [],
                  "aggregation": "independent SySRs horizons; other methods matched to each seed's actual terminal spend",
                  "axis_semantics": "mean seed-specific profiling budget in cents"}
    for label, result, path in zip(labels, results, files):
        comparison["series"].append({"strategy": label, "version": result["version"],
                                     "settings": result["settings"], "curve": [],
                                     "result_path": str(path), "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                     "implementation_sha256": result["implementation_sha256"],
                                     "specification_sha256": result["specification"]["sha256"]})
    comparison["series"].append({"strategy": "sysrs", "version": VERSIONS["sysrs"],
                                 "reference": REFERENCE, "curve": [],
                                 "implementation_sha256": horizons[0]["implementation_sha256"],
                                 "specification_sha256": horizons[0]["specification"]["sha256"],
                                 "source_results": horizon_sources,
                                 "settings": {**horizons[0]["settings"], "planned_budgets": planned,
                                              "curve_semantics": "independent-horizon"}})
    cost_tables = [[[Decimal(p["cost_cents"]) for p in r["history"]] for r in result["runs"]]
                   for result in results]
    anchors = [(0, [r["history"][0] for r in horizons[0]["runs"]])]
    anchors += [(r["settings"]["planned_budget"], [run["history"][-1] for run in r["runs"]])
                for r in horizons]
    previous_mean = Decimal(-1)
    for planned_pairs, terminal in anchors:
        caps = [Decimal(p["cost_cents"]) for p in terminal]
        budget = sum(caps) / len(caps)
        if budget < previous_mean:
            raise ValueError("Mean actual spend is nonmonotone across horizons; plot discrete points instead.")
        previous_mean = budget
        gaps_by_series = []
        for result, tables in zip(results, cost_tables):
            gaps = []
            for run, costs, cap in zip(result["runs"], tables, caps):
                if cap > costs[-1]:
                    raise ValueError("A comparison source does not support the matched budget; no extrapolation.")
                gaps.append(run["history"][bisect_right(costs, cap) - 1]["gap_pp"])
            gaps_by_series.append(gaps)
        gaps_by_series.append([p["gap_pp"] for p in terminal])
        comparison["budget_anchors"].append({"planned_sysrs_pairs": planned_pairs,
                                              "cost_cents_by_seed": [str(c) for c in caps]})
        for series, gaps in zip(comparison["series"], gaps_by_series):
            series["curve"].append({"cost_cents": str(budget), "mean_gap_pp": sum(gaps) / len(gaps),
                                     "p10_gap_pp": vine.quantile(gaps, .1), "p90_gap_pp": vine.quantile(gaps, .9),
                                     "optimal_fraction": sum(abs(g) < 1e-10 for g in gaps) / len(gaps)})
    rows = [{"strategy": s["strategy"], **p} for s in comparison["series"] for p in s["curve"]]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(comparison, indent=2, allow_nan=False), encoding="utf-8")
    with output.with_suffix(".csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return comparison


def save_budget_summary(results, output, *, source_files=None):
    """Each point is a separately run SySRs horizon, not an anytime trace."""
    import csv
    rows = []
    for result in results:
        terminal = [r["history"][-1] for r in result["runs"]]
        costs = [Decimal(p["cost_cents"]) for p in terminal]
        gaps = [p["gap_pp"] for p in terminal]
        rows.append({"planned_pairs": result["settings"]["planned_budget"],
                     "mean_actual_pairs": sum(p["step"] for p in terminal) / len(terminal),
                     "mean_cost_cents": str(sum(costs) / len(costs)),
                     "min_cost_cents": str(min(costs)), "max_cost_cents": str(max(costs)),
                     "mean_gap_pp": sum(gaps) / len(gaps),
                     "p10_gap_pp": vine.quantile(gaps, .1), "p90_gap_pp": vine.quantile(gaps, .9),
                     "optimal_fraction": sum(abs(g) < 1e-10 for g in gaps) / len(gaps)})
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": "sysrs-budget-sweep-v1", "source": results[0]["source"],
               "exhaustive": results[0]["exhaustive"], "reference": REFERENCE,
               "seeds": [r["seed"] for r in results[0]["runs"]],
               "semantics": "independent horizon reruns; terminal recommendation and actual spend",
               "implementation_sha256": results[0]["implementation_sha256"],
               "specification_sha256": results[0]["specification"]["sha256"],
               "source_results": [artifact_record(p) for p in source_files] if source_files else [],
               "points": rows}
    output.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    with output.with_suffix(".csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return payload


def export_portable(output_dir, portable_dir):
    """Save compact new values; preserve the original three baseline snapshots."""
    output_dir, portable_dir = Path(output_dir).resolve(), Path(portable_dir).resolve()
    names = ("gittins.csv", "sysrs.csv", "sysrs-budget-sweep.json", "sysrs-budget-sweep.csv",
             "search-comparison-extended.json", "search-comparison-extended.csv",
             "search-comparison-budget-matched.json", "search-comparison-budget-matched.csv")
    inputs = [output_dir / name for name in names]
    if any(not p.is_file() for p in inputs):
        raise ValueError("Portable export needs both policies, the budget sweep and both comparisons.")
    if output_dir == portable_dir:
        raise ValueError("Keep full results and portable exports in separate directories.")

    def relative_paths(value):
        if isinstance(value, dict):
            return {k: relative_paths(v) for k, v in value.items()}
        if isinstance(value, list):
            return [relative_paths(v) for v in value]
        if isinstance(value, str) and (value.startswith(str(vine.ROOT) + "\\") or
                                       value.startswith(str(vine.ROOT) + "/")):
            return Path(value).relative_to(vine.ROOT).as_posix()
        return value

    portable_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for source in inputs:
        output = portable_dir / source.name
        if source.suffix == ".json":
            payload = relative_paths(json.loads(source.read_text(encoding="utf-8")))
            payload["plotter"] = relative_paths(artifact_record(vine.ROOT / "scripts/mathqa_search_plot.py"))
            output.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
        else:
            output.write_bytes(source.read_bytes())
        written.append(str(output))
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=vine.DATABASE)
    parser.add_argument("--run-id", default=vine.RUN_ID)
    parser.add_argument("--grader-version", default=vine.GRADER)
    parser.add_argument("--strategy", choices=("gittins", "sysrs", "both"), default="both")
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--first-seed", type=int, default=0)
    parser.add_argument("--sysrs-budget", type=int, help="Planned pair count; default is 10% of matrix size.")
    parser.add_argument("--budget-sweep", action="store_true", help="Also rerun SySRs at 10% increments of matrix size.")
    parser.add_argument("--output-dir", type=Path, default=search.OUTPUT_DIR)
    parser.add_argument("--portable-dir", type=Path, help="Explicitly export compact new values here, preserving original baselines.")
    parser.add_argument("--plot", action="store_true", help="Overlay with three existing full-history result files.")
    args = parser.parse_args()
    try:
        dataset = vine.load_dataset(args.database, args.run_id, args.grader_version)
        selected = list(VERSIONS) if args.strategy == "both" else [args.strategy]
        paths, results = [], {}
        for strategy in selected:
            result = experiment(dataset, strategy=strategy, seeds=args.seeds, first_seed=args.first_seed,
                                planned_budget=args.sysrs_budget if strategy == "sysrs" else None)
            results[strategy] = result
            paths.append(save_result(result, args.output_dir / f"{strategy}.json"))
        sweep, horizon_paths = [], []
        if args.budget_sweep:
            for budget in sorted({max(len(dataset.sequences) + 1, round(f * len(dataset.observations)))
                                  for f in DEFAULT_BUDGET_FRACTIONS}):
                result = results.get("sysrs")
                if result is None or result["settings"]["planned_budget"] != budget:
                    result = experiment(dataset, strategy="sysrs", seeds=args.seeds,
                                        first_seed=args.first_seed, planned_budget=budget)
                horizon_paths.append(save_result(result, args.output_dir / "sysrs-horizons" / f"sysrs-{budget}.json"))
                sweep.append(result)
            save_budget_summary(sweep, args.output_dir / "sysrs-budget-sweep.json", source_files=horizon_paths)
        if args.plot:
            from mathqa_search_plot import plot_comparison
            old = [args.output_dir / f"{name}.json" for name in ("vinelm-adapted", "agentopt", "random")]
            output = args.output_dir / "search-comparison-extended.json"
            comparison = save_extended_comparison([*old, *paths], output)
            plot_comparison(comparison, output.with_suffix(".png"))
            if sweep:
                others = [*old, args.output_dir / "gittins.json"]
                output = args.output_dir / "search-comparison-budget-matched.json"
                comparison = save_budget_matched_comparison(others, sweep, output, horizon_files=horizon_paths)
                plot_comparison(comparison, output.with_suffix(".png"))
        if args.portable_dir:
            export_portable(args.output_dir, args.portable_dir)
    except (ValueError, ImportError, sqlite3.Error, OSError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps({"outputs": [str(p) for p in paths], "new_model_requests": 0,
                      "terminal_mean_gap_pp": {s: sum(r["history"][-1]["gap_pp"] for r in result["runs"]) / args.seeds
                                               for s, result in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
