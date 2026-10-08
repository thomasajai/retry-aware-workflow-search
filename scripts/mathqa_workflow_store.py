"""Offline workflow storage and additive migrations; no model requests."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
from uuid import uuid4

from mathqa_batch import DATABASE_PATH, initialize_database as initialize_legacy_database

MIGRATIONS = Path(__file__).parent / "migrations"
SECRET_KEYS = {"authorization", "proxyauthorization", "apikey", "openrouterapikey", "accesstoken"}


def now():
    return datetime.now(timezone.utc).isoformat()


def clean(value):
    """Remove credential fields/known key patterns, including in error strings."""
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()
                if re.sub(r"[^a-z]", "", k.lower()) not in SECRET_KEYS}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"sk-or-v1-[A-Za-z0-9_-]+", "[REDACTED]", value)
    return value


def encode(value):
    return json.dumps(clean(value), ensure_ascii=False, sort_keys=True, allow_nan=False)


def connect(path):
    c = sqlite3.connect(Path(path), timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def _statements(sql):
    buffer = ""
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            yield buffer
            buffer = ""
    if buffer.strip():
        raise ValueError("Migration ends with an incomplete SQL statement.")


def migrate(database_path=DATABASE_PATH, *, migration_dir=MIGRATIONS):
    """Back up existing databases before upgrades; checksum and apply atomically."""
    path = Path(database_path).resolve()
    files = sorted(Path(migration_dir).glob("[0-9][0-9][0-9]_*.sql"))
    if not files:
        raise ValueError("No workflow migrations found.")
    versions = [f.name.split("_", 1)[0] for f in files]
    if len(set(versions)) != len(versions):
        raise ValueError("Duplicate migration version.")
    sources = {f.name: (f.read_text(encoding="utf-8"), hashlib.sha256(f.read_bytes()).hexdigest()) for f in files}
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists() and path.stat().st_size > 0
    backup_path = None
    with closing(connect(path)) as c:
        tables = {row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        applied = {row["name"]: row["sha256"] for row in c.execute("SELECT * FROM schema_migrations ORDER BY name")} if "schema_migrations" in tables else {}
        for name, checksum in applied.items():
            if name not in sources or checksum != sources[name][1]:
                raise ValueError(f"Unknown or changed applied migration: {name}.")
        names = [f.name for f in files]
        if list(applied) != names[:len(applied)]:
            raise ValueError("Applied migrations are not a contiguous prefix.")
        pending = [f for f in files if f.name not in applied]
        if not pending:
            return {"applied": [], "backup_path": None}
        if existed:
            backup_dir = path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            backup_path = backup_dir / f"{path.stem}_{stamp}_{uuid4().hex[:8]}.sqlite3"
            with closing(sqlite3.connect(backup_path)) as backup:
                c.backup(backup)
    # Fresh databases need the legacy calls table for saved-answer foreign keys.
    if "calls" not in tables:
        initialize_legacy_database(path)
    with closing(connect(path)) as c:
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("CREATE TABLE IF NOT EXISTS schema_migrations ("
                      "name TEXT PRIMARY KEY NOT NULL, sha256 TEXT NOT NULL, applied_at_utc TEXT NOT NULL)")
            for f in pending:
                sql, checksum = sources[f.name]
                for statement in _statements(sql):
                    c.execute(statement)
                c.execute("INSERT INTO schema_migrations VALUES (?, ?, ?)", (f.name, checksum, now()))
            c.commit()
        except BaseException:
            c.rollback()
            raise
    return {"applied": [f.name for f in pending], "backup_path": str(backup_path) if backup_path else None}


def create_run(kind, dataset_path, dataset_sha256, question_ids, settings, *,
               database_path=DATABASE_PATH, budget_usd=None, max_requests=None, plan_sha256=None):
    if not question_ids or len(set(question_ids)) != len(question_ids):
        raise ValueError("Question IDs must be nonempty and unique.")
    run_id = str(uuid4())
    with closing(connect(database_path)) as c, c:
        c.execute("INSERT INTO workflow_runs (run_id,kind,created_at_utc,dataset_path,dataset_sha256,"
                  "question_ids_json,settings_json,budget_usd,max_requests,plan_sha256) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (run_id, kind, now(), str(dataset_path), dataset_sha256, encode(question_ids), encode(settings), budget_usd, max_requests, plan_sha256))
    return run_id


def create_config(run_id, name, snapshot, *, database_path=DATABASE_PATH):
    config_id = str(uuid4())
    serialized = encode(snapshot)
    with closing(connect(database_path)) as c, c:
        c.execute("INSERT INTO workflow_configs VALUES (?,?,?,?,?)", (
            config_id, run_id, name, serialized, hashlib.sha256(serialized.encode()).hexdigest()))
    return config_id


def create_execution(run_id, config_id, question, *, repetition=1, database_path=DATABASE_PATH):
    # Build a runtime snapshot explicitly; never persist the key/rationale here.
    runtime = {"id": question["id"], "problem": question["problem"], "options": question["options"]}
    execution_id = str(uuid4())
    with closing(connect(database_path)) as c, c:
        run = c.execute("SELECT question_ids_json FROM workflow_runs WHERE run_id=?", (run_id,)).fetchone()
        if run is None or question["id"] not in json.loads(run[0]):
            raise ValueError("Question is outside the run's selected questions.")
        c.execute("INSERT INTO workflow_executions (execution_id,run_id,config_id,question_id,repetition,question_json) "
                  "VALUES (?,?,?,?,?,?)", (execution_id, run_id, config_id, question["id"], repetition, encode(runtime)))
    return execution_id


def create_attempt(execution_id, position, solver_model, *, historical_solver_call_id=None, offline_source=None, database_path=DATABASE_PATH):
    attempt_id = str(uuid4())
    with closing(connect(database_path)) as c, c:
        execution = c.execute("SELECT * FROM workflow_executions WHERE execution_id=?", (execution_id,)).fetchone()
        if execution is None or execution["status"] not in ("prepared", "running"):
            raise ValueError("Execution is missing or already terminal.")
        previous = c.execute("SELECT * FROM workflow_attempts WHERE execution_id=? ORDER BY position", (execution_id,)).fetchall()
        if position != len(previous) + 1:
            raise ValueError("Attempt positions must be contiguous, starting at one.")
        if previous and (previous[-1]["usable"] is None or previous[-1]["verification_status"] in ("pending", "accept")
                         or (previous[-1]["usable"] and previous[-1]["verification_status"] == "not_requested")):
            raise ValueError("Previous attempt must be resolved without acceptance before retrying.")
        if historical_solver_call_id:
            source = c.execute("SELECT question_id,requested_model FROM calls WHERE call_id=?", (historical_solver_call_id,)).fetchone()
            if source is None or source[0] != execution["question_id"] or source[1] != solver_model:
                raise ValueError("Historical solver call does not match the execution question/model.")
        c.execute("INSERT INTO workflow_attempts (attempt_id,execution_id,position,solver_model,historical_solver_call_id,offline_source_json) "
                  "VALUES (?,?,?,?,?,?)", (attempt_id, execution_id, position, solver_model, historical_solver_call_id,
                  encode(offline_source) if offline_source is not None else None))
        c.execute("UPDATE workflow_executions SET status='running' WHERE execution_id=?", (execution_id,))
    return attempt_id


def record_usability(attempt_id, result, *, database_path=DATABASE_PATH):
    with closing(connect(database_path)) as c, c:
        attempt = c.execute("SELECT * FROM workflow_attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
        if attempt is None:
            raise ValueError("Missing attempt.")
        if attempt["offline_source_json"] is not None:
            source = json.loads(attempt["offline_source_json"])
        else:
            table, call_id = ("calls", attempt["historical_solver_call_id"]) if attempt["historical_solver_call_id"] else ("workflow_calls", attempt["solver_call_id"])
            source = c.execute(f"SELECT status,finish_reason FROM {table} WHERE call_id=?", (call_id,)).fetchone()
        if source is None or source["status"] == "running":
            raise ValueError("Usability evidence needs a finished solver source.")
        if result["usable"] and (source["status"] != "completed" or source["finish_reason"] in ("length", "error")):
            raise ValueError("A failed/truncated solver source cannot be usable.")
        cursor = c.execute("UPDATE workflow_attempts SET usable=?,parsed_fields_json=?,diagnostics_json=? "
                           "WHERE attempt_id=? AND usable IS NULL", (int(result["usable"]), encode(result.get("fields")),
                           encode(result.get("diagnostics", {})), attempt_id))
        if cursor.rowcount != 1:
            raise ValueError("Attempt is missing or already has usability evidence.")


def create_call(attempt_id, role, requested_model, request, *, cost_reservation_usd=None, database_path=DATABASE_PATH):
    """Record initiation only. This helper does not execute HTTP requests."""
    if role not in ("solver", "verifier"):
        raise ValueError("Unknown call role.")
    call_id = str(uuid4())
    with closing(connect(database_path)) as c, c:
        attempt = c.execute("SELECT * FROM workflow_attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
        if attempt is None:
            raise ValueError("Missing attempt.")
        execution = c.execute("SELECT status FROM workflow_executions WHERE execution_id=?", (attempt["execution_id"],)).fetchone()
        if execution[0] not in ("prepared", "running"):
            raise ValueError("Cannot initiate calls for a terminal execution.")
        if role == "solver" and (attempt["historical_solver_call_id"] or attempt["offline_source_json"] or requested_model != attempt["solver_model"]):
            raise ValueError("New solver call conflicts with historical source or selected model.")
        if role == "verifier" and attempt["usable"] != 1:
            raise ValueError("Only usable answers can be verified.")
        if request.get("model", requested_model) != requested_model:
            raise ValueError("Request model differs from the recorded model.")
        c.execute("INSERT INTO workflow_calls (call_id,attempt_id,role,requested_model,started_at_utc,request_json,cost_reservation_usd) "
                  "VALUES (?,?,?,?,?,?,?)", (call_id, attempt_id, role, requested_model, now(), encode(request), _measurement(cost_reservation_usd)))
        column = "solver_call_id" if role == "solver" else "verifier_call_id"
        c.execute(f"UPDATE workflow_attempts SET {column}=? WHERE attempt_id=?", (call_id, attempt_id))
        if role == "verifier":
            c.execute("UPDATE workflow_attempts SET verification_status='pending' WHERE attempt_id=?", (attempt_id,))
    return call_id


def _measurement(value, *, integer=False):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("Measurements must be finite, nonnegative numbers or None.")
    if integer and not isinstance(value, int):
        raise ValueError("Token measurements must be integers.")
    return value


def _reported_measurement(value, *, integer=False):
    # Preserve malformed provider usage in the raw payload, but never turn it
    # into a trusted measurement or lose a finished response over it.
    try:
        return _measurement(value, integer=integer)
    except ValueError:
        return None


def _reported_text(value):
    return clean(value) if isinstance(value, str) else None


def _finish_response(call_id, *, table, status, elapsed_seconds, payload=None, raw_response=None,
                http_status=None, error_type=None, error_message=None, database_path=DATABASE_PATH):
    if table not in ("workflow_calls", "workflow_transport_calls"):
        raise ValueError("Invalid response table.")
    if status not in ("completed", "failed", "interrupted"):
        raise ValueError("Invalid final call status.")
    p = payload if isinstance(payload, dict) else {}
    usage = p.get("usage") if isinstance(p.get("usage"), dict) else {}
    choices = p.get("choices")
    choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else {}
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    details = usage.get("completion_tokens_details") if isinstance(usage.get("completion_tokens_details"), dict) else {}
    with closing(connect(database_path)) as c, c:
        cursor = c.execute(f"UPDATE {table} SET status=?,finished_at_utc=?,elapsed_seconds=?,response_json=?,"
                           "response_body_text=?,answer_text=?,returned_model=?,provider=?,response_id=?,http_status=?,"
                           "finish_reason=?,usage_json=?,input_tokens=?,output_tokens=?,reasoning_tokens=?,cost_usd=?,"
                           "error_type=?,error_message=? WHERE call_id=? AND status='running'", (
            status, now(), _measurement(elapsed_seconds), encode(payload) if payload is not None else None,
            clean(raw_response), clean(message.get("content")) if isinstance(message.get("content"), str) else None,
            _reported_text(p.get("model")), _reported_text(p.get("provider")), _reported_text(p.get("id")), http_status, _reported_text(choice.get("finish_reason")), encode(usage),
            _reported_measurement(usage.get("prompt_tokens"), integer=True), _reported_measurement(usage.get("completion_tokens"), integer=True),
            _reported_measurement(details.get("reasoning_tokens"), integer=True), _reported_measurement(usage.get("cost")),
            error_type, clean(error_message), call_id))
        if cursor.rowcount != 1:
            raise ValueError("Call is missing or already finished.")


def finish_call(call_id, **kwargs):
    _finish_response(call_id,table="workflow_calls",**kwargs)


def create_transport_call(logical_call_id, request, reservation, *, database_path=DATABASE_PATH):
    with closing(connect(database_path)) as c,c:
        parent = c.execute("SELECT * FROM workflow_calls WHERE call_id=?",(logical_call_id,)).fetchone()
        if parent is None or parent["status"] != "running" or parent["request_json"] != encode(request):
            raise ValueError("Transport request must match its running logical call.")
        previous = c.execute("SELECT * FROM workflow_transport_calls WHERE logical_call_id=? ORDER BY ordinal",(logical_call_id,)).fetchall()
        if previous and (previous[-1]["status"] != "failed" or previous[-1]["retry_wait_seconds"] is None):
            raise ValueError("Retry needs finished, authorized rate-limit evidence.")
        call_id = str(uuid4())
        c.execute("INSERT INTO workflow_transport_calls (call_id,logical_call_id,ordinal,started_at_utc,request_json,cost_reservation_usd) "
                  "VALUES (?,?,?,?,?,?)",(call_id,logical_call_id,len(previous)+1,now(),encode(request),_measurement(reservation)))
        return call_id


def finish_transport_call(call_id, *, headers, database_path=DATABASE_PATH, **kwargs):
    _finish_response(call_id,table="workflow_transport_calls",database_path=database_path,**kwargs)
    with closing(connect(database_path)) as c,c:
        c.execute("UPDATE workflow_transport_calls SET response_headers_json=? WHERE call_id=?",
                  (encode({k:v for k,v in headers.items() if k.lower()=="retry-after"}),call_id))


def record_transport_retry(call_id, delay, *, expected_provider, database_path=DATABASE_PATH):
    from mathqa_transport import retry_policy, upstream_429
    policy = retry_policy()
    with closing(connect(database_path)) as c,c:
        row = c.execute("SELECT t.*,w.requested_model FROM workflow_transport_calls t JOIN workflow_calls w ON w.call_id=t.logical_call_id "
                        "WHERE t.call_id=?",(call_id,)).fetchone()
        if (row is None or row["status"]!="failed" or row["retry_wait_seconds"] is not None
                or row["ordinal"]>policy["max_retries_per_call"]
                or not upstream_429(row["http_status"],json.loads(row["response_json"]),expected_provider,row["requested_model"])):
            raise ValueError("Retry needs eligible, finished upstream 429 evidence.")
        wait = _measurement(delay)
        if wait is None or wait > policy["max_wait_seconds"]:
            raise ValueError("Invalid bounded cooldown.")
        c.execute("UPDATE workflow_transport_calls SET retry_wait_seconds=?,held_cost_usd=? WHERE call_id=?",
                  (wait,row["cost_reservation_usd"] if row["cost_usd"] is None else None,call_id))


def billing_rows(run_id, *, database_path=DATABASE_PATH, ignore_unstarted_call=None):
    """Physical calls when present; historical logical calls counted once."""
    with closing(connect(database_path)) as c:
        has_view = c.execute("SELECT 1 FROM sqlite_master WHERE name='workflow_billable_calls'").fetchone()
        table = "workflow_billable_calls" if has_view else "workflow_calls"
        rows = [dict(r) for r in c.execute(f"SELECT w.* FROM {table} w JOIN workflow_attempts a USING(attempt_id) "
                    "JOIN workflow_executions e USING(execution_id) WHERE e.run_id=?",(run_id,))]
    for row in rows:
        row.setdefault("logical_call_id",row["call_id"])
        row.setdefault("held_cost_usd",None)
        row.setdefault("retry_wait_seconds",None)
    return [r for r in rows if not (r["call_id"]==ignore_unstarted_call and r["call_id"]==r["logical_call_id"])]


def billing_totals(rows):
    from decimal import Decimal
    known = sum((Decimal(str(r["cost_usd"])) for r in rows if r["cost_usd"] is not None),Decimal(0))
    held = sum((Decimal(str(r["held_cost_usd"])) for r in rows if r["cost_usd"] is None and r["held_cost_usd"] is not None),Decimal(0))
    return {"requests":len(rows),"known_cost_usd":str(known),"unknown_cost_calls":sum(r["cost_usd"] is None for r in rows),
            "held_unknown_cost_usd":str(held),"accounted_exposure_usd":str(known+held)}


def record_verification(attempt_id, verdict, *, database_path=DATABASE_PATH):
    if verdict not in ("accept", "reject", "error", "invalid"):
        raise ValueError("Invalid verification state.")
    with closing(connect(database_path)) as c, c:
        row = c.execute("SELECT w.* FROM workflow_calls w JOIN workflow_attempts a ON a.verifier_call_id=w.call_id "
                        "WHERE a.attempt_id=? AND a.verification_status='pending'", (attempt_id,)).fetchone()
        if row is None or row["status"] == "running":
            raise ValueError("Verdict needs a finished verifier call and a pending attempt.")
        if verdict in ("accept", "reject") and (row["status"] != "completed" or row["finish_reason"] in ("length", "error")):
            raise ValueError("A failed/truncated verifier cannot supply a valid verdict.")
        from mathqa_verifier import parse_verdict
        actual = parse_verdict(row["answer_text"], status=row["status"], finish_reason=row["finish_reason"])
        if actual["status"] != verdict:
            raise ValueError("Recorded verdict does not match the saved verifier response.")
        c.execute("UPDATE workflow_attempts SET verification_status=? WHERE attempt_id=?", (verdict, attempt_id))


def finish_execution(execution_id, status, reason, elapsed_seconds, *, accepted_attempt_id=None, database_path=DATABASE_PATH):
    if status not in ("accepted", "exhausted", "failed", "interrupted", "budget_stopped"):
        raise ValueError("Invalid terminal execution status.")
    with closing(connect(database_path)) as c, c:
        attempts = c.execute("SELECT * FROM workflow_attempts WHERE execution_id=? ORDER BY position", (execution_id,)).fetchall()
        if status == "accepted":
            if not any(a["attempt_id"] == accepted_attempt_id and a["verification_status"] == "accept" for a in attempts):
                raise ValueError("Accepted attempt must belong to this execution and have an acceptance verdict.")
        elif accepted_attempt_id is not None:
            raise ValueError("Only accepted executions reference an accepted attempt.")
        if status == "exhausted" and (len(attempts) != 3 or any(a["usable"] is None or a["verification_status"] in ("accept", "pending")
                or (a["usable"] and a["verification_status"] == "not_requested") for a in attempts)):
            raise ValueError("Exhaustion requires three resolved, non-accepted solver slots.")
        if c.execute("SELECT COUNT(*) FROM workflow_calls w JOIN workflow_attempts a ON a.attempt_id=w.attempt_id "
                     "WHERE a.execution_id=? AND w.status='running'", (execution_id,)).fetchone()[0]:
            raise ValueError("Finalize running calls before their execution.")
        cursor = c.execute("UPDATE workflow_executions SET status=?,accepted_attempt_id=?,terminal_reason=?,elapsed_seconds=? "
                           "WHERE execution_id=? AND status IN ('prepared','running')", (
                           status, accepted_attempt_id, clean(reason), _measurement(elapsed_seconds), execution_id))
        if cursor.rowcount != 1:
            raise ValueError("Execution is missing or already terminal.")


def record_grade(execution_id, grader_version, dataset_sha256, label_source, *, attempt_id=None,
                 option_correct=None, reasoning_valid=None, workflow_score=None, reviewer=None,
                 diagnostics=None, database_path=DATABASE_PATH):
    if not label_source or (reasoning_valid is not None and not reviewer):
        raise ValueError("Independent labels need provenance; reasoning labels need a reviewer.")
    with closing(connect(database_path)) as c, c:
        execution = c.execute("SELECT e.*,r.dataset_sha256 FROM workflow_executions e JOIN workflow_runs r USING(run_id) "
                              "WHERE execution_id=?", (execution_id,)).fetchone()
        if execution is None or dataset_sha256 != execution["dataset_sha256"]:
            raise ValueError("Grade dataset checksum does not match the execution.")
        if attempt_id and not c.execute("SELECT 1 FROM workflow_attempts WHERE attempt_id=? AND execution_id=?",
                                      (attempt_id, execution_id)).fetchone():
            raise ValueError("Grade attempt belongs to another execution.")
        if attempt_id is None and workflow_score is not None:
            if execution["status"] in ("prepared", "running", "interrupted", "budget_stopped"):
                raise ValueError("Unfinished executions cannot receive a workflow score.")
            expected = int(execution["status"] == "accepted" and option_correct == 1)
            if workflow_score != expected:
                raise ValueError("Workflow score must follow acceptance and independent option correctness.")
        c.execute("INSERT INTO workflow_grades VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
            str(uuid4()), execution_id, attempt_id, grader_version, now(), dataset_sha256,
            option_correct, workflow_score, reasoning_valid, label_source, reviewer, encode(diagnostics or {})))


def cost_summary(run_id, *, database_path=DATABASE_PATH):
    rows = billing_rows(run_id,database_path=database_path)
    result = []
    for role in sorted({r["role"] for r in rows}):
        totals = billing_totals([r for r in rows if r["role"]==role])
        result.append({"role":role,"requests":totals["requests"],"known_cost_usd":float(totals["known_cost_usd"]),
                       "unknown_cost_calls":totals["unknown_cost_calls"]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument("--migrate", action="store_true", help="Apply offline migrations, backing up an existing database first.")
    args = parser.parse_args()
    if not args.migrate:
        parser.error("Choose --migrate; this command never makes model requests.")
    try:
        print(json.dumps(migrate(args.database), indent=2))
    except (OSError, ValueError, sqlite3.Error) as e:
        parser.exit(1, f"Migration failed: {e}\n")


if __name__ == "__main__":
    main()
