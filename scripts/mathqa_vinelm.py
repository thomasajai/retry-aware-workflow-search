"""Adapted VineLM offline profiling of a frozen question/configuration grid.

Reads SQLite in query-only mode. No workflow runners, credentials or HTTP.
Only the evaluator sees the complete grid; the estimator receives queried traces.
"""

import argparse
from bisect import bisect_right
from collections import defaultdict
from contextlib import closing
import csv
from dataclasses import dataclass
from decimal import Decimal
import hashlib
from importlib.metadata import PackageNotFoundError, version as package_version
from itertools import product
import json
import math
from pathlib import Path
import random
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "experiments" / "mathqa_runs.sqlite3"
RUN_ID = "f0c941bc-5479-4e86-ae2d-261b521a3317"
GRADER = "workflow-option-v1"
VERSION = "vinelm-adapted-v1"
SPECIFICATION = ROOT / "notes" / "workflow-search-experiment-spec.md"
OUTCOMES = ("correct_accept", "continue", "incorrect_stop")


@dataclass(frozen=True)
class Observation:
    question_id: str
    sequence: tuple
    outcomes: tuple
    cost_usd: Decimal


@dataclass(frozen=True)
class Dataset:
    sequences: tuple
    questions: tuple
    observations: dict
    accuracy: dict
    names: dict
    source: dict


def load_dataset(database=DATABASE, run_id=RUN_ID, grader=GRADER):
    """Fail closed on incomplete grids, traces, grades, or billing."""
    path = Path(database).resolve()
    before_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA query_only=ON")
        c.execute("BEGIN")
        run = c.execute("SELECT * FROM workflow_runs WHERE run_id=?", (run_id,)).fetchone()
        if run is None or run["kind"] != "sequence_evaluation":
            raise ValueError("Choose a saved sequence evaluation.")
        configs = list(c.execute("SELECT * FROM workflow_configs WHERE run_id=?", (run_id,)))
        executions = list(c.execute("SELECT * FROM workflow_executions WHERE run_id=?", (run_id,)))
        attempts = list(c.execute("SELECT a.* FROM workflow_attempts a JOIN workflow_executions e "
                                  "USING(execution_id) WHERE e.run_id=? ORDER BY position", (run_id,)))
        grades = list(c.execute("SELECT g.* FROM workflow_grades g JOIN workflow_executions e "
                                "USING(execution_id) WHERE e.run_id=? AND grader_version=?", (run_id, grader)))
        calls = list(c.execute("SELECT w.* FROM workflow_billable_calls w JOIN workflow_attempts a "
                               "USING(attempt_id) JOIN workflow_executions e USING(execution_id) "
                               "WHERE e.run_id=?", (run_id,)))
    snapshots = {f["config_id"]: json.loads(f["snapshot_json"]) for f in configs}
    by_config = {cid: tuple(snapshot["solver_sequence"]) for cid, snapshot in snapshots.items()}
    sequences = tuple(sorted(by_config.values()))
    aliases = sorted({model for seq in sequences for model in seq})
    if not aliases or sequences != tuple(product(aliases, repeat=3)):
        raise ValueError("Require all distinct three-position model combinations.")
    solver_settings, verifier_settings = {}, None
    for snapshot in snapshots.values():
        for alias, solver in zip(snapshot["solver_sequence"], snapshot["solvers"]):
            if alias in solver_settings and solver_settings[alias] != solver:
                raise ValueError("Shared model aliases require identical solver settings.")
            solver_settings[alias] = solver
        if verifier_settings is not None and verifier_settings != snapshot["verifier"]:
            raise ValueError("Configurations require identical verifier settings.")
        verifier_settings = snapshot["verifier"]
    questions = tuple(sorted(json.loads(run["question_ids_json"])))
    if not questions or len(set(questions)) != len(questions):
        raise ValueError("Require distinct scheduled questions.")
    final_grades, attempt_grades = {}, {}
    for g in grades:
        key = g["attempt_id"] or g["execution_id"]
        target = attempt_grades if g["attempt_id"] else final_grades
        if key in target or g["dataset_sha256"] != run["dataset_sha256"]:
            raise ValueError("Duplicate or mismatched grade provenance.")
        target[key] = g
    attempts_by_execution = defaultdict(list)
    costs_by_execution = defaultdict(lambda: Decimal(0))
    calls_by_attempt = defaultdict(list)
    for a in attempts:
        attempts_by_execution[a["execution_id"]].append(a)
    by_attempt = {a["attempt_id"]: a for a in attempts}
    call_ids = set()
    for w in calls:
        cost = Decimal(str(w["cost_usd"])) if w["cost_usd"] is not None else None
        if cost is None or not cost.is_finite() or cost < 0 or w["call_id"] in call_ids:
            raise ValueError("Unknown, invalid or duplicate billing.")
        call_ids.add(w["call_id"])
        calls_by_attempt[w["attempt_id"]].append(w)
        costs_by_execution[by_attempt[w["attempt_id"]]["execution_id"]] += cost
    observations, scores = {}, defaultdict(list)
    for e in executions:
        seq = by_config[e["config_id"]]
        key = (e["question_id"], seq)
        if key in observations or e["question_id"] not in questions or e["repetition"] != 1:
            raise ValueError("Unexpected or repeated question/configuration cell.")
        if e["status"] not in ("accepted", "exhausted") or e["execution_id"] not in final_grades:
            raise ValueError("Require completed, independently graded executions.")
        reached = attempts_by_execution[e["execution_id"]]
        if not reached or [a["position"] for a in reached] != list(range(1, len(reached) + 1)) or len(reached) > 3:
            raise ValueError("Invalid attempt positions.")
        outcomes = []
        for a in reached:
            if a["solver_model"] != snapshots[e["config_id"]]["solvers"][a["position"] - 1]["model"]:
                raise ValueError("Attempt model differs from configuration.")
            g = attempt_grades.get(a["attempt_id"])
            if g is None or g["execution_id"] != e["execution_id"] or not any(
                    w["role"] == "solver" for w in calls_by_attempt[a["attempt_id"]]):
                raise ValueError("Missing attempt grade or solver billing.")
            accepted = a["verification_status"] == "accept"
            if a["verification_status"] not in ("accept", "reject", "not_requested"):
                raise ValueError("Unsupported incomplete verification.")
            if a["usable"] not in (0, 1) or (a["usable"] == 1 and a["verification_status"] == "not_requested"):
                raise ValueError("Usable attempts require completed verification.")
            if a["usable"] == 1 and g["option_correct"] not in (0, 1):
                raise ValueError("Usable attempts require independent option grades.")
            if a["usable"] == 0 and accepted:
                raise ValueError("An unusable answer cannot be accepted.")
            if a["verification_status"] in ("accept", "reject") and not any(
                    w["role"] == "verifier" for w in calls_by_attempt[a["attempt_id"]]):
                raise ValueError("Missing verifier billing.")
            outcome = ("correct_accept" if g["option_correct"] == 1 else "incorrect_stop") if accepted else (
                "continue" if a["position"] < 3 else "incorrect_stop")
            if accepted and a is not reached[-1]:
                raise ValueError("Trace continues after acceptance.")
            outcomes.append(outcome)
        accepted_last = reached[-1]["verification_status"] == "accept"
        if (e["status"] == "accepted") != accepted_last or (not accepted_last and len(reached) != 3):
            raise ValueError("Terminal status disagrees with attempts.")
        if e["accepted_attempt_id"] != (reached[-1]["attempt_id"] if accepted_last else None):
            raise ValueError("Accepted attempt identity disagrees with trace.")
        score = int("correct_accept" in outcomes)
        if final_grades[e["execution_id"]]["workflow_score"] != score:
            raise ValueError("Final grade disagrees with accepted answer.")
        observations[key] = Observation(e["question_id"], seq, tuple(outcomes), costs_by_execution[e["execution_id"]])
        scores[seq].append(score)
    if set(observations) != set(product(questions, sequences)):
        raise ValueError("Require a complete question/configuration grid.")
    if hashlib.sha256(path.read_bytes()).hexdigest() != before_sha256:
        raise ValueError("Database changed while loading; use a frozen snapshot.")
    names = {by_config[f["config_id"]]: f["name"] for f in configs}
    return Dataset(sequences, questions, observations,
                   {seq: sum(values) / len(questions) for seq, values in scores.items()}, names,
                   {"database": str(path), "database_sha256": before_sha256,
                    "run_id": run_id, "dataset_sha256": run["dataset_sha256"],
                    "plan_sha256": run["plan_sha256"], "grader_version": grader,
                    "billable_requests": len(calls), "question_count": len(questions),
                    "configuration_count": len(sequences)})


def rank_one_rates(rates, sequences, fallback=0.5):
    """Paper's depth-3 SVD projection, with observed-column-mean fill-in.

    This is a one-pass projection, clipped to probability bounds. No unqueried
    outcomes enter rates; missing whole columns use the fixed fallback.
    """
    import numpy as np

    parents = sorted({seq[:2] for seq in sequences})
    models = sorted({seq[2] for seq in sequences})
    column_means = {m: sum(v for p, v in rates.items() if p[2] == m) /
                    sum(1 for p in rates if p[2] == m) if any(p[2] == m for p in rates) else fallback
                    for m in models}
    matrix = np.array([[rates.get(p + (m,), column_means[m]) for m in models] for p in parents])
    u, singular, vt = np.linalg.svd(matrix, full_matrices=False)
    projected = np.clip(singular[0] * np.outer(u[:, 0], vt[0]), 0, 1)
    return {p + (m,): float(projected[i, j]) for i, p in enumerate(parents) for j, m in enumerate(models)}


class VineLMEstimator:
    """Receives public configuration identities and queried observations only."""

    def __init__(self, sequences, *, pseudocount=0.5, smoothing=True, tie_seed=0):
        if not math.isfinite(pseudocount) or pseudocount <= 0:
            raise ValueError("Pseudocount must be finite and positive.")
        self.sequences = tuple(sorted(sequences))
        self.pseudocount = pseudocount
        self.smoothing = smoothing
        self.counts = defaultdict(lambda: [0, 0, 0])
        self.seen = set()
        self.tie_order = list(self.sequences)
        random.Random(tie_seed).shuffle(self.tie_order)

    def observe(self, observation):
        key = (observation.question_id, observation.sequence)
        if key in self.seen:
            raise ValueError("A saved pair may be observed only once.")
        if observation.sequence not in self.sequences or not 1 <= len(observation.outcomes) <= 3:
            raise ValueError("Invalid observation.")
        for i, outcome in enumerate(observation.outcomes):
            if outcome not in OUTCOMES or (i < len(observation.outcomes) - 1 and outcome != "continue"):
                raise ValueError("Invalid cascade outcomes.")
        if observation.outcomes[-1] == "continue":
            raise ValueError("A complete trace must terminate.")
        self.seen.add(key)
        for depth, outcome in enumerate(observation.outcomes, 1):
            self.counts[observation.sequence[:depth]][OUTCOMES.index(outcome)] += 1

    def rates(self, prefix):
        correct, continuation, incorrect = self.counts.get(prefix, (0, 0, 0))
        alpha = self.pseudocount
        categories = 2 if len(prefix) == 3 else 3
        denominator = correct + continuation + incorrect + categories * alpha
        return (correct + alpha) / denominator, (continuation + alpha) / denominator if categories == 3 else 0.0

    def estimates(self):
        third = {seq: self.rates(seq)[0] for seq in self.sequences if sum(self.counts.get(seq, ())) > 0}
        if self.smoothing:
            third = rank_one_rates(third, self.sequences)
        else:
            third = {seq: self.rates(seq)[0] for seq in self.sequences}
        estimates = {}
        for seq in self.sequences:
            s1, r1 = self.rates(seq[:1])
            s2, r2 = self.rates(seq[:2])
            estimates[seq] = s1 + r1 * s2 + r1 * r2 * third[seq]
        return estimates

    def recommend(self):
        estimates = self.estimates()
        maximum = max(estimates.values())
        # A fixed, seeded tie ordering does not disturb the sampling RNG.
        choice = next(seq for seq in self.tie_order if math.isclose(estimates[seq], maximum, rel_tol=0, abs_tol=1e-12))
        return choice, estimates[choice]


def simulate(dataset, *, seed=0, max_pairs=None, pseudocount=0.5, smoothing=True):
    pairs = list(product(dataset.questions, dataset.sequences))
    if max_pairs is None:
        max_pairs = len(pairs)
    if not 0 <= max_pairs <= len(pairs):
        raise ValueError("max_pairs must lie within the saved grid.")
    random.Random(seed).shuffle(pairs)
    estimator = VineLMEstimator(dataset.sequences, pseudocount=pseudocount,
                                smoothing=smoothing, tie_seed=seed + 1_000_003)
    best = max(dataset.accuracy.values())
    history, cost = [], Decimal(0)

    def record(step, pair=None):
        choice, estimate = estimator.recommend()
        accuracy = dataset.accuracy[choice]  # Evaluator-only; never fed back.
        history.append({"step": step, "cost_cents": str(cost * 100),
                        "queried_question": pair[0] if pair else None,
                        "queried_configuration": dataset.names[pair[1]] if pair else None,
                        "recommendation": dataset.names[choice], "estimated_accuracy": estimate,
                        "full_dataset_accuracy": accuracy, "gap_pp": 100 * (best - accuracy)})

    record(0)  # Seeded prior-only recommendation; no hidden-data warmup.
    for step, pair in enumerate(pairs[:max_pairs], 1):
        observation = dataset.observations[pair]
        estimator.observe(observation)
        cost += observation.cost_usd
        record(step, pair)
    return {"seed": seed, "history": history,
            "prefix_counts": {"/".join(p): dict(zip(OUTCOMES, counts)) for p, counts in sorted(estimator.counts.items())}}


def quantile(values, probability):
    values = sorted(values)
    position = (len(values) - 1) * probability
    lower = math.floor(position)
    return values[lower] + (values[math.ceil(position)] - values[lower]) * (position - lower)


def aggregate(runs, *, points=121, budgets=None):
    """Step-hold at common spend; never interpolate or use a future observation.

    Truncate at the smallest terminal spend: no extrapolation past a run's end.
    Bounds describe randomness of profiling order, not population uncertainty.
    """
    if not runs or points < 2:
        raise ValueError("Require runs and at least two grid points.")
    maximum = min(Decimal(r["history"][-1]["cost_cents"]) for r in runs)
    costs = [[Decimal(p["cost_cents"]) for p in r["history"]] for r in runs]
    curve = []
    if budgets is None:
        budgets = [maximum * i / (points - 1) for i in range(points)]
    if not budgets or any(b < 0 or b > maximum for b in budgets) or list(budgets) != sorted(budgets):
        raise ValueError("Budgets must be ordered, nonnegative, and within every run's terminal cost.")
    for budget in budgets:
        gaps = [r["history"][bisect_right(cs, budget) - 1]["gap_pp"] for r, cs in zip(runs, costs)]
        curve.append({"cost_cents": str(budget), "mean_gap_pp": sum(gaps) / len(gaps),
                      "p10_gap_pp": quantile(gaps, .1), "p90_gap_pp": quantile(gaps, .9),
                      "optimal_fraction": sum(abs(g) < 1e-10 for g in gaps) / len(gaps)})
    return curve


def experiment(dataset, *, seeds=100, first_seed=0, max_pairs=None, pseudocount=0.5, smoothing=True):
    if seeds < 1:
        raise ValueError("Require at least one seed.")
    runs = [simulate(dataset, seed=seed, max_pairs=max_pairs, pseudocount=pseudocount, smoothing=smoothing)
            for seed in range(first_seed, first_seed + seeds)]
    total = sum((o.cost_usd for o in dataset.observations.values()), Decimal(0)) * 100
    best = max(dataset.accuracy.values())
    dependencies = {}
    for name in ("numpy", "matplotlib"):
        try:
            dependencies[name] = package_version(name)
        except PackageNotFoundError:
            dependencies[name] = None
    return {"version": VERSION, "source": dataset.source,
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "specification": {"path": str(SPECIFICATION),
                              "sha256": hashlib.sha256(SPECIFICATION.read_bytes()).hexdigest()},
            "python_version": sys.version,
            "dependencies": dependencies,
            "settings": {"seeds": seeds, "first_seed": first_seed, "max_pairs": max_pairs,
                         "pseudocount": pseudocount, "depth3_rank_one_smoothing": smoothing,
                         "sampling": "uniform unseen pairs, without replacement",
                         "ties": "fixed seeded random priority; accuracy only",
                         "priors": "Dirichlet(alpha,alpha,alpha) at depths 1/2; Beta(alpha,alpha) at depth 3",
                         "missing_depth3": "mean of observed posterior rates in the model column; 0.5 if none",
                         "cost_policy": "full recorded solver and verifier cost; no checkpoint discounts",
                         "band": "10th-90th percentile across profiling orders, not a confidence interval",
                         "origin": "seeded prior-only recommendation before any profiling",
                         "limitations": ["prefix pooling need not recover exact finite-grid column means",
                                         "fixed original keys; known question and verifier issues",
                                         "one recorded execution per pair; no generation resampling",
                                         "no checkpoint reuse or runtime controller"]},
            "exhaustive": {"pairs": len(dataset.observations), "cost_cents": str(total), "accuracy": best,
                           "optimal_configurations": [dataset.names[s] for s in dataset.sequences if dataset.accuracy[s] == best]},
            "curve": aggregate(runs), "runs": runs}


def save_outputs(result, output):
    output = Path(output).resolve()
    if output.suffix.lower() != ".json" or output == Path(result["source"]["database"]).resolve():
        raise ValueError("Choose a .json output distinct from the database.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    curve_file = output.with_suffix(".csv")
    with curve_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(result["curve"][0]))
        writer.writeheader()
        writer.writerows(result["curve"])
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE)
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--grader-version", default=GRADER)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--first-seed", type=int, default=0)
    parser.add_argument("--max-pairs", type=int)
    parser.add_argument("--pseudocount", type=float, default=0.5)
    parser.add_argument("--no-smoothing", action="store_true", help="Conditional decomposition ablation.")
    parser.add_argument("--plot", action="store_true", help="Also export a PNG and SVG scientific figure.")
    parser.add_argument("--output", type=Path, default=ROOT / "results/workflow_search/vinelm-adapted.json")
    args = parser.parse_args()
    try:
        dataset = load_dataset(args.database, args.run_id, args.grader_version)
        result = experiment(dataset, seeds=args.seeds, first_seed=args.first_seed, max_pairs=args.max_pairs,
                            pseudocount=args.pseudocount, smoothing=not args.no_smoothing)
        output = save_outputs(result, args.output)
        if args.plot:
            from mathqa_search_plot import plot_result
            plot_result(result, output.with_suffix(".png"))
    except (ValueError, ImportError, sqlite3.Error) as exc:
        parser.exit(1, f"{exc}\nFor smoothing/plots use: uv run --extra profiling python scripts/mathqa_vinelm.py --plot\n")
    print(json.dumps({"output": str(output), "seeds": args.seeds, "exhaustive": result["exhaustive"],
                      "final_mean_gap_pp": result["curve"][-1]["mean_gap_pp"],
                      "final_optimal_fraction": result["curve"][-1]["optimal_fraction"], "new_model_requests": 0}, indent=2))


if __name__ == "__main__":
    main()
