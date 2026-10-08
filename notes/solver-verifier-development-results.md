# Development evaluation stopped at an upstream error — October 8, 2026

The approved 540-execution evaluation started from clean commit **`203e79b`**
and stopped after **45 requests** when DeepInfra returned HTTP 429 with no
reported cost or usage. Known new spend is **$0.00555908**, plus **one unreported
charge**. Fourteen executions finished, one remains incomplete, and 525 were
unreached. No question completed all twenty-seven configurations. The full
comparison is **incomplete**; no ranking, finalist or accuracy/cost frontier
is reported. Milestone 4 remains open.

The stop respected the frozen policy, not the numeric cap: $3.50 and 3,240
requests were approved. No transport retry, provider fallback, resume or rerun
occurred. The report exporter also exposed a bug on the failed answer; it is
now fixed, with a regression test, and the saved records have been exported
without further API calls.

## Execution evidence and stopping reason

- Run: `e1267ddd-c37a-4439-8327-eefc69d58852`.
- Status: `budget_stopped`; reason: `unknown_cost`.
- UTC start/end: `2026-10-08T17:03:03.519233+00:00` /
  `2026-10-08T17:05:31.784387+00:00` (1:03–1:05 p.m. New York).
- Elapsed: 148.27 seconds. Code revision:
  `203e79b1a5548ccc11540f2f0d0391379b5b38a8`, clean at execution.
- Approved [proposal](solver-verifier-development-proposal.md) and plan SHA-256:
  `9e80da128d3b2f2894d62b1fccd50d918df22c6edc2637774b83f09e00699588`.

The failing call `203f5836-4077-4727-8bdf-0a1522a4f4a4` was a first-slot
DeepSeek V3.2 solver request pinned to `deepinfra/fp4`. It returned HTTP 429,
`provider_error_code=engine_overloaded`, and
`limit_source=upstream_provider_shared_pool` after 0.25 seconds. The response
contains no generation ID, usage, returned model, or reported charge. There
is no per-generation lookup ID for reconciling this request. The absence of a
billable completion does not establish a measured zero charge.

[OpenRouter's guidance](https://openrouter.ai/blog/insights/reliability-failover/)
describes failed requests as normally unbilled but identifies exceptions for
some 429 responses and partial outputs, recommending an activity-log check.
Keep this charge unknown; do not infer zero from HTTP status or count the
per-call reservation ($0.00058196) as the actual charge. This request's failure
is an infrastructure event, not a mathematical rejection.

## Actual requests and known spend

| Role/model | Provider | Requests | Completed / failed | Known cost | Unknown charges | Input tokens | Output including reasoning |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| Qwen2.5 7B solver | Phala | 5 | 5 / 0 | $0.00017850 | 0 | 1,515 | 135 |
| Qwen3 32B solver | SiliconFlow | 8 | 8 / 0 | $0.00048212 | 0 | 2,320 | 276 |
| DeepSeek V3.2 solver | DeepInfra | 10 | 9 / 1 | $0.00061446 | 1 | 2,241 known | 434 known |
| Gemini 2.5 Flash-Lite verifier | Google AI Studio | 22 | 22 / 0 | $0.00428400 | 0 | 6,884 | 8,989 |
| Total | | **45** | **44 / 1** | **$0.00555908** | **1** | **12,960 known** | **9,834 known** |

Gemini reported 8,934 reasoning tokens within its total output, counted once.
All forty-four successful calls returned the expected model/provider, HTTP 200
and `stop`, with known usage and charges within per-call reservations. All
twenty-two solver answers from successful calls were usable. No verifier output
failed its Boolean contract. No missing usage is filled with zero in the source.

Total known workflow spend, including prior screening/pilot runs, is
**$0.01589450 across 146 requests**, with one unknown charge. This is not the
total spend of legacy batch experiments. The expected $0.39651192 was for a
complete evaluation; stopping early explains most of the smaller known charge.

## Partial observations, separate from a configuration comparison

Only the first scheduled question, `mathqa_test_0435`, was reached. Fourteen
different sequences finished on it: thirteen accepted the key-correct option;
`qwen25-qwen25-qwen25` exhausted all three rejections and scored zero. Its
three rejected options all matched the key, but the agreed workflow rule still
scores an execution without an accepted answer as zero. The fifteenth execution
`deepseek-qwen25-qwen25` was budget-stopped at its first solver call and has no
final grade. The remaining sequences/questions have no observations.

There were thirteen verifier acceptances and nine rejections, all judged against
usable solver proposals selecting the key's option c, 60000. Six finished
executions rejected their first proposal; five later accepted a key-correct
answer and one exhausted. All eight usable retries repeated a prior option/value.
This confirms that fresh requests with a small non-zero temperature do not
guarantee a different proposed answer.

The counts above describe one question and incomplete configuration coverage.
They are not a twenty-question accuracy estimate, a baseline comparison, a
verifier population error rate, or evidence of a winning sequence. Report
rankings and the frontier remain null. All stored reasoning-validity grades
remain unknown, independently of option grading.

## Question assumptions and verifier behavior

The question gives x's investment as 40000 and a profit-sharing ratio 2:3,
asking y's investment. Under the intended textbook convention of equal
investment duration and profit proportional to capital, y invests
`40000*3/2=60000`, matching option c. The question does not explicitly state
that duration or allocation rule; without it the initial capital is not uniquely
determined. That is a material interpretation ambiguity.

All twenty-two displayed calculations are arithmetically consistent with the
intended convention. Gemini nevertheless rejected all five Qwen2.5 proposals
`40000*3/2`, three Qwen3 proposals `(40000 * 3) / 2 = 60000`, and one DeepSeek
proposal equating the investment/profit ratios. It accepted other equivalent
proposals. Saved verifier explanations for the first rejected examples question
the unstated profit-to-investment assumption; accepted examples adopt it.

This is an assistant review of saved evidence, not a human annotation or a
causal explanation of every verdict. Do not label nine key-correct rejections
as nine proven false rejections without deciding how the dataset convention and
unstated assumptions should be judged. Preserve the question, decisions and
scores; do not silently exclude it, rewrite prompts, or reopen model selection.
Gemini remains the user's provisional fixed verifier.

## Reporter repair and audit

The failed attempt correctly stored `usable=0` and JSON `null` as its parsed
fields. The repeat-answer reporter treated the nonempty string `"null"` as
parsed fields and tried to index the decoded `None`. Restricting that metric
to usable attempts fixes the exporter and its denominator. The error occurred
after the run was safely stopped and all calls were durably recorded.

A mocked HTTP 429 regression now verifies unknown billing, JSON null fields,
zero usable retries and no ranking. All **133 offline tests pass**, including
ten evaluation tests. There are no further paid calls during repair or audit.

The read-only audit independently recomputed every reached attempt/final option
grade from the dataset and reconstructed every request from the original frozen
question, profile and price ceiling. It confirms:

- Exact request reconstruction with no feedback, answer key or review-label leak.
- No calls after acceptance; at most three reached solver slots per execution.
- Fourteen final grades and none for the interrupted execution; missing scores
  were not imputed or converted into mathematical failures.
- All prior workflow records and legacy tables unchanged; integrity `ok`, zero
  foreign-key errors, zero active calls. Audit itself leaves the database unchanged.
- Original plan/profile/schedule validation against the run's committed source
  revision. The current source adds only the post-stop reporting repair; the
  historical frozen plan cannot be executed under changed source hashes.

Ignored artifacts under `results/workflow_previews/`:

- `evaluation-development-approved-2026-10-08.json`, original frozen plan.
- `development-evaluation-report-2026-10-08.json`, recovered partial summary.
- `development-before-audit-2026-10-08.json` and
  `development-after-audit-2026-10-08.json`, fingerprints and complete reached traces.
- Raw calls/grades remain in `results/mathqa_runs.sqlite3`.
- Pre-run database backup: `results/backups/development-before-2026-10-08.sqlite3`.

## Next checkpoint

Address the DeepInfra shared-pool failure before paying for another broad
evaluation. Current free metadata advertises other active DeepSeek endpoints;
Venice is one compatible candidate at $0.26829 input / $0.39024 output per
million tokens. Availability and control advertising are not evidence of reliable
live service. A different pin requires a new frozen profile and costed plan;
do not silently mix providers into this stopped configuration run.

Keep the known/unknown billing distinction and preserve the partial evidence.
Any paid continuation or rerun needs a new advance notice and authorization
under the explicit no-automatic-resume policy. No continuation has been scheduled.
