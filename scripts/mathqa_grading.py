"""Answer-only grading of complete saved batches; never sends API requests."""

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from mathqa_response import unique_object


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "results" / "mathqa_runs.sqlite3"
GRADER_VERSION = "answer-only-v1"


def initialize_grading_tables(connection: sqlite3.Connection) -> None:
    """Add result storage without altering runs, calls, or validations."""
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS run_gradings (
            run_id TEXT PRIMARY KEY REFERENCES runs(run_id),
            grader_version TEXT NOT NULL,
            dataset_sha256 TEXT NOT NULL,
            graded_at_utc TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS call_gradings (
            call_id TEXT PRIMARY KEY REFERENCES calls(call_id),
            run_id TEXT NOT NULL REFERENCES run_gradings(run_id),
            score INTEGER NOT NULL CHECK (score IN (0, 1)),
            option_letter TEXT,
            returned_value TEXT,
            gradable INTEGER NOT NULL CHECK (gradable IN (0, 1)),
            value_conflict INTEGER CHECK (value_conflict IN (0, 1)),
            diagnostics_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS model_gradings (
            run_id TEXT NOT NULL REFERENCES run_gradings(run_id),
            model TEXT NOT NULL,
            correct_count INTEGER NOT NULL,
            denominator INTEGER NOT NULL CHECK (denominator > 0),
            accuracy_percent REAL NOT NULL,
            generation_failures INTEGER NOT NULL,
            ungradable_completed INTEGER NOT NULL,
            format_invalid_completed INTEGER NOT NULL,
            format_unvalidated_completed INTEGER NOT NULL,
            PRIMARY KEY (run_id, model)
        );
    """)


def generation_completed(call: dict) -> bool:
    return call["status"] == "completed" and call["finish_reason"] not in ("length", "error")


def extract_final_answer(answer: str | None, contract: str) -> dict:
    """Extract explicit final fields, independently of calculation validity."""
    fields = None
    errors = []
    if not isinstance(answer, str) or not answer.strip():
        errors.append("Missing answer text.")
    elif contract == "json-v1":
        try:
            parsed = json.loads(answer, object_pairs_hook=unique_object)
            if isinstance(parsed, dict):
                fields = parsed
            else:
                errors.append("Expected one JSON object.")
        except ValueError as error:
            errors.append(f"Invalid JSON: {error}")
    elif contract == "line-v1":
        # More than one option marker is ambiguous; never choose the last one.
        markers = re.findall(r"(?:^|;)\s*[a-e]\s*\)", answer)
        match = re.fullmatch(r"[^\r\n]*;\s*([a-e])\s*\)\s*([^;\r\n]*)", answer.strip())
        if match is None or len(markers) != 1 or re.search(r"\b[a-e]\s*\)", match[2]):
            errors.append("Expected one unambiguous terminal ; a-e) value segment.")
        else:
            fields = {"option": match[1], "value": match[2]}
    else:
        errors.append(f"Unsupported response contract: {contract}.")

    raw_option = fields.get("option") if fields is not None else None
    raw_value = fields.get("value") if fields is not None else None
    option = raw_option if isinstance(raw_option, str) and raw_option in list("abcde") else None
    value = raw_value if isinstance(raw_value, str) else None
    if fields is not None:
        if option is None:
            errors.append("Final option must be one explicit lowercase letter a-e.")
        if value is None or not value.strip():
            errors.append("Returned value is missing or is not a nonempty string.")
    return {"option_letter": option, "returned_value": value,
            "diagnostics": {"errors": errors, "raw_option": raw_option, "raw_value": raw_value}}


def grade_answer(call: dict, contract: str, question: dict) -> dict:
    result = extract_final_answer(call["answer_text"], contract)
    option, value = result["option_letter"], result["returned_value"]
    completed = generation_completed(call)
    result["gradable"] = completed and option is not None
    result["score"] = int(result["gradable"] and option == question["correct"])
    result["value_conflict"] = None
    if option is not None and isinstance(value, str) and value.strip():
        result["value_conflict"] = " ".join(value.split()) != " ".join(question["parsed_options"][option].split())
        if result["value_conflict"]:
            result["diagnostics"]["errors"].append("Returned value differs from the selected option text.")
    if not completed:
        result["diagnostics"]["errors"].append("Generation failed or was truncated; score is 0 regardless of partial text.")
    result["diagnostics"]["response_contract"] = contract
    return result


def grade_run(run_id: str, database_path: Path = DATABASE_PATH) -> list[dict]:
    """Verify completion/checksum, then atomically save all scores and summaries."""
    connection = sqlite3.connect(database_path.resolve().as_uri() + "?mode=rw", uri=True)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        initialize_grading_tables(connection)
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            run = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            if run is None or run["status"] not in ("completed", "completed_with_errors") or not run["finished_at_utc"]:
                raise ValueError("Only a finished batch can be graded.")
            models = json.loads(run["models_json"])
            questions = json.loads(run["question_ids_json"])
            if not models or not questions or len(set(models)) != len(models) or len(set(questions)) != len(questions):
                raise ValueError("Saved model/question selection is empty or duplicated.")
            has_validations = connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'call_validations'").fetchone()
            validation = "v.format_valid" if has_validations else "NULL AS format_valid"
            join = " LEFT JOIN call_validations v USING (call_id)" if has_validations else ""
            calls = [dict(row) for row in connection.execute(
                f"SELECT c.*, {validation} FROM calls c{join} WHERE run_id = ? ORDER BY attempt_number", (run_id,))]
            planned = {(q, m) for q in questions for m in models}
            if (not calls or {(c["question_id"], c["requested_model"]) for c in calls} != planned
                    or any(c["status"] not in ("completed", "failed") or not c["finished_at_utc"] for c in calls)):
                raise ValueError("All planned attempts must have completed or failed final outcomes before grading.")
            dataset = Path(run["dataset_path"])
            if not dataset.is_absolute():
                dataset = PROJECT_ROOT / dataset
            raw = dataset.read_bytes()
            if hashlib.sha256(raw).hexdigest() != run["dataset_sha256"]:
                raise ValueError("Dataset checksum differs from the saved run; grading refused.")
            records = json.loads(raw)
            by_id = {q["id"]: q for q in records}
            if len(by_id) != len(records):
                raise ValueError("Dataset has duplicate question IDs.")
            for qid in questions:
                q = by_id.get(qid)
                if (q is None or q.get("correct") not in list("abcde")
                        or not isinstance(q.get("parsed_options"), dict)
                        or any(not isinstance(q["parsed_options"].get(letter), str) for letter in "abcde")):
                    raise ValueError(f"Dataset has no usable answer key/options for {qid}.")
            settings = json.loads(run["request_settings_json"])
            grades = {}
            latest = {}
            for call in calls:
                model = call["requested_model"]
                # Baseline runs predate profiles and used the line response contract.
                contract = settings.get("model_configs", {}).get(model, {}).get("response_contract", "line-v1")
                grades[call["call_id"]] = grade_answer(call, contract, by_id[call["question_id"]])
                latest[(call["question_id"], model)] = call
            summaries = []
            for model in models:
                selected_calls = [latest[(q, model)] for q in questions]
                correct = sum(grades[c["call_id"]]["score"] for c in selected_calls)
                summaries.append({
                    "model": model, "correct_count": correct, "denominator": len(questions),
                    "accuracy_percent": correct / len(questions) * 100,
                    "generation_failures": sum(not generation_completed(c) for c in selected_calls),
                    "ungradable_completed": sum(generation_completed(c) and not grades[c["call_id"]]["gradable"] for c in selected_calls),
                    "format_invalid_completed": sum(generation_completed(c) and c["format_valid"] == 0 for c in selected_calls),
                    "format_unvalidated_completed": sum(generation_completed(c) and c["format_valid"] is None for c in selected_calls),
                })
            connection.execute("INSERT INTO run_gradings VALUES (?, ?, ?, ?) "
                               "ON CONFLICT(run_id) DO UPDATE SET grader_version=excluded.grader_version, "
                               "dataset_sha256=excluded.dataset_sha256, graded_at_utc=excluded.graded_at_utc",
                               (run_id, GRADER_VERSION, run["dataset_sha256"], datetime.now(timezone.utc).isoformat()))
            for call_id, result in grades.items():
                connection.execute("INSERT OR REPLACE INTO call_gradings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (call_id, run_id, result["score"], result["option_letter"], result["returned_value"],
                     int(result["gradable"]), result["value_conflict"], json.dumps(result["diagnostics"], ensure_ascii=False)))
            for summary in summaries:
                connection.execute("INSERT OR REPLACE INTO model_gradings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                   (run_id, *summary.values()))
            return summaries
    finally:
        connection.close()


def print_summaries(summaries: list[dict]) -> None:
    for s in summaries:
        print(f"{s['model']}: {s['correct_count']}/{s['denominator']} correct "
              f"({s['accuracy_percent']:.2f}%); generation failures: {s['generation_failures']}; "
              f"ungradable completed: {s['ungradable_completed']}; "
              f"format-invalid completed: {s['format_invalid_completed']}; "
              f"format-unvalidated completed: {s['format_unvalidated_completed']}.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    args = parser.parse_args()
    try:
        print_summaries(grade_run(args.run_id, args.database))
        from mathqa_table import export_table
        print(f"HTML report: {export_table(args.run_id, database_path=args.database)}")
    except (OSError, sqlite3.Error, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
