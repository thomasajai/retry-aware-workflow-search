# Routed 27-configuration development comparison — October 8, 2026

Status: the user approved this single $4.25 / 3,240-request comparison. The
[run stopped](solver-verifier-routed-development-results.md) after 223 requests
and $0.0284535204 reported spend when a fully billed solver answer truncated.
There are no new unknown charges; 59 of 540 executions were graded. This
approval is consumed. The [v5 amendment and fresh-run proposal](solver-verifier-routed-development-v5-proposal.md)
awaits separate approval under the
[OpenRouter spending rule](../README.md#openrouter-spending-rule).

## Purpose and scope

Measure average independently graded accuracy, reported cost, latency,
acceptance, and retries for every ordered three-solver assignment. Use the same
**20 development questions × 27 configurations × one repetition = 540
executions** as the prior stopped comparisons. Every configuration answers every
question with fresh model calls. This supplies a development reference for
later search-method experiments; no shared-prefix reuse, new verifier search or
automatic finalist selection.

Solvers remain Qwen2.5 7B, Qwen3 32B and DeepSeek V3.2. Every slot uses
temperature 0.2 and output cap 512, retaining the existing prompt, response
contract and other sampling/reasoning controls. DeepSeek uses the successful
automatic routing policy with fixed $0.60/$1.70 input/output price ceilings per
million tokens, required parameter support and provider fallbacks. Qwen2.5
remains pinned to Phala; Qwen3 remains pinned to SiliconFlow/fp8. Gemini 2.5
Flash-Lite remains the fixed Google AI Studio recomputation/reasoning verifier:
temperature zero, reasoning cap 512, total output cap 1,024.

Each execution has at most three mathematical attempts. Rejected/unusable
answers advance; retries receive the original question/options only. Acceptance
stops immediately. Three rejected attempts score zero. Score one requires an
accepted final option matching the independent MathQA key. Verifier acceptance
and independent correctness remain separate, with separate reasoning reviews.
The small routed check observed a false rejection of valid work, so a perfect
verifier is not assumed and recovery does not erase that error.

Question selection seed `20261007`, schedule seed `20261008`, all question IDs,
question-block ordering and within-block configuration ordering match the
original approved development plan. Do not replace difficult or ambiguous
questions in response to observed performance. Exact IDs:

```text
mathqa_test_0435  mathqa_test_0661  mathqa_test_0187  mathqa_test_0566
mathqa_test_1092  mathqa_test_1096  mathqa_test_1292  mathqa_test_1076
mathqa_test_1408  mathqa_test_0237  mathqa_test_0515  mathqa_test_0284
mathqa_test_0952  mathqa_test_1029  mathqa_test_1455  mathqa_test_0260
mathqa_test_0902  mathqa_test_0013  mathqa_test_1105  mathqa_test_0383
```

These questions come from the first hundred records, excluding the two pilot
questions, and already have legacy development exposure. The last hundred
remain reserved for later finalist evaluation; no recorded calls expose them.
This is a record-based exposure audit, not a guarantee against unrecorded
inspection. One observation per configuration/question is noisy; close results
are not evidence of a reliable winner.

## Routing and technical safeguards

Calls are serial, with 60-second inactivity timeouts and **zero client network
retries**. The maximum below counts client HTTP requests to OpenRouter. Its
internal provider attempts are not separately observable or bounded by our
request counter. No unknown-cost continuation/held reservation allowance is
enabled. Missing billing/usage, unexpected provider/model, inconsistent usage,
price/reservation overruns or gateway failures stop the run as incomplete.
No automatic restart, resume, token increase or model change follows.

Fresh public metadata at **2026-10-08 18:57:33 UTC (2:57:33 p.m. EDT)** lists
seven active compatible DeepSeek providers under the ceilings: Baidu,
DeepInfra, DigitalOcean, Friendli, Google, SiliconFlow and Venice. It also lists
three temporarily inactive compatible providers: Alibaba, AtlasCloud and
GMICloud. Save capabilities, advertised prices, status and quantization for all
ten; record the provider actually returned for each call.

Provider status changed between the small check and this refresh. The response
audit therefore recognizes **known compatible providers even if temporarily
inactive at preflight**, so they can return when available without stopping a
long run solely because of a stale status. At least one compatible provider
must be active at preflight. Unsupported controls/output limits, invalid prices,
nonzero per-request fees, and prices above the ceiling remain excluded. An
unknown provider name still stops scheduling. This changes response recognition,
not the outgoing routing policy, price limits, prompts or retry rules.

Default OpenRouter routing may vary the provider and quantization between
calls. Results describe DeepSeek under this fixed routing policy rather than a
single endpoint. Account routing settings and upstream capacity can still
restrict availability. See [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection).
Public price/capability sources are saved in the frozen metadata:
[Qwen2.5](https://openrouter.ai/api/v1/models/qwen/qwen-2.5-7b-instruct/endpoints),
[Qwen3](https://openrouter.ai/api/v1/models/qwen/qwen3-32b/endpoints),
[DeepSeek](https://openrouter.ai/api/v1/models/deepseek/deepseek-v3.2/endpoints),
[Gemini](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash-lite/endpoints).

## Advance cost breakdown

USD per million input/output tokens; DeepSeek uses its **routing ceilings** for
estimation and reservations, not the cheapest available provider. This accounts
for a more expensive fallback. Expected/max counts include mathematical retries.

| Role/model | Provider policy | Input/output rates | Expected/max requests | Estimated input/output tokens | Input subtotal | Output subtotal | Expected role total |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5 7B solver | Phala pin | $0.10 / $0.20 | 360 / 540 | 140,652 / 34,560 | $0.01406520 | $0.00691200 | $0.02097720 |
| Qwen3 32B solver | SiliconFlow/fp8 pin | $0.14 / $0.57 | 360 / 540 | 141,840 / 34,560 | $0.01985760 | $0.01969920 | $0.03955680 |
| DeepSeek V3.2 solver | automatic; ceiling rates | $0.60 / $1.70 | 360 / 540 | 140,652 / 34,560 | $0.08439120 | $0.05875200 | $0.14314320 |
| Gemini 2.5 Flash-Lite verifier | Google AI Studio pin | $0.10 / $0.40 | 1,080 / 1,620 | 650,916 / 552,960 | $0.06509160 | $0.22118400 | $0.28627560 |

Estimated total **$0.48995280**, approximately **$0.49**, for **2,160 gateway
requests**. Maximum **3,240 gateway requests**, covering all three attempts of
all 540 executions: 1,620 solver and 1,620 verifier calls. No additional client
HTTP retry calls. Assume two mathematical slots reached per execution, 96
solver output tokens, 512 verifier output tokens including reasoning once,
message characters/3 plus 96 framing tokens for inputs, and no cache discount.
Early acceptance or cheaper DeepSeek providers can reduce cost; deeper retries
and longer outputs can increase it.

Conservative full-cap reservations:

| Role | Reservation |
| --- | ---: |
| Qwen2.5 | $0.13365810 |
| Qwen3 | $0.31114854 |
| DeepSeek | $0.94342860 |
| Gemini verifier | $2.36684430 |
| **Total** | **$3.75507954** |

Proposed scheduling cap **$4.25**. This reserves for all three attempts, full
output caps, full UTF-8 request size plus 256 framing tokens, and an
8,192-character calculation for stressed verifier inputs. The builder adds
10% and rounds up to a quarter dollar. These stress assumptions explain the
difference from the $0.49 estimate; the cap is permission up to that limit,
not a spending target or a guarantee of provider billing.

Before every request, recorded new spend plus its conservative reservation
must fit the approved cap. Unknown billing stops further scheduling and remains
unresolved; no failed request is assumed free. These limits cover only this new
run. Across the four prior development/availability runs, known costs remain
**$0.01190422829 plus five unresolved charges**, separate from the proposed new
cap and not a whole-project/account total.

Rough duration is **one to two hours**, with substantial uncertainty from
provider latency and retry depth. The small check averaged about 2.7 seconds
per request, but it used only two relatively simple questions. This is not a
runtime guarantee. Progress is reported after each complete question block;
the user can stop execution earlier.

## Reporting and checkpoint

Report each configuration's average independent answer-key score, acceptance
coverage, reported cost per execution, latency, attempts and requests, along
with provider-level counts/spend, repeated answers and recovery after rejection.
Full rankings and the descriptive accuracy/cost Pareto frontier require all
540 scores and complete reported billing. An incomplete run retains costs and
coverage with explicitly completed-only means; it gets no final ranking or
imputed scores. Do not pool prior stopped runs into the new comparison.

Reuse this run's fresh first-slot generations for one-attempt diagnostics:
nine initial generations per model/question, 180 per solver, with **zero
additional paid calls**. Historical outputs do not replace new solver attempts.
Use Wilson accuracy intervals and 1,000 paired question-block bootstrap
resamples, seed `20261009`, for descriptive uncertainty. The observed top
configuration is selected on the same twenty questions; this does not prove a
universal winner or support multiple-comparison significance claims.

At completion or the first technical/budget stop, report costs, unresolved
charges, coverage and results, and commit the checkpoint. Review the comparison
before choosing finalists, repeats or held-out scope. Any follow-up paid stage
requires its own cost proposal and approval. Milestone 4 remains open until the
comparison and separately authorized finalist assessment are handled.

## Frozen artifacts and validation

Final execution plan:
`results/workflow_previews/routed-development-final-plan-2026-10-08.json`.
SHA-256:
`c4b21c8648a92095120120b97822b5c75c75a38380dc703041e9e7edcf4e1581`.
The earlier provisional plan is preserved and is not the plan proposed for
execution. Metadata, dataset, eleven source files, controls,
prices, split and schedule are frozen. The paid command cannot override routing
or rerun a used plan. Metadata must be less than twenty-four hours old at
execution; refresh and re-disclose a new plan if delayed.

The read-only preparation audit independently checks cost arithmetic, sums and
cap, all 27 balanced sequences, unchanged original questions/schedule, solver
prompts/sampling, fixed verifier, original-only retry policy, recorded held-out
exposure, database fingerprints, integrity and foreign keys. It confirms zero
new generation requests and preserves the prior stopped/completed runs. Local
audit: `results/workflow_previews/routed-development-final-preparation-audit-2026-10-08.json`.

All **166 offline tests pass** (106.533 seconds), including thirteen focused
routing tests and a new case in which a known
compatible provider becomes available after being inactive at preflight, and
rejection of a plan with no active compatible provider. The frozen final plan
validates after regression verification.
No database migration or dependency change is needed.
