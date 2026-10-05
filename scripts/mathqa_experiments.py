"""Preview or run one model's MathQA formatting trial (five questions by default)."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import sqlite3
from uuid import UUID

from dotenv import load_dotenv

import mathqa_batch as batch
from mathqa_table import export_table
from mathqa_models import MODEL_PROFILES, EXPERIMENTS, experiment_config


def build_report(run_id: str, database_path: Path) -> dict:
    """Read-only diagnostics; use all selected questions for format success rate."""
    connection = sqlite3.connect(database_path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        connection.row_factory = sqlite3.Row
        run = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if run is None:
            raise ValueError("Unknown run ID.")
        has_validations = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'call_validations'"
        ).fetchone() is not None
        validation_columns = (
            "v.response_contract, v.format_valid, v.parsed_fields_json, v.validation_errors_json"
            if has_validations else
            "NULL AS response_contract, NULL AS format_valid, NULL AS parsed_fields_json, NULL AS validation_errors_json"
        )
        validation_join = " LEFT JOIN call_validations v ON v.call_id = c.call_id" if has_validations else ""
        calls = connection.execute(
            f"SELECT c.*, {validation_columns} FROM calls c{validation_join} "
            "WHERE c.run_id = ? AND c.attempt_number = ("
            "SELECT MAX(latest.attempt_number) FROM calls latest WHERE latest.run_id = c.run_id "
            "AND latest.question_id = c.question_id AND latest.requested_model = c.requested_model) "
            "ORDER BY c.row_number", (run_id,),
        ).fetchall()
    finally:
        connection.close()
    selected = len(json.loads(run["question_ids_json"]))
    summaries = []
    diagnostics = []
    for model in json.loads(run["models_json"]):
        model_calls = [call for call in calls if call["requested_model"] == model]
        for call in model_calls:
            payload = json.loads(call["response_json"]) if call["response_json"] else {}
            payload = payload if isinstance(payload, dict) else {}
            usage = payload.get("usage") or {}
            details = (usage.get("completion_tokens_details") or {}) if isinstance(usage, dict) else {}
            reasoning = details.get("reasoning_tokens") if isinstance(details, dict) else None
            diagnostics.append({
                "call_id": call["call_id"], "question_id": call["question_id"], "model": model,
                "generation_status": call["status"], "finish_reason": call["finish_reason"],
                "format_valid": bool(call["format_valid"]) if call["format_valid"] is not None else None,
                "parsed_fields": json.loads(call["parsed_fields_json"]) if call["parsed_fields_json"] else None,
                "validation_errors": json.loads(call["validation_errors_json"]) if call["validation_errors_json"] else None,
                "answer_text": call["answer_text"], "provider": payload.get("provider"),
                "reasoning_tokens": reasoning, "output_tokens": call["output_tokens"],
                "cost_usd": call["cost_usd"], "elapsed_seconds": call["elapsed_seconds"],
                "error_type": call["error_type"], "error_message": call["error_message"],
            })
        completed = sum(call["status"] == "completed" for call in model_calls)
        valid = sum(call["status"] == "completed" and call["format_valid"] == 1 for call in model_calls)
        summaries.append({
            "model": model, "selected_questions": selected,
            "generation_completed": completed,
            "generation_failed": sum(call["status"] == "failed" for call in model_calls),
            "generation_unfinished": sum(call["status"] in ("running", "interrupted") for call in model_calls),
            "missing_calls": selected - len(model_calls),
            "invalid_completed_responses": sum(call["status"] == "completed" and call["format_valid"] == 0 for call in model_calls),
            "format_invalid_all_calls": sum(call["format_valid"] == 0 for call in model_calls),
            "validation_missing": sum(call["format_valid"] is None for call in model_calls),
            "format_successes": valid, "format_success_rate": valid / selected,
            "reported_cost_usd": sum(call["cost_usd"] for call in model_calls if call["cost_usd"] is not None),
            "calls_without_reported_cost": sum(call["cost_usd"] is None for call in model_calls),
        })
    return {"run_id": run_id, "run_status": run["status"],
            "settings": json.loads(run["request_settings_json"]),
            "summaries": summaries, "calls": diagnostics}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List candidate experiments without requests or database changes.")
    parser.add_argument("--model", choices=MODEL_PROFILES, help="Select one model for a reviewable trial.")
    parser.add_argument("--experiment", choices=EXPERIMENTS,
                        help="Override the model default: qwen25/deepseek=json-prompt; qwen3=json-schema-no-think.")
    parser.add_argument("--questions", type=int, default=5)
    parser.add_argument("--database", type=Path, default=batch.DATABASE_PATH)
    parser.add_argument("--run", action="store_true", help="Make paid requests; default is a read-only preview.")
    parser.add_argument("--report-run", help="Inspect a saved trial without API requests.")
    args = parser.parse_args()
    if args.report_run:
        if args.run or args.model or args.list:
            parser.error("--report-run cannot be combined with --run, --model, or --list.")
        print(json.dumps(build_report(args.report_run, args.database), ensure_ascii=False, indent=2))
        return 0
    if args.list:
        if args.run:
            parser.error("--list cannot be combined with --run.")
        for alias, profile in MODEL_PROFILES.items():
            variants = EXPERIMENTS if alias == "qwen3" else EXPERIMENTS[:3]
            print(f"{alias} ({profile.model}): {', '.join(variants)} (default: {profile.default_experiment})")
        return 0
    if not args.model:
        parser.error("Choose --model, or use --list or --report-run.")
    args.experiment = args.experiment or MODEL_PROFILES[args.model].default_experiment
    try:
        model, config = experiment_config(args.model, args.experiment)
        questions = batch.load_questions(args.questions)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Model: {model}; experiment: {args.experiment}")
    print(f"Planned calls: {len(questions)}; concurrency: {batch.MAX_CONCURRENT_REQUESTS}; retries: 0")
    print(f"Question IDs: {', '.join(question['id'] for question in questions)}")
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nFirst question's exact prompt:\n" + config["prompt_template"].format(**questions[0]))
    if not args.run:
        print("\nPreview only: no API requests or database changes. Add --run for a paid trial.")
        return 0
    load_dotenv(batch.PROJECT_ROOT / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        parser.error("Set OPENROUTER_API_KEY in the repository's .env file.")
    batch.initialize_database(args.database)
    run_id = batch.create_run(questions, args.database, model_configs={model: config})
    print(f"Run ID: {run_id}", flush=True)
    try:
        status = asyncio.run(batch.run_batch(run_id, questions, api_key, database_path=args.database))
    except KeyboardInterrupt:
        print(f"Interrupted run: {run_id}; saved calls remain in SQLite.")
        return 130
    report = build_report(run_id, args.database)
    report_path = batch.PROJECT_ROOT / "results" / "mathqa_experiments" / f"{UUID(run_id)}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summaries"], indent=2))
    print(f"Diagnostics (answers, validation, provider, reasoning, cost, timing): {report_path}")
    print(f"Original answer table: {export_table(run_id, database_path=args.database)}")
    all_valid = all(summary["format_successes"] == len(questions) for summary in report["summaries"])
    return 0 if status == "completed" and all_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
