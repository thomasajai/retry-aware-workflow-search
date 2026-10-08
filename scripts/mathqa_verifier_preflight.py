"""Read public provider metadata and estimate verifier cost. No generation/key."""

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
from urllib.request import urlopen

from mathqa_verifier import profile


def fetch_metadata(candidates):
    models = {}
    for alias in candidates:
        model = profile(alias)["model"]
        url = f"https://openrouter.ai/api/v1/models/{model}/endpoints"
        with urlopen(url, timeout=30) as response:
            payload = json.load(response)
        models[model] = {"source_url": url, "data": payload["data"]}
    return {"fetched_at_utc": datetime.now(timezone.utc).isoformat(), "models": models}


def select_endpoint(metadata, alias):
    p = profile(alias)
    tag = p["settings"]["provider"]["only"][0]
    data = metadata["models"][p["model"]]["data"]
    if data.get("id") != p["model"]:
        raise ValueError("Provider metadata model ID mismatch.")
    matches = [e for e in data["endpoints"] if e.get("tag") == tag and e.get("status") == 0]
    if len(matches) != 1:
        raise ValueError(f"Expected one active endpoint for {alias} / {tag}.")
    endpoint = matches[0]
    needed = {"temperature", "max_tokens", "reasoning", "response_format"}
    if not needed <= set(endpoint.get("supported_parameters", [])):
        raise ValueError(f"Endpoint does not advertise requested controls for {alias}.")
    if endpoint.get("max_completion_tokens") is not None and endpoint["max_completion_tokens"] < p["settings"]["max_tokens"]:
        raise ValueError("Output limit exceeds provider capability.")
    for kind in ("prompt", "completion", "internal_reasoning"):
        if kind == "internal_reasoning" and kind not in endpoint["pricing"]:
            continue
        rate = Decimal(endpoint["pricing"][kind])
        if not rate.is_finite() or rate <= 0:
            raise ValueError("Expected finite positive token prices.")
    if Decimal(str(endpoint["pricing"].get("request", 0))) != 0:
        raise ValueError("This text-only pilot does not support per-request charges.")
    return endpoint


def input_token_reservation(request):
    # A deliberately generous text-only estimate, not provider tokenization.
    # Account for UTF-8 text plus chat/schema framing and leave a fixed margin.
    return len(json.dumps(request, ensure_ascii=False).encode("utf-8")) + 256


def request_cost(request, endpoint, *, output_tokens=None, input_tokens=None):
    pricing = endpoint["pricing"]
    billed_output = request["max_tokens"] if output_tokens is None else output_tokens
    estimated_input = input_token_reservation(request) if input_tokens is None else input_tokens
    output_rate = max(Decimal(pricing["completion"]), Decimal(pricing.get("internal_reasoning", pricing["completion"])))
    return Decimal(estimated_input) * Decimal(pricing["prompt"]) + Decimal(billed_output) * output_rate


def estimate(preview, metadata, *, output_assumptions=None):
    rows = []
    for alias in preview["profiles"]:
        endpoint = select_endpoint(metadata, alias)
        requests = [item["requests"][alias] for item in preview["natural_answers"] + preview["reviewed_diagnostics"] if alias in item["requests"]]
        # Planning assumption: text tokens about characters/3 plus framing.
        inputs = [max(1, (sum(len(m["content"]) for m in r["messages"]) + 2) // 3 + 96) for r in requests]
        output_assumption = (output_assumptions or {}).get(alias, 256 if alias == "flashlite31" else 32)
        expected = sum((request_cost(r, endpoint, output_tokens=output_assumption, input_tokens=n) for r, n in zip(requests, inputs)), Decimal(0))
        reserve = sum((request_cost(r, endpoint) for r in requests), Decimal(0))
        rows.append({"candidate": alias, "model": profile(alias)["model"], "provider_tag": endpoint["tag"],
                     "calls": len(requests), "input_usd_per_million": float(Decimal(endpoint["pricing"]["prompt"]) * 1_000_000),
                     "output_usd_per_million": float(Decimal(endpoint["pricing"]["completion"]) * 1_000_000),
                     "estimated_input_tokens_total": sum(inputs), "assumed_billed_output_tokens_per_call": output_assumption,
                     "max_billed_output_tokens_per_call": profile(alias)["settings"]["max_tokens"],
                     "estimated_input_cost_usd": float(sum(inputs) * Decimal(endpoint["pricing"]["prompt"])),
                     "estimated_output_cost_usd": float(expected - sum(inputs) * Decimal(endpoint["pricing"]["prompt"])),
                     "estimated_cost_usd": float(expected), "conservative_reservation_usd": float(reserve)})
    return {"metadata_fetched_at_utc": metadata["fetched_at_utc"], "breakdown": rows,
            "estimated_total_usd": sum(r["estimated_cost_usd"] for r in rows),
            "conservative_reservation_total_usd": sum(r["conservative_reservation_usd"] for r in rows),
            "note": "Output includes reasoning. Reservations use UTF-8 size plus framing and max output, not guaranteed provider billing. No cache discount assumed.",
            "new_generation_requests": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Fetch free public metadata; no key or generation request.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate", action="append", default=None, choices=("flashlite25", "flashlite31", "deepseek"))
    args = parser.parse_args()
    if not args.fetch:
        parser.error("Choose --fetch for public metadata only.")
    metadata = fetch_metadata(args.candidate or ["flashlite25", "flashlite31", "deepseek"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "fetched_at_utc": metadata["fetched_at_utc"],
                      "models": list(metadata["models"]), "generation_requests": 0}, indent=2))


if __name__ == "__main__":
    main()
