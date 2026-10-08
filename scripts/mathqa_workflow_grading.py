"""Independent offline option grades for finished solver/verifier executions."""

from contextlib import closing
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from mathqa_batch import PROJECT_ROOT
import mathqa_workflow_store as store

GRADER_VERSION = "workflow-option-v1"


def grade_execution(execution_id, *, database_path):
    with closing(store.connect(database_path)) as c:
        execution = c.execute("SELECT e.*,r.kind,r.dataset_path,r.dataset_sha256 FROM workflow_executions e "
            "JOIN workflow_runs r USING(run_id) WHERE execution_id=?", (execution_id,)).fetchone()
    if execution is None or execution["kind"] != "sequence_evaluation":
        raise ValueError("Workflow grading requires a sequence execution, not a verifier screen.")
    dataset_path = Path(execution["dataset_path"])
    if not dataset_path.is_absolute():
        dataset_path = PROJECT_ROOT / dataset_path
    raw = dataset_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != execution["dataset_sha256"]:
        raise ValueError("Dataset checksum changed; grading refused.")
    records = json.loads(raw)
    by_id = {r["id"]: r for r in records}
    if len(by_id) != len(records):
        raise ValueError("Duplicate dataset question IDs.")
    record = by_id.get(execution["question_id"])
    if record is None or record.get("correct") not in list("abcde"):
        raise ValueError("Missing independent answer key.")
    runtime = {"id": record["id"], "problem": record["Problem"], "options": record["options"]}
    if json.loads(execution["question_json"]) != runtime:
        raise ValueError("Stored runtime question differs from the grading dataset.")
    with closing(store.connect(database_path)) as c, c:
        # Freeze all related grades atomically; a duplicate version rolls back.
        execution = c.execute("SELECT * FROM workflow_executions WHERE execution_id=?", (execution_id,)).fetchone()
        if execution["status"] in ("prepared", "running", "budget_stopped", "interrupted"):
            return {"execution_id": execution_id, "status": execution["status"], "workflow_score": None,
                    "note": "Incomplete execution excluded from accuracy; no final grade stored."}
        attempts = c.execute("SELECT * FROM workflow_attempts WHERE execution_id=? ORDER BY position", (execution_id,)).fetchall()
        if not attempts:
            raise ValueError("Finished execution has no solver attempts.")
        if c.execute("SELECT COUNT(*) FROM workflow_calls w JOIN workflow_attempts a USING(attempt_id) "
                     "WHERE a.execution_id=? AND w.status='running'", (execution_id,)).fetchone()[0]:
            raise ValueError("Execution still has a running call.")
        options = {}
        for attempt in attempts:
            fields = json.loads(attempt["parsed_fields_json"]) if attempt["parsed_fields_json"] else None
            option = fields.get("option") if isinstance(fields, dict) and attempt["usable"] == 1 else None
            options[attempt["attempt_id"]] = None if option not in list("abcde") else option == record["correct"]
            _insert(c, execution_id, execution_checksum=hashlib.sha256(raw).hexdigest(),
                attempt_id=attempt["attempt_id"], option_correct=options[attempt["attempt_id"]],
                diagnostics={"option": option, "verification_status": attempt["verification_status"],
                             "reasoning_validity": "unknown; option key is not a reasoning review"})
        accepted_correct = options.get(execution["accepted_attempt_id"])
        score = int(execution["status"] == "accepted" and accepted_correct is True)
        _insert(c, execution_id, execution_checksum=hashlib.sha256(raw).hexdigest(),
            option_correct=accepted_correct, workflow_score=score,
            diagnostics={"status": execution["status"], "terminal_reason": execution["terminal_reason"],
                         "accepted_attempt_id": execution["accepted_attempt_id"]})
    return {"execution_id": execution_id, "status": execution["status"], "workflow_score": score,
            "accepted_option_correct": accepted_correct, "attempt_count": len(attempts)}


def _insert(connection, execution_id, *, execution_checksum, attempt_id=None,
            option_correct=None, workflow_score=None, diagnostics):
    connection.execute("INSERT INTO workflow_grades VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
        str(uuid4()), execution_id, attempt_id, GRADER_VERSION, store.now(), execution_checksum,
        option_correct, workflow_score, None, "independent dataset option key", None, store.encode(diagnostics)))
