"""Prepare a MathQA batch, or execute it with --run using bounded concurrency."""

import argparse
import asyncio
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import httpx
from dotenv import load_dotenv

from mathqa_table import export_table
from mathqa_response import CONTRACTS, validate_answer
from mathqa_models import default_model_configs
from mathqa_grading import initialize_grading_tables, grade_run, print_summaries


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "mathqa_200" / "mathqa_200.json"
DATABASE_PATH = PROJECT_ROOT / "results" / "mathqa_runs.sqlite3"

MODELS = list(default_model_configs())
QUESTION_COUNT = 50
# Limit the number of simultaneous requests within each model's batch.
MAX_CONCURRENT_REQUESTS = 5
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 60.0


def initialize_database(database_path: Path = DATABASE_PATH) -> None:
    """Create tables additively; do not insert experiment records yet."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        # Enable this on every future connection, too: SQLite defaults it off.
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY NOT NULL,
                created_at_utc TEXT NOT NULL,
                started_at_utc TEXT,
                finished_at_utc TEXT,
                status TEXT NOT NULL CHECK (
                    status IN (
                        'prepared', 'running', 'completed', 'completed_with_errors', 'interrupted'
                    )
                ),
                models_json TEXT NOT NULL,
                question_ids_json TEXT NOT NULL,
                dataset_path TEXT NOT NULL,
                dataset_sha256 TEXT NOT NULL,
                prompt_template TEXT NOT NULL,
                request_settings_json TEXT NOT NULL,
                max_concurrent_requests INTEGER NOT NULL CHECK (
                    max_concurrent_requests > 0
                )
            );

            CREATE TABLE IF NOT EXISTS calls (
                call_id TEXT PRIMARY KEY NOT NULL,
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                question_id TEXT NOT NULL,
                row_number INTEGER NOT NULL CHECK (row_number > 0),
                requested_model TEXT NOT NULL,
                attempt_number INTEGER NOT NULL DEFAULT 1 CHECK (attempt_number > 0),
                started_at_utc TEXT NOT NULL,
                finished_at_utc TEXT,
                status TEXT NOT NULL CHECK (
                    status IN ('running', 'completed', 'failed', 'interrupted')
                ),
                request_json TEXT NOT NULL,
                answer_text TEXT,
                response_json TEXT,
                response_body_text TEXT,
                response_id TEXT,
                returned_model TEXT,
                http_status INTEGER,
                finish_reason TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                cost_usd REAL,
                elapsed_seconds REAL,
                error_type TEXT,
                error_message TEXT,
                UNIQUE (run_id, question_id, requested_model, attempt_number)
            );

            CREATE TABLE IF NOT EXISTS call_validations (
                call_id TEXT PRIMARY KEY NOT NULL REFERENCES calls(call_id),
                response_contract TEXT NOT NULL,
                format_valid INTEGER NOT NULL CHECK (format_valid IN (0, 1)),
                parsed_fields_json TEXT,
                validation_errors_json TEXT NOT NULL
            );
            """
        )
        # Earlier steps created this database before raw response text was added.
        call_columns = {row[1] for row in connection.execute("PRAGMA table_info(calls)")}
        if "response_body_text" not in call_columns:
            with connection:
                connection.execute("ALTER TABLE calls ADD COLUMN response_body_text TEXT")
        initialize_grading_tables(connection)
    finally:
        connection.close()


def load_questions(question_count: int = QUESTION_COUNT) -> list[dict[str, str]]:
    """Read the requested number of records in file order, keeping solver inputs."""
    if question_count < 1:
        raise ValueError("Question count must be at least 1.")
    records = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    if len(records) < question_count:
        raise ValueError(
            f"Requested {question_count} questions, but the dataset contains {len(records)}."
        )

    return [
        {
            "id": record["id"],
            "problem": record["Problem"],
            "options": record["options"],
        }
        for record in records[:question_count]
    ]


def build_prompt(question: dict[str, str], model: str | None = None) -> str:
    """Preview a current model profile (execution uses the saved run instead)."""
    configs = default_model_configs()
    config = configs[next(iter(configs)) if model is None else model]
    return config["prompt_template"].format(
        problem=question["problem"], options=question["options"]
    )


def create_run(
    questions: list[dict[str, str]], database_path: Path = DATABASE_PATH,
    *, model_configs: dict[str, dict] | None = None,
) -> str:
    """Save the experiment settings and return its new run ID."""
    run_id = str(uuid4())
    created_at_utc = datetime.now(timezone.utc).isoformat()
    dataset_sha256 = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
    request_settings = {
        "api_url": OPENROUTER_URL,
        "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "automatic_retries": 0,
        "execution_mode": "parallel_within_model_sequential_between_models",
    }
    model_configs = default_model_configs() if model_configs is None else model_configs
    if not model_configs:
        raise ValueError("At least one model configuration is required.")
    for config in model_configs.values():
        if config.get("response_contract") not in CONTRACTS:
            raise ValueError("Each model needs a known response contract.")
        if not isinstance(config.get("body_settings"), dict):
            raise ValueError("Each model needs explicit body_settings.")
        for question in questions:
            config["prompt_template"].format(problem=question["problem"], options=question["options"])
    request_settings["model_configs"] = model_configs
    models = list(model_configs)

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        # Commit on success; roll back the insert if an exception occurs.
        with connection:
            connection.execute(
                """
                INSERT INTO runs (
                    run_id, created_at_utc, status, models_json, question_ids_json,
                    dataset_path, dataset_sha256, prompt_template,
                    request_settings_json, max_concurrent_requests
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    created_at_utc,
                    "prepared",
                    json.dumps(models),
                    json.dumps([question["id"] for question in questions]),
                    DATASET_PATH.relative_to(PROJECT_ROOT).as_posix(),
                    dataset_sha256,
                    # Legacy column remains readable; model_configs holds every template.
                    next(iter(model_configs.values()))["prompt_template"],
                    json.dumps(request_settings),
                    MAX_CONCURRENT_REQUESTS,
                ),
            )
    finally:
        connection.close()

    return run_id


def create_call(
    run_id: str,
    question_id: str,
    row_number: int,
    model: str,
    request_body: dict,
    *,
    attempt_number: int = 1,
    database_path: Path = DATABASE_PATH,
) -> str:
    """Commit a running call record before the caller sends its HTTP request."""
    call_id = str(uuid4())
    started_at_utc = datetime.now(timezone.utc).isoformat()

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            connection.execute(
                """
                INSERT INTO calls (
                    call_id, run_id, question_id, row_number, requested_model,
                    attempt_number, started_at_utc, status, request_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    run_id,
                    question_id,
                    row_number,
                    model,
                    attempt_number,
                    started_at_utc,
                    "running",
                    json.dumps(request_body, ensure_ascii=False),
                ),
            )
    finally:
        connection.close()

    return call_id


def finish_call(
    call_id: str,
    *,
    status: str,
    elapsed_seconds: float,
    response_payload: object | None = None,
    response_body_text: str | None = None,
    http_status: int | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    response_contract: str | None = None,
    options: str = "",
    database_path: Path = DATABASE_PATH,
) -> None:
    """Save a call's final outcome, preserving any answer, usage, and full JSON."""
    if status not in ("completed", "failed", "interrupted"):
        raise ValueError("Final call status must be completed, failed, or interrupted.")
    if elapsed_seconds < 0:
        raise ValueError("Elapsed seconds cannot be negative.")

    payload = response_payload if isinstance(response_payload, dict) else {}
    # Error responses can omit choices or usage, or provide null instead.
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        usage = {}
    choices = payload.get("choices")
    choice = {}
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        choice = choices[0]
    message = choice.get("message")
    answer_text = message.get("content") if isinstance(message, dict) else None
    if not isinstance(answer_text, str):
        answer_text = None

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            cursor = connection.execute(
                """
                UPDATE calls SET
                    finished_at_utc = ?, status = ?, answer_text = ?,
                    response_json = ?, response_body_text = ?, response_id = ?, returned_model = ?,
                    http_status = ?, finish_reason = ?, input_tokens = ?,
                    output_tokens = ?, total_tokens = ?, cost_usd = ?,
                    elapsed_seconds = ?, error_type = ?, error_message = ?
                WHERE call_id = ? AND status = 'running'
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    status,
                    answer_text,
                    json.dumps(response_payload, ensure_ascii=False)
                    if response_payload is not None else None,
                    response_body_text,
                    payload.get("id"),
                    payload.get("model"),
                    http_status,
                    choice.get("finish_reason"),
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    usage.get("total_tokens"),
                    usage.get("cost"),
                    elapsed_seconds,
                    error_type,
                    error_message,
                    call_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"Call {call_id!r} does not exist or is already finished.")
            if response_contract is not None:
                validation = validate_answer(answer_text, response_contract, options)
                connection.execute(
                    "INSERT INTO call_validations VALUES (?, ?, ?, ?, ?)",
                    (call_id, response_contract, int(validation["valid"]),
                     json.dumps(validation["parsed_fields"], ensure_ascii=False)
                     if validation["parsed_fields"] is not None else None,
                     json.dumps(validation["errors"], ensure_ascii=False)),
                )
    finally:
        connection.close()


async def call_model(
    client: httpx.AsyncClient,
    run_id: str,
    question: dict[str, str],
    row_number: int,
    model: str,
    api_key: str,
    *,
    database_path: Path = DATABASE_PATH,
) -> str:
    """Send one request, save its outcome, and return the local call ID."""
    if not api_key:
        raise ValueError("An OpenRouter API key is required.")

    connection = sqlite3.connect(database_path)
    try:
        connection.row_factory = sqlite3.Row
        run = connection.execute(
            "SELECT prompt_template, request_settings_json FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    finally:
        connection.close()
    if run is None:
        raise ValueError(f"Run {run_id!r} does not exist.")

    settings = json.loads(run["request_settings_json"])
    if "model_configs" in settings:
        # A missing profile is a setup error, never a fallback to shared controls.
        model_config = settings["model_configs"][model]
    else:
        model_config = None  # Compatibility with saved baseline runs.
    prompt_template = model_config["prompt_template"] if model_config is not None else run["prompt_template"]
    body_settings = model_config["body_settings"] if model_config is not None else settings["body_settings"]
    prompt = prompt_template.format(problem=question["problem"], options=question["options"])
    request_body = {
        **body_settings,
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    call_id = create_call(
        run_id, question["id"], row_number, model, request_body,
        database_path=database_path,
    )

    status = "failed"
    response_payload = None
    response_body_text = None
    http_status = None
    error_type = None
    error_message = None
    elapsed_seconds = 0.0
    try:
        started = perf_counter()
        try:
            response = await client.post(
                settings["api_url"],
                headers={"Authorization": f"Bearer {api_key}"},
                json=request_body,
                timeout=settings["timeout_seconds"],
                follow_redirects=False,
            )
        finally:
            # The non-streaming request includes reading the response body.
            elapsed_seconds = perf_counter() - started

        http_status = response.status_code
        response_body_text = response.text
        try:
            response_payload = response.json()
        except ValueError:
            raise ValueError("Response body was not valid JSON.") from None

        # Parse first so JSON error responses are preserved, too.
        response.raise_for_status()
        if not isinstance(response_payload, dict):
            raise ValueError("Expected the API response to be a JSON object.")
        if response_payload.get("error"):
            raise ValueError("OpenRouter returned an API error; see the saved response.")
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ValueError("OpenRouter returned no valid response choice.")
        choice = choices[0]
        if choice.get("finish_reason") == "length":
            raise ValueError("The response reached the output token limit.")
        if choice.get("finish_reason") == "error":
            raise ValueError("The model reported a generation error.")
        message = choice.get("message")
        answer = message.get("content") if isinstance(message, dict) else None
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("OpenRouter returned no answer text.")
        status = "completed"
    except asyncio.CancelledError:
        status = "interrupted"
        error_type = "CancelledError"
        error_message = "The request task was cancelled; provider usage may be unknown."
        raise
    except httpx.HTTPError as error:
        error_type = type(error).__name__
        # Avoid copying request details or credentials from exception messages.
        error_message = (
            f"OpenRouter returned HTTP {http_status}."
            if isinstance(error, httpx.HTTPStatusError)
            else "The HTTP request failed; see error_type for the failure category."
        )
    except ValueError as error:
        error_type = type(error).__name__
        error_message = str(error)
    except Exception as error:
        error_type = type(error).__name__
        error_message = "Unexpected error while handling the API request."
        raise
    finally:
        # Database failures propagate so the batch cannot silently lose results.
        finish_call(
            call_id,
            status=status,
            elapsed_seconds=elapsed_seconds,
            response_payload=response_payload,
            response_body_text=response_body_text,
            http_status=http_status,
            error_type=error_type,
            error_message=error_message,
            response_contract=model_config.get("response_contract") if model_config is not None else None,
            options=question["options"],
            database_path=database_path,
        )

    return call_id


def set_run_status(
    run_id: str, status: str, database_path: Path = DATABASE_PATH
) -> None:
    """Record an execution start or finish, enforcing the previous run status."""
    if status == "running":
        previous_status = "prepared"
        timestamp_column = "started_at_utc"
    elif status in ("completed", "completed_with_errors", "interrupted"):
        previous_status = "running"
        timestamp_column = "finished_at_utc"
    else:
        raise ValueError("Invalid execution status.")

    connection = sqlite3.connect(database_path)
    try:
        with connection:
            cursor = connection.execute(
                # The column name comes only from the fixed choices above.
                f"UPDATE runs SET status = ?, {timestamp_column} = ? "
                "WHERE run_id = ? AND status = ?",
                (status, datetime.now(timezone.utc).isoformat(), run_id, previous_status),
            )
            if cursor.rowcount != 1:
                raise ValueError("Run does not exist or cannot make this status transition.")
    finally:
        connection.close()


async def run_batch(
    run_id: str,
    questions: list[dict[str, str]],
    api_key: str,
    *,
    database_path: Path = DATABASE_PATH,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str:
    """Finish one model's concurrent question batch before starting the next."""
    if not api_key:
        raise ValueError("An OpenRouter API key is required.")
    connection = sqlite3.connect(database_path)
    try:
        connection.row_factory = sqlite3.Row
        run = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        existing_calls = connection.execute(
            "SELECT COUNT(*) FROM calls WHERE run_id = ?", (run_id,)
        ).fetchone()[0]
    finally:
        connection.close()
    if run is None or run["status"] != "prepared" or existing_calls:
        raise ValueError("Only a prepared run with no previous calls can be executed.")
    if json.loads(run["question_ids_json"]) != [question["id"] for question in questions]:
        raise ValueError("The questions or their order differ from the saved run.")
    if hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest() != run["dataset_sha256"]:
        raise ValueError("The dataset file has changed since this run was prepared.")

    models = json.loads(run["models_json"])
    concurrency = run["max_concurrent_requests"]
    expected_calls = len(models) * len(questions)
    semaphore = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    set_run_status(run_id, "running", database_path)
    final_status = "interrupted"
    try:
        async with httpx.AsyncClient(
            transport=transport if transport is not None else httpx.AsyncHTTPTransport(
                retries=0, limits=limits
            ),
            limits=limits,
            follow_redirects=False,
        ) as client:
            for model in models:
                finished = 0
                print(f"\nStarting {model}: {len(questions)} questions, concurrency {concurrency}.", flush=True)

                async def solve_one(row_number: int, question: dict[str, str]) -> None:
                    nonlocal finished
                    async with semaphore:
                        await call_model(
                            client, run_id, question, row_number, model, api_key,
                            database_path=database_path,
                        )
                        finished += 1
                        print(
                            f"{model}: {finished}/{len(questions)} attempts finished "
                            f"({question['id']}).",
                            flush=True,
                        )

                # Exiting the group waits for every task before advancing the model loop.
                async with asyncio.TaskGroup() as group:
                    for row_number, question in enumerate(questions, start=1):
                        group.create_task(solve_one(row_number, question))

        connection = sqlite3.connect(database_path)
        try:
            counts = dict(connection.execute(
                "SELECT status, COUNT(*) FROM calls WHERE run_id = ? GROUP BY status",
                (run_id,),
            ).fetchall())
            format_counts = connection.execute(
                "SELECT SUM(v.format_valid = 1), SUM(v.format_valid = 0), "
                "SUM(v.call_id IS NULL) FROM calls c "
                "LEFT JOIN call_validations v ON v.call_id = c.call_id "
                "WHERE c.run_id = ? AND c.status = 'completed'",
                (run_id,),
            ).fetchone()
        finally:
            connection.close()
        completed = counts.get("completed", 0)
        failed = counts.get("failed", 0)
        if completed + failed != expected_calls:
            raise RuntimeError("The batch ended without all planned call outcomes recorded.")
        final_status = "completed_with_errors" if failed else "completed"
        print(f"\nCalls completed: {completed}; failed: {failed}.", flush=True)
        valid, invalid, unvalidated = format_counts
        print(
            f"Completed generations: format valid: {valid or 0}; "
            f"invalid: {invalid or 0}; unvalidated: {unvalidated or 0}. "
            "Answer grading follows after all model batches finish.",
            flush=True,
        )
    finally:
        # TaskGroup has finished or cancelled its children before this update.
        set_run_status(run_id, final_status, database_path)

    # This is outside the model loop and after every planned final outcome.
    # Exceptions/cancellation skip this step and leave the batch ungraded.
    print_summaries(grade_run(run_id, database_path))
    return final_status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", action="store_true",
        help="Execute the paid API batch; omit this flag to save a prepared run only.",
    )
    parser.add_argument(
        "--questions", type=int, default=QUESTION_COUNT,
        help=f"Number of questions per model, starting from the first record (default: {QUESTION_COUNT}).",
    )
    args = parser.parse_args()
    try:
        questions = load_questions(args.questions)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    api_key = None
    if args.run:
        load_dotenv(PROJECT_ROOT / ".env")
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            parser.error("Set OPENROUTER_API_KEY in the repository's .env file.")

    initialize_database()
    model_configs = default_model_configs()
    run_id = create_run(questions, model_configs=model_configs)
    if not args.run:
        print("Setup only: a prepared run was saved; no API requests.")
    print(f"Database: {DATABASE_PATH}")
    print(f"Run ID: {run_id}")
    print("Run status: prepared.")
    print(f"Questions per model: {len(questions)}")
    print(f"Planned API calls: {len(questions) * len(model_configs)}")
    print(f"Planned concurrency per model: {MAX_CONCURRENT_REQUESTS}")
    print("Finish all questions for each model before starting the next model.")

    print("\nModel order:")
    for position, (model, config) in enumerate(model_configs.items(), start=1):
        body = config["body_settings"]
        provider = ", ".join(body["provider"]["only"])
        print(f"{position}. {model}: {config['experiment']}; provider: {provider}; "
              f"max_tokens: {body['max_tokens']}; contract: {config['response_contract']}.")

    print("\nSelected question IDs in table row order:")
    for row_number, question in enumerate(questions, start=1):
        print(f"{row_number:2}. {question['id']}")

    if not args.run:
        print("\nUse --run to create and execute a new batch.")
        return 0
    try:
        status = asyncio.run(run_batch(run_id, questions, api_key))
    except KeyboardInterrupt:
        print(f"\nRun {run_id} interrupted; saved results remain in the database.")
        print(f"HTML table: {export_table(run_id)}")
        return 130
    print(f"Run status: {status}")
    print(f"HTML table: {export_table(run_id)}")
    return 0 if status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
