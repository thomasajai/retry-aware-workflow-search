"""Bounded LangGraph solver/verifier loop. CLI preview/demo are entirely offline.

The runner accepts an explicit request sender, provider expectations, and cost
reservations. No HTTP client, API key loading, or paid CLI is supplied here.
Live integration requires a separately prepared and approved pilot.
"""

import argparse
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from itertools import product
import json
from time import perf_counter, sleep
from typing import TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from mathqa_models import MODEL_PROFILES, workflow_model_configs
from mathqa_verifier import build_request, extract_usable, parse_verdict, profile
from mathqa_verifier_preflight import input_token_reservation
import mathqa_workflow_store as store
from mathqa_transport import retry_policy, upstream_429, retry_delay

SELECTED_VERIFIER = "flashlite25__reasoning"


def configuration(sequence, *, temperature=0.2, max_tokens=512, deepseek_provider="deepinfra/fp4", rate_limit_retries=False):
    if type(rate_limit_retries) is not bool:
        raise ValueError("Rate-limit recovery must be explicitly enabled or disabled.")
    if deepseek_provider == "auto" and rate_limit_retries:
        raise ValueError("Automatic provider routing uses no client transport retries.")
    if len(sequence) != 3 or any(alias not in MODEL_PROFILES for alias in sequence):
        raise ValueError("A sequence has exactly three declared solver aliases, with repetitions allowed.")
    models = workflow_model_configs(temperature=temperature, max_tokens=max_tokens, deepseek_provider=deepseek_provider)
    result = {"version": "solver-verifier-config-v1", "solver_sequence": list(sequence),
            "solvers": [deepcopy(models[alias]) for alias in sequence],
            "verifier_alias": SELECTED_VERIFIER, "verifier": profile(SELECTED_VERIFIER),
            "verifier_selection": "provisional user choice after verifier screening",
            "policy": {"max_attempts": 3, "transport_retries": 0, "feedback_to_solver": False,
                "technical_failure": "advance when billing/usage are known; otherwise stop",
                "solver_settings": "proposed loop settings; live pilot pending"}}
    if deepseek_provider != "deepinfra/fp4":
        result.update(version="solver-verifier-config-v2", deepseek_provider=deepseek_provider)
    if rate_limit_retries:
        result.update(version="solver-verifier-config-v3",deepseek_provider=deepseek_provider,transport_policy=retry_policy())
        result["policy"]["transport_retries"] = 2
        result["policy"]["technical_failure"] = "bounded upstream 429 recovery; stop if unresolved or exhausted"
    if deepseek_provider == "auto":
        result["version"] = "solver-verifier-config-v4"
        result["policy"]["technical_failure"] = "stop on gateway failures; no client transport retries"
    return result


def configurations(*, deepseek_provider="deepinfra/fp4", rate_limit_retries=False):
    return [configuration(sequence, deepseek_provider=deepseek_provider,rate_limit_retries=rate_limit_retries) for sequence in product(MODEL_PROFILES, repeat=3)]


def solver_request(solver, question):
    # This allowlist, rather than graph history, is the only solver input.
    return {"model": solver["model"], **deepcopy(solver["body_settings"]), "messages": [{
        "role": "user", "content": solver["prompt_template"].format(
            problem=question["problem"], options=question["options"])}]}


@dataclass(frozen=True)
class Limits:
    budget_usd: float
    max_requests: int

    def __post_init__(self):
        if (isinstance(self.budget_usd, bool) or not isinstance(self.budget_usd, (int, float))
                or not Decimal(str(self.budget_usd)).is_finite() or self.budget_usd <= 0):
            raise ValueError("A finite positive budget is required.")
        if type(self.max_requests) is not int or self.max_requests < 1:
            raise ValueError("A positive request limit is required.")


class WorkflowState(TypedDict, total=False):
    question: dict
    position: int
    attempt_id: str
    call: dict
    usability: dict
    verdict: dict
    halt_status: str | None
    halt_reason: str | None
    technical_errors: int
    outcome: dict


class Runner:
    """One frozen config, durable calls, and a shared run-wide spending gate.

    sender(request) returns (HTTP status, decoded response). It receives neither
    the answer key nor graph history. Tests/demo supply controlled senders.
    reservations(request) quotes a conservative charge, excluding past spend.
    """

    def __init__(self, run_id, config_id, config, *, database_path, sender, reservations, providers, limits, price_limits=None, waiter=None):
        self.run_id, self.config_id = run_id, config_id
        self.config = deepcopy(config)
        expected = configuration(config["solver_sequence"],
            temperature=config["solvers"][0]["body_settings"]["temperature"],
            max_tokens=config["solvers"][0]["body_settings"]["max_tokens"],
            deepseek_provider=config.get("deepseek_provider", "deepinfra/fp4"),rate_limit_retries="transport_policy" in config)
        if self.config != expected:
            raise ValueError("Workflow configuration differs from trusted profile builders.")
        self.db, self.sender, self.reservations = database_path, sender, reservations
        self.providers, self.limits = deepcopy(providers), limits
        self.retry_policy = deepcopy(config.get("transport_policy"))
        self.waiter = waiter or sleep
        self.price_limits = deepcopy(price_limits)
        if config.get("deepseek_provider") == "auto" and self.price_limits is None:
            raise ValueError("Automatic routing requires explicit price ceilings.")
        active_profiles = {p["model"]: p for p in self.config["solvers"] + [self.config["verifier"]]}
        for model, active_profile in active_profiles.items():
            expected_providers = self.providers.get(model)
            routed = model == MODEL_PROFILES["deepseek"].model and config.get("deepseek_provider") == "auto"
            if routed:
                if (not isinstance(expected_providers, list) or not expected_providers
                        or any(not isinstance(p, str) or not p for p in expected_providers)
                        or len(set(expected_providers)) != len(expected_providers)):
                    raise ValueError("Automatic routing needs frozen eligible provider names.")
                if self.price_limits.get(model) != active_profile["body_settings"]["provider"]["max_price"]:
                    raise ValueError("Automatic routing price ceilings differ from the profile.")
            elif not isinstance(expected_providers, str) or not expected_providers:
                raise ValueError("Pinned models require one provider expectation.")
        if self.price_limits is not None:
            for model in {p["model"] for p in self.config["solvers"] + [self.config["verifier"]]}:
                ceiling = self.price_limits.get(model, {})
                if (set(ceiling) != {"prompt", "completion", "request"} or ceiling["request"] != 0
                        or any(isinstance(ceiling[k], bool) or not isinstance(ceiling[k], (int, float))
                               or not Decimal(str(ceiling[k])).is_finite() or ceiling[k] <= 0 for k in ("prompt", "completion"))):
                    raise ValueError("Every pilot model needs finite positive token price ceilings and zero per-request charge.")
        with closing(store.connect(self.db)) as c:
            row = c.execute("SELECT * FROM workflow_configs WHERE config_id=? AND run_id=?", (config_id, run_id)).fetchone()
            run = c.execute("SELECT * FROM workflow_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or json.loads(row["snapshot_json"]) != self.config:
            raise ValueError("Stored configuration does not match the runner.")
        if run["kind"] != "sequence_evaluation" or run["status"] not in ("prepared", "running"):
            raise ValueError("Runner requires an unfinished sequence evaluation.")
        if run["budget_usd"] != limits.budget_usd or run["max_requests"] != limits.max_requests:
            raise ValueError("Limits must match the recorded run budget/request cap.")

    def priced_request(self, request):
        if self.price_limits is not None:
            request["provider"]["max_price"] = deepcopy(self.price_limits[request["model"]])
        return request

    def provider_matches(self, model, provider):
        expected = self.providers[model]
        return isinstance(provider, str) and (provider in expected if isinstance(expected, list) else provider == expected)

    def gate(self, request, *, ignore_unstarted_call=None):
        reserve = Decimal(str(self.reservations(deepcopy(request))))
        if not reserve.is_finite() or reserve <= 0:
            raise ValueError("A finite positive per-call reservation is required.")
        if request["model"] not in self.providers:
            raise ValueError("Missing provider expectation.")
        with closing(store.connect(self.db)) as c:
            running = c.execute("SELECT w.call_id FROM workflow_calls w JOIN workflow_attempts a USING(attempt_id) "
                "JOIN workflow_executions e USING(execution_id) WHERE e.run_id=? AND w.status='running'",(self.run_id,)).fetchall()
        if any(r["call_id"]!=ignore_unstarted_call for r in running):
            return reserve,"unreconciled_call"
        rows = store.billing_rows(self.run_id,database_path=self.db,ignore_unstarted_call=ignore_unstarted_call)
        if any(r["status"] == "running" or (r["cost_usd"] is None and
                (self.retry_policy is None or r["held_cost_usd"] is None)) for r in rows):
            return reserve, "unreconciled_call"
        if len(rows) >= self.limits.max_requests:
            return reserve, "request_limit"
        spent = Decimal(store.billing_totals(rows)["accounted_exposure_usd"])
        return reserve, "spending_limit" if spent + reserve > Decimal(str(self.limits.budget_usd)) else None

    def perform(self, attempt_id, role, request, reservation):
        if self.retry_policy is not None:
            return self.perform_with_retries(attempt_id,role,request,reservation)
        call_id = store.create_call(attempt_id, role, request["model"], request,
            cost_reservation_usd=float(reservation), database_path=self.db)
        started, payload, http_status = perf_counter(), None, None
        status, error, unexpected = "completed", None, None
        try:
            response = self.sender(deepcopy(request))
            http_status, payload = response[:2]
            if not isinstance(payload, dict):
                payload = None
                status, error = "failed", "InvalidResponse"
            elif http_status != 200 or "error" in payload:
                status, error = "failed", "ProviderError"
            elif payload.get("model") != request["model"] or not self.provider_matches(request["model"], payload.get("provider")):
                status, error = "failed", "ProviderOrModelMismatch"
            else:
                choices = payload.get("choices")
                if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict) or choices[0].get("finish_reason") != "stop":
                    status, error = "failed", "IncompleteGeneration"
        except KeyboardInterrupt:
            status, error = "interrupted", "KeyboardInterrupt"
        except httpx.HTTPError:
            status, error = "failed", "TransportError"
        except Exception as exception:
            status, error, unexpected = "failed", type(exception).__name__, exception
        store.finish_call(call_id, status=status, elapsed_seconds=perf_counter()-started, payload=payload,
            http_status=http_status, error_type=error, database_path=self.db)
        if unexpected is not None:
            raise unexpected
        with closing(store.connect(self.db)) as c:
            row = dict(c.execute("SELECT * FROM workflow_calls WHERE call_id=?", (call_id,)).fetchone())
            spent = c.execute("SELECT SUM(w.cost_usd) FROM workflow_calls w JOIN workflow_attempts a USING(attempt_id) "
                "JOIN workflow_executions e USING(execution_id) WHERE e.run_id=?", (self.run_id,)).fetchone()[0]
        halt, reason = None, None
        if status == "interrupted":
            halt, reason = "interrupted", "cancelled_billing_may_be_unknown"
        elif row["cost_usd"] is None:
            halt, reason = "budget_stopped", "unknown_cost"
        elif row["returned_model"] != request["model"] or not self.provider_matches(request["model"], row["provider"]):
            halt, reason = "budget_stopped", "provider_or_model_mismatch"
        elif row["input_tokens"] is None or row["output_tokens"] is None:
            halt, reason = "budget_stopped", "unknown_token_usage"
        elif row["reasoning_tokens"] is not None and row["reasoning_tokens"] > row["output_tokens"]:
            halt, reason = "budget_stopped", "inconsistent_reasoning_usage"
        elif (isinstance(self.providers[request["model"]], list) and
              Decimal(str(row["cost_usd"])) > (Decimal(str(self.price_limits[request["model"]]["prompt"]))*row["input_tokens"]
              + Decimal(str(self.price_limits[request["model"]]["completion"]))*row["output_tokens"])/1_000_000 + Decimal("0.000000000001")):
            halt, reason = "budget_stopped", "price_ceiling_exceeded"
        elif (row["input_tokens"] > input_token_reservation(request) or row["output_tokens"] > request["max_tokens"]
              or Decimal(str(row["cost_usd"])) > reservation or Decimal(str(spent)) > Decimal(str(self.limits.budget_usd))):
            halt, reason = "budget_stopped", "reservation_exceeded"
        elif self.config.get("deepseek_provider") == "auto" and status != "completed":
            halt, reason = "budget_stopped", "gateway_failure"
        return row, halt, reason

    def retry_decision(self, physical, request, headers):
        policy = self.retry_policy
        if not upstream_429(physical["http_status"],json.loads(physical["response_json"]),self.providers[request["model"]],request["model"]):
            return None,"ineligible_rate_limit"
        rows = store.billing_rows(self.run_id,database_path=self.db)
        retried = [r for r in rows if r["retry_wait_seconds"] is not None]
        if physical["ordinal"]>policy["max_retries_per_call"] or len(retried)>=policy["max_retry_requests"]:
            return None,"rate_limit_retry_limit"
        try:
            delay = retry_delay(json.loads(physical["response_json"]),headers,physical["ordinal"])
        except ValueError:
            return None,"rate_limit_cooldown_limit_or_invalid"
        if sum(r["retry_wait_seconds"] for r in retried)+delay>policy["max_total_wait_seconds"]:
            return None,"rate_limit_total_cooldown_limit"
        totals = store.billing_totals(rows)
        hold = Decimal(str(physical["cost_reservation_usd"])) if physical["cost_usd"] is None else Decimal(0)
        if hold and (sum(r["held_cost_usd"] is not None for r in rows)>=policy["max_unknown_429_calls"]
                or Decimal(totals["held_unknown_cost_usd"])+hold>Decimal(policy["max_unknown_reservation_usd"])):
            return None,"unknown_429_allowance_limit"
        if len(rows)>=self.limits.max_requests:
            return None,"request_limit"
        next_reserve = Decimal(str(self.reservations(deepcopy(request))))
        if not next_reserve.is_finite() or next_reserve<=0:
            raise ValueError("Invalid retry reservation.")
        if Decimal(totals["accounted_exposure_usd"])+hold+next_reserve>Decimal(str(self.limits.budget_usd)):
            return None,"spending_limit"
        if any(r["status"]=="running" or (r["cost_usd"] is None and r["held_cost_usd"] is None
                and r["call_id"]!=physical["call_id"]) for r in rows):
            return None,"unreconciled_call"
        return delay,None

    def perform_with_retries(self, attempt_id, role, request, reservation):
        logical = store.create_call(attempt_id,role,request["model"],request,cost_reservation_usd=float(reservation),database_path=self.db)
        whole_started = perf_counter()
        halt = reason = None
        last_payload = None
        last_http = None
        status,error,unexpected = "failed","TransportError",None
        for ordinal in range(1,4):
            if ordinal>1:
                reservation,stop = self.gate(request,ignore_unstarted_call=logical)
                if stop:
                    halt,reason = "budget_stopped",stop
                    break
            physical = store.create_transport_call(logical,request,float(reservation),database_path=self.db)
            started = perf_counter()
            status,error,headers = "completed",None,{}
            last_payload,last_http = None,None
            try:
                response = self.sender(deepcopy(request))
                last_http,last_payload = response[:2]
                headers = response[2] if len(response)==3 else {}
                if not isinstance(headers,dict):
                    headers = {}
                    raise ValueError("Invalid response headers.")
                if not isinstance(last_payload,dict):
                    last_payload = None
                    status,error = "failed","InvalidResponse"
                elif last_http!=200 or "error" in last_payload:
                    status,error = "failed","ProviderError"
                elif last_payload.get("model")!=request["model"] or last_payload.get("provider")!=self.providers[request["model"]]:
                    status,error = "failed","ProviderOrModelMismatch"
                else:
                    choices = last_payload.get("choices")
                    if not isinstance(choices,list) or not choices or not isinstance(choices[0],dict) or choices[0].get("finish_reason")!="stop":
                        status,error = "failed","IncompleteGeneration"
            except KeyboardInterrupt:
                status,error = "interrupted","KeyboardInterrupt"
            except httpx.HTTPError:
                status,error = "failed","TransportError"
            except Exception as exception:
                status,error,unexpected = "failed",type(exception).__name__,exception
            store.finish_transport_call(physical,headers=headers,status=status,elapsed_seconds=perf_counter()-started,
                payload=last_payload,http_status=last_http,error_type=error,database_path=self.db)
            with closing(store.connect(self.db)) as c:
                row = dict(c.execute("SELECT * FROM workflow_transport_calls WHERE call_id=?",(physical,)).fetchone())
            if status=="interrupted":
                halt,reason = "interrupted","cancelled_billing_may_be_unknown"
                break
            if unexpected:
                break
            if upstream_429(last_http,last_payload,self.providers[request["model"]],request["model"]):
                delay,stop = self.retry_decision(row,request,headers)
                if stop:
                    halt,reason = "budget_stopped",stop
                    break
                store.record_transport_retry(physical,delay,expected_provider=self.providers[request["model"]],database_path=self.db)
                try:
                    self.waiter(delay)
                except KeyboardInterrupt:
                    status,error,halt,reason = "interrupted","KeyboardInterrupt","interrupted","cancelled_during_cooldown"
                    break
                except Exception as exception:
                    status,error,unexpected = "failed",type(exception).__name__,exception
                    break
                continue
            totals = store.billing_totals(store.billing_rows(self.run_id,database_path=self.db))
            if row["cost_usd"] is None:
                halt,reason = "budget_stopped","unknown_cost"
            elif row["returned_model"]!=request["model"] or row["provider"]!=self.providers[request["model"]]:
                halt,reason = "budget_stopped","provider_or_model_mismatch"
            elif row["input_tokens"] is None or row["output_tokens"] is None:
                halt,reason = "budget_stopped","unknown_token_usage"
            elif row["reasoning_tokens"] is not None and row["reasoning_tokens"]>row["output_tokens"]:
                halt,reason = "budget_stopped","inconsistent_reasoning_usage"
            elif (row["input_tokens"]>input_token_reservation(request) or row["output_tokens"]>request["max_tokens"]
                    or Decimal(str(row["cost_usd"]))>reservation or Decimal(totals["accounted_exposure_usd"])>Decimal(str(self.limits.budget_usd))):
                halt,reason = "budget_stopped","reservation_exceeded"
            break
        store.finish_call(logical,status=status,elapsed_seconds=perf_counter()-whole_started,payload=last_payload,
            http_status=last_http,error_type=error,database_path=self.db)
        if unexpected is not None:
            raise unexpected
        with closing(store.connect(self.db)) as c:
            final = dict(c.execute("SELECT * FROM workflow_calls WHERE call_id=?",(logical,)).fetchone())
        return final,halt,reason

    def execute(self, question, *, repetition=1):
        with closing(store.connect(self.db)) as c:
            run = c.execute("SELECT status FROM workflow_runs WHERE run_id=?", (self.run_id,)).fetchone()
        if run[0] not in ("prepared", "running"):
            raise ValueError("A terminal run cannot schedule executions.")
        with closing(store.connect(self.db)) as c, c:
            c.execute("UPDATE workflow_runs SET status='running',started_at_utc=COALESCE(started_at_utc,?) WHERE run_id=?",
                      (store.now(), self.run_id))
        runtime_question = {k: question[k] for k in ("id", "problem", "options")}
        execution_id = store.create_execution(self.run_id, self.config_id, runtime_question,
            repetition=repetition, database_path=self.db)
        started = perf_counter()

        def solve(state):
            solver = self.config["solvers"][state["position"]-1]
            request = self.priced_request(solver_request(solver, state["question"]))
            reserve, stop = self.gate(request)
            if stop:
                return {"halt_status": "budget_stopped", "halt_reason": stop}
            attempt = store.create_attempt(execution_id, state["position"], solver["model"], database_path=self.db)
            call, halt, reason = self.perform(attempt, "solver", request, reserve)
            return {"attempt_id": attempt, "call": call, "halt_status": halt, "halt_reason": reason,
                    "technical_errors": state["technical_errors"] + int(call["status"] != "completed")}

        def usable(state):
            solver = self.config["solvers"][state["position"]-1]
            call = state["call"]
            result = extract_usable(call["answer_text"], solver["response_contract"],
                status=call["status"], finish_reason=call["finish_reason"])
            store.record_usability(state["attempt_id"], result, database_path=self.db)
            return {"usability": result}

        def verify(state):
            request = self.priced_request(build_request(self.config["verifier_alias"], state["question"], state["usability"]["fields"]))
            reserve, stop = self.gate(request)
            if stop:
                return {"halt_status": "budget_stopped", "halt_reason": stop}
            call, halt, reason = self.perform(state["attempt_id"], "verifier", request, reserve)
            verdict = parse_verdict(call["answer_text"], status=call["status"], finish_reason=call["finish_reason"])
            store.record_verification(state["attempt_id"], verdict["status"], database_path=self.db)
            return {"verdict": verdict, "halt_status": halt, "halt_reason": reason,
                    "technical_errors": state["technical_errors"] + int(verdict["status"] in ("error", "invalid"))}

        def advance(state):
            return {"position": state["position"]+1, "attempt_id": None, "call": None,
                    "usability": None, "verdict": None}

        def finish(state):
            accepted = not state.get("halt_status") and (state.get("verdict") or {}).get("status") == "accept"
            status = state.get("halt_status") or ("accepted" if accepted else "failed" if state["technical_errors"] else "exhausted")
            reason = state.get("halt_reason") or ("verifier_accept" if accepted else
                "attempt_limit_with_technical_errors" if state["technical_errors"] else "attempt_limit_rejected_or_unusable")
            store.finish_execution(execution_id, status, reason, perf_counter()-started,
                accepted_attempt_id=state["attempt_id"] if accepted else None, database_path=self.db)
            return {"outcome": {"execution_id": execution_id, "status": status, "terminal_reason": reason,
                "accepted_fields": state["usability"]["fields"] if accepted else None}}

        builder = StateGraph(WorkflowState)
        for name, node in (("solver", solve), ("usability", usable), ("verifier", verify), ("advance", advance), ("finish", finish)):
            builder.add_node(name, node)
        builder.add_edge(START, "solver")
        builder.add_conditional_edges("solver", lambda s: "finish" if s.get("halt_status") and s.get("call") is None else "usability")
        builder.add_conditional_edges("usability", lambda s: "finish" if s.get("halt_status") else
            "verifier" if s["usability"]["usable"] else "advance" if s["position"] < 3 else "finish")
        builder.add_conditional_edges("verifier", lambda s: "finish" if s.get("halt_status") or s["verdict"]["status"] == "accept"
            else "advance" if s["position"] < 3 else "finish")
        builder.add_edge("advance", "solver")
        builder.add_edge("finish", END)
        try:
            result = builder.compile().invoke({"question": runtime_question, "position": 1, "technical_errors": 0},
                                               config={"recursion_limit": 24})
        except BaseException:
            try:
                store.finish_execution(execution_id, "interrupted", "unexpected_failure_review_calls", perf_counter()-started,
                                       database_path=self.db)
            finally:
                with closing(store.connect(self.db)) as c, c:
                    c.execute("UPDATE workflow_runs SET status='interrupted',finished_at_utc=?,stop_reason=? WHERE run_id=?",
                              (store.now(), "unexpected_failure_review_calls", self.run_id))
            raise
        if result["outcome"]["status"] in ("interrupted", "budget_stopped"):
            with closing(store.connect(self.db)) as c, c:
                c.execute("UPDATE workflow_runs SET status=?,finished_at_utc=?,stop_reason=? WHERE run_id=?",
                    (result["outcome"]["status"], store.now(), result["outcome"]["terminal_reason"], self.run_id))
        return result["outcome"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Print all 27 configurations without calls or database writes.")
    args = parser.parse_args()
    if not args.preview:
        parser.error("Choose --preview. No paid execution command exists yet.")
    print(json.dumps({"mode": "offline_preview", "configurations": configurations(), "count": 27,
                      "max_calls_per_question_per_config": 6, "new_generation_requests": 0}, indent=2))


if __name__ == "__main__":
    main()
