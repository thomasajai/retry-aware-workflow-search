"""Offline controlled loop demo. No HTTP, credentials, or OpenRouter requests."""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path

import mathqa_workflow as workflow
from mathqa_workflow_grading import grade_execution
import mathqa_workflow_store as store


def run_demo(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Choose a new output directory; demo never overwrites results.")
    output.mkdir(parents=True)
    dataset = output / "controlled-question.json"
    question = {"id": "controlled_6_times_7", "problem": "What is 6 times 7?", "options": "a)40, b)42, c)44, d)46, e)48"}
    dataset.write_text(json.dumps([{"id": question["id"], "Problem": question["problem"], "options": question["options"],
                                  "correct": "b", "Rationale": "OFFLINE_KEY_ONLY"}]) + "\n", encoding="utf-8")
    db = output / "controlled-loop.sqlite3"
    store.migrate(db)
    limits = workflow.Limits(1.0, 30)
    run = store.create_run("sequence_evaluation", dataset, hashlib.sha256(dataset.read_bytes()).hexdigest(),
        [question["id"]], {"mode": "offline_controlled_demo", "no_generation_requests": True},
        budget_usd=limits.budget_usd, max_requests=limits.max_requests, database_path=db)
    config = workflow.configuration(["qwen25", "qwen3", "deepseek"])
    scenarios = (("accept_first", [True], False), ("accept_third", [False, False, True], False),
                 ("reject_all_key_correct", [False, False, False], False), ("accept_wrong_option", [True], True))
    results = []
    for name, verdicts, wrong in scenarios:
        cid = store.create_config(run, name, config, database_path=db)
        sent = []
        def sender(request):
            sent.append(request)
            is_verifier = request["messages"][0]["role"] == "system"
            if is_verifier:
                index = sum(r["messages"][0]["role"] == "system" for r in sent)-1
                content = {"accepted": verdicts[index]}
            else:
                content = {"calculation": "6*7=40" if wrong else "6*7=42", "option": "a" if wrong else "b", "value": "40" if wrong else "42"}
            return 200, {"model": request["model"], "provider": "Offline fixture", "id": "offline-controlled",
                "choices": [{"message": {"content": json.dumps(content)}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "completion_tokens_details": {"reasoning_tokens": 0}, "cost": 0}}
        models = [p["model"] for p in config["solvers"]] + [config["verifier"]["model"]]
        runner = workflow.Runner(run, cid, config, database_path=db, sender=sender, reservations=lambda _: 0.001,
                                 providers={m: "Offline fixture" for m in models}, limits=limits)
        result = runner.execute(question)
        results.append({"scenario": name, **result, "grade": grade_execution(result["execution_id"], database_path=db),
                        "mock_calls": len(sent)})
    with closing(store.connect(db)) as c, c:
        c.execute("UPDATE workflow_runs SET status='completed',finished_at_utc=? WHERE run_id=?", (store.now(), run))
    report = {"mode": "offline_controlled_demo", "run_id": run, "database": str(db), "results": results,
              "mock_calls": sum(r["mock_calls"] for r in results), "new_generation_requests": 0,
              "actual_openrouter_cost_usd": 0, "note": "Controlled routes only; these are not live model accuracy results."}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run_demo(args.output), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Offline demo failed: {error}\n")


if __name__ == "__main__":
    main()
