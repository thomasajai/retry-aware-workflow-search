"""Opt-in, bounded upstream 429 recovery; no HTTP requests in this module."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime


def retry_policy():
    return {"version":"upstream-429-v1", "max_retries_per_call":2, "max_retry_requests":2,
            "max_unknown_429_calls":2, "max_unknown_reservation_usd":"0.002",
            "backoff_seconds":[30,60], "max_wait_seconds":60, "max_total_wait_seconds":120,
            "billing":"Retain unknown actual costs; hold full call reservations against the cap.",
            "retry_scope":"Only empty upstream_provider_shared_pool 429s from the pinned provider."}


def upstream_429(status, payload, provider, model):
    if status != 429 or not isinstance(payload,dict):
        return False
    error = payload.get("error")
    if not isinstance(error,dict) or error.get("code") != 429:
        return False
    metadata = error.get("metadata")
    if (not isinstance(metadata,dict) or metadata.get("limit_source") != "upstream_provider_shared_pool"
            or metadata.get("provider_name") != provider):
        return False
    if payload.get("choices") or payload.get("id") or payload.get("model",model) != model or payload.get("provider",provider) != provider:
        return False
    # Retry only responses without generation evidence; malformed/nonzero usage
    # is not grounds to treat a request as safely recoverable.
    usage = payload.get("usage",{})
    if not isinstance(usage,dict) or set(usage)-{"cost","prompt_tokens","completion_tokens"}:
        return False
    return all(not isinstance(v,bool) and isinstance(v,(int,float)) and v==0 for v in usage.values())


def retry_delay(payload, headers, ordinal, *, now=None):
    """Honor the longest advertised delay; never shorten a provider cooldown."""
    policy = retry_policy()
    metadata = payload["error"]["metadata"]
    values = []
    for source in (headers,metadata.get("headers",{})):
        if not isinstance(source,dict):
            raise ValueError("Invalid retry headers.")
        values.extend(v for k,v in source.items() if k.lower()=="retry-after")
    if "retry_after_seconds" in metadata:
        values.append(metadata["retry_after_seconds"])
    delays = [policy["backoff_seconds"][ordinal-1]]
    instant = now or datetime.now(timezone.utc)
    for value in values:
        if isinstance(value,bool) or not isinstance(value,(str,int,float)):
            raise ValueError("Invalid Retry-After.")
        try:
            seconds = Decimal(str(value))
        except InvalidOperation:
            try:
                date = parsedate_to_datetime(value)
                if date.tzinfo is None:
                    raise ValueError("Retry date lacks timezone.")
                seconds = Decimal(str(max(0,(date-instant).total_seconds())))
            except (TypeError,ValueError,OverflowError) as error:
                raise ValueError("Invalid Retry-After.") from error
        if not seconds.is_finite() or seconds < 0:
            raise ValueError("Invalid Retry-After.")
        delays.append(float(seconds))
    delay = max(delays)
    if delay > policy["max_wait_seconds"]:
        raise ValueError("Provider cooldown exceeds the approved wait limit.")
    return delay


def decode_response(response, reject_nonfinite):
    import json
    import mathqa_workflow_store as store
    try:
        payload = json.loads(response.text,parse_constant=reject_nonfinite)
    except ValueError:
        payload = {"error":{"type":"InvalidJSON","raw_response":store.clean(response.text)}}
    headers = {"retry-after":response.headers["retry-after"]} if "retry-after" in response.headers else {}
    return response.status_code,payload,headers
