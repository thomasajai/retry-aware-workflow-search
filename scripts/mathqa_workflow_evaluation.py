"""Prepare a balanced 27-sequence development evaluation; paid execution is explicit."""

import argparse
from collections import defaultdict
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sqlite3
import subprocess
from urllib.request import urlopen

import httpx
from dotenv import load_dotenv

from mathqa_batch import DATASET_PATH, DATABASE_PATH, OPENROUTER_URL, PROJECT_ROOT
from mathqa_models import workflow_model_configs, WORKFLOW_DEEPSEEK_PROVIDERS
from mathqa_verifier import build_request
from mathqa_verifier_preflight import request_cost
from mathqa_transport import decode_response, retry_policy
import mathqa_workflow as workflow
from mathqa_workflow_grading import grade_execution, GRADER_VERSION
import mathqa_workflow_pilot as pilot
import mathqa_workflow_store as store

SELECTION_SEED = 20261007
SCHEDULE_SEED = 20261008
QUESTION_COUNT = 20
REPETITIONS = 1
SOURCE_FILES = pilot.SOURCE_FILES + ("mathqa_workflow_evaluation.py",)


def fetch_metadata():
    """Public GETs only; no key, generation or credit consumption."""
    profiles = list(workflow_model_configs().values()) + [workflow.configuration(pilot.SEQUENCES[0])["verifier"]]
    models = [p["model"] for p in profiles]
    result = {"models": {}}
    for model in models:
        url = "https://openrouter.ai/api/v1/models/" + model + "/endpoints"
        with urlopen(url, timeout=30) as response:
            result["models"][model] = {"source_url": url, "data": json.load(response)["data"]}
    url = "https://openrouter.ai/api/v1/models"
    with urlopen(url, timeout=30) as response:
        catalog = json.load(response)["data"]
    result["catalog"] = {"source_url": url, "models": {m["id"]: {k:m.get(k) for k in
        ("id", "reasoning", "supported_parameters")} for m in catalog if m["id"] in models}}
    result["fetched_at_utc"] = store.now()
    return result


def exposure_snapshot(database_path):
    """Conservative exposure includes saved/failed/prepared attempts; read only."""
    path = Path(database_path).resolve()
    with closing(sqlite3.connect(path.as_uri()+"?mode=ro", uri=True)) as c:
        legacy = sorted(r[0] for r in c.execute("SELECT DISTINCT question_id FROM calls"))
        workflows = sorted(r[0] for r in c.execute("SELECT DISTINCT question_id FROM workflow_executions"))
    return {"as_of_utc": store.now(), "database": str(path), "legacy_question_ids": legacy,
            "workflow_question_ids": workflows, "note": "Recorded exposure, not a guarantee against unrecorded inspection."}


def prepare_plan(metadata, exposure, *, dataset_path=DATASET_PATH, created_at=None, deepseek_provider="deepinfra/fp4", rate_limit_retries=False):
    raw = Path(dataset_path).read_bytes()
    records = json.loads(raw)
    if len(records) != 200 or len({r["id"] for r in records}) != 200:
        raise ValueError("This stage requires the fixed 200-question dataset with unique IDs.")
    development, held_out = records[:100], records[100:]
    exposed = set(exposure["legacy_question_ids"]) | set(exposure["workflow_question_ids"])
    held_out_exposed = sorted(exposed & {r["id"] for r in held_out})
    if held_out_exposed:
        raise ValueError("Reserved held-out questions have recorded exposure; revise the split explicitly.")
    eligible = [r for r in development if r["id"] not in pilot.QUESTION_IDS]
    selected = random.Random(SELECTION_SEED).sample(eligible, QUESTION_COUNT)
    if any(r.get("correct") not in list("abcde") for r in selected):
        raise ValueError("Selected questions require independent option keys.")
    questions = [{"id":r["id"], "problem":r["Problem"], "options":r["options"]} for r in selected]
    configs = {"-".join(c["solver_sequence"]):c for c in workflow.configurations(deepseek_provider=deepseek_provider,rate_limit_retries=rate_limit_retries)}
    profiles = list(workflow_model_configs(deepseek_provider=deepseek_provider).values()) + [next(iter(configs.values()))["verifier"]]
    endpoints, ceilings = {}, {}
    for p in profiles:
        m, settings = p["model"], p.get("body_settings",p.get("settings"))
        endpoints[m] = deepcopy(pilot.endpoint(metadata,m,settings))
        ceilings[m] = {k:float(Decimal(endpoints[m]["pricing"][k])*1_000_000) for k in ("prompt","completion")}
        ceilings[m]["request"] = 0
    catalog = metadata["catalog"]["models"][profiles[-1]["model"]]
    if (catalog["id"] != profiles[-1]["model"] or "reasoning" not in catalog["supported_parameters"]
            or not isinstance(catalog["reasoning"],dict)):
        raise ValueError("Verifier reasoning capabilities are missing.")
    def priced(r):
        r["provider"]["max_price"] = deepcopy(ceilings[r["model"]])
        return r
    costs = []
    maximum_reservation = Decimal(0)
    for p in profiles:
        verifier = "settings" in p
        m, ep = p["model"], endpoints[p["model"]]
        requests = [priced(build_request(workflow.SELECTED_VERIFIER,q,{"calculation":"x"*160,"option":"a","value":"x"*120}))
                    if verifier else priced(workflow.solver_request(p,q)) for q in questions]
        inputs = [(sum(len(msg["content"]) for msg in r["messages"])+2)//3+96 for r in requests]
        # Across 27 triples: each model appears nine times in each position.
        expected_weight, max_weight = (54,81) if verifier else (18,27)
        output = 512 if verifier else 96
        input_cost = sum(inputs)*expected_weight*Decimal(ep["pricing"]["prompt"])
        expected = sum((request_cost(r,ep,input_tokens=n,output_tokens=output)
                        for r,n in zip(requests,inputs)),Decimal(0))*expected_weight
        stressed = [priced(build_request(workflow.SELECTED_VERIFIER,q,{"calculation":"x"*8192,"option":"a","value":"x"*120}))
                    for q in questions] if verifier else requests
        reserve = sum((request_cost(r,ep) for r in stressed),Decimal(0))*max_weight
        maximum_reservation = max(maximum_reservation,max(request_cost(r,ep) for r in stressed))
        costs.append({"role":"verifier" if verifier else "solver", "model":m, "provider":ep["provider_name"],
            "provider_tag":ep["tag"], "expected_calls":len(questions)*expected_weight,"maximum_calls":len(questions)*max_weight,
            "estimated_input_tokens":sum(inputs)*expected_weight,"estimated_output_tokens_including_reasoning":output*len(questions)*expected_weight,
            "input_usd_per_million":ceilings[m]["prompt"],"output_usd_per_million":ceilings[m]["completion"],
            "estimated_input_cost_usd":str(input_cost),"estimated_output_cost_usd":str(expected-input_cost),
            "estimated_cost_usd":str(expected),"conservative_reservation_usd":str(reserve)})
    reserve_total = sum((Decimal(c["conservative_reservation_usd"]) for c in costs),Decimal(0))
    if rate_limit_retries:
        reserve_total += maximum_reservation*retry_policy()["max_retry_requests"]
    cap = (reserve_total*Decimal("1.10")*4).to_integral_value(rounding=ROUND_CEILING)/4
    rng = random.Random(SCHEDULE_SEED)
    schedule = []
    for q in questions:
        names = list(configs)
        rng.shuffle(names)
        schedule.extend({"question_id":q["id"],"configuration":name,"repetition":1} for name in names)
    plan = {"version":"workflow-evaluation-plan-v1", "created_at_utc":created_at or store.now(),
        "dataset":{"path":str(Path(dataset_path).resolve()),"sha256":hashlib.sha256(raw).hexdigest()},
        "split":{"development_pool_ids":[r["id"] for r in development],"reserved_held_out_ids":[r["id"] for r in held_out],
                 "excluded_pilot_ids":list(pilot.QUESTION_IDS),"selection_seed":SELECTION_SEED,"exposure_snapshot":deepcopy(exposure)},
        "questions":questions,"configurations":configs,"schedule":schedule,"scheduling_seed":SCHEDULE_SEED,"repetitions":REPETITIONS,
        "metadata":deepcopy(metadata),"endpoints":endpoints,"price_limits":ceilings,
        "code_sha256":{f:hashlib.sha256((PROJECT_ROOT/"scripts"/f).read_bytes()).hexdigest() for f in SOURCE_FILES},
        "execution_policy":{"concurrency":1,"transport_retries":0,"timeout_inactivity_seconds":60,
            "maximum_attempts":3,"maximum_requests":len(schedule)*6,"maximum_budget_usd":float(cap),"metadata_max_age_hours":24,"held_out":False},
        "analysis_policy":{"primary":"Mean independently graded workflow score on completed full coverage only",
            "selection":"Descriptive accuracy/cost Pareto frontier; no automatic finalist or held-out run",
            "baselines":"Reuse new first-slot observations: nine independent generations/model/question; raw option and one-attempt verified scores",
            "uncertainty":"Wilson accuracy intervals plus 1000 paired question-block bootstrap resamples, seed 20261009; descriptive intervals, no multiple-comparison significance claim",
            "reasoning":"Separate review labels; option correctness never implies reasoning validity",
            "incomplete":"No imputed scores or ranking; report costs and per-configuration coverage"},
        "cost_preview":{"breakdown":costs,"expected_calls":len(schedule)*4,"maximum_calls":len(schedule)*6,
            "estimated_total_usd":str(sum((Decimal(c["estimated_cost_usd"]) for c in costs),Decimal(0))),
            "conservative_reservation_total_usd":str(reserve_total),
            "assumptions":"Two slots per execution, solver output 96/verifier 512 including reasoning once; chars/3+96 input; no cache discount. Stress: full UTF-8 request+256 framing, 8192-character calculation and full output caps. Estimates are not billing guarantees."}}
    if deepseek_provider != "deepinfra/fp4":
        plan.update(version="workflow-evaluation-plan-v2", deepseek_provider=deepseek_provider)
    if rate_limit_retries:
        plan.update(version="workflow-evaluation-plan-v3",deepseek_provider=deepseek_provider,rate_limit_retries=True)
        extra = retry_policy()["max_retry_requests"]
        plan["execution_policy"].update(transport_retries=2,transport_policy=retry_policy(),maximum_requests=len(schedule)*6+extra)
        plan["cost_preview"].update(maximum_calls=len(schedule)*6+extra,maximum_retry_requests=extra,
                                    extra_retry_reservation_usd=str(maximum_reservation*extra))
    plan["sha256"] = pilot.digest(plan)
    return plan


def validate_plan(plan):
    if plan.get("version") not in ("workflow-evaluation-plan-v1", "workflow-evaluation-plan-v2", "workflow-evaluation-plan-v3") or plan.get("sha256") != pilot.digest({k:v for k,v in plan.items() if k!="sha256"}):
        raise ValueError("Evaluation checksum/version failed.")
    age = (datetime.now(timezone.utc)-datetime.fromisoformat(plan["metadata"]["fetched_at_utc"])).total_seconds()
    if age < -300 or age > 24*3600:
        raise ValueError("Refresh free metadata and prepare a new proposal.")
    rebuilt = prepare_plan(plan["metadata"],plan["split"]["exposure_snapshot"],dataset_path=plan["dataset"]["path"],created_at=plan["created_at_utc"],
                           deepseek_provider=plan.get("deepseek_provider", "deepinfra/fp4"),rate_limit_retries=plan.get("rate_limit_retries",False))
    if rebuilt != plan:
        raise ValueError("Dataset, code, profiles, schedule or evidence changed; prepare a new plan.")


def bootstrap(values, draws):
    samples = sorted(sum(values[i] for i in draw)/len(values) for draw in draws)
    return [samples[24],samples[974]]


def wilson(successes, count):
    # Bootstrap alone degenerates at 0%/100%; retain finite-sample uncertainty.
    z = 1.959963984540054
    p = successes/count
    denominator = 1+z*z/count
    center = (p+z*z/(2*count))/denominator
    radius = z*math.sqrt(p*(1-p)/count+z*z/(4*count*count))/denominator
    return [max(0,center-radius),min(1,center+radius)]


def evaluation_summary(run_id, *, database_path):
    report = pilot.summary(run_id,database_path=database_path)
    with closing(store.connect(database_path)) as c:
        plan = json.loads(c.execute("SELECT settings_json FROM workflow_runs WHERE run_id=?",(run_id,)).fetchone()[0])["plan"]
        attempts = [dict(r) for r in c.execute("SELECT a.*,e.question_id,f.name configuration,g.option_correct "
            "FROM workflow_attempts a JOIN workflow_executions e USING(execution_id) JOIN workflow_configs f USING(config_id) "
            "LEFT JOIN workflow_grades g ON g.attempt_id=a.attempt_id AND g.grader_version=? WHERE e.run_id=?",(GRADER_VERSION,run_id))]
        logical_calls = {r["call_id"]:dict(r) for r in c.execute("SELECT w.* FROM workflow_calls w JOIN workflow_attempts a USING(attempt_id) "
            "JOIN workflow_executions e USING(execution_id) WHERE e.run_id=?",(run_id,))}
    calls = defaultdict(list)
    for row in store.billing_rows(run_id,database_path=database_path):
        calls[row["logical_call_id"]].append(row)
    expected_questions = [q["id"] for q in plan["questions"]]
    grouped = defaultdict(list)
    by_exec = defaultdict(list)
    for a in attempts:
        by_exec[a["execution_id"]].append(a)
    for rows in by_exec.values():
        rows.sort(key=lambda a:a["position"])
    for e in report["executions"]:
        grouped[e["configuration"]].append(e)
    rng = random.Random(20261009)
    draws = [[rng.randrange(len(expected_questions)) for _ in expected_questions] for _ in range(1000)]
    configurations = []
    scores = {}
    for name in plan["configurations"]:
        executions = grouped[name]
        completed = [e for e in executions if e["workflow_score"] is not None]
        reached_calls = [call for e in executions for a in by_exec[e["execution_id"]]
                         for k in ("solver_call_id","verifier_call_id") if a[k] for call in calls[a[k]]]
        cost = sum((Decimal(str(r["cost_usd"])) for r in reached_calls if r["cost_usd"] is not None),Decimal(0))
        all_complete = len(completed)==len(expected_questions)
        if all_complete:
            score_by_q = {e["question_id"]:e["workflow_score"] for e in completed}
            scores[name] = [score_by_q[q] for q in expected_questions]
        configurations.append({"configuration":name,"planned":len(expected_questions),"reached":len(executions),"scored":len(completed),
            "accuracy_completed_only":sum(e["workflow_score"] for e in completed)/len(completed) if completed else None,
            "complete_coverage":all_complete,"known_cost_usd":str(cost),"unknown_cost_calls":sum(r["cost_usd"] is None for r in reached_calls),
            "mean_cost_usd_per_planned_execution":float(cost)/len(expected_questions) if all_complete and all(r["cost_usd"] is not None for r in reached_calls) else None,
            "accepted_answer_coverage":sum(e["status"]=="accepted" for e in completed)/len(completed) if completed else None,
            "mean_wall_seconds_completed":sum(e["elapsed_seconds"] for e in completed)/len(completed) if completed else None,
            "solver_attempts":sum(len(by_exec[e["execution_id"]]) for e in executions),"requests":len(reached_calls),
            "question_bootstrap_95_interval":bootstrap(scores[name],draws) if all_complete else None,
            "answer_accuracy_wilson_95_interval":wilson(sum(scores[name]),len(expected_questions)) if all_complete else None,
            "question_scores":[{"question_id":e["question_id"],"score":e["workflow_score"]} for e in completed]})
    complete = report["complete_coverage"]
    cost_complete = complete and report["unknown_cost_calls"]==0
    ranking = sorted(configurations,key=lambda r:(-r["accuracy_completed_only"],float(r["known_cost_usd"]),r["configuration"])) if cost_complete else None
    frontier = None
    if cost_complete:
        frontier = [r["configuration"] for r in configurations if not any(
            s["accuracy_completed_only"]>=r["accuracy_completed_only"] and Decimal(s["known_cost_usd"])<=Decimal(r["known_cost_usd"])
            and (s["accuracy_completed_only"]>r["accuracy_completed_only"] or Decimal(s["known_cost_usd"])<Decimal(r["known_cost_usd"])) for s in configurations)]
    paired = []
    if ranking:
        reference = ranking[0]["configuration"]
        for name in plan["configurations"]:
            difference = [a-b for a,b in zip(scores[reference],scores[name])]
            paired.append({"reference":reference,"configuration":name,"mean_accuracy_difference":sum(difference)/len(difference),
                           "question_bootstrap_95_interval":bootstrap(difference,draws)})
    baselines = []
    for model in workflow_model_configs().values():
        # Failed/unusable first calls are scored zero if their execution is finished.
        finished_ids = {e["execution_id"] for e in report["executions"] if e["workflow_score"] is not None}
        initial = [a for a in attempts if a["position"]==1 and a["solver_model"]==model["model"] and a["execution_id"] in finished_ids]
        baseline_scores = {q:[a for a in initial if a["question_id"]==q] for q in expected_questions}
        baseline_complete = all(len(rows)==9 for rows in baseline_scores.values())
        values = [sum(a["option_correct"]==1 for a in baseline_scores[q])/9 for q in expected_questions]
        raw_cost = sum((Decimal(str(call["cost_usd"])) for a in initial for call in calls[a["solver_call_id"]] if call["cost_usd"] is not None),Decimal(0))
        first_calls = [call for a in initial for k in ("solver_call_id","verifier_call_id") if a[k] for call in calls[a[k]]]
        verified_cost = sum((Decimal(str(r["cost_usd"])) for r in first_calls if r["cost_usd"] is not None),Decimal(0))
        baselines.append({"model":model["model"],"planned_first_slot_calls":9*len(expected_questions),"scored_first_slot_calls":len(initial),
            "complete_coverage":baseline_complete,"raw_solver_accuracy":sum(a["option_correct"]==1 for a in initial)/len(initial) if initial else None,
            "one_attempt_verified_accuracy":sum(a["option_correct"]==1 and a["verification_status"]=="accept" for a in initial)/len(initial) if initial else None,
            "raw_solver_known_cost_usd":str(raw_cost),"one_attempt_verified_known_cost_usd":str(verified_cost),
            "mean_raw_solver_cost_usd":float(raw_cost)/len(initial) if initial and all(call["cost_usd"] is not None for a in initial for call in calls[a["solver_call_id"]]) else None,
            "mean_one_attempt_verified_cost_usd":float(verified_cost)/len(initial) if initial and all(r["cost_usd"] is not None for r in first_calls) else None,
            "mean_raw_solver_wall_seconds":sum(logical_calls[a["solver_call_id"]]["elapsed_seconds"] for a in initial)/len(initial) if initial else None,
            "unknown_cost_calls":sum(r["cost_usd"] is None for r in first_calls),
            "question_bootstrap_95_interval":bootstrap(values,draws) if baseline_complete else None})
    repeated = 0
    eligible_retries = 0
    recovery = 0
    rejected_first = 0
    for e in report["executions"]:
        rows = by_exec[e["execution_id"]]
        seen = set()
        for a in rows:
            if a["usable"] == 1 and a["parsed_fields_json"]:
                fields = json.loads(a["parsed_fields_json"])
                signature = (fields["option"],fields["value"])
                if a["position"]>1:
                    eligible_retries += 1
                    repeated += signature in seen
                seen.add(signature)
        if rows and rows[0]["verification_status"]=="reject" and e["workflow_score"] is not None:
            rejected_first += 1
            recovery += e["workflow_score"]==1
    report.update({"configurations":configurations,"ranking":ranking,"accuracy_cost_frontier":frontier,"paired_differences":paired,"cost_comparison_complete":cost_complete,
        "one_attempt_baselines":baselines,"recovery_after_first_rejection":{"finished_executions":rejected_first,"correct_final":recovery},
        "repeat_option_value_after_retry":{"usable_retries":eligible_retries,"repeats_of_any_prior_answer":repeated},
        "note":"Development comparison; intervals are descriptive, without selection/multiple-comparison adjustment. Bootstrap can degenerate at boundaries; Wilson intervals retain finite-sample uncertainty. Cost rankings/frontier require resolved billing as well as full score coverage. No automatic finalist. Reasoning validity requires separate review."})
    return report


def run_evaluation(plan, *, database_path, budget_usd, max_requests, api_key, client, waiter=None):
    validate_plan(plan)
    return _run_schedule(plan,database_path=database_path,budget_usd=budget_usd,max_requests=max_requests,api_key=api_key,client=client,waiter=waiter)


def _run_schedule(plan, *, database_path, budget_usd, max_requests, api_key, client, reporter=evaluation_summary, waiter=None):
    """Shared adapter; public entry points validate their frozen plans first."""
    limits = workflow.Limits(budget_usd,max_requests)
    if budget_usd>plan["execution_policy"]["maximum_budget_usd"] or max_requests>plan["execution_policy"]["maximum_requests"]:
        raise ValueError("Limits exceed frozen evaluation scope.")
    if not api_key:
        raise ValueError("API key required for explicit paid execution.")
    # Recheck held-out exposure at the destination before any mutation/request.
    if Path(database_path).exists():
        current = exposure_snapshot(database_path)
        exposed = set(current["legacy_question_ids"])|set(current["workflow_question_ids"])
        if exposed & set(plan["split"]["reserved_held_out_ids"]):
            raise ValueError("Reserved held-out exposure changed; review the split.")
    store.migrate(database_path)
    revision = subprocess.run(["git","rev-parse","HEAD"],cwd=PROJECT_ROOT,text=True,capture_output=True,check=True).stdout.strip()
    dirty = bool(subprocess.run(["git","status","--porcelain"],cwd=PROJECT_ROOT,text=True,capture_output=True,check=True).stdout.strip())
    try:
        run = store.create_run("sequence_evaluation",plan["dataset"]["path"],plan["dataset"]["sha256"],
            [q["id"] for q in plan["questions"]],{"plan":plan,"code_revision":revision,"code_dirty":dirty},
            database_path=database_path,budget_usd=budget_usd,max_requests=max_requests,plan_sha256=plan["sha256"])
    except sqlite3.IntegrityError as error:
        raise ValueError("This plan already has a run; no automatic retry/rerun/resume.") from error
    providers = {m:e["provider_name"] for m,e in plan["endpoints"].items()}
    def sender(request):
        response = client.post(OPENROUTER_URL,json=request,headers={"Authorization":"Bearer "+api_key},timeout=60)
        return decode_response(response,pilot._reject_nonfinite)
    with closing(store.connect(database_path)) as c,c:
        c.execute("UPDATE workflow_runs SET status='running',started_at_utc=? WHERE run_id=?",(store.now(),run))
    try:
        config_ids = {name:store.create_config(run,name,config,database_path=database_path) for name,config in plan["configurations"].items()}
        questions = {q["id"]:q for q in plan["questions"]}
        for index,item in enumerate(plan["schedule"]):
            config = plan["configurations"][item["configuration"]]
            runner = workflow.Runner(run,config_ids[item["configuration"]],config,database_path=database_path,
                sender=sender,reservations=lambda r:request_cost(r,plan["endpoints"][r["model"]]),providers=providers,
                limits=limits,price_limits=plan["price_limits"],waiter=waiter)
            outcome = runner.execute(questions[item["question_id"]],repetition=item["repetition"])
            if outcome["status"] in ("interrupted","budget_stopped"):
                break
            grade_execution(outcome["execution_id"],database_path=database_path)
            if (index+1)%27==0:
                print(json.dumps({"finished_executions":index+1,"planned":len(plan["schedule"])}),flush=True)
        else:
            with closing(store.connect(database_path)) as c,c:
                errors = c.execute("SELECT COUNT(*) FROM workflow_attempts a JOIN workflow_executions e USING(execution_id) "
                    "WHERE e.run_id=? AND (a.verification_status IN ('invalid','error') OR EXISTS "
                    "(SELECT 1 FROM workflow_billable_calls w WHERE w.attempt_id=a.attempt_id AND w.status!='completed'))",(run,)).fetchone()[0]
                c.execute("UPDATE workflow_runs SET status=?,finished_at_utc=? WHERE run_id=?",("completed_with_errors" if errors else "completed",store.now(),run))
    except BaseException:
        with closing(store.connect(database_path)) as c,c:
            c.execute("UPDATE workflow_runs SET status='interrupted',finished_at_utc=?,stop_reason=? WHERE run_id=?",
                      (store.now(),"unexpected_failure_review_calls",run))
        raise
    return reporter(run,database_path=database_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path)
    parser.add_argument("--metadata",type=Path)
    parser.add_argument("--deepseek-provider",choices=WORKFLOW_DEEPSEEK_PROVIDERS,help="Offline preparation only; execution uses the frozen plan.")
    parser.add_argument("--rate-limit-retries",action="store_true",help="Offline preparation only; opt into the bounded upstream 429 policy.")
    parser.add_argument("--fetch-metadata",type=Path,help="Free public metadata only; no generation.")
    parser.add_argument("--database",type=Path,default=DATABASE_PATH)
    parser.add_argument("--run",action="store_true")
    parser.add_argument("--budget-usd",type=float)
    parser.add_argument("--max-requests",type=int)
    parser.add_argument("--report",type=Path)
    args = parser.parse_args()
    try:
        protected = {args.database.resolve(),DATASET_PATH.resolve()}
        for output in (args.fetch_metadata,args.plan,args.report):
            if output and output.resolve() in protected:
                raise ValueError("Output cannot overwrite dataset/database.")
        outputs = [p.resolve() for p in (args.fetch_metadata,args.plan,args.report) if p]
        if len(set(outputs))!=len(outputs) or args.metadata and args.metadata.resolve() in outputs:
            raise ValueError("Inputs/outputs must use distinct paths.")
        if args.fetch_metadata:
            if args.run or args.plan or args.metadata or args.report or args.deepseek_provider or args.rate_limit_retries:
                parser.error("--fetch-metadata is a separate free operation.")
            if args.fetch_metadata.exists():
                raise ValueError("Metadata file exists; choose a new filename.")
            result = fetch_metadata()
            args.fetch_metadata.parent.mkdir(parents=True,exist_ok=True)
            args.fetch_metadata.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
            print(json.dumps({"metadata":str(args.fetch_metadata),"fetched_at_utc":result["fetched_at_utc"],"generation_requests":0}))
        elif not args.run:
            if not args.plan or not args.metadata:
                parser.error("Offline preparation requires --plan and --metadata.")
            if args.plan.exists():
                raise ValueError("Plan exists; choose a new filename.")
            plan = prepare_plan(json.loads(args.metadata.read_text(encoding="utf-8")),exposure_snapshot(args.database),
                                deepseek_provider=args.deepseek_provider or "deepinfra/fp4",rate_limit_retries=args.rate_limit_retries)
            validate_plan(plan)
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            args.plan.write_text(json.dumps(plan,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            print(json.dumps({"mode":"offline","sha256":plan["sha256"],"questions":[q["id"] for q in plan["questions"]],
                "executions":len(plan["schedule"]),"limits":plan["execution_policy"],"cost_preview":plan["cost_preview"],"generation_requests":0},indent=2))
        else:
            if args.deepseek_provider or args.rate_limit_retries:
                parser.error("Execution provider is frozen in --plan; --deepseek-provider applies only to preparation.")
            if not args.plan or args.budget_usd is None or args.max_requests is None or not args.report:
                parser.error("--run requires --plan, --budget-usd, --max-requests and --report.")
            if args.report.exists():
                raise ValueError("Report exists; choose a new filename.")
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            validate_plan(plan)
            load_dotenv(PROJECT_ROOT/".env")
            with httpx.Client(follow_redirects=False) as client:
                result = run_evaluation(plan,database_path=args.database,budget_usd=args.budget_usd,max_requests=args.max_requests,
                    api_key=os.getenv("OPENROUTER_API_KEY"),client=client)
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
            print(json.dumps({k:result[k] for k in ("run_id","status","complete_coverage","new_requests","known_new_cost_usd","unknown_cost_calls","accuracy_cost_frontier")},indent=2))
    except (ValueError,KeyError,OSError,sqlite3.Error) as error:
        parser.exit(1,f"Evaluation stopped: {error}\n")


if __name__=="__main__":
    main()
