-- Additive workflow storage. Legacy batch tables remain unchanged.
CREATE TABLE workflow_runs (
    run_id TEXT PRIMARY KEY NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('verifier_screen', 'sequence_evaluation')),
    created_at_utc TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'prepared' CHECK (status IN
        ('prepared', 'running', 'completed', 'completed_with_errors', 'interrupted', 'budget_stopped')),
    dataset_path TEXT NOT NULL,
    dataset_sha256 TEXT NOT NULL,
    question_ids_json TEXT NOT NULL,
    settings_json TEXT NOT NULL,
    budget_usd REAL CHECK (budget_usd >= 0),
    max_requests INTEGER CHECK (max_requests > 0)
);
CREATE TABLE workflow_configs (
    config_id TEXT PRIMARY KEY NOT NULL,
    run_id TEXT NOT NULL REFERENCES workflow_runs(run_id),
    name TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    snapshot_sha256 TEXT NOT NULL,
    UNIQUE (run_id, name),
    UNIQUE (run_id, config_id)
);
CREATE TABLE workflow_executions (
    execution_id TEXT PRIMARY KEY NOT NULL,
    run_id TEXT NOT NULL,
    config_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    repetition INTEGER NOT NULL CHECK (repetition > 0),
    question_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'prepared' CHECK (status IN
        ('prepared', 'running', 'accepted', 'exhausted', 'failed', 'interrupted', 'budget_stopped')),
    accepted_attempt_id TEXT REFERENCES workflow_attempts(attempt_id),
    terminal_reason TEXT,
    elapsed_seconds REAL CHECK (elapsed_seconds >= 0),
    FOREIGN KEY (run_id, config_id) REFERENCES workflow_configs(run_id, config_id),
    UNIQUE (run_id, config_id, question_id, repetition),
    CHECK ((status = 'accepted' AND accepted_attempt_id IS NOT NULL) OR
           (status != 'accepted' AND accepted_attempt_id IS NULL))
);
CREATE TABLE workflow_attempts (
    attempt_id TEXT PRIMARY KEY NOT NULL,
    execution_id TEXT NOT NULL REFERENCES workflow_executions(execution_id),
    position INTEGER NOT NULL CHECK (position BETWEEN 1 AND 3),
    solver_model TEXT NOT NULL,
    solver_call_id TEXT REFERENCES workflow_calls(call_id),
    historical_solver_call_id TEXT REFERENCES calls(call_id),
    verifier_call_id TEXT REFERENCES workflow_calls(call_id),
    usable INTEGER CHECK (usable IN (0, 1)),
    parsed_fields_json TEXT,
    diagnostics_json TEXT NOT NULL DEFAULT '{}',
    verification_status TEXT NOT NULL DEFAULT 'not_requested' CHECK (verification_status IN
        ('not_requested', 'pending', 'accept', 'reject', 'error', 'invalid')),
    UNIQUE (execution_id, position),
    CHECK (solver_call_id IS NULL OR historical_solver_call_id IS NULL)
);
CREATE TABLE workflow_calls (
    call_id TEXT PRIMARY KEY NOT NULL,
    attempt_id TEXT NOT NULL REFERENCES workflow_attempts(attempt_id),
    role TEXT NOT NULL CHECK (role IN ('solver', 'verifier')),
    requested_model TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    finished_at_utc TEXT,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'interrupted')),
    request_json TEXT NOT NULL,
    response_json TEXT,
    response_body_text TEXT,
    answer_text TEXT,
    returned_model TEXT,
    provider TEXT,
    response_id TEXT,
    http_status INTEGER,
    finish_reason TEXT,
    usage_json TEXT,
    input_tokens INTEGER CHECK (input_tokens >= 0),
    output_tokens INTEGER CHECK (output_tokens >= 0),
    reasoning_tokens INTEGER CHECK (reasoning_tokens >= 0),
    cost_usd REAL CHECK (cost_usd >= 0),
    elapsed_seconds REAL CHECK (elapsed_seconds >= 0),
    error_type TEXT,
    error_message TEXT,
    UNIQUE (attempt_id, role)
);
CREATE TABLE workflow_grades (
    grade_id TEXT PRIMARY KEY NOT NULL,
    execution_id TEXT NOT NULL REFERENCES workflow_executions(execution_id),
    attempt_id TEXT REFERENCES workflow_attempts(attempt_id),
    grader_version TEXT NOT NULL,
    graded_at_utc TEXT NOT NULL,
    dataset_sha256 TEXT NOT NULL,
    option_correct INTEGER CHECK (option_correct IN (0, 1)),
    workflow_score INTEGER CHECK (workflow_score IN (0, 1)),
    reasoning_valid INTEGER CHECK (reasoning_valid IN (0, 1)),
    label_source TEXT NOT NULL,
    reviewer TEXT,
    diagnostics_json TEXT NOT NULL,
    CHECK (attempt_id IS NULL OR workflow_score IS NULL)
);
CREATE UNIQUE INDEX workflow_execution_grade_version
    ON workflow_grades(execution_id, grader_version) WHERE attempt_id IS NULL;
CREATE UNIQUE INDEX workflow_attempt_grade_version
    ON workflow_grades(attempt_id, grader_version) WHERE attempt_id IS NOT NULL;
CREATE INDEX workflow_executions_question ON workflow_executions(run_id, question_id);
