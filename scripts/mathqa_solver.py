"""Solve one fixed MathQA question through LangGraph and track API usage."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import NotRequired, TypedDict

import httpx
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph


MODELS = [
    "qwen/qwen-2.5-7b-instruct",
    "qwen/qwen3-32b",
    "deepseek/deepseek-v3.2",
]
SELECTED_MODEL = MODELS[0]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "mathqa_200" / "mathqa_200.json"
QUESTION_ID = "mathqa_test_0002"
CALL_LOG_PATH = PROJECT_ROOT / "results" / "mathqa_calls.jsonl"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class CallUsage(TypedDict):
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None


class SolverState(TypedDict):
    question: dict[str, str]
    model: str
    answer: NotRequired[str]
    usage: NotRequired[CallUsage]
    elapsed_seconds: NotRequired[float]


def load_question() -> dict[str, str]:
    """Find the fixed question and return only fields intended for the solver."""
    questions = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    question = next(
        (item for item in questions if item["id"] == QUESTION_ID),
        None,
    )
    if question is None:
        raise ValueError(f"Question {QUESTION_ID!r} was not found in {DATASET_PATH}")

    return {
        "id": question["id"],
        "problem": question["Problem"],
        "options": question["options"],
    }


def build_prompt(question: dict[str, str]) -> str:
    """Ask for an explanation, calculation, and the chosen option."""
    return (
        "Solve this multiple-choice math problem.\n"
        "Explain the reasoning and show the calculation supporting your answer.\n"
        "Finish with: Final answer: <option letter>) <option value>.\n\n"
        f"Problem: {question['problem']}\n"
        f"Options: {question['options']}"
    )


def call_openrouter(
    question: dict[str, str], model: str
) -> tuple[str, CallUsage, float]:
    """Make one request and log its reported usage, even if the answer is invalid."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Set OPENROUTER_API_KEY in the repository's .env file.")

    usage: CallUsage = {
        "input_tokens": None,
        "output_tokens": None,
        "cost_usd": None,
    }
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "question_id": question["id"],
        "model": model,
        "status": "failed",
        "usage": usage,
    }

    # Open the log before requesting a generation so logging is ready first.
    CALL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CALL_LOG_PATH.open("a", encoding="utf-8") as log_file:
        try:
            started = perf_counter()
            try:
                response = httpx.post(
                    OPENROUTER_URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": build_prompt(question)}],
                        "temperature": 0,
                        "max_tokens": 512,
                        "stream": False,
                    },
                    timeout=60.0,
                )
            finally:
                # With stream=False, post() reads the complete response body.
                elapsed_seconds = perf_counter() - started
                record["elapsed_seconds"] = elapsed_seconds
            record["http_status"] = response.status_code
            response.raise_for_status()
            payload = response.json()
            record["response_id"] = payload.get("id")
            record["returned_model"] = payload.get("model")

            reported_usage = payload.get("usage") or {}
            usage.update(
                input_tokens=reported_usage.get("prompt_tokens"),
                output_tokens=reported_usage.get("completion_tokens"),
                cost_usd=reported_usage.get("cost"),
            )
            # Preserve additional fields, including reasoning and cached tokens.
            record["raw_usage"] = reported_usage

            if payload.get("error"):
                raise RuntimeError("OpenRouter returned an API error; see the call log.")
            choice = payload["choices"][0]
            record["finish_reason"] = choice.get("finish_reason")
            answer = choice["message"].get("content")
            if not isinstance(answer, str) or not answer.strip():
                raise RuntimeError("OpenRouter returned no answer text; see the call log.")
            if choice.get("finish_reason") == "length":
                raise RuntimeError("The response reached the token limit; see the call log.")

            record["status"] = "completed"
            return answer, usage, elapsed_seconds
        except Exception as error:
            # Store the exception type, without logging credentials or headers.
            record["error_type"] = type(error).__name__
            raise
        finally:
            log_file.write(json.dumps(record) + "\n")


def solver(state: SolverState) -> dict:
    """Read the graph state and return updates for its answer and usage."""
    answer, usage, elapsed_seconds = call_openrouter(state["question"], state["model"])
    return {"answer": answer, "usage": usage, "elapsed_seconds": elapsed_seconds}


def build_workflow():
    builder = StateGraph(SolverState)
    builder.add_node("solver", solver)
    builder.add_edge(START, "solver")
    builder.add_edge("solver", END)
    return builder.compile()


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    question = load_question()
    print(f"Selected model: {SELECTED_MODEL}")
    print(f"Question ID: {question['id']}")
    print(f"Problem: {question['problem']}")
    print(f"Options: {question['options']}", flush=True)

    workflow = build_workflow()
    result = workflow.invoke({"question": question, "model": SELECTED_MODEL})
    print(f"\n{result['answer']}")

    usage = result["usage"]
    print(f"\nInput tokens: {usage['input_tokens']}")
    print(f"Output tokens: {usage['output_tokens']}")
    cost = usage["cost_usd"]
    cost_text = f"${cost:.8f}" if cost is not None else "unavailable"
    # This workflow makes one call, so its call cost is also the run's total.
    print(f"Total cost this run: {cost_text}")
    print(f"Elapsed seconds: {result['elapsed_seconds']:.3f}")
    print(f"Call log: {CALL_LOG_PATH}")


if __name__ == "__main__":
    main()
