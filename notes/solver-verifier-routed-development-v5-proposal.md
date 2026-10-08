# Routed development comparison v5 — fresh-run proposal, October 8, 2026

Status: prepared and tested offline; **paid approval is pending** for one new
run with a **$4.25 cap and 3,240 maximum gateway requests**. The preceding
approval was consumed by the [stopped v4 run](solver-verifier-routed-development-results.md).
No further model calls have run. Follow the [OpenRouter spending rule](../README.md#openrouter-spending-rule).

## Purpose and policy amendment

Complete the balanced 27-configuration development comparison without stopping
globally on an unusable solver answer whose billing and identity are fully
reconciled. Offline reuse established the truncation-handling repair; fresh
calls are needed to measure all configurations under one consistent policy.
Start a separate run, with **20 unchanged development questions × 27 ordered
solver sequences × one repetition = 540 executions**. Do not resume, pool or
reuse the 59 old scores as new observations. The selected questions and shuffled
schedule exactly match the original comparison, including the flagged
`mathqa_test_0187` option/key inconsistency. No held-out question is included.

The opt-in `solver_truncation_unusable` policy requires HTTP 200, failed
`IncompleteGeneration`, and `finish_reason=length` on a **solver** call. All
existing model/provider, finite billing, consistent usage, reasoning, price,
reservation and run-budget checks run before continuation. Only this narrow
case becomes an unusable mathematical attempt. Preserve its failed call, raw
partial text, request count and reported cost. Never send partial output to
the verifier. If a slot remains, send the next solver only the original question
and choices; after three rejected/unusable attempts, score zero and move to the
next execution. This adds no client HTTP retry and no fourth attempt.

Verifier truncation, gateway errors, unknown cost, inconsistent/missing usage,
unexpected model/provider and price/reservation overruns still stop scheduling.
No token increase, automatic resume or fallback outside the frozen routing
policy. V1–v4 defaults remain unchanged. New configuration and evaluation plan
versions are v5; execution cannot override this frozen policy.

Models, provider controls, prompts, sampling and output limits are unchanged:

- Qwen2.5 7B/Phala and Qwen3 32B/SiliconFlow fp8 solvers.
- DeepSeek V3.2 with automatic OpenRouter routing, required parameter support,
  provider fallbacks, and $0.60/$1.70 per-million input/output price ceilings.
  Recognize all ten frozen compatible providers, require one active at
  preflight, and record the actual provider returned.
- All solvers: temperature 0.2, output cap 512.
- Gemini 2.5 Flash-Lite/Google AI Studio verifier: recomputation plus reasoning,
  temperature zero, reasoning cap 512, total output cap 1,024. It remains
  provisional; prior false rejections and acceptances are not erased.
- At most three mathematical attempts, original-input-only retries, acceptance
  requiring reasoning and option, independent answer-key grading kept separate.
- Serial calls, 60-second inactivity timeouts, zero client network retries and
  zero unknown-cost continuation allowance. Internal OpenRouter provider tries
  are not observable or separately bounded by the client request counter.

## Advance cost breakdown

USD per million input/output tokens. DeepSeek is budgeted at its routing
ceilings to cover expensive fallback providers, without a cache discount.
Public metadata was fetched free at **18:57:33 UTC on October 8**; the same
rates, limits and cost preview remain frozen. Execution requires metadata less
than 24 hours old; a delayed run needs refreshed metadata and a new plan/notice.

| Role/model | Provider | Input/output rates | Expected/max requests | Estimated input/output tokens | Input subtotal | Output subtotal | Expected total |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5 7B | Phala | $0.10 / $0.20 | 360 / 540 | 140,652 / 34,560 | $0.01406520 | $0.00691200 | $0.02097720 |
| Qwen3 32B | SiliconFlow/fp8 | $0.14 / $0.57 | 360 / 540 | 141,840 / 34,560 | $0.01985760 | $0.01969920 | $0.03955680 |
| DeepSeek V3.2 | automatic; ceiling rates | $0.60 / $1.70 | 360 / 540 | 140,652 / 34,560 | $0.08439120 | $0.05875200 | $0.14314320 |
| Gemini 2.5 Flash-Lite verifier | Google AI Studio | $0.10 / $0.40 | 1,080 / 1,620 | 650,916 / 552,960 | $0.06509160 | $0.22118400 | $0.28627560 |

Expected total **$0.48995280 (about $0.49)** for **2,160 requests**. Maximum
**3,240 gateway requests**: 1,620 solver and 1,620 verifier calls if all three
slots are reached and usable. Estimate assumptions: two reached slots per
execution, 96 solver output tokens, 512 verifier output tokens including
reasoning once, input message characters/3 plus 96 framing tokens, no cache
discount. Acceptance and cheaper providers may reduce spend; more retries and
longer output may increase it.

| Role | Conservative full-cap reservation |
| --- | ---: |
| Qwen2.5 | $0.13365810 |
| Qwen3 | $0.31114854 |
| DeepSeek | $0.94342860 |
| Gemini verifier | $2.36684430 |
| **Total** | **$3.75507954** |

The **$4.25 scheduling cap** includes all three slots, full output caps, full
UTF-8 request size plus 256 framing tokens, and an 8,192-character calculation
for stressed verifier inputs, with 10% margin rounded up to a quarter dollar.
It is permission up to a limit, not a spending target or billing guarantee.
Before every request, recorded spend plus its reservation must fit the cap.
Any unknown charge stops further scheduling; failed requests are not assumed
free. The preceding run's $0.0284535204 spend is separate from this proposed
limit. Five older unresolved charges remain separately recorded.

Duration may be one to two hours, with substantial latency/retry uncertainty.
Report progress throughout execution and at each complete question block. No
automatic follow-up, rerun, held-out stage or new verifier experiment.

## Validation, records and reporting

All **174 offline tests pass** (137.015 seconds), including known truncation
followed by an exact original-input retry, three truncations scoring zero,
continuation to another execution, final-slot exhaustion, request-limit
enforcement, retained costs/raw output, old-policy preservation, and failures
for verifier truncation, unknown billing, identity drift and output overruns.
Old configuration builders match their committed v1–v4 snapshots. No database
migration or dependency change is required.

The read-only preparation audit confirms identical questions/schedule and cost
arithmetic, balanced sequences, unchanged prompts/sampling/verifier/routing,
unexposed reserved questions, SQLite integrity/foreign keys, and unchanged
database fingerprints. It validates the frozen plan and makes zero generation
requests. The prior run has its own independently passing historical audit.

Frozen plan:
`results/workflow_previews/routed-development-v5-plan-2026-10-08.json`.
SHA-256:
`c8afff2663e82c7d58476d567134eb1945215200707161173d413acef6fcf365`.
It binds metadata, dataset, source hashes, all three migration hashes, controls,
prices, split, schedule and the new policy. Local audit:
`results/workflow_previews/routed-development-v5-preparation-audit-2026-10-08.json`.
Commit the implementation and documentation before any approved execution,
then verify the frozen plan and take a database backup.

Report independent answer-key averages separately from acceptance and reasoning
reviews, coverage, cost, latency, attempts, repeated answers, recovery and
observed providers. Reuse this run's first-slot generations for baseline
diagnostics with zero additional calls. Full rankings/frontier require all
540 scores and reconciled billing; incomplete coverage gets completed-only
means without imputed scores. Keep the existing Wilson/paired question-block
bootstrap uncertainty policy and development-selection caveats. At completion
or first guard stop, audit and commit the checkpoint. Milestone 4 remains open;
finalist evaluation requires separate review and paid approval.
