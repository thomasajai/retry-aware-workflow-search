"""Prepare an offline, paired verifier comparison; execute via the guarded screen runner."""

import argparse
from collections import defaultdict
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import random
import sqlite3

from mathqa_batch import DATABASE_PATH
from mathqa_verifier import COMPARISON_ARMS, VERIFIER_PROFILES, parse_verdict, profile
from mathqa_verifier_preflight import estimate
import mathqa_verifier_screen as screen
from mathqa_verifier_trials import DEFAULT_SOURCE_RUN, preview_saved
import mathqa_workflow_store as store

DEFAULT_PILOT = "090a84fd-9ef1-43fc-9663-178e7c042765"


def candidates(excluded=()):
    all_profiles = [base if arm == "baseline" else base + "__" + arm
                    for base in VERIFIER_PROFILES for arm in COMPARISON_ARMS]
    if len(set(excluded)) != len(excluded) or not set(excluded) <= set(all_profiles):
        raise ValueError("Excluded profiles must be unique declared comparison profiles.")
    selected = [alias for alias in all_profiles if alias not in excluded]
    if not selected:
        raise ValueError("Comparison needs at least one selected profile.")
    return selected


def check_reasoning_metadata(metadata, selected=None):
    for base in VERIFIER_PROFILES:
        if selected is not None and base + "__reasoning" not in selected:
            continue
        p = profile(base + "__reasoning")
        model = metadata["models"][p["model"]]
        if model["id"] != p["model"] or "reasoning" not in model["supported_parameters"]:
            raise ValueError("Reasoning model metadata mismatch or missing support.")
        controls = model.get("reasoning")
        if not isinstance(controls, dict):
            raise ValueError("Model does not advertise reasoning capabilities.")
        effort = p["settings"]["reasoning"].get("effort")
        if effort is not None and effort not in (controls.get("supported_efforts") or []):
            raise ValueError("Requested reasoning effort is not advertised by this model.")


def _cache(database_path, pilot_run_id, source_run_id, checksum, *, allow_stopped=False):
    # Offline reuse is limited to the explicit source run; no broad search or
    # outcome-dependent choice among repeated verdicts.
    uri = Path(database_path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as c:
        c.row_factory = sqlite3.Row
        run = c.execute("SELECT * FROM workflow_runs WHERE run_id=?", (pilot_run_id,)).fetchone()
        allowed_statuses = {"completed", "completed_with_errors", "budget_stopped", "interrupted"} if allow_stopped else {"completed"}
        if (run is None or run["kind"] != "verifier_screen" or run["status"] not in allowed_statuses
                or not run["finished_at_utc"] or run["dataset_sha256"] != checksum):
            raise ValueError("Reuse source must be a finished verifier screen on the same dataset.")
        if c.execute("SELECT COUNT(*) FROM workflow_calls w JOIN workflow_attempts a USING(attempt_id) "
                     "JOIN workflow_executions e USING(execution_id) WHERE e.run_id=? "
                     "AND (w.status='running' OR w.finished_at_utc IS NULL)", (pilot_run_id,)).fetchone()[0]:
            raise ValueError("Reuse source still has unfinished calls.")
        source_plan = json.loads(run["settings_json"])["plan"]
        if source_plan["source_run_id"] != source_run_id:
            raise ValueError("Reuse source has a different solver batch.")
        rows = [dict(r) for r in c.execute("SELECT w.*,a.historical_solver_call_id,a.verification_status,g.diagnostics_json "
            "FROM workflow_calls w JOIN workflow_attempts a USING(attempt_id) JOIN workflow_executions e USING(execution_id) "
            "JOIN workflow_grades g ON g.attempt_id=a.attempt_id WHERE e.run_id=? ORDER BY w.started_at_utc,w.call_id", (pilot_run_id,))]
    cache, regression_cases = {}, set()
    for row in rows:
        if row["historical_solver_call_id"] is None:
            continue
        regression_cases.add(row["historical_solver_call_id"])
        if row["status"] != "completed" or row["verification_status"] not in ("accept", "reject") or row["cost_usd"] is None:
            continue
        if allow_stopped:
            # A mathematically wrong Boolean verdict is reusable. A completed
            # request with incomplete billing/usage measurements is not.
            if (any(row[k] is None for k in ("input_tokens", "output_tokens", "reasoning_tokens"))
                    or row["reasoning_tokens"] > row["output_tokens"]
                    or row["cost_reservation_usd"] is None
                    or row["cost_usd"] > row["cost_reservation_usd"]
                    or row["input_tokens"] > screen.input_token_reservation(json.loads(row["request_json"]))
                    or row["output_tokens"] > json.loads(row["request_json"])["max_tokens"]):
                continue
            payload = json.loads(row["response_json"])
            if payload["choices"][0]["message"]["content"] != row["answer_text"]:
                raise ValueError("Saved verifier response content differs from its recorded answer.")
        actual = parse_verdict(row["answer_text"], status=row["status"], finish_reason=row["finish_reason"])
        if actual["status"] != row["verification_status"]:
            raise ValueError("Saved verifier verdict differs from its recorded response.")
        key = (row["historical_solver_call_id"], screen.digest(json.loads(row["request_json"])))
        if key in cache:
            raise ValueError("Ambiguous reuse: source contains repeated judgments for the same request.")
        cache[key] = {**row, "reuse_source_run_id": pilot_run_id}
    return cache, regression_cases


def prepare_comparison(preview, metadata, natural_review, reasoning_metadata, *, database_path,
                       pilot_run_id=DEFAULT_PILOT, seed=42, created_at=None,
                       reuse_run_ids=None, excluded_candidates=None):
    amended = reuse_run_ids is not None or excluded_candidates is not None
    excluded = excluded_candidates or []
    selected = candidates(excluded)
    reuse_ids = list(reuse_run_ids) if reuse_run_ids is not None else [pilot_run_id]
    if not reuse_ids or len(set(reuse_ids)) != len(reuse_ids):
        raise ValueError("Reuse run IDs must be explicit, nonempty, and unique.")
    if list(preview["profiles"]) != selected or preview["reviewed_diagnostics"]:
        raise ValueError("Comparison requires the declared selected profiles and natural answers only.")
    check_reasoning_metadata(reasoning_metadata, selected)
    plan = screen.prepare_plan(preview, metadata, natural_review, created_at=created_at)
    del plan["sha256"]
    cache, regressions = {}, set()
    for reuse_id in reuse_ids:
        source_cache, source_cases = _cache(database_path, reuse_id, plan["source_run_id"],
            plan["dataset"]["sha256"], allow_stopped=amended)
        if set(cache) & set(source_cache):
            raise ValueError("Ambiguous reuse: sources contain repeated judgments for the same request.")
        cache.update(source_cache)
        regressions.update(source_cases)
    remaining, reused = [], []
    for entry in plan["entries"]:
        if not entry["labels"].get("review"):
            raise ValueError("Every usable comparison response requires an independent reasoning review.")
        entry["evaluation_group"] = "regression" if entry["case_id"] in regressions else "expansion"
        row = cache.get((entry["historical_solver_call_id"], screen.digest(entry["request"])))
        if row is not None:
            old_labels = json.loads(row["diagnostics_json"])
            if any(old_labels.get(k) != v for k, v in entry["labels"].items()):
                raise ValueError("Saved verifier labels differ from the current review.")
            if row["provider"] != entry["endpoint"]["provider_name"] or row["returned_model"] != entry["request"]["model"]:
                raise ValueError("Saved verifier response violates the requested provider/model.")
            reused.append({"entry": entry, "run_id": row["reuse_source_run_id"], "call_id": row["call_id"],
                "response_sha256": screen.digest(json.loads(row["response_json"])),
                "grade_sha256": screen.digest(old_labels), "verdict": row["verification_status"],
                "historical_cost_usd": row["cost_usd"]})
        else:
            remaining.append(entry)
    if not remaining:
        raise ValueError("No new comparisons to execute.")
    rng = random.Random(seed)
    # Diagnose settings on inspected cases first. Balance the arms within each
    # question block so partial runs retain a clear coverage record.
    ordered = []
    for group in ("regression", "expansion"):
        ids = list(dict.fromkeys(e["question"]["id"] for e in remaining if e["evaluation_group"] == group))
        rng.shuffle(ids)
        for qid in ids:
            block = [e for e in remaining if e["evaluation_group"] == group and e["question"]["id"] == qid]
            rng.shuffle(block)
            ordered.extend(block)
    cost_preview = deepcopy(preview)
    allowed = {(e["case_id"], e["candidate"]): e["request"] for e in ordered}
    for item in cost_preview["natural_answers"]:
        item["requests"] = {alias: request for (cid, alias), request in allowed.items() if cid == item["source_call_id"]}
    assumptions = {a: 512 if a.endswith("__reasoning") else 32 for a in selected}
    plan.update(version="verifier-comparison-plan-v1", entries=ordered, reused_entries=reused,
        reuse_run_id=pilot_run_id, scheduling_seed=seed, reasoning_metadata=reasoning_metadata,
        cost_preview=estimate(cost_preview, metadata, output_assumptions=assumptions),
        comparison={"arms": list(COMPARISON_ARMS), "planned_observations": len(ordered) + len(reused),
            "new_requests": len(ordered), "reused_observations": len(reused),
            "usable_natural_answers": sum(i["usability"]["usable"] for i in preview["natural_answers"]),
            "unusable_natural_answers": sum(not i["usability"]["usable"] for i in preview["natural_answers"]),
            "regression_cases": sorted(regressions), "regression_is_held_out": False,
            "note": "Development comparison, one trial per profile/answer. Reasoning arm also raises the combined output cap. No causal claim about reasoning alone; no synthetic reruns."})
    plan["execution_policy"]["stop_on_verifier_error"] = True
    if amended:
        plan["version"] = "verifier-comparison-plan-v2"
        del plan["reuse_run_id"]
        plan["reuse_run_ids"] = reuse_ids
        plan["excluded_candidates"] = list(excluded)
    plan = deepcopy(plan)
    plan["sha256"] = screen.digest(plan)
    return plan


def comparison_summary(plan, rows):
    entries = plan["entries"] + [r["entry"] for r in plan["reused_entries"]]
    observations = {}
    for reused in plan["reused_entries"]:
        entry = reused["entry"]
        observations[(entry["candidate"], entry["case_id"])] = {"verdict": reused["verdict"], "reused": True, "new_cost_usd": 0}
    for row in rows:
        labels = json.loads(row["diagnostics_json"])
        observations[(row["candidate"], labels["case_id"])] = {
            "verdict": row["verification_status"], "reused": False, "new_cost_usd": row["cost_usd"]}
    by_entry = {(e["candidate"], e["case_id"]): e for e in entries}
    groups = defaultdict(list)
    for entry in entries:
        groups[(entry["candidate"], entry["evaluation_group"])].append(entry)
    quality = []
    for (alias, group), group_entries in groups.items():
        observed = [(e, observations[(alias, e["case_id"])]) for e in group_entries if (alias, e["case_id"]) in observations]
        valid = [(e, o) for e, o in observed if o["verdict"] in ("accept", "reject")]
        bad = [(e, o) for e, o in valid if e["labels"].get("expected_accept") is False]
        good = [(e, o) for e, o in valid if e["labels"].get("expected_accept") is True]
        base, *suffix = alias.split("__")
        quality.append({"candidate": base, "arm": suffix[0] if suffix else "baseline", "evaluation_group": group,
            "planned": len(group_entries), "observed": len(observed), "reused": sum(o["reused"] for _, o in observed),
            "new_calls": sum(not o["reused"] for _, o in observed), "technical_or_format_errors": len(observed) - len(valid),
            "false_acceptances": sum(o["verdict"] == "accept" for _, o in bad), "invalid_denominator": len(bad),
            "false_rejections": sum(o["verdict"] == "reject" for _, o in good), "valid_denominator": len(good),
            "unknown_labels": sum(e["labels"].get("expected_accept") is None for e, _ in valid),
            "new_known_cost_usd": sum(o["new_cost_usd"] or 0 for _, o in observed),
            "new_unknown_cost_calls": sum(not o["reused"] and o["new_cost_usd"] is None for _, o in observed)})
    paired = []
    for base in VERIFIER_PROFILES:
        for arm, reference in (("recompute", "baseline"), ("reasoning", "baseline"), ("reasoning", "recompute")):
            a, b = base + "__" + arm, base if reference == "baseline" else base + "__" + reference
            if a not in plan["profiles"] or b not in plan["profiles"]:
                continue
            for group in ("regression", "expansion"):
                stats = {"candidate": base, "arm": arm, "reference_arm": reference, "evaluation_group": group,
                    "paired_labeled_verdicts": 0, "improved": 0, "worsened": 0, "both_correct": 0, "both_wrong": 0,
                    "unpaired_or_error": 0, "unknown_label_pairs": 0}
                for entry in entries:
                    if entry["candidate"] != a or entry["evaluation_group"] != group:
                        continue
                    key_a, key_b = (a, entry["case_id"]), (b, entry["case_id"])
                    if key_a not in observations or key_b not in observations or any(observations[k]["verdict"] not in ("accept", "reject") for k in (key_a, key_b)):
                        stats["unpaired_or_error"] += 1
                        continue
                    expected = entry["labels"].get("expected_accept")
                    if expected is None:
                        stats["unknown_label_pairs"] += 1
                        continue
                    if by_entry[key_b]["labels"] != entry["labels"]:
                        raise ValueError("Paired observations must use the same independent labels.")
                    correct_a = (observations[key_a]["verdict"] == "accept") == expected
                    correct_b = (observations[key_b]["verdict"] == "accept") == expected
                    stats["paired_labeled_verdicts"] += 1
                    stats["both_correct" if correct_a and correct_b else "both_wrong" if not correct_a and not correct_b else "improved" if correct_a else "worsened"] += 1
                paired.append(stats)
    return {"design": plan["comparison"], "quality": quality, "paired_changes": paired,
            "note": "Reused costs are historical and excluded from new spend. Regression and expansion stay separate. Outputs from one question are related; counts do not establish population error rates."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument("--source-run", default=DEFAULT_SOURCE_RUN)
    parser.add_argument("--reuse-run", action="append", help="Explicit reuse source; repeat for multiple finished screens.")
    parser.add_argument("--exclude-candidate", action="append", choices=candidates(), default=[])
    parser.add_argument("--questions", type=int, default=8)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--reasoning-metadata", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.plan.exists():
            raise ValueError("Plan already exists; choose a new filename.")
        preview = preview_saved(args.source_run, database_path=args.database, questions=args.questions,
                                candidates=candidates(args.exclude_candidate))
        plan = prepare_comparison(preview, json.loads(args.metadata.read_text(encoding="utf-8")),
            json.loads(screen.NATURAL_REVIEW.read_text(encoding="utf-8")), json.loads(args.reasoning_metadata.read_text(encoding="utf-8")),
            database_path=args.database, reuse_run_ids=args.reuse_run,
            excluded_candidates=args.exclude_candidate if args.exclude_candidate else None)
        screen.validate_plan(plan, args.database)
        args.plan.parent.mkdir(parents=True, exist_ok=True)
        args.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"mode": "offline_comparison_preparation", "plan": str(args.plan.resolve()), "sha256": plan["sha256"],
            "comparison": plan["comparison"], "cost_preview": plan["cost_preview"], "new_generation_requests": 0}, indent=2))
    except (ValueError, KeyError, OSError, sqlite3.Error) as error:
        parser.exit(1, f"Comparison preparation failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
