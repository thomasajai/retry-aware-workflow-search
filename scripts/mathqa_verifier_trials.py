"""Preview verifier screening against saved answers. Offline only in Milestone 1."""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

from mathqa_batch import DATABASE_PATH, PROJECT_ROOT
from mathqa_verifier import VERIFIER_PROFILES, VERIFIER_PROMPT, build_request, extract_usable, profile

DEFAULT_SOURCE_RUN = "6e8ba4fd-3f6d-41f9-9522-23c84e0d332d"
REVIEW_PATH = PROJECT_ROOT / "data" / "verifier_review" / "cases.json"


def load_review(path=REVIEW_PATH):
    review = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = review["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Review cases must be nonempty and uniquely identified.")
    for case in cases:
        labels = case["labels"]
        for key in ("option_correct", "reasoning_valid", "expected_accept"):
            if labels[key] is not None and type(labels[key]) is not bool:
                raise ValueError("Review labels must be Boolean or unknown.")
        if not case["review"]["reviewer"] or not case["review"]["explanation"]:
            raise ValueError("Reviewed cases need attribution and explanation.")
    return review


def preview_saved(source_run=DEFAULT_SOURCE_RUN, *, database_path=DATABASE_PATH, questions=20,
                  candidates=None, include_reviewed=False, review_path=REVIEW_PATH):
    if questions < 1:
        raise ValueError("Question count must be positive.")
    candidates = list(VERIFIER_PROFILES) if candidates is None else list(candidates)
    if not candidates or len(set(candidates)) != len(candidates):
        raise ValueError("Candidates must be nonempty and unique.")
    profiles = {alias: profile(alias) for alias in candidates}
    # Read-only URI prevents accidental source creation or migration.
    uri = Path(database_path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as c:
        c.row_factory = sqlite3.Row
        row = c.execute("SELECT * FROM runs WHERE run_id=?", (source_run,)).fetchone()
        if row is None or row["status"] not in ("completed", "completed_with_errors") or not row["finished_at_utc"]:
            raise ValueError("Source must be a finished saved batch.")
        run = dict(row)
        all_ids = json.loads(run["question_ids_json"])
        if questions > len(all_ids):
            raise ValueError("Question count exceeds the saved run selection.")
        ids = all_ids[:questions]
        models = json.loads(run["models_json"])
        configs = json.loads(run["request_settings_json"]).get("model_configs", {})
        calls = [dict(row) for row in c.execute("SELECT * FROM calls WHERE run_id=? ORDER BY attempt_number", (source_run,))]
    dataset = (PROJECT_ROOT / run["dataset_path"]).resolve()
    checksum = hashlib.sha256(dataset.read_bytes()).hexdigest()
    if checksum != run["dataset_sha256"]:
        raise ValueError("Saved dataset checksum no longer matches.")
    records = json.loads(dataset.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in records}
    if len(by_id) != len(records) or any(q not in by_id for q in ids):
        raise ValueError("Dataset IDs are duplicated or selected questions are missing.")
    latest = {}
    for call in calls:
        if call["question_id"] in ids and call["requested_model"] in models:
            if call["status"] not in ("completed", "failed", "interrupted"):
                raise ValueError("Source contains unfinished selected calls.")
            key = (call["question_id"], call["requested_model"])
            if key not in latest or call["attempt_number"] > latest[key]["attempt_number"]:
                latest[key] = call
            elif call["attempt_number"] == latest[key]["attempt_number"]:
                raise ValueError("Source contains duplicate final attempts.")
    natural, historical_costs = [], []
    for qid in ids:
        record = by_id[qid]
        question = {"id": qid, "problem": record["Problem"], "options": record["options"]}
        for model in models:
            call = latest.get((qid, model))
            if call is None:
                raise ValueError(f"Missing source call for {qid}, {model}.")
            contract = configs.get(model, {}).get("response_contract")
            if contract is None:
                contract = json.loads(run["request_settings_json"]).get("response_contract")
            result = extract_usable(call["answer_text"], contract, status=call["status"], finish_reason=call["finish_reason"])
            fields = result["fields"]
            option_correct = (fields["option"] == record["correct"]) if result["usable"] else None
            natural.append({"source_call_id": call["call_id"], "question_id": qid, "question": question, "solver_model": model,
                            "generation_status": call["status"], "original_answer": call["answer_text"],
                            "usability": result, "offline_labels": {"option_correct": option_correct, "reasoning_valid": None,
                            "source": "dataset option key only; reasoning not reviewed"},
                            "requests": {a: build_request(a, question, fields) for a in candidates} if result["usable"] else {}})
            historical_costs.append(call["cost_usd"])
    reviewed = []
    review_metadata = None
    if include_reviewed:
        fixture = load_review(review_path)
        review_metadata = {k: v for k, v in fixture.items() if k != "cases"}
        for case in fixture["cases"]:
            result = extract_usable(case["answer"], case["contract"], status=case.get("generation_status", "completed"),
                                    finish_reason=case.get("finish_reason", "stop"))
            reviewed.append({**case, "usability": result,
                             "requests": {a: build_request(a, case["question"], result["fields"]) for a in candidates} if result["usable"] else {}})
    usable = sum(item["usability"]["usable"] for item in natural)
    reviewed_usable = sum(item["usability"]["usable"] for item in reviewed)
    breakdown = [{"candidate": a, "model": profiles[a]["model"], "natural_calls": usable,
                  "diagnostic_calls": reviewed_usable, "max_calls": usable + reviewed_usable,
                  "estimated_cost_usd": None, "reason": "Provider/rates and billed reasoning usage not yet verified."} for a in candidates]
    return {"mode": "offline_preview", "paid_execution_available": False, "source_run_id": source_run,
            "dataset": {"path": str(dataset), "sha256": checksum, "question_ids": ids},
            "profiles": profiles, "verifier_prompt": VERIFIER_PROMPT,
            "summary": {"selected_questions": questions, "source_attempts": len(natural), "usable_source_answers": usable,
                        "unusable_source_answers": len(natural) - usable, "reviewed_diagnostic_cases": len(reviewed),
                        "usable_reviewed_cases": reviewed_usable, "natural_max_requests": usable * len(candidates),
                        "diagnostic_max_requests": reviewed_usable * len(candidates),
                        "total_max_requests": (usable + reviewed_usable) * len(candidates),
                        "new_requests_made": 0, "new_cost_usd": 0,
                        "historical_known_solver_cost_usd": sum(x for x in historical_costs if x is not None),
                        "historical_unknown_cost_calls": sum(x is None for x in historical_costs)},
            "cost_preview": breakdown, "review_metadata": review_metadata,
            "natural_answers": natural, "reviewed_diagnostics": reviewed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", default=DEFAULT_SOURCE_RUN)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument("--questions", type=int, default=20)
    parser.add_argument("--candidate", action="append", choices=VERIFIER_PROFILES)
    parser.add_argument("--include-reviewed", action="store_true")
    parser.add_argument("--output", type=Path, help="Save a full preview JSON; prints a compact summary instead.")
    args = parser.parse_args()
    try:
        report = preview_saved(args.source_run, database_path=args.database, questions=args.questions,
                               candidates=args.candidate, include_reviewed=args.include_reviewed)
        serialized = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        if args.output:
            if args.output.resolve() in (args.database.resolve(), Path(report["dataset"]["path"]), REVIEW_PATH.resolve()):
                raise ValueError("Preview output cannot overwrite the database, dataset, or review fixture.")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized + "\n", encoding="utf-8")
            print(json.dumps({"mode": report["mode"], "summary": report["summary"], "cost_preview": report["cost_preview"],
                              "output": str(args.output.resolve())}, indent=2))
        else:
            print(serialized)
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.exit(1, f"Preview failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
