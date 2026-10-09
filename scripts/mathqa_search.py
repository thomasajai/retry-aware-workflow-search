"""Database-only Matrix UCB-E and Random pair search, plus saved-curve overlay.

No AgentOpt runtime or paid workflow adapter is imported. Its published selection
rule is implemented against one saved question/configuration observation at a time.
"""

import argparse
from collections import defaultdict
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

import mathqa_vinelm as vine

VERSIONS = {"agentopt": "agentopt-matrix-ucb-e-v1", "random": "random-pair-search-v1"}
OUTPUT_DIR = vine.ROOT / "results" / "workflow_search"


class PairSearch:
    """Public grid identities and queried scores only; no oracle/cost lookup."""

    def __init__(self, sequences, questions, *, strategy, seed=0, exploration=1.0):
        if strategy not in VERSIONS:
            raise ValueError("Choose agentopt or random.")
        if not math.isfinite(exploration) or exploration < 0:
            raise ValueError("Exploration weight must be finite and nonnegative.")
        self.sequences = tuple(sorted(sequences))
        self.questions = tuple(sorted(questions))
        if not self.sequences or not self.questions:
            raise ValueError("Require a nonempty candidate grid.")
        self.strategy, self.exploration = strategy, exploration
        self.rng = random.Random(seed)
        self.priority = list(self.sequences)
        random.Random(seed + 1_000_003).shuffle(self.priority)
        self.counts = defaultdict(lambda: [0, 0])  # successes, observations
        self.seen = set()
        self.pairs = list(product(self.questions, self.sequences))
        if strategy == "random":
            self.rng.shuffle(self.pairs)  # Exactly the VineLM pair permutation.
        self.cursor = 0

    def bound(self, sequence):
        successes, n = self.counts.get(sequence, (0, 0))
        if n == len(self.questions):
            return -math.inf
        if n == 0:
            return math.inf
        return successes / n + math.sqrt(self.exploration / n)

    def next_pair(self):
        if len(self.seen) == len(self.questions) * len(self.sequences):
            return None
        if self.strategy == "random":
            pair = self.pairs[self.cursor]
            self.cursor += 1
            return pair
        # Exact maximum; first in seeded priority wins a sampling-score tie.
        sequence = max(self.priority, key=self.bound)
        available = [q for q in self.questions if (q, sequence) not in self.seen]
        return self.rng.choice(available), sequence

    def observe(self, pair, score):
        question, sequence = pair
        if question not in self.questions or sequence not in self.sequences or pair in self.seen:
            raise ValueError("Unexpected or repeated pair.")
        if score not in (0, 1):
            raise ValueError("Require a binary independent workflow score.")
        self.seen.add(pair)
        self.counts[sequence][0] += score
        self.counts[sequence][1] += 1

    def recommend(self):
        observed = [s for s in self.priority if self.counts.get(s, (0, 0))[1] > 0]
        if not observed:
            return self.priority[0], None  # Seeded choice, no fabricated score.
        means = {s: self.counts[s][0] / self.counts[s][1] for s in observed}
        highest = max(means.values())
        choice = next(s for s in observed if math.isclose(means[s], highest, rel_tol=0, abs_tol=1e-12))
        return choice, means[choice]


def simulate(dataset, *, strategy, seed=0, max_pairs=None, exploration=1.0):
    total = len(dataset.questions) * len(dataset.sequences)
    if max_pairs is None:
        max_pairs = total
    if not 0 <= max_pairs <= total:
        raise ValueError("max_pairs must lie within the saved grid.")
    search = PairSearch(dataset.sequences, dataset.questions, strategy=strategy, seed=seed, exploration=exploration)
    best = max(dataset.accuracy.values())
    cost, history = Decimal(0), []

    def record(step, pair=None):
        choice, estimate = search.recommend()
        accuracy = dataset.accuracy[choice]  # Evaluator-only; never returned to search.
        history.append({"step": step, "cost_cents": str(cost * 100),
                        "queried_question": pair[0] if pair else None,
                        "queried_configuration": dataset.names[pair[1]] if pair else None,
                        "recommendation": dataset.names[choice], "estimated_accuracy": estimate,
                        "full_dataset_accuracy": accuracy, "gap_pp": 100 * (best - accuracy)})

    record(0)
    for step in range(1, max_pairs + 1):
        pair = search.next_pair()
        observation = dataset.observations[pair]
        score = int("correct_accept" in observation.outcomes)
        search.observe(pair, score)
        cost += observation.cost_usd
        record(step, pair)
    return {"seed": seed, "history": history,
            "configuration_counts": {dataset.names[s]: {"correct": counts[0], "observations": counts[1]}
                                     for s, counts in sorted(search.counts.items())}}


def experiment(dataset, *, strategy, seeds=100, first_seed=0, max_pairs=None, exploration=1.0):
    if seeds < 1:
        raise ValueError("Require at least one seed.")
    runs = [simulate(dataset, strategy=strategy, seed=seed, max_pairs=max_pairs, exploration=exploration)
            for seed in range(first_seed, first_seed + seeds)]
    best = max(dataset.accuracy.values())
    dependencies = {}
    for name in ("numpy", "matplotlib"):
        try:
            dependencies[name] = package_version(name)
        except PackageNotFoundError:
            dependencies[name] = None
    return {"version": VERSIONS[strategy], "strategy": strategy, "source": dataset.source,
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "shared_implementation_sha256": hashlib.sha256(Path(vine.__file__).read_bytes()).hexdigest(),
            "specification": {"path": str(vine.SPECIFICATION),
                              "sha256": hashlib.sha256(vine.SPECIFICATION.read_bytes()).hexdigest()},
            "python_version": sys.version, "dependencies": dependencies,
            "settings": {"seeds": seeds, "first_seed": first_seed, "max_pairs": max_pairs,
                         "exploration_weight": exploration if strategy == "agentopt" else None,
                         "batch_size": 1,
                         "sampling": "Matrix UCB-E: choose max UCB, then uniform unseen question" if strategy == "agentopt"
                                     else "uniform unseen pairs, without replacement; same orders as VineLM",
                         "recommendation": "maximum raw mean of observed workflow scores; unobserved excluded",
                         "priors": "none; seeded initial recommendation has null estimated accuracy",
                         "ties": "fixed seeded random priority; accuracy only",
                         "cost_policy": "full recorded solver and verifier cost; no cache discounts",
                         "band": "10th-90th percentile across profiling orders, not a confidence interval",
                         "limitations": ["fixed original keys; known question and verifier issues",
                                         "one recorded execution per pair; no generation resampling",
                                         "Random is pair sampling, not the paper's full-configuration variant",
                                         "seeded ties and Python RNG are replay choices, not library bitwise reproduction"]},
            "exhaustive": {"pairs": len(dataset.observations),
                           "cost_cents": str(sum((o.cost_usd for o in dataset.observations.values()), Decimal(0)) * 100),
                           "accuracy": best,
                           "optimal_configurations": [dataset.names[s] for s in dataset.sequences if dataset.accuracy[s] == best]},
            "curve": vine.aggregate(runs), "runs": runs}


def save_result(result, output):
    """Persist shared curve schema plus the exact spec/code companions."""
    spec_bytes, code_bytes = vine.SPECIFICATION.read_bytes(), Path(__file__).read_bytes()
    shared_bytes = Path(vine.__file__).read_bytes()
    if hashlib.sha256(spec_bytes).hexdigest() != result["specification"]["sha256"] or hashlib.sha256(
            code_bytes).hexdigest() != result["implementation_sha256"] or hashlib.sha256(
            shared_bytes).hexdigest() != result["shared_implementation_sha256"]:
        raise ValueError("Specification or implementation changed during the experiment.")
    output = vine.save_outputs(result, output)
    output.with_suffix(".spec.md").write_bytes(spec_bytes)
    output.with_suffix(".implementation.py").write_bytes(code_bytes)
    output.with_suffix(".shared-implementation.py").write_bytes(shared_bytes)
    return output


def assert_compatible(results):
    """Overlay only the same frozen grid and the same per-seed run scope."""
    if not results:
        raise ValueError("Require at least one saved result.")
    first = results[0]
    fields = ("database_sha256", "run_id", "dataset_sha256", "plan_sha256", "grader_version",
              "question_count", "configuration_count")
    for result in results[1:]:
        if any(result["source"][key] != first["source"][key] for key in fields) or result["exhaustive"] != first["exhaustive"]:
            raise ValueError("Cannot overlay results from different datasets or exhaustive references.")
        if [run["seed"] for run in result["runs"]] != [run["seed"] for run in first["runs"]] or any(
                len(a["history"]) != len(b["history"]) for a, b in zip(result["runs"], first["runs"])):
            raise ValueError("Cannot overlay different seed sets or observation limits.")


def save_comparison(files, output):
    """Rebuild a combined chart table from saved histories, with no simulations."""
    import csv

    files = [Path(f).resolve() for f in files]
    results = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    assert_compatible(results)
    labels = [result.get("strategy", "vinelm") for result in results]
    if len(set(labels)) != len(labels):
        raise ValueError("Require distinct strategies in a comparison.")
    minimum = min(Decimal(run["history"][-1]["cost_cents"]) for result in results for run in result["runs"])
    # Shared budget grid even when a --max-pairs limit gives different terminal costs.
    curves = []
    for label, result in zip(labels, results):
        curve = vine.aggregate(result["runs"], budgets=[minimum * i / 120 for i in range(121)])
        curves.extend({"strategy": label, **point} for point in curve)
    output = Path(output).resolve()
    if output.suffix.lower() != ".json" or output in files or output == Path(results[0]["source"]["database"]).resolve():
        raise ValueError("Choose a comparison .json distinct from source files and database.")
    output.parent.mkdir(parents=True, exist_ok=True)
    comparison = {"version": "workflow-search-comparison-v1", "source": results[0]["source"],
                  "exhaustive": results[0]["exhaustive"],
                  "series": [{"strategy": label, "version": result["version"], "settings": result["settings"],
                              "result_path": str(f), "result_sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                              "curve": [p for p in curves if p["strategy"] == label]}
                             for label, result, f in zip(labels, results, files)]}
    output.write_text(json.dumps(comparison, indent=2, allow_nan=False), encoding="utf-8")
    with output.with_suffix(".csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(curves[0]))
        writer.writeheader()
        writer.writerows(curves)
    return comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=vine.DATABASE)
    parser.add_argument("--run-id", default=vine.RUN_ID)
    parser.add_argument("--grader-version", default=vine.GRADER)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--first-seed", type=int, default=0)
    parser.add_argument("--max-pairs", type=int)
    parser.add_argument("--exploration", type=float, default=1.0)
    parser.add_argument("--strategy", choices=("agentopt", "random", "both"), default="both")
    parser.add_argument("--vinelm-result", type=Path, default=OUTPUT_DIR / "vinelm-adapted.json")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    try:
        dataset = vine.load_dataset(args.database, args.run_id, args.grader_version)
        selected = list(VERSIONS) if args.strategy == "both" else [args.strategy]
        results = [experiment(dataset, strategy=strategy, seeds=args.seeds, first_seed=args.first_seed,
                              max_pairs=args.max_pairs, exploration=args.exploration) for strategy in selected]
        # Validate saved VineLM compatibility before writing any comparison artifacts.
        saved_vine = json.loads(args.vinelm_result.read_text(encoding="utf-8")) if args.plot else None
        if saved_vine:
            assert_compatible([saved_vine, *results])
        paths = [save_result(result, args.output_dir / f"{strategy}.json")
                 for strategy, result in zip(selected, results)]
        if args.plot:
            from mathqa_search_plot import plot_comparison
            comparison_file = args.output_dir / "search-comparison.json"
            comparison = save_comparison([args.vinelm_result, *paths], comparison_file)
            plot_comparison(comparison, comparison_file.with_suffix(".png"))
    except (ValueError, ImportError, sqlite3.Error, OSError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps({"outputs": [str(p) for p in paths], "new_model_requests": 0,
                      "final_mean_gaps_pp": {s: r["curve"][-1]["mean_gap_pp"] for s, r in zip(selected, results)}}, indent=2))


if __name__ == "__main__":
    main()
