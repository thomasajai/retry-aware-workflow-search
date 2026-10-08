-- Each physical HTTP request is separate from its solver/verifier slot.
-- Existing workflow_calls remain the final response used for parsing/grading.
CREATE TABLE workflow_transport_calls (
    call_id TEXT PRIMARY KEY NOT NULL,
    logical_call_id TEXT NOT NULL REFERENCES workflow_calls(call_id),
    ordinal INTEGER NOT NULL CHECK (ordinal BETWEEN 1 AND 3),
    started_at_utc TEXT NOT NULL,
    finished_at_utc TEXT,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','completed','failed','interrupted')),
    request_json TEXT NOT NULL,
    response_json TEXT,
    response_body_text TEXT,
    response_headers_json TEXT NOT NULL DEFAULT '{}',
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
    cost_reservation_usd REAL NOT NULL CHECK (cost_reservation_usd > 0),
    held_cost_usd REAL CHECK (held_cost_usd > 0),
    retry_wait_seconds REAL CHECK (retry_wait_seconds BETWEEN 0 AND 60),
    UNIQUE (logical_call_id, ordinal),
    CHECK (held_cost_usd IS NULL OR (status='failed' AND http_status=429 AND cost_usd IS NULL
        AND held_cost_usd=cost_reservation_usd AND retry_wait_seconds IS NOT NULL))
);
CREATE VIEW workflow_billable_calls AS
SELECT t.call_id,t.logical_call_id,w.attempt_id,w.role,w.requested_model,
       t.started_at_utc,t.finished_at_utc,t.status,t.request_json,t.response_json,t.response_body_text,
       t.answer_text,t.returned_model,t.provider,t.response_id,t.http_status,t.finish_reason,t.usage_json,
       t.input_tokens,t.output_tokens,t.reasoning_tokens,t.cost_usd,t.elapsed_seconds,t.error_type,t.error_message,
       t.cost_reservation_usd,t.held_cost_usd,t.retry_wait_seconds
FROM workflow_transport_calls t JOIN workflow_calls w ON w.call_id=t.logical_call_id
UNION ALL
SELECT w.call_id,w.call_id,w.attempt_id,w.role,w.requested_model,
       w.started_at_utc,w.finished_at_utc,w.status,w.request_json,w.response_json,w.response_body_text,
       w.answer_text,w.returned_model,w.provider,w.response_id,w.http_status,w.finish_reason,w.usage_json,
       w.input_tokens,w.output_tokens,w.reasoning_tokens,w.cost_usd,w.elapsed_seconds,w.error_type,w.error_message,
       w.cost_reservation_usd,NULL,NULL
FROM workflow_calls w WHERE NOT EXISTS
    (SELECT 1 FROM workflow_transport_calls t WHERE t.logical_call_id=w.call_id);
