"""Export a saved solver/verifier run as an interactive, offline HTML trie.

Standard library only. Opens SQLite read-only; no credentials or network calls.
"""

import argparse
from collections import defaultdict
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import re
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "results" / "mathqa_runs.sqlite3"
DEFAULT_RUN_ID = "f0c941bc-5479-4e86-ae2d-261b521a3317"
TEMPLATE_PATH = Path(__file__).parent / "templates" / "mathqa_workflow_trie.html"
OUTPUT_DIRECTORY = PROJECT_ROOT / "results" / "workflow_trees"
LABELS = {"qwen25": "Qwen2.5", "qwen3": "Qwen3", "deepseek": "DeepSeek"}
GRADER_VERSION = "workflow-option-v1"


def _sum_cost(calls):
    return sum((Decimal(str(c["cost_usd"])) for c in calls if c["cost_usd"] is not None), Decimal(0))


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def prefix_metrics(prefix, executions, attempts, calls, schedule, *, question_id=None):
    """Pool fresh observations of a prefix; never treat them as reused calls.

    Cumulative spend includes solver AND verifier calls through this position.
    Means use scheduled executions. Accuracy uses finished independent grades;
    no score is imputed for an incomplete execution or an uncalled later slot.
    """
    depth = len(prefix) or 3
    matches = lambda seq: tuple(seq[:len(prefix)]) == tuple(prefix)
    selected = [e for e in executions if matches(e["sequence"])
                and (question_id is None or e["question_id"] == question_id)]
    selected_ids = {e["execution_id"] for e in selected}
    planned = sum(matches(s["sequence"]) and (question_id is None or s["question_id"] == question_id) for s in schedule)
    selected_attempts = [a for a in attempts if a["execution_id"] in selected_ids and a["position"] <= depth]
    attempt_ids = {a["attempt_id"] for a in selected_attempts}
    cumulative_calls = [c for c in calls if c["attempt_id"] in attempt_ids]
    at_slot = [a for a in selected_attempts if a["position"] == depth]
    slot_ids = {a["attempt_id"] for a in at_slot}
    slot_calls = [c for c in cumulative_calls if c["attempt_id"] in slot_ids]
    graded = [e for e in selected if e["score"] is not None]
    accepted = [e for e in graded if e["status"] == "accepted" and e["accepted_position"] <= depth]
    correct = sum(e["score"] == 1 for e in accepted)
    cost = _sum_cost(cumulative_calls)
    return {
        "planned": planned, "reached_executions": len(selected), "graded": len(graded),
        "complete": len(graded) == planned and planned > 0,
        "cost_usd": str(cost), "mean_cost_usd": str(cost / planned) if planned else None,
        "unknown_cost_calls": sum(c["cost_usd"] is None for c in cumulative_calls),
        "requests": len(cumulative_calls), "through_accepted": len(accepted), "through_correct": correct,
        "through_accuracy": _ratio(correct, len(graded)),
        "final_correct": sum(e["score"] == 1 for e in graded),
        "final_accuracy": _ratio(sum(e["score"] == 1 for e in graded), len(graded)),
        "slot_reached": len(at_slot), "slot_graded": sum(a["has_grade"] for a in at_slot),
        "slot_key_correct": sum(a["option_correct"] == 1 for a in at_slot if a["has_grade"]),
        "slot_accepted": sum(a["verification_status"] == "accept" for a in at_slot),
        "slot_requests": len(slot_calls), "slot_cost_usd": str(_sum_cost(slot_calls)),
        "slot_solver_cost_usd": str(_sum_cost([c for c in slot_calls if c["role"] == "solver"])),
        "slot_verifier_cost_usd": str(_sum_cost([c for c in slot_calls if c["role"] == "verifier"])),
        "solver_cost_usd": str(_sum_cost([c for c in cumulative_calls if c["role"] == "solver"])),
        "verifier_cost_usd": str(_sum_cost([c for c in cumulative_calls if c["role"] == "verifier"])),
        "truncations": sum(c["role"] == "solver" and c["finish_reason"] == "length" for c in cumulative_calls),
        "input_tokens": sum(c["input_tokens"] or 0 for c in cumulative_calls),
        "output_tokens": sum(c["output_tokens"] or 0 for c in cumulative_calls),
        "reasoning_tokens": sum(c["reasoning_tokens"] or 0 for c in cumulative_calls),
        "mean_call_seconds": _ratio(sum(c["elapsed_seconds"] or 0 for c in cumulative_calls), planned),
        "mean_wall_seconds": _ratio(sum(e["elapsed_seconds"] or 0 for e in graded), len(graded)),
    }


def load_run(run_id=DEFAULT_RUN_ID, *, database_path=DATABASE_PATH, grader_version=GRADER_VERSION):
    database_path = Path(database_path).resolve()
    with closing(sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA query_only=ON")
        c.execute("BEGIN")  # One consistent snapshot if another process is writing.
        row = c.execute("SELECT * FROM workflow_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or row["kind"] != "sequence_evaluation":
            raise ValueError("Choose a saved solver-sequence evaluation run.")
        run = dict(row)
        settings = json.loads(run["settings_json"])
        plan = settings.get("plan")
        if not isinstance(plan, dict) or not plan.get("schedule"):
            raise ValueError("This exporter requires the run's saved evaluation plan.")
        configs = [dict(r) for r in c.execute("SELECT * FROM workflow_configs WHERE run_id=? ORDER BY name", (run_id,))]
        for config in configs:
            config["snapshot"] = json.loads(config["snapshot_json"])
            config["sequence"] = config["snapshot"]["solver_sequence"]
            if config["snapshot"] != plan["configurations"].get(config["name"]):
                raise ValueError("Stored configuration differs from the saved plan.")
        aliases = sorted({a for f in configs for a in f["sequence"]}, key=lambda a: (list(LABELS).index(a) if a in LABELS else 99, a))
        if len(aliases) != 3 or len(configs) != 27 or any(len(f["sequence"]) != 3 for f in configs):
            raise ValueError("This view requires three solver models and all 27 three-position configurations.")
        sequences = {tuple(f["sequence"]) for f in configs}
        if len(sequences) != 27:
            raise ValueError("Configuration sequences must be distinct.")
        by_id = {f["config_id"]: f for f in configs}
        executions = [dict(r) for r in c.execute("SELECT * FROM workflow_executions WHERE run_id=? ORDER BY rowid", (run_id,))]
        attempts = [dict(r) for r in c.execute("SELECT a.* FROM workflow_attempts a JOIN workflow_executions e USING(execution_id) WHERE e.run_id=? ORDER BY a.rowid", (run_id,))]
        calls = [dict(r) for r in c.execute("SELECT w.* FROM workflow_billable_calls w JOIN workflow_attempts a USING(attempt_id) JOIN workflow_executions e USING(execution_id) WHERE e.run_id=?", (run_id,))]
        grades = [dict(r) for r in c.execute("SELECT g.* FROM workflow_grades g JOIN workflow_executions e USING(execution_id) WHERE e.run_id=? AND g.grader_version=?", (run_id, grader_version))]
    final_grades = {g["execution_id"]: g for g in grades if g["attempt_id"] is None}
    attempt_grades = {g["attempt_id"]: g for g in grades if g["attempt_id"] is not None}
    attempts_by_id = {a["attempt_id"]: a for a in attempts}
    for a in attempts:
        g = attempt_grades.get(a["attempt_id"])
        a.update(has_grade=g is not None, option_correct=g["option_correct"] if g else None)
    for e in executions:
        e["sequence"] = by_id[e["config_id"]]["sequence"]
        e["configuration"] = by_id[e["config_id"]]["name"]
        e["score"] = final_grades.get(e["execution_id"], {}).get("workflow_score")
        e["accepted_position"] = attempts_by_id[e["accepted_attempt_id"]]["position"] if e["accepted_attempt_id"] else None
    schedule = [{**s, "sequence": plan["configurations"][s["configuration"]]["solver_sequence"]} for s in plan["schedule"]]
    prefixes = {()}
    for config in configs:
        prefixes.update(tuple(config["sequence"][:depth]) for depth in range(1, 4))
    questions = plan["questions"]
    nodes = []
    for prefix in sorted(prefixes, key=lambda p: (len(p), [aliases.index(a) for a in p])):
        nodes.append({"id": "/".join(prefix) or "root", "prefix": list(prefix), "depth": len(prefix),
            "configuration": next((f["name"] for f in configs if tuple(f["sequence"]) == prefix), None),
            "configuration_count": sum(tuple(f["sequence"][:len(prefix)]) == prefix for f in configs),
            "metrics": {key: prefix_metrics(prefix, executions, attempts, calls, schedule, question_id=qid)
                        for key, qid in [("all", None)] + [(q["id"], q["id"]) for q in questions]}})
    models = []
    provider_totals = defaultdict(lambda: {"requests": 0, "cost": Decimal(0), "unknown": 0})
    for call in calls:
        p = provider_totals[(call["requested_model"], call["provider"] or "Unreported")]
        p["requests"] += 1
        p["cost"] += Decimal(str(call["cost_usd"])) if call["cost_usd"] is not None else Decimal(0)
        p["unknown"] += call["cost_usd"] is None
    for alias in aliases:
        snapshots = [s for f in configs for a, s in zip(f["sequence"], f["snapshot"]["solvers"]) if a == alias]
        if any(s != snapshots[0] for s in snapshots):
            raise ValueError("A solver alias has inconsistent settings within this run.")
        solver = snapshots[0]
        models.append({"alias": alias, "label": LABELS.get(alias, alias), "role": "solver", "model": solver["model"],
                       "settings": solver["body_settings"], "prompt": solver["prompt_template"],
                       "response_contract": solver["response_contract"]})
    verifier = configs[0]["snapshot"]["verifier"]
    if any(f["snapshot"]["verifier"] != verifier for f in configs):
        raise ValueError("Verifier settings differ between configurations.")
    verifier_calls = [r for r in calls if r["role"] == "verifier"]
    saved_verifier_request = json.loads(verifier_calls[0]["request_json"]) if verifier_calls else None
    verifier_prompt = verifier.get("prompt")
    if verifier_prompt is None and saved_verifier_request:
        verifier_prompt = saved_verifier_request["messages"][0]["content"]
    models.append({"alias": "verifier", "label": "Gemini 2.5 Flash-Lite" if verifier["model"] == "google/gemini-2.5-flash-lite" else verifier["model"],
                   "role": "verifier", "model": verifier["model"], "settings": verifier["settings"], "prompt": verifier_prompt})
    for model in models:
        ep = plan["endpoints"][model["model"]]
        model.update(endpoint=ep, providers=[{"provider": provider, "requests": v["requests"], "cost_usd": str(v["cost"]), "unknown": v["unknown"]}
                     for (mid, provider), v in provider_totals.items() if mid == model["model"]])
    costs_by_execution = defaultdict(lambda: Decimal(0))
    attempts_per_execution = defaultdict(int)
    for a in attempts:
        attempts_per_execution[a["execution_id"]] += 1
    for call in calls:
        costs_by_execution[attempts_by_id[call["attempt_id"]]["execution_id"]] += _sum_cost([call])
    traces = [{"configuration": e["configuration"], "question_id": e["question_id"], "status": e["status"], "score": e["score"],
               "accepted_position": e["accepted_position"], "cost_usd": str(costs_by_execution[e["execution_id"]]),
               "attempts": attempts_per_execution[e["execution_id"]], "elapsed_seconds": e["elapsed_seconds"]} for e in executions]
    reviews = {}
    notes_path = PROJECT_ROOT / "notes" / "solver-verifier-routed-development-v5-results.md"
    if run_id == DEFAULT_RUN_ID and notes_path.exists():
        for line in notes_path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\| `(mathqa_test_\d+)` \| (.+?) \| (.+?) \|$", line)
            if match:
                reviews[match[1]] = {"finding": match[2].replace("`", ""), "key_note": match[3].replace("`", ""), "source": notes_path.name}
    root_metrics = next(n for n in nodes if n["id"] == "root")["metrics"]["all"]
    leaves = [n for n in nodes if n["depth"] == 3]
    if _sum_cost(calls) != sum((Decimal(n["metrics"]["all"]["cost_usd"]) for n in leaves), Decimal(0)):
        raise ValueError("Leaf costs do not reconcile with recorded run spend.")
    return {
        "run": {k: run[k] for k in ("run_id", "kind", "status", "started_at_utc", "finished_at_utc", "budget_usd", "max_requests", "plan_sha256", "dataset_sha256", "stop_reason")},
        "source": {"database": str(database_path), "grader_version": grader_version, "code_revision": settings.get("code_revision"),
                   "exported_at_utc": datetime.now(timezone.utc).isoformat(), "generation_requests": 0},
        "aliases": aliases, "models": models, "nodes": nodes, "questions": questions, "reviews": reviews, "executions": traces,
        "summary": root_metrics, "policy": plan["execution_policy"], "configuration_policy": configs[0]["snapshot"]["policy"],
        "split": {k: plan["split"].get(k) for k in ("selection_seed", "excluded_pilot_ids")},
        "scheduling_seed": plan.get("scheduling_seed"), "repetitions": plan.get("repetitions"),
        "expected_cost_usd": plan["cost_preview"]["estimated_total_usd"],
        "analysis_policy": plan.get("analysis_policy", {}),
        "saved_verifier_message_structure": {"question": "Original question", "options": "Original choices", "solver_proposal": {"calculation": "Solver calculation", "option": "Selected a–e", "value": "Returned value"}},
    }


def export_trie(run_id=DEFAULT_RUN_ID, *, database_path=DATABASE_PATH, output_path=None, grader_version=GRADER_VERSION):
    data = load_run(run_id, database_path=database_path, grader_version=grader_version)
    output = Path(output_path) if output_path else OUTPUT_DIRECTORY / f"workflow_{run_id}.html"
    output = output.resolve()
    if output.suffix.lower() != ".html" or output in {Path(database_path).resolve(), TEMPLATE_PATH.resolve()}:
        raise ValueError("Choose an .html output distinct from the input database and template.")
    # All strings, including stored questions, must stay data inside the HTML.
    payload = json.dumps(data, ensure_ascii=False, allow_nan=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if template.count("__RUN_DATA__") != 1:
        raise ValueError("HTML template must have exactly one data marker.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.replace("__RUN_DATA__", payload), encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID, help="Saved workflow evaluation ID; defaults to the completed October 8 comparison.")
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--grader-version", default=GRADER_VERSION, help="Independent grade version to display; never creates grades.")
    args = parser.parse_args()
    try:
        output = export_trie(args.run_id, database_path=args.database, output_path=args.output, grader_version=args.grader_version)
    except (ValueError, KeyError, OSError, sqlite3.Error) as error:
        parser.exit(1, f"Tree export stopped: {error}\n")
    print(json.dumps({"output": str(output), "run_id": args.run_id, "mode": "offline", "generation_requests": 0}, indent=2))


if __name__ == "__main__":
    main()
