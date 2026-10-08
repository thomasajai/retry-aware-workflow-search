"""Prepare a frozen small loop pilot offline, or execute with --run and numeric caps."""

import argparse
from collections import Counter, defaultdict
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import random
import sqlite3
import subprocess

import httpx
from dotenv import load_dotenv

from mathqa_batch import DATASET_PATH, DATABASE_PATH, OPENROUTER_URL, PROJECT_ROOT
from mathqa_verifier import build_request
from mathqa_verifier_preflight import request_cost
from mathqa_transport import decode_response
import mathqa_workflow as workflow
from mathqa_workflow_grading import grade_execution, GRADER_VERSION
import mathqa_workflow_store as store

QUESTION_IDS = ("mathqa_test_0002", "mathqa_test_0047")
SEQUENCES = (("qwen25", "qwen3", "deepseek"), ("qwen3", "deepseek", "qwen25"), ("deepseek", "qwen25", "qwen3"))
SOURCE_FILES = ("mathqa_batch.py", "mathqa_response.py", "mathqa_models.py", "mathqa_verifier.py", "mathqa_verifier_preflight.py", "mathqa_workflow.py", "mathqa_transport.py",
                "mathqa_workflow_grading.py", "mathqa_workflow_store.py", "mathqa_workflow_pilot.py")


def digest(value):
    return hashlib.sha256(store.encode(value).encode("utf-8")).hexdigest()


def _reject_nonfinite(value):
    raise ValueError("Nonfinite JSON constant: " + value)


def endpoint(metadata, model, settings):
    data = metadata["models"][model]["data"]
    if "only" not in settings["provider"]:
        return routed_endpoint(data, model, settings)
    matches = [e for e in data["endpoints"] if e.get("tag") == settings["provider"]["only"][0] and e.get("status") == 0]
    if data["id"] != model or len(matches) != 1:
        raise ValueError("Expected one active pinned endpoint for " + model)
    selected = matches[0]
    validate_endpoint(selected, settings)
    return selected


def validate_endpoint(selected, settings):
    required = set(settings) - {"provider", "stream"}
    if not required <= set(selected["supported_parameters"]):
        raise ValueError("Provider lacks requested controls.")
    if selected.get("max_completion_tokens") is not None and selected["max_completion_tokens"] < settings["max_tokens"]:
        raise ValueError("Output cap exceeds endpoint capability.")
    for kind in ("prompt", "completion", "internal_reasoning"):
        if kind not in selected["pricing"] and kind == "internal_reasoning":
            continue
        rate = Decimal(selected["pricing"][kind])
        if not rate.is_finite() or rate <= 0:
            raise ValueError("Token prices must be finite and positive.")
    if Decimal(str(selected["pricing"].get("request", 0))) != 0:
        raise ValueError("Per-request charges are unsupported.")


def routed_endpoint(data, model, settings):
    """Freeze compatible identities and reserve at ceilings, not cheapest prices.

    The returned pricing object is a budget envelope, not a real endpoint.
    OpenRouter can try providers internally; our request cap counts gateway HTTP
    requests and never claims to bound or observe its individual upstream tries.
    """
    from mathqa_models import MODEL_PROFILES, WORKFLOW_DEEPSEEK_PRICE_LIMITS
    policy = {"allow_fallbacks": True, "require_parameters": True,
              "max_price": deepcopy(WORKFLOW_DEEPSEEK_PRICE_LIMITS)}
    if model != MODEL_PROFILES["deepseek"].model or data["id"] != model or settings["provider"] != policy:
        raise ValueError("Undeclared automatic routing policy/model.")
    ceilings = policy["max_price"]
    eligible = []
    for candidate in data["endpoints"]:
        # Availability is transient. Recognize compatible metadata endpoints
        # that become available later without changing the outgoing routing.
        if type(candidate.get("status")) is not int:
            continue
        try:
            validate_endpoint(candidate, settings)
            if (not isinstance(candidate.get("provider_name"), str) or not candidate["provider_name"]
                    or not isinstance(candidate.get("tag"), str) or not candidate["tag"]):
                continue
            if any(Decimal(candidate["pricing"][k])*1_000_000 > Decimal(str(ceilings[k]))
                   for k in ("prompt", "completion")):
                continue
            if Decimal(candidate["pricing"].get("internal_reasoning", candidate["pricing"]["completion"]))*1_000_000 > Decimal(str(ceilings["completion"])):
                continue
        except (ValueError, KeyError, TypeError, ArithmeticError):
            continue
        eligible.append(deepcopy(candidate))
    active = [e for e in eligible if e["status"] == 0]
    if not active:
        raise ValueError("No active providers satisfy controls and price ceilings.")
    eligible.sort(key=lambda e: e["tag"])
    return {"provider_name": "OpenRouter automatic routing", "tag": "auto", "status": 0,
            "provider_names": sorted({e["provider_name"] for e in eligible}),
            "active_provider_names": sorted({e["provider_name"] for e in active}),
            "eligible_endpoints": eligible, "routing_policy": policy,
            "pricing": {"prompt": str(Decimal(str(ceilings["prompt"]))/1_000_000),
                        "completion": str(Decimal(str(ceilings["completion"]))/1_000_000), "request": "0"}}


def prepare_plan(metadata, *, dataset_path=DATASET_PATH, created_at=None):
    raw = Path(dataset_path).read_bytes()
    records = json.loads(raw)
    by_id = {r["id"]: r for r in records}
    if len(by_id) != len(records):
        raise ValueError("Dataset IDs must be unique.")
    questions = []
    for qid in QUESTION_IDS:
        record = by_id[qid]
        if record.get("correct") not in list("abcde"):
            raise ValueError("Pilot questions require independent answer keys.")
        questions.append({"id": qid, "problem": record["Problem"], "options": record["options"]})
    configs = {"-".join(s): workflow.configuration(s) for s in SEQUENCES}
    sample = next(iter(configs.values()))
    endpoints, prices = {}, {}
    for p in sample["solvers"] + [sample["verifier"]]:
        model, settings = p["model"], p.get("body_settings", p.get("settings"))
        endpoints[model] = deepcopy(endpoint(metadata, model, settings))
        prices[model] = {kind: float(Decimal(endpoints[model]["pricing"][kind])*1_000_000) for kind in ("prompt", "completion")}
        prices[model]["request"] = 0
    catalog = metadata["catalog"]["models"][sample["verifier"]["model"]]
    if catalog["id"] != sample["verifier"]["model"] or "reasoning" not in catalog["supported_parameters"] or not isinstance(catalog["reasoning"], dict):
        raise ValueError("Verifier reasoning capabilities are missing.")
    def priced(request):
        request["provider"]["max_price"] = deepcopy(prices[request["model"]])
        return request
    costs = []
    for p in sample["solvers"] + [sample["verifier"]]:
        is_verifier = "settings" in p
        model, selected = p["model"], endpoints[p["model"]]
        normal = [priced(build_request(workflow.SELECTED_VERIFIER, q, {"calculation": "x"*160, "option": "a", "value": "x"*120}))
                  if is_verifier else priced(workflow.solver_request(p, q)) for q in questions]
        # Planning assumption: two slots reached per execution, balanced rotations.
        multiplier, max_multiplier = (6, 9) if is_verifier else (2, 3)
        output = 512 if is_verifier else 96
        inputs = [(sum(len(m["content"]) for m in r["messages"])+2)//3+96 for r in normal]
        expected = sum((request_cost(r, selected, output_tokens=output, input_tokens=n) for r,n in zip(normal,inputs)), Decimal(0))*multiplier
        stressed = [priced(build_request(workflow.SELECTED_VERIFIER, q, {"calculation": "x"*8192, "option": "a", "value": "x"*120}))
                    for q in questions] if is_verifier else normal
        reservation = sum((request_cost(r,selected) for r in stressed),Decimal(0))*max_multiplier
        input_cost = Decimal(sum(inputs)*multiplier)*Decimal(selected["pricing"]["prompt"])
        costs.append({"role": "verifier" if is_verifier else "solver", "model": model, "provider": selected["provider_name"],
            "provider_tag": selected["tag"], "expected_calls": len(normal)*multiplier, "maximum_calls": len(normal)*max_multiplier,
            "estimated_input_tokens": sum(inputs)*multiplier, "estimated_output_tokens_including_reasoning": output*len(normal)*multiplier,
            "input_usd_per_million": prices[model]["prompt"], "output_usd_per_million": prices[model]["completion"],
            "estimated_input_cost_usd": str(input_cost), "estimated_output_cost_usd": str(expected-input_cost),
            "estimated_cost_usd": str(expected), "conservative_reservation_usd": str(reservation)})
    rng = random.Random(17)
    schedule = []
    for question in questions:
        names = list(configs)
        rng.shuffle(names)
        schedule.extend({"question_id": question["id"], "configuration": name, "repetition": 1} for name in names)
    plan = {"version": "workflow-pilot-plan-v1", "created_at_utc": created_at or store.now(),
        "dataset": {"path": str(Path(dataset_path).resolve()), "sha256": hashlib.sha256(raw).hexdigest()},
        "questions": questions, "configurations": configs, "schedule": schedule, "scheduling_seed": 17,
        "metadata": deepcopy(metadata), "endpoints": endpoints, "price_limits": prices,
        "code_sha256": {f: hashlib.sha256((PROJECT_ROOT/"scripts"/f).read_bytes()).hexdigest() for f in SOURCE_FILES},
        "execution_policy": {"concurrency": 1, "transport_retries": 0, "timeout_inactivity_seconds": 60,
            "maximum_attempts": 3, "maximum_requests": 36, "maximum_budget_usd": 0.04, "metadata_max_age_hours": 24, "held_out": False},
        "cost_preview": {"breakdown": costs, "expected_calls": 24, "maximum_calls": 36,
            "estimated_total_usd": str(sum((Decimal(r["estimated_cost_usd"]) for r in costs),Decimal(0))),
            "conservative_reservation_total_usd": str(sum((Decimal(r["conservative_reservation_usd"]) for r in costs),Decimal(0))),
            "assumptions": "Two slots per execution; solver output 96 and verifier output 512 including reasoning. No cache discount. Stress reservations use an 8192-character calculation, full UTF-8 request plus framing, and full output caps; this is not a tokenizer/billing guarantee. Actual verifier input is reserved before each call."}}
    plan["sha256"] = digest(plan)
    return plan


def validate_plan(plan, *, check_age=True):
    if plan.get("version") != "workflow-pilot-plan-v1" or plan.get("sha256") != digest({k:v for k,v in plan.items() if k!="sha256"}):
        raise ValueError("Pilot plan checksum/version failed.")
    if check_age:
        age = (datetime.now(timezone.utc)-datetime.fromisoformat(plan["metadata"]["fetched_at_utc"])).total_seconds()
        if age < -300 or age > 24*3600:
            raise ValueError("Refresh free endpoint metadata and prepare a new proposal.")
    rebuilt = prepare_plan(plan["metadata"], dataset_path=plan["dataset"]["path"], created_at=plan["created_at_utc"])
    if rebuilt != plan:
        raise ValueError("Dataset, code, profiles, controls, or schedule changed; prepare a new pilot plan.")


def summary(run_id, *, database_path):
    with closing(store.connect(database_path)) as c:
        run = dict(c.execute("SELECT * FROM workflow_runs WHERE run_id=?", (run_id,)).fetchone())
        plan = json.loads(run["settings_json"])["plan"]
        executions = [dict(r) for r in c.execute("SELECT e.*,f.name configuration,g.workflow_score,g.option_correct FROM workflow_executions e "
            "JOIN workflow_configs f USING(config_id) LEFT JOIN workflow_grades g ON g.execution_id=e.execution_id "
            "AND g.attempt_id IS NULL AND g.grader_version=? WHERE e.run_id=? ORDER BY e.rowid", (GRADER_VERSION,run_id))]
        attempts = [dict(r) for r in c.execute("SELECT a.* FROM workflow_attempts a JOIN workflow_executions e USING(execution_id) WHERE e.run_id=?",(run_id,))]
    calls = store.billing_rows(run_id,database_path=database_path)
    totals = store.billing_totals(calls)
    per_model = []
    groups = defaultdict(list)
    for row in calls:
        groups[(row["role"],row["requested_model"])].append(row)
    for (role,model),rows in groups.items():
        per_model.append({"role":role,"model":model,"requests":len(rows),
            "known_cost_usd":str(sum((Decimal(str(r["cost_usd"])) for r in rows if r["cost_usd"] is not None),Decimal(0))),
            "unknown_cost_calls":sum(r["cost_usd"] is None for r in rows),
            "input_tokens":sum(r["input_tokens"] or 0 for r in rows),"output_tokens_including_reasoning":sum(r["output_tokens"] or 0 for r in rows),
            "reasoning_tokens_subset":sum(r["reasoning_tokens"] or 0 for r in rows)})
    scored = [r for r in executions if r["workflow_score"] is not None]
    result = {"run_id":run_id,"status":run["status"],"stop_reason":run["stop_reason"],"plan_sha256":plan["sha256"],
        "held_unknown_cost_usd":totals["held_unknown_cost_usd"],"accounted_exposure_usd":totals["accounted_exposure_usd"],
        "transport_retry_requests":len(calls)-len({r["logical_call_id"] for r in calls}),
        "planned_executions":len(plan["schedule"]),"reached_executions":len(executions),"scored_executions":len(scored),
        "score_total":sum(r["workflow_score"] for r in scored),"accuracy_completed_only":sum(r["workflow_score"] for r in scored)/len(scored) if scored else None,
        "complete_coverage":len(scored)==len(plan["schedule"]),"executions":executions,"costs":per_model,
        "new_requests":len(calls),"known_new_cost_usd":str(sum((Decimal(str(r["cost_usd"])) for r in calls if r["cost_usd"] is not None),Decimal(0))),
        "unknown_cost_calls":sum(r["cost_usd"] is None for r in calls),"unusable_attempts":sum(a["usable"]==0 for a in attempts),
        "verification_statuses":dict(Counter(a["verification_status"] for a in attempts)),
        "attempts_per_execution":dict(Counter(a["execution_id"] for a in attempts)),
        "wall_elapsed_seconds":(datetime.fromisoformat(run["finished_at_utc"])-datetime.fromisoformat(run["started_at_utc"])).total_seconds(),
        "note":"Small development integration pilot, not a 27-sequence accuracy comparison. Reasoning validity remains a separate review measure."}
    if any("provider_names" in e for e in plan["endpoints"].values()):
        provider_groups = defaultdict(list)
        for row in calls:
            provider_groups[(row["role"],row["requested_model"],row["provider"])].append(row)
        result["provider_costs"] = [{"role":role,"model":model,"provider":provider,"requests":len(rows),
            "known_cost_usd":str(sum((Decimal(str(r["cost_usd"])) for r in rows if r["cost_usd"] is not None),Decimal(0))),
            "unknown_cost_calls":sum(r["cost_usd"] is None for r in rows)}
            for (role,model,provider),rows in provider_groups.items()]
        result["request_count_scope"] = "Client HTTP requests to OpenRouter; individual internal provider tries are unobserved."
    return result


def run_pilot(plan, *, database_path, budget_usd, max_requests, api_key, client):
    limits = workflow.Limits(budget_usd,max_requests)
    if max_requests > plan["execution_policy"]["maximum_requests"]:
        raise ValueError("Request cap exceeds the frozen pilot scope.")
    if budget_usd > plan["execution_policy"]["maximum_budget_usd"]:
        raise ValueError("Spending cap exceeds the frozen pilot scope.")
    if not api_key:
        raise ValueError("An API key is required for explicit paid execution.")
    validate_plan(plan)
    store.migrate(database_path)
    revision = subprocess.run(["git","rev-parse","HEAD"],cwd=PROJECT_ROOT,text=True,capture_output=True,check=True).stdout.strip()
    dirty = bool(subprocess.run(["git","status","--porcelain"],cwd=PROJECT_ROOT,text=True,capture_output=True,check=True).stdout.strip())
    try:
        run = store.create_run("sequence_evaluation",plan["dataset"]["path"],plan["dataset"]["sha256"],
            [q["id"] for q in plan["questions"]],{"plan":plan,"code_revision":revision,"code_dirty":dirty},
            database_path=database_path,budget_usd=budget_usd,max_requests=max_requests,plan_sha256=plan["sha256"])
    except sqlite3.IntegrityError as error:
        raise ValueError("This plan already has a run; no automatic retry/rerun/resume.") from error
    with closing(store.connect(database_path)) as c,c:
        c.execute("UPDATE workflow_runs SET status='running',started_at_utc=? WHERE run_id=?",(store.now(),run))
    providers = {m:e["provider_name"] for m,e in plan["endpoints"].items()}
    def sender(request):
        response = client.post(OPENROUTER_URL,json=request,headers={"Authorization":"Bearer "+api_key},timeout=60)
        return decode_response(response,_reject_nonfinite)
    config_ids = {name:store.create_config(run,name,config,database_path=database_path) for name,config in plan["configurations"].items()}
    questions = {q["id"]:q for q in plan["questions"]}
    try:
        for item in plan["schedule"]:
            config = plan["configurations"][item["configuration"]]
            runner = workflow.Runner(run,config_ids[item["configuration"]],config,database_path=database_path,
                sender=sender,reservations=lambda r:request_cost(r,plan["endpoints"][r["model"]]),providers=providers,
                limits=limits,price_limits=plan["price_limits"])
            outcome = runner.execute(questions[item["question_id"]],repetition=item["repetition"])
            if outcome["status"] in ("interrupted","budget_stopped"):
                break
            grade_execution(outcome["execution_id"],database_path=database_path)
        else:
            with closing(store.connect(database_path)) as c,c:
                errors = c.execute("SELECT COUNT(*) FROM workflow_attempts a JOIN workflow_executions e USING(execution_id) "
                    "WHERE e.run_id=? AND (a.verification_status IN ('invalid','error') OR EXISTS "
                    "(SELECT 1 FROM workflow_calls w WHERE w.attempt_id=a.attempt_id AND w.status!='completed'))",(run,)).fetchone()[0]
                c.execute("UPDATE workflow_runs SET status=?,finished_at_utc=? WHERE run_id=?",
                          ("completed_with_errors" if errors else "completed",store.now(),run))
    except BaseException:
        with closing(store.connect(database_path)) as c,c:
            c.execute("UPDATE workflow_runs SET status='interrupted',finished_at_utc=?,stop_reason=? WHERE run_id=?",
                      (store.now(),"unexpected_failure_review_calls",run))
        raise
    return summary(run,database_path=database_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--metadata",type=Path)
    parser.add_argument("--database",type=Path,default=DATABASE_PATH)
    parser.add_argument("--run",action="store_true",help="Consumes credits; requires advance disclosure and numeric limits.")
    parser.add_argument("--budget-usd",type=float)
    parser.add_argument("--max-requests",type=int)
    parser.add_argument("--report",type=Path)
    args = parser.parse_args()
    try:
        protected = {args.database.resolve(),DATASET_PATH.resolve()}
        if args.metadata:
            protected.add(args.metadata.resolve())
        if args.plan.resolve() in protected or args.report and args.report.resolve() in protected|{args.plan.resolve()}:
            raise ValueError("Output cannot overwrite an input or database.")
        if not args.run:
            if not args.metadata:
                parser.error("Offline preparation requires --metadata.")
            if args.plan.exists():
                raise ValueError("Plan exists; choose a new filename.")
            plan = prepare_plan(json.loads(args.metadata.read_text(encoding="utf-8")))
            validate_plan(plan)
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            args.plan.write_text(json.dumps(plan,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            print(json.dumps({"mode":"offline_pilot_preparation","sha256":plan["sha256"],"cost_preview":plan["cost_preview"],"generation_requests":0},indent=2))
        else:
            if args.budget_usd is None or args.max_requests is None or not args.report:
                parser.error("--run requires --budget-usd, --max-requests, and --report.")
            if args.report.exists():
                raise ValueError("Report exists; choose a new filename.")
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            validate_plan(plan)
            load_dotenv(PROJECT_ROOT/".env")
            with httpx.Client(follow_redirects=False) as client:
                result = run_pilot(plan,database_path=args.database,budget_usd=args.budget_usd,max_requests=args.max_requests,
                                   api_key=os.getenv("OPENROUTER_API_KEY"),client=client)
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
            print(json.dumps(result,indent=2))
    except (ValueError,KeyError,OSError,sqlite3.Error) as error:
        parser.exit(1,f"Pilot stopped: {error}\n")


if __name__ == "__main__":
    main()
