-- Offline proposals are sources, not paid solver calls.
ALTER TABLE workflow_attempts ADD COLUMN offline_source_json TEXT;
ALTER TABLE workflow_calls ADD COLUMN cost_reservation_usd REAL CHECK (cost_reservation_usd >= 0);
ALTER TABLE workflow_runs ADD COLUMN started_at_utc TEXT;
ALTER TABLE workflow_runs ADD COLUMN finished_at_utc TEXT;
ALTER TABLE workflow_runs ADD COLUMN stop_reason TEXT;
ALTER TABLE workflow_runs ADD COLUMN plan_sha256 TEXT;
CREATE UNIQUE INDEX workflow_run_plan ON workflow_runs(plan_sha256) WHERE plan_sha256 IS NOT NULL;
CREATE TRIGGER workflow_source_insert BEFORE INSERT ON workflow_attempts
WHEN (NEW.solver_call_id IS NOT NULL) + (NEW.historical_solver_call_id IS NOT NULL) + (NEW.offline_source_json IS NOT NULL) > 1
BEGIN
    SELECT RAISE(ABORT, 'A solver slot has only one source');
END;
CREATE TRIGGER workflow_source_update BEFORE UPDATE ON workflow_attempts
WHEN (NEW.solver_call_id IS NOT NULL) + (NEW.historical_solver_call_id IS NOT NULL) + (NEW.offline_source_json IS NOT NULL) > 1
BEGIN
    SELECT RAISE(ABORT, 'A solver slot has only one source');
END;
