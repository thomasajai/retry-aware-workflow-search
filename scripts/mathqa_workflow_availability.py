"""Prepare a six-execution availability check offline; paid execution is explicit."""
import argparse
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
import os
from pathlib import Path
import sqlite3

import httpx
from dotenv import load_dotenv

from mathqa_batch import DATASET_PATH, DATABASE_PATH, PROJECT_ROOT
from mathqa_verifier import build_request
from mathqa_verifier_preflight import request_cost
import mathqa_workflow as workflow
import mathqa_workflow_evaluation as evaluation
import mathqa_workflow_pilot as pilot
import mathqa_workflow_store as store
from mathqa_transport import retry_policy

SOURCE_FILES = evaluation.SOURCE_FILES+("mathqa_workflow_availability.py",)


def prepare_plan(metadata, exposure, *, dataset_path=DATASET_PATH, created_at=None):
    raw = Path(dataset_path).read_bytes()
    records = json.loads(raw)
    if len(records)!=200 or len({r["id"] for r in records})!=200:
        raise ValueError("Availability check needs the fixed 200 unique questions.")
    exposed = set(exposure["legacy_question_ids"])|set(exposure["workflow_question_ids"])
    if exposed & {r["id"] for r in records[100:]}:
        raise ValueError("Reserved held-out exposure changed.")
    chosen = [next(r for r in records if r["id"]==qid) for qid in pilot.QUESTION_IDS]
    if any(r.get("correct") not in list("abcde") for r in chosen):
        raise ValueError("Questions need independent option keys.")
    questions = [{"id":r["id"],"problem":r["Problem"],"options":r["options"]} for r in chosen]
    config = workflow.configuration(["deepseek"]*3,deepseek_provider="venice",rate_limit_retries=True)
    endpoints,ceilings = {},{}
    for p in [config["solvers"][0],config["verifier"]]:
        model,settings = p["model"],p.get("body_settings",p.get("settings"))
        endpoints[model] = deepcopy(pilot.endpoint(metadata,model,settings))
        ceilings[model] = {k:float(Decimal(endpoints[model]["pricing"][k])*1_000_000) for k in ("prompt","completion")}
        ceilings[model]["request"] = 0
    capability = metadata["catalog"]["models"][config["verifier"]["model"]]
    if "reasoning" not in capability["supported_parameters"] or not isinstance(capability["reasoning"],dict):
        raise ValueError("Verifier reasoning capability missing.")
    def priced(request):
        request["provider"]["max_price"] = deepcopy(ceilings[request["model"]])
        return request
    costs,max_reservations = [],[]
    for role,p in [("solver",config["solvers"][0]),("verifier",config["verifier"])]:
        model,ep = p["model"],endpoints[p["model"]]
        requests = [priced(workflow.solver_request(p,q)) if role=="solver" else
            priced(build_request(workflow.SELECTED_VERIFIER,q,{"calculation":"x"*160,"option":"a","value":"x"*120})) for q in questions]
        inputs = [(sum(len(m["content"]) for m in r["messages"])+2)//3+96 for r in requests]
        output = 96 if role=="solver" else 512
        input_cost = sum(inputs)*6*Decimal(ep["pricing"]["prompt"])
        expected = sum((request_cost(r,ep,input_tokens=n,output_tokens=output) for r,n in zip(requests,inputs)),Decimal(0))*6
        stressed = requests if role=="solver" else [priced(build_request(workflow.SELECTED_VERIFIER,q,
            {"calculation":"x"*8192,"option":"a","value":"x"*120})) for q in questions]
        reserve = sum((request_cost(r,ep) for r in stressed),Decimal(0))*9
        max_reservations.extend(request_cost(r,ep) for r in stressed)
        costs.append({"role":role,"model":model,"provider":ep["provider_name"],"provider_tag":ep["tag"],
            "expected_calls":12,"maximum_logical_calls":18,"estimated_input_tokens":sum(inputs)*6,
            "estimated_output_tokens_including_reasoning":12*output,"input_usd_per_million":ceilings[model]["prompt"],
            "output_usd_per_million":ceilings[model]["completion"],"estimated_input_cost_usd":str(input_cost),
            "estimated_output_cost_usd":str(expected-input_cost),"estimated_cost_usd":str(expected),"conservative_reservation_usd":str(reserve)})
    retry_reserve = 2*max(max_reservations)
    reserve_total = sum((Decimal(r["conservative_reservation_usd"]) for r in costs),Decimal(0))+retry_reserve
    cap = (reserve_total*Decimal("1.10")*100).to_integral_value(rounding=ROUND_CEILING)/100
    plan = {"version":"workflow-availability-plan-v1","created_at_utc":created_at or store.now(),
        "dataset":{"path":str(Path(dataset_path).resolve()),"sha256":hashlib.sha256(raw).hexdigest()},
        "split":{"exposure_snapshot":deepcopy(exposure),"reserved_held_out_ids":[r["id"] for r in records[100:]]},
        "questions":questions,"configurations":{"deepseek-deepseek-deepseek":config},
        "schedule":[{"question_id":q["id"],"configuration":"deepseek-deepseek-deepseek","repetition":rep}
                    for rep in range(1,4) for q in questions],"repetitions":3,
        "metadata":deepcopy(metadata),"endpoints":endpoints,"price_limits":ceilings,
        "code_sha256":{f:hashlib.sha256((PROJECT_ROOT/"scripts"/f).read_bytes()).hexdigest() for f in SOURCE_FILES},
        "migration_sha256":{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in store.MIGRATIONS.glob("*.sql")},
        "execution_policy":{"concurrency":1,"maximum_attempts":3,"transport_policy":retry_policy(),
            "maximum_requests":38,"maximum_budget_usd":float(cap),"timeout_inactivity_seconds":60,"metadata_max_age_hours":24,"held_out":False},
        "cost_preview":{"breakdown":costs,"expected_calls":24,"maximum_logical_calls":36,"maximum_retry_requests":2,"maximum_calls":38,
            "estimated_total_usd":str(sum((Decimal(r["estimated_cost_usd"]) for r in costs),Decimal(0))),
            "extra_retry_reservation_usd":str(retry_reserve),"conservative_reservation_total_usd":str(reserve_total),
            "assumptions":"Two solver attempts/execution, 96 solver and 512 verifier output tokens including reasoning once, chars/3+96 input, no cache discount. Stress uses full UTF-8 request+256, full caps and 8192-character calculation. Two extra physical requests shared across roles; not two extra per role."},
        "analysis_policy":"Availability/integration evidence only; no configuration ranking or automatic broad evaluation."}
    plan["sha256"] = pilot.digest(plan)
    return plan


def validate_plan(plan):
    if plan.get("version")!="workflow-availability-plan-v1" or plan.get("sha256")!=pilot.digest({k:v for k,v in plan.items() if k!="sha256"}):
        raise ValueError("Availability plan checksum/version failed.")
    age = (datetime.now(timezone.utc)-datetime.fromisoformat(plan["metadata"]["fetched_at_utc"])).total_seconds()
    if age < -300 or age > 24*3600:
        raise ValueError("Refresh free metadata and re-disclose the plan.")
    rebuilt = prepare_plan(plan["metadata"],plan["split"]["exposure_snapshot"],dataset_path=plan["dataset"]["path"],created_at=plan["created_at_utc"])
    if plan!=rebuilt:
        raise ValueError("Availability scope, controls, prices, sources or migrations changed.")


def summary(run_id, *, database_path):
    result = pilot.summary(run_id,database_path=database_path)
    rows = store.billing_rows(run_id,database_path=database_path)
    result["cooldowns"] = [{"call_id":r["call_id"],"logical_call_id":r["logical_call_id"],"role":r["role"],
        "wait_seconds":r["retry_wait_seconds"],"known_cost_usd":r["cost_usd"],"held_unknown_cost_usd":r["held_cost_usd"]}
        for r in rows if r["retry_wait_seconds"] is not None]
    result["note"] = "Small availability/integration check, not a sequence comparison or proof of sustained capacity. Unknown billing remains unresolved despite successful recovery."
    return result


def run_check(plan, *, database_path, budget_usd, max_requests, api_key, client, waiter=None):
    validate_plan(plan)
    return evaluation._run_schedule(plan,database_path=database_path,budget_usd=budget_usd,max_requests=max_requests,
                                    api_key=api_key,client=client,reporter=summary,waiter=waiter)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata",type=Path)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--database",type=Path,default=DATABASE_PATH)
    parser.add_argument("--run",action="store_true")
    parser.add_argument("--budget-usd",type=float)
    parser.add_argument("--max-requests",type=int)
    parser.add_argument("--report",type=Path)
    args = parser.parse_args()
    try:
        protected = {args.database.resolve(),DATASET_PATH.resolve()}
        if args.metadata:
            protected.add(args.metadata.resolve())
        if args.plan.resolve() in protected or args.report and args.report.resolve() in protected|{args.plan.resolve()}:
            raise ValueError("Output cannot overwrite input/database.")
        if not args.run:
            if not args.metadata or args.report or args.budget_usd is not None or args.max_requests is not None:
                parser.error("Offline preparation needs only --metadata and --plan (optional --database).")
            if args.plan.exists():
                raise ValueError("Plan already exists; choose a new filename.")
            plan = prepare_plan(json.loads(args.metadata.read_text(encoding="utf-8")),evaluation.exposure_snapshot(args.database))
            validate_plan(plan)
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            args.plan.write_text(json.dumps(plan,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            print(json.dumps({"mode":"offline","sha256":plan["sha256"],"execution_policy":plan["execution_policy"],"cost_preview":plan["cost_preview"],"generation_requests":0},indent=2))
        else:
            if args.metadata or args.budget_usd is None or args.max_requests is None or not args.report:
                parser.error("Paid execution requires frozen --plan, --budget-usd, --max-requests and --report.")
            if args.report.exists():
                raise ValueError("Report exists; choose a new filename.")
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            validate_plan(plan)
            load_dotenv(PROJECT_ROOT/".env")
            with httpx.Client(follow_redirects=False) as client:
                result = run_check(plan,database_path=args.database,budget_usd=args.budget_usd,max_requests=args.max_requests,
                                   api_key=os.getenv("OPENROUTER_API_KEY"),client=client)
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
            print(json.dumps({k:result[k] for k in ("run_id","status","new_requests","known_new_cost_usd","unknown_cost_calls","held_unknown_cost_usd","transport_retry_requests")},indent=2))
    except (ValueError,KeyError,OSError,sqlite3.Error) as error:
        parser.exit(1,f"Availability check stopped: {error}\n")


if __name__=="__main__":
    main()
