"""Prepare a frozen verifier pilot offline; paid execution requires --run and caps."""

import argparse
from collections import defaultdict
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
from time import perf_counter

import httpx
from dotenv import load_dotenv

from mathqa_batch import DATABASE_PATH, OPENROUTER_URL, PROJECT_ROOT
from mathqa_verifier import parse_verdict
from mathqa_verifier_preflight import estimate, input_token_reservation, request_cost, select_endpoint
from mathqa_verifier_trials import DEFAULT_SOURCE_RUN, preview_saved
import mathqa_workflow_store as store

NATURAL_REVIEW = PROJECT_ROOT / "data" / "verifier_review" / "natural_reviews.json"


def digest(value):
    return hashlib.sha256(store.encode(value).encode("utf-8")).hexdigest()


def attach_reviews(preview, review):
    if review["source_run_id"] != preview["source_run_id"] or review["dataset_sha256"] != preview["dataset"]["sha256"]:
        raise ValueError("Natural review does not match the source run/dataset.")
    reviews = {r["source_call_id"]: r for r in review["reviews"]}
    if len(reviews) != len(review["reviews"]):
        raise ValueError("Duplicate natural review source.")
    for item in preview["natural_answers"]:
        r = reviews.get(item["source_call_id"])
        if r is None:
            continue
        if (r["question_id"] != item["question_id"] or r["solver_model"] != item["solver_model"]
                or r["answer_sha256"] != hashlib.sha256(item["original_answer"].encode()).hexdigest()):
            raise ValueError("Reviewed solver response changed.")
        labels = r["labels"]
        if any(labels[k] is not None and type(labels[k]) is not bool for k in ("option_correct", "reasoning_valid", "expected_accept")):
            raise ValueError("Review labels must be Boolean or unknown.")
        if not item["usability"]["usable"] or labels["option_correct"] != item["offline_labels"]["option_correct"]:
            raise ValueError("Natural review conflicts with extraction/answer key.")
        if not r["review"]["reviewer"] or not r["review"]["explanation"]:
            raise ValueError("Review needs attribution and explanation.")
        if labels["expected_accept"] is True and (labels["reasoning_valid"] is not True or labels["option_correct"] is not True):
            raise ValueError("Acceptance label requires valid reasoning and correct option.")
        item["offline_labels"] = {**labels, "source": "independent assistant review of saved solver answer",
                                  "review": r["review"], "annotation_uncertainty": r["annotation_uncertainty"]}


def prepare_plan(preview, metadata, natural_review, *, created_at=None):
    preview = deepcopy(preview)
    attach_reviews(preview, natural_review)
    entries = []
    # Round-robin candidates over cases; serial execution, no transport retries.
    for group, items in (("natural", preview["natural_answers"]), ("synthetic", preview["reviewed_diagnostics"])):
        for item in items:
            if not item["usability"]["usable"]:
                continue
            for alias, request in item["requests"].items():
                endpoint = select_endpoint(metadata, alias)
                request = deepcopy(request)
                pricing = endpoint["pricing"]
                request["provider"]["max_price"] = {
                    "prompt": float(Decimal(pricing["prompt"]) * 1_000_000),
                    "completion": float(Decimal(pricing["completion"]) * 1_000_000), "request": 0}
                item["requests"][alias] = request
                question = deepcopy(item["question"])
                if group == "synthetic":
                    question["id"] = "diagnostic:" + item["id"]
                entries.append({"candidate": alias, "group": group,
                    "case_id": item["source_call_id"] if group == "natural" else item["id"],
                    "question": question, "solver_model": item.get("solver_model", "offline/synthetic"),
                    "historical_solver_call_id": item.get("source_call_id"),
                    "offline_source": None if group == "natural" else {
                        "status": item.get("generation_status", "completed"), "finish_reason": item.get("finish_reason", "stop"),
                        "answer": item["answer"], "fixture_id": item["id"]},
                    "usability": item["usability"], "request": request,
                    "labels": item["offline_labels"] if group == "natural" else {**item["labels"], "review": item["review"], "source": item["source"]},
                    "endpoint": {"tag": endpoint["tag"], "provider_name": endpoint["provider_name"], "pricing": pricing},
                    "input_token_reservation": input_token_reservation(request),
                    "cost_reservation_usd": str(request_cost(request, endpoint))})
    if not entries:
        raise ValueError("No usable answers to screen.")
    plan = {"version": "verifier-screen-plan-v1", "created_at_utc": created_at or store.now(),
            "source_run_id": preview["source_run_id"], "dataset": preview["dataset"], "profiles": preview["profiles"],
            "questions": preview["summary"]["selected_questions"], "include_reviewed": bool(preview["reviewed_diagnostics"]),
            "provider_metadata": metadata, "natural_review": natural_review,
            "cost_preview": estimate(preview, metadata), "entries": entries,
            "execution_policy": {"concurrency": 1, "transport_retries": 0, "solver_calls": 0,
                "stop_on_unknown_cost": True, "max_metadata_age_hours": 24, "timeout_seconds": 60}}
    plan = deepcopy(plan)
    plan["sha256"] = digest(plan)
    return plan


def validate_plan(plan, database_path, *, check_age=True):
    if plan.get("sha256") != digest({k: v for k, v in plan.items() if k != "sha256"}):
        raise ValueError("Screening plan checksum failed.")
    if check_age:
        fetched = datetime.fromisoformat(plan["provider_metadata"]["fetched_at_utc"])
        age = (datetime.now(timezone.utc) - fetched).total_seconds()
        if age < -300 or age > 24 * 3600:
            raise ValueError("Refresh free provider metadata and prepare a new cost proposal (24-hour limit).")
        if plan.get("reasoning_metadata"):
            reasoning_age = (datetime.now(timezone.utc) - datetime.fromisoformat(plan["reasoning_metadata"]["fetched_at_utc"])).total_seconds()
            if reasoning_age < -300 or reasoning_age > 24 * 3600:
                raise ValueError("Refresh free reasoning metadata (24-hour limit).")
    # Rebuild requests from trusted builders, source DB/dataset, and versioned
    # reviews. A checksum alone would not protect against a hand-edited request.
    review = json.loads(NATURAL_REVIEW.read_text(encoding="utf-8"))
    preview = preview_saved(plan["source_run_id"], database_path=database_path, questions=plan["questions"],
                            candidates=list(plan["profiles"]), include_reviewed=plan["include_reviewed"])
    if plan["version"] in ("verifier-comparison-plan-v1", "verifier-comparison-plan-v2"):
        from mathqa_verifier_compare import prepare_comparison
        reuse_options = ({"pilot_run_id": plan["reuse_run_id"]} if plan["version"] == "verifier-comparison-plan-v1"
                         else {"reuse_run_ids": plan["reuse_run_ids"], "excluded_candidates": plan["excluded_candidates"]})
        rebuilt = prepare_comparison(preview, plan["provider_metadata"], review, plan["reasoning_metadata"],
            database_path=database_path, seed=plan["scheduling_seed"], created_at=plan["created_at_utc"], **reuse_options)
    elif plan["version"] == "verifier-screen-plan-v1":
        rebuilt = prepare_plan(preview, plan["provider_metadata"], review, created_at=plan["created_at_utc"])
    else:
        raise ValueError("Unknown screening plan version.")
    if rebuilt != plan:
        raise ValueError("Source, reviews, profiles, or request settings changed; prepare a new plan.")


def _set_run(run_id, status, database_path, reason=None):
    with closing(store.connect(database_path)) as c, c:
        if status == "running":
            c.execute("UPDATE workflow_runs SET status=?,started_at_utc=? WHERE run_id=?", (status, store.now(), run_id))
        else:
            c.execute("UPDATE workflow_runs SET status=?,finished_at_utc=?,stop_reason=? WHERE run_id=?",
                      (status, store.now(), reason, run_id))


def screening_summary(run_id, *, database_path=DATABASE_PATH):
    with closing(store.connect(database_path)) as c:
        run = dict(c.execute("SELECT * FROM workflow_runs WHERE run_id=?", (run_id,)).fetchone())
        rows = c.execute("SELECT f.name AS candidate,f.snapshot_json,w.*,a.verification_status,g.diagnostics_json "
            "FROM workflow_calls w JOIN workflow_attempts a USING(attempt_id) JOIN workflow_executions e USING(execution_id) "
            "JOIN workflow_configs f USING(config_id) LEFT JOIN workflow_grades g ON g.attempt_id=a.attempt_id "
            "WHERE e.run_id=? ORDER BY w.started_at_utc,w.call_id", (run_id,)).fetchall()
    grouped = defaultdict(list)
    planned = defaultdict(int)
    for entry in json.loads(run["settings_json"])["plan"]["entries"]:
        planned[(entry["candidate"], entry["group"])] += 1
        grouped[(entry["candidate"], entry["group"])]  # retain zero-coverage groups
    for row in rows:
        labels = json.loads(row["diagnostics_json"])
        grouped[(row["candidate"], labels["group"])].append((row, labels))
    quality = []
    for (candidate, group), items in grouped.items():
        accepted = sum(r["verification_status"] == "accept" for r, _ in items)
        valid = [(r, l) for r, l in items if r["verification_status"] in ("accept", "reject")]
        invalid = [(r, l) for r, l in valid if l.get("expected_accept") is False]
        correct = [(r, l) for r, l in valid if l.get("expected_accept") is True]
        quality.append({"candidate": candidate, "group": group, "planned_calls": planned[(candidate, group)], "attempted_calls": len(items), "accepted": accepted,
            "valid_verdicts": len(valid), "technical_or_format_errors": len(items) - len(valid),
            "reviewed_invalid_attempted": sum(l.get("expected_accept") is False for _, l in items),
            "reviewed_valid_attempted": sum(l.get("expected_accept") is True for _, l in items),
            "false_acceptances": sum(r["verification_status"] == "accept" for r, _ in invalid), "invalid_solution_denominator": len(invalid),
            "false_rejections": sum(r["verification_status"] == "reject" for r, _ in correct), "valid_solution_denominator": len(correct),
            "unknown_label_valid_verdicts": sum(l.get("expected_accept") is None for _, l in valid),
            "accepted_wrong_options": sum(r["verification_status"] == "accept" and l.get("option_correct") is False for r, l in items),
            "known_cost_usd": sum(r["cost_usd"] or 0 for r, _ in items), "unknown_cost_calls": sum(r["cost_usd"] is None for r, _ in items),
            "unreconciled_reservations_usd": sum(r["cost_reservation_usd"] for r, _ in items if r["cost_usd"] is None),
            "sum_call_elapsed_seconds": sum(r["elapsed_seconds"] or 0 for r, _ in items),
            "input_tokens": sum(r["input_tokens"] or 0 for r, _ in items), "billed_output_tokens": sum(r["output_tokens"] or 0 for r, _ in items),
            "reasoning_tokens_subset": sum(r["reasoning_tokens"] or 0 for r, _ in items),
            "unknown_reasoning_measurements": sum(r["reasoning_tokens"] is None for r, _ in items)})
    report = {"run_id": run_id, "status": run["status"], "stop_reason": run["stop_reason"],
            "budget_usd": run["budget_usd"], "max_requests": run["max_requests"], "plan_sha256": run["plan_sha256"],
            "wall_elapsed_seconds": (datetime.fromisoformat(run["finished_at_utc"]) - datetime.fromisoformat(run["started_at_utc"])).total_seconds() if run["finished_at_utc"] else None,
            "costs": store.cost_summary(run_id, database_path=database_path), "quality": quality,
            "note": "Assistant-reviewed development examples. Natural and synthetic results stay separate. Unknown labels/errors are outside binary quality denominators. A small pilot cannot establish reliability or select a winner."}
    plan = json.loads(run["settings_json"])["plan"]
    if plan["version"] in ("verifier-comparison-plan-v1", "verifier-comparison-plan-v2"):
        from mathqa_verifier_compare import comparison_summary
        report["comparison"] = comparison_summary(plan, rows)
    return report


def _invalid_json_constant(value):
    raise ValueError("Nonfinite JSON constant in provider response.")


def run_screen(plan, *, database_path, budget_usd, max_requests, api_key, client):
    if isinstance(budget_usd, bool) or not math.isfinite(float(budget_usd)) or budget_usd <= 0:
        raise ValueError("A finite positive spending limit is required.")
    if type(max_requests) is not int or max_requests < 1:
        raise ValueError("A positive integer request limit is required.")
    if not api_key:
        raise ValueError("An OpenRouter API key is required for --run.")
    validate_plan(plan, database_path)
    store.migrate(database_path)
    ids = list(dict.fromkeys(e["question"]["id"] for e in plan["entries"]))
    try:
        run_id = store.create_run("verifier_screen", plan["dataset"]["path"], plan["dataset"]["sha256"], ids,
            {"plan": plan}, database_path=database_path, budget_usd=float(budget_usd), max_requests=max_requests, plan_sha256=plan["sha256"])
    except sqlite3.IntegrityError as error:
        raise ValueError("This frozen plan already has a run; no automatic rerun/resume is allowed.") from error
    _set_run(run_id, "running", database_path)
    cap, spent = Decimal(str(budget_usd)), Decimal(0)
    configs, repetitions = {}, defaultdict(int)
    for alias in plan["profiles"]:
        configs[alias] = store.create_config(run_id, alias, {"profile": plan["profiles"][alias], "plan_sha256": plan["sha256"]}, database_path=database_path)
    requested, errors, stop_reason = 0, 0, None
    terminal = "completed"
    try:
        for entry in plan["entries"]:
            reservation = Decimal(entry["cost_reservation_usd"])
            if requested >= max_requests or spent + reservation > cap:
                stop_reason = "request_limit" if requested >= max_requests else "spending_limit"
                terminal = "budget_stopped"
                break
            alias, question = entry["candidate"], entry["question"]
            repetitions[(alias, question["id"])] += 1
            execution = store.create_execution(run_id, configs[alias], question,
                repetition=repetitions[(alias, question["id"])], database_path=database_path)
            attempt = store.create_attempt(execution, 1, entry["solver_model"], historical_solver_call_id=entry["historical_solver_call_id"],
                offline_source=entry["offline_source"], database_path=database_path)
            store.record_usability(attempt, entry["usability"], database_path=database_path)
            labels = entry["labels"]
            store.record_grade(execution, "verifier-screen-review-v1", plan["dataset"]["sha256"], labels["source"],
                attempt_id=attempt, option_correct=labels.get("option_correct"), reasoning_valid=labels.get("reasoning_valid"),
                reviewer=labels.get("review", {}).get("reviewer"), diagnostics={**labels, "group": entry["group"], "case_id": entry["case_id"]}, database_path=database_path)
            call_id = store.create_call(attempt, "verifier", entry["request"]["model"], entry["request"],
                cost_reservation_usd=float(reservation), database_path=database_path)
            requested += 1
            started = perf_counter()
            payload, raw, http_status, error_type = None, None, None, None
            call_status = "completed"
            interrupted = False
            try:
                response = client.post(OPENROUTER_URL, json=entry["request"], headers={"Authorization": f"Bearer {api_key}"}, timeout=60)
                raw, http_status = response.text, response.status_code
                payload = json.loads(raw, parse_constant=_invalid_json_constant)
                if not isinstance(payload, dict):
                    payload = None
                    raise ValueError("Provider response is not an object.")
                if http_status != 200 or "error" in payload:
                    call_status, error_type = "failed", "ProviderError"
                elif payload.get("provider") != entry["endpoint"]["provider_name"] or payload.get("model") != entry["request"]["model"]:
                    call_status, error_type = "failed", "ProviderOrModelMismatch"
                else:
                    choices = payload.get("choices")
                    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict) or choices[0].get("finish_reason") != "stop":
                        call_status, error_type = "failed", "IncompleteGeneration"
            except KeyboardInterrupt:
                call_status, error_type, interrupted = "interrupted", "KeyboardInterrupt", True
            except (httpx.HTTPError, ValueError):
                call_status, error_type = "failed", "TransportOrResponseError"
            elapsed = perf_counter() - started
            store.finish_call(call_id, status=call_status, elapsed_seconds=elapsed, payload=payload, raw_response=raw,
                http_status=http_status, error_type=error_type,
                error_message="See recorded response; no client retries." if error_type else None, database_path=database_path)
            with closing(store.connect(database_path)) as c:
                row = dict(c.execute("SELECT * FROM workflow_calls WHERE call_id=?", (call_id,)).fetchone())
            verdict = parse_verdict(row["answer_text"], status=row["status"], finish_reason=row["finish_reason"])
            store.record_verification(attempt, verdict["status"], database_path=database_path)
            accepted = verdict["status"] == "accept"
            store.finish_execution(execution, "interrupted" if interrupted else "accepted" if accepted else "failed",
                "screen_" + verdict["status"], elapsed, accepted_attempt_id=attempt if accepted else None, database_path=database_path)
            errors += verdict["status"] in ("error", "invalid")
            if row["cost_usd"] is not None:
                spent += Decimal(str(row["cost_usd"]))
            if interrupted:
                stop_reason, terminal = "interrupted_billing_may_be_unknown", "interrupted"
            elif row["cost_usd"] is None:
                stop_reason, terminal = "unknown_cost", "budget_stopped"
            elif row["provider"] != entry["endpoint"]["provider_name"] or row["returned_model"] != entry["request"]["model"]:
                stop_reason, terminal = "provider_or_model_mismatch", "budget_stopped"
            elif row["input_tokens"] is None or row["output_tokens"] is None:
                stop_reason, terminal = "unknown_token_usage", "budget_stopped"
            elif row["reasoning_tokens"] is not None and row["reasoning_tokens"] > row["output_tokens"]:
                stop_reason, terminal = "inconsistent_reasoning_usage", "budget_stopped"
            elif (row["input_tokens"] > entry["input_token_reservation"] or row["output_tokens"] > entry["request"]["max_tokens"]
                    or Decimal(str(row["cost_usd"])) > reservation or spent > cap):
                stop_reason, terminal = "reservation_exceeded", "budget_stopped"
            elif plan["execution_policy"].get("stop_on_verifier_error") and verdict["status"] in ("error", "invalid"):
                stop_reason, terminal = "verifier_error_review_settings", "budget_stopped"
            if stop_reason:
                break
    except BaseException:
        # Unexpected storage/programming failures never schedule another call.
        _set_run(run_id, "interrupted", database_path, "unexpected_failure_review_durable_calls")
        raise
    if terminal == "completed" and errors:
        terminal = "completed_with_errors"
    _set_run(run_id, terminal, database_path, stop_reason)
    return screening_summary(run_id, database_path=database_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument("--source-run", default=DEFAULT_SOURCE_RUN)
    parser.add_argument("--questions", type=int, default=1)
    parser.add_argument("--metadata", type=Path, help="Saved free public endpoint metadata, needed to prepare a plan.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--run", action="store_true", help="Consumes credits; requires advance notice/authorization and numeric caps.")
    parser.add_argument("--budget-usd", type=float)
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        protected = {args.database.resolve(), NATURAL_REVIEW.resolve(),
            (PROJECT_ROOT / "data/mathqa_200/mathqa_200.json").resolve(), (PROJECT_ROOT / "data/verifier_review/cases.json").resolve()}
        if args.plan.resolve() in protected or args.metadata and args.plan.resolve() == args.metadata.resolve():
            raise ValueError("Plan cannot overwrite an input/database.")
        if args.report and (args.report.resolve() in protected or args.report.resolve() == args.plan.resolve()):
            raise ValueError("Report cannot overwrite an input/database/plan.")
        if not args.run:
            if not args.metadata:
                parser.error("Offline preparation requires --metadata (fetch it with mathqa_verifier_preflight.py).")
            if args.plan.exists():
                raise ValueError("Plan already exists; use a new filename to retain the approved snapshot.")
            preview = preview_saved(args.source_run, database_path=args.database, questions=args.questions, include_reviewed=True)
            plan = prepare_plan(preview, json.loads(args.metadata.read_text(encoding="utf-8")), json.loads(NATURAL_REVIEW.read_text(encoding="utf-8")))
            args.plan.parent.mkdir(parents=True, exist_ok=True)
            args.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            print(json.dumps({"mode": "offline_preparation", "plan": str(args.plan.resolve()), "sha256": plan["sha256"],
                "proposed_requests": len(plan["entries"]), "cost_preview": plan["cost_preview"], "new_generation_requests": 0}, indent=2))
        else:
            if args.budget_usd is None or args.max_requests is None:
                parser.error("--run requires --budget-usd and --max-requests; no implicit budget.")
            if not args.report:
                parser.error("--run requires --report to save the summary.")
            if args.report.exists():
                raise ValueError("Report already exists; choose a new filename.")
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            validate_plan(plan, args.database)
            load_dotenv(PROJECT_ROOT / ".env")
            # Default httpx transport has zero retries; serial requests only.
            with httpx.Client(follow_redirects=False) as client:
                result = run_screen(plan, database_path=args.database, budget_usd=args.budget_usd,
                    max_requests=args.max_requests, api_key=os.getenv("OPENROUTER_API_KEY"), client=client)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, indent=2))
    except (ValueError, KeyError, OSError, sqlite3.Error) as error:
        parser.exit(1, f"Screening stopped: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
