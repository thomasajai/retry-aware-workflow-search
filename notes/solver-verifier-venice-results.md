# Venice development run stopped at an upstream 429 — October 8, 2026

The user approved the [Venice proposal](solver-verifier-venice-proposal.md) with
a $3.50 cap and 3,240 maximum requests. The single run stopped after **29
requests** because Venice returned a DeepSeek rate-limit error with no reported
usage or cost. Known additional spend is **$0.00379209782**, plus **one unresolved
charge**. This is an unknown-billing safeguard stop, not exhaustion of the dollar
cap. No automatic retry, provider fallback, restart or additional paid diagnostic
occurred. Milestone 4 remains open.

## Frozen execution and scope

- Run ID: `54628295-8859-493c-9b8f-fe8270d51704`.
- Code commit: `63965d401bcd3b8ac34fd18ecac7acff19c52485`; clean working tree at start.
- Plan SHA-256: `a24147002ebe7f2205bcccf049db44c15caabf1b174507ec7227b21161c8ee08`.
- Started `2026-10-08T17:26:24.837969+00:00`; stopped
  `2026-10-08T17:27:39.608098+00:00`; wall time 74.770129 seconds.
- Status `budget_stopped`, reason `unknown_cost`.
- Planned twenty questions × twenty-seven sequences = 540 executions; ten
  finished, one incomplete, 529 unreached. No complete question block.

All ten finished executions were accepted and independently scored one. These
observations cover only `mathqa_test_0435`, not the planned question distribution.
No final sequence ranking, accuracy/cost frontier or winner is reported. All
other per-sequence and baseline coverage remains visibly incomplete.

## Actual spending and failure

| Role/model | Requests | Known input tokens | Known output tokens | Reasoning within output | Known spend |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5 solver / Phala | 1 | 303 | 27 | 0 | $0.00003570 |
| Qwen3 solver / SiliconFlow | 7 | 2,030 | 235 | 0 | $0.00041815 |
| DeepSeek solver / Venice | 7 (six successful) | 1,494 | 279 | 0 | $0.00042124782 |
| Gemini verifier / Google AI Studio | 14 | 4,366 | 6,201 | 6,168 | $0.00291700 |
| Total | 29 | 8,193 | 6,742 | 6,168 | $0.00379209782 |

Token totals and known spend exclude the failed call's unreported usage/charge.
The expected $0.398 estimate applied to all 540 executions; this partial run's
cost cannot be extrapolated as a comparison result. Together with the previous
[DeepInfra attempt](solver-verifier-development-results.md), the two development
runs consumed **$0.00935117782 known spend plus two unresolved charges**.

Failed solver call `eecf5952-e1ee-4e27-a516-c460ee9cd833` was the second slot of
`qwen3-deepseek-deepseek`. It returned HTTP 429 after approximately 0.155 seconds.
Error metadata identifies `Venice`, `limit_source=upstream_provider_shared_pool`,
and `Retry-After: 30`. It supplied no generation ID, model/provider usage or cost.
The saved pre-call reservation of $0.00059928669 is an estimate, **not a reported
charge or a guarantee**. The runner preserved the error, made no verifier call
for its unusable output, and stopped all further scheduling. The incomplete
execution has no final grade, even though its rejected first option matched the
dataset key. No identifier is available for a per-generation billing lookup.

Venice successfully served six earlier DeepSeek calls with the expected model,
provider and reasoning-off controls. The failure therefore does not establish
that the endpoint is entirely unavailable. The public active status advertised
compatibility; it did not guarantee sustained capacity.

## Solver/verifier observations

There were fourteen usable answers and fourteen verifier judgments: ten accepts
and four rejects. Every usable answer selected `c`, value `60000`, matching the
dataset key. Three finished executions recovered after an initial rejection;
their retries repeated the same option/value. The fourth rejection led to the
incomplete execution stopped on the next solver call. No rejected fallback was
accepted or graded as final.

As in the prior run, this investment/profit question omits an explicit statement
about equal investment duration or profit proportional to capital. The usual
textbook convention produces the key, while a literal reading is underdetermined.
Do not label these four key-matching rejections as proven reasoning errors by
the verifier. Do not infer reasoning validity from ten key-matching acceptances,
and do not tune the prompt or remove the question after these observations.
Gemini and the full twenty-question selection remain unchanged.

## Preservation and validation

All 136 offline tests passed before execution. This run required no code repair.
The read-only postflight audit reconstructs every solver and verifier request,
including the provider pin and price ceilings; independently recomputes every
attempt/final option grade; confirms early acceptance and maximum three slots;
checks reported usage, provider identity and reservations for completed calls;
and confirms incomplete scores/rankings are absent. Database integrity is `ok`,
foreign-key checks are clear, and all pre-existing rows are unchanged.

Ignored local artifacts under `results/workflow_previews/`:

- `venice-evaluation-report-2026-10-08.json`.
- `venice-before-audit-2026-10-08.json` and `venice-after-audit-2026-10-08.json`.
- `venice_preflight_20261008.py`, `venice_progress_20261008.py`, and
  `venice_postflight_20261008.py`.

Pre-run backup: `results/backups/venice-before-2026-10-08.sqlite3`. The backup and
prior run are preserved, and audit reads do not mutate the live database.

## Next checkpoint

Both provider pins have now encountered upstream 429s. Another broad rerun with
a different pin would again use the full experiment as an availability test.
First design explicit cooldown and bounded transport retries, with an approved
policy for unresolved billing. Preserve unknown actual charges separately and
reserve any allowed uncertain exposure; do not assume errors cost zero, weaken
the cap, or automatically resume these terminal runs. Transport retries must
remain distinct from the three mathematical solver attempts.

Then propose a small availability diagnostic with its own call count, rate,
estimated spend and cap before paid execution. No new provider/model, retry
policy, diagnostic, or rerun is authorized by the completed single-run approval.
Continue with the fixed Gemini verifier; this failure concerns infrastructure.
