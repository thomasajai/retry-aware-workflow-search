# Verifier comparison checkpoint — October 7, 2026, New York

The user approved the [frozen comparison](solver-verifier-comparison-proposal.md)
with a $0.25 cap and at most 189 new requests. It stopped after **five new
verifier calls**, spending **$0.00136376**. The remaining 184 requests were not
made. No solver calls, transport retries, or automatic continuation occurred.
Milestone 2 remains open; there is insufficient coverage to select a verifier.

## Why it stopped

DeepSeek V3.2 with reasoning enabled took 109.06 seconds, exhausted its
2,048-token output cap, and returned no Boolean verdict. Its usage reported
2,092 reasoning tokens against 2,048 total completion tokens. The
`inconsistent_reasoning_usage` guard stopped scheduling immediately; the
response is also a truncation error, excluded from mathematical quality counts.
The stop status is `budget_stopped`, but the numeric spending cap was not
reached. This status also covers measurement guards.

A separate authenticated **GET of generation metadata**, with no generation
request, confirmed the $0.00082374 charge, `length` finish reason, and the same
inconsistent native token counts. The metadata also supplies a separate
normalized completion count of 2,092. Preserve these distinctions; do not
silently replace the original usage or disable the guard. The response's
reported cost is known and within its reservation.

The configured HTTP timeout is an inactivity timeout, not an absolute wall-time
deadline. This call demonstrates that distinction. A strict elapsed-time limit
and durable handling of a request whose billing is still pending should be
considered before another reasoning-enabled live experiment.

## Observed results and cost

All five new calls concern the first inspected development question,
`mathqa_test_0002`. Nine exact baseline judgments were reused from the pilot,
with their historical expense excluded from this run. None of the seven
expansion questions was reached.

| New profile | Reviewed proposal | Verdict / outcome | Reported cost | Seconds |
| --- | --- | --- | ---: | ---: |
| Gemini 2.5 Flash-Lite, recompute plus reasoning | Valid | Accepted correctly | $0.00017520 | 2.24 |
| Gemini 2.5 Flash-Lite, recompute | Valid | **False rejection** | $0.00003120 | 0.37 |
| DeepSeek V3.2, recompute | Invalid | Rejected correctly | $0.00007312 | 1.60 |
| Gemini 3.1 Flash-Lite, recompute plus reasoning | Invalid | **False acceptance** | $0.00026050 | 1.00 |
| DeepSeek V3.2, recompute plus reasoning | Invalid | No usable verdict; truncated | $0.00082374 | 109.06 |
| Total | | Five new calls | **$0.00136376** | |

The valid proposal calculates 30 stations and 870 directed tickets. The rejected
invalid proposal uses `28*(28-1)/2=380`; the falsely accepted invalid proposal
uses `(28+2)*(28+1)/2=380`. Both are wrong in interpretation and arithmetic.
Labels are independent assistant reviews, not human annotations.

The observed false acceptance shows that this extra reasoning allowance does
not eliminate verifier mistakes. Each changed profile has only one observation
at most, so these results cannot rank models or estimate their general error
rates. The failed request is a technical error, not a mathematical rejection.

Known verifier-selection spend so far is **$0.00300343**: $0.00163967 for the
completed pilot plus $0.00136376 for this stopped comparison. All 41 actual
requests have known reported costs. Total wall time for this comparison was
114.74 seconds.

## Audit and next checkpoint

The read-only audit confirmed five finished calls and no active calls, zero new
solver calls, and no final workflow scores assigned. Database integrity and
foreign-key checks pass. All six legacy batch tables match the pre-screening
backup exactly. The 82 offline tests passed before execution; this checkpoint
changes documentation only and does not add another paid run.

Recommended next step: prepare an amended comparison offline that excludes
DeepSeek's reasoning-enabled profile and reuses the nine original baseline
judgments plus the four valid new verdicts. This would leave 163 new requests
for eight profiles across the same 22 usable proposals. That is a proposed
scope that initially needed support for multiple explicit reuse sources and a
selected profile subset. Following the user's instruction to proceed, the
[amended comparison](solver-verifier-comparison-amended-proposal.md) is now
implemented and validated offline, with fresh metadata, 89 passing tests,
estimated cost $0.03962351, and proposed $0.22 cap. The user approved the proposal;
the [amended run](solver-verifier-comparison-amended-results.md) stopped after
forty new calls costing $0.00483675 when DeepSeek recompute truncated without a
verdict. Do not rerun the original plan or increase the
failed profile's token limit automatically.

Artifacts retained under ignored `results/workflow_previews/`:

- Frozen plan: `verifier-comparison-2026-10-07.json`.
- Plan SHA-256: `a881986fca6e05dc0596aa00c618d986d6b6de2c282fa77338ef4e4b9a5038e9`.
- Run: `f551e8d9-e2b1-4214-b17b-03c520cb25fc`.
- Partial report: `verifier-comparison-2026-10-07-results.json`.
- Billing/storage audit: `verifier-comparison-2026-10-07-audit.json`.

Generation metadata API reference:
[OpenRouter generation metadata](https://openrouter.ai/docs/api/api-reference/generations/get-request-&-usage-metadata-for-a-generation).
