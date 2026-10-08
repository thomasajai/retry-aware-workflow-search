# Bounded 429 recovery and availability check — October 8, 2026

Status: the user requested the implementation and small diagnostic proposal.
All preparation is offline; **the new paid check awaits approval** under the
[spending rule](../README.md#openrouter-spending-rule). No automatic continuation
of either stopped development run is allowed.

## What changed and why

DeepInfra and Venice each served requests before returning DeepSeek upstream
429s with no usage/cost. Stopping on every such error made the broad experiment
fragile. Add explicitly enabled, bounded rate-limit recovery, distinct from the
three mathematical solver attempts. Original prompts, model settings, verifier
selection and independent grading remain fixed.

Recover only an empty HTTP 429 with `error.code=429`, the pinned provider named
in its metadata, and `limit_source=upstream_provider_shared_pool`. Reject
generation evidence, conflicting provider/model identities, malformed or nonzero
usage. Do not retry timeouts, 402/503 errors, platform credit-limit errors,
malformed responses or unknown successful-call billing. Other known technical
failures retain the original workflow handling; missing usage/billing still
halts unless the narrow 429 exception explicitly applies.

The fixed opt-in policy permits at most **two additional physical HTTP
requests for the entire run**, also at most two retries of one logical call.
Backoff is 30 seconds then 60 seconds within a call. Honor the longest advertised
`Retry-After` value, supporting seconds or HTTP dates from the actual HTTP header
and error metadata. A longer delay is honored only up to 60 seconds per cooldown
and 120 seconds total; malformed/excessive delays stop scheduling rather than
being shortened. Retry the exact same request against the same model/provider.
Transport recovery neither consumes a mathematical attempt nor supplies solver
feedback. Exhausted rate-limit recovery is an incomplete infrastructure stop,
not three rejected math answers. Defaults remain zero transport retries.

OpenRouter documents [Retry-After handling](https://github.com/OpenRouterTeam/docs/blob/main/api_reference/errors-and-debugging.mdx)
and warns that some [429 edge cases may incur charges](https://openrouter.ai/blog/insights/reliability-failover/).
These sources support the cooldown and retained-unknown-billing design; the
specific limits above are this project's conservative choices.

## Explicit billing exception to approve

Previously, any missing cost immediately stopped the run. This proposal allows
up to **two eligible 429 calls with unreported billing** to be retried, retaining
each `cost_usd=NULL` and holding its **entire pre-call reservation** against the
new run's cap. Held reservations may total at most **$0.002**. Before waiting or
sending the retry, check known spend + existing held reservations + the new hold
+ the next request's reservation against the approved cap and count every
physical request. Recheck immediately before transmission after cooldown.

The hold is a conservative estimate, **not an actual charge, a zero-cost
classification, or a guaranteed billing maximum**. A successful retry does not
reconcile the failed call. Raw responses, usage and unknown cost remain available
for later review. Any failure outside this exception, third exhausted 429, held
allowance limit or other safeguard stops scheduling. A final unreported error
may therefore remain unknown without an authorized hold; no more calls follow.
Never publish a cost ranking/frontier or an exact mean cost while charges remain
unresolved, even if all final option grades exist. Accuracy and billing coverage
are reported separately.

## Concrete paid scope and purpose

Run `scripts/mathqa_workflow_availability.py` once on **two previously exposed
pilot questions × three repetitions = six executions**, using only
`deepseek-deepseek-deepseek` on Venice and the existing Gemini verifier. IDs:
`mathqa_test_0002` and `mathqa_test_0047`. No Qwen calls, new verifier search,
reserved held-out questions, automatic provider fallback or full sweep follows.
Each execution still permits at most three mathematical solver attempts.

This checks provider responses over several calls and verifies the actual
workflow with bounded recovery if an eligible 429 occurs. Offline simulations
have already exercised recovery; saved responses cannot establish current
provider capacity. A successful small check is evidence of availability during
that window, not a guarantee for 540 executions. If no 429 occurs, report that
live recovery was not exercised. Any broad rerun needs a separate frozen plan
and cost notice.

DeepSeek remains temperature 0.2, reasoning disabled, output cap 512. Gemini
2.5 Flash-Lite remains temperature zero, recomputation/reasoning verifier,
reasoning cap 512 and total output cap 1,024. HTTP calls are serial, with
60-second inactivity timeouts. No automatic run-level resume/restart.

## Advance cost breakdown

Free public metadata refreshed at `2026-10-08T17:50:57.433412+00:00`. Rates and
advertised controls are frozen with explicit provider price ceilings. Sources:
[DeepSeek endpoint metadata](https://openrouter.ai/api/v1/models/deepseek/deepseek-v3.2/endpoints)
and [Gemini endpoint metadata](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash-lite/endpoints).

| Role/model | Provider pin | USD per million input/output | Expected/max logical calls | Estimated input/output tokens | Input cost | Output cost | Expected subtotal |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Solver `deepseek/deepseek-v3.2` | `venice` | $0.26829 / $0.39024 | 12 / 18 | 4,752 / 1,152 | $0.00127491408 | $0.00044955648 | $0.00172447056 |
| Verifier `google/gemini-2.5-flash-lite` | `google-ai-studio` | $0.10 / $0.40 | 12 / 18 | 7,296 / 6,144 | $0.00072960 | $0.00245760 | $0.00318720 |

Expected **24 physical requests / $0.00491167056**, approximately **$0.0049**,
assuming two mathematical attempts per execution and no transport failures.
Maximum **36 logical calls + two shared HTTP retries = 38 physical requests**.
The two retries may belong to either role; they are not two extra for each role.
Maximum individual role exposure is therefore twenty requests, within the
shared thirty-eight-request total.

Conservative full-cap reservations: DeepSeek $0.01086442794, verifier $0.02632500,
and two extra physical calls reserved at the largest stressed quote $0.00292560.
Total **$0.04011502794**. Proposed additional scheduling cap **$0.05**. The $0.002
unreported-429 allowance is **inside** this cap, not an additional budget.

Expected assumptions: 96 solver output tokens and 512 verifier output tokens
including reasoning once, message characters/3 plus 96 framing tokens for
inputs, no cache discount. Gemini reasoning uses its $0.40 output rate.
Reservations use full UTF-8 request size plus 256 framing tokens, full output
caps and an 8,192-character solver calculation for stressed verifier inputs.
Actual usage and billing may differ; next-call checks use the actual request.

These limits apply only to this new check. Prior development attempts remain
**$0.00935117782 known spend plus two unresolved charges**, separate from the new
run's allowance. Approval does not reconcile or erase those charges.

## Storage, compatibility and validation

Add `003_transport.sql` through the existing backed-up, checksummed SQLite
migration mechanism; no Alembic or new dependency. The new
`workflow_transport_calls` table records every physical request before sending,
its response, selected response headers, usage, cost, reservation and cooldown.
Existing `workflow_calls` holds the final response used for parsing/grading.
`workflow_billable_calls` counts physical requests for new retry-enabled calls
and historical logical calls once, avoiding double billing in reports. Existing
attempt/source constraints remain intact. Migration runs on the live database
only as part of the authorized check, after a backup.

Version-three configuration snapshots explicitly freeze the retry policy.
Old version-one/two profile builders and legacy batch defaults match their
pre-change values. Plans bind source and migration hashes, dataset, metadata,
provider settings and schedule. Execution cannot turn retries on using a CLI
override; the frozen plan must include them.

Validation: the full existing/new suite passed **152 offline tests**; after one
additional durability/mathematical-retry test, all **16 focused availability
tests** passed, giving **153 passing tests across those runs**. Simulations cover
solver/verifier recovery, exact retry input, separate mathematical attempts,
physical initiation before HTTP, known-zero versus unknown charges, exhausted
and global retry limits, budget/request guards before cooldown, HTTP dates,
malformed/excessive cooldowns, cancellation, timeouts, profile/source drift,
duplicate plans, independent wrong-option grading and physical request accounting
in sequence/baseline reports. No tests use paid requests or actual cooldown waits.

A migration rehearsal on a database copy preserved every original row and
historical report total, passed integrity/foreign-key checks, and verified that
the billing view does not double-count. The real database remains unchanged.
Ignored audit: `results/workflow_previews/availability-preparation-audit-2026-10-08.json`.

Frozen local plan: `results/workflow_previews/availability-retry-plan-2026-10-08.json`,
SHA-256 `2ec0304ea57c393bbe8334bac301e1099b32d73b03709a40a5afab7c93f1f5e3`.
Metadata must remain under twenty-four hours old; if delayed, refresh and
re-disclose changes before execution. Commit the offline implementation first,
then obtain approval of this check's **$0.05 / 38-request limits and explicit
unknown-429 allowance**. Report actual known spend, unresolved charges, cooldowns,
coverage and what the check establishes at the next checkpoint.
