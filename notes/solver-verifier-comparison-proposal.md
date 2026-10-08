# Verifier recomputation comparison — 2026-10-07, New York

The user approved this frozen comparison with a $0.25 cap and 189 requests
maximum. It stopped after five new calls costing **$0.00136376**, when DeepSeek's
reasoning profile returned a truncated response with inconsistent token usage.
See the [partial results and audit](solver-verifier-comparison-results.md).
The original proposal below records the authorized scope; no automatic
continuation is authorized. **82 offline tests passed** before execution.

## Design and scope

Compare three variants within each of the same three models:

1. **Baseline:** the original prompt and settings, unchanged.
2. **Recompute:** derive the answer independently, then audit every equality,
   interpretation, and option/value mapping. Only the prompt changes.
3. **Recompute plus reasoning:** the same new prompt with more reasoning
   allowance and a larger total output limit. This measures the additional
   allowance as a bundle, not the causal effect of reasoning effort alone.

Every variant returns the same single-Boolean verdict. No key, review
explanation, previous verdict, or failure-specific example enters its input.
The new prompt is generic and contains no train-ticket answer. Prompts,
providers, reasoning settings, token limits, and scheduling seed are frozen.

| Model / provider pin | Baseline and recompute reasoning / total output cap | Recompute plus reasoning / total output cap |
| --- | --- | --- |
| Gemini 2.5 Flash-Lite / `google-ai-studio` | Disabled / 256 | Thinking budget 512 / 1,024 |
| Gemini 3.1 Flash-Lite / `google-ai-studio` | Minimal effort / 1,024 | Low effort / 2,048 |
| DeepSeek V3.2 / `deepinfra/fp4` | Disabled / 256 | Enabled / 2,048 |

Google documents 512 as Gemini 2.5 Flash-Lite's minimum enabled thinking
budget. The public OpenRouter catalog advertises low effort for Gemini 3.1.
DeepSeek's catalog advertises enable/disable without an effort selector, so
its profile bounds total output rather than claiming an exact thinking budget.
These allowances differ across models; actual usage and completeness must be
measured. The pinned endpoints advertise the requested controls, but live
behavior of the new settings is untested.

Use the first eight development questions from source solver batch
`6e8ba4fd-3f6d-41f9-9522-23c84e0d332d`: `mathqa_test_0002`,
`mathqa_test_0013`, `mathqa_test_0026`, `mathqa_test_0047`,
`mathqa_test_0079`, `mathqa_test_0102`, `mathqa_test_0108`, and
`mathqa_test_0122`. Their 24 saved outputs contain 22 usable proposals, all
reviewed independently by the assistant: ten valid, eleven invalid, one unknown
acceptance label. The reviews are not human annotations. Two unusable outputs
incur no verifier expense. Unknown labels remain outside binary quality counts.

`22 proposals * 3 models * 3 variants = 198` planned observations.
**Nine exact baseline judgments** from pilot
`090a84fd-9ef1-43fc-9663-178e7c042765` are reused, leaving **189 new expected/
maximum calls**. Per model: 19 new baseline requests, 22 recompute requests,
22 recompute-plus-reasoning requests. There are zero new solver requests,
zero transport retries, and no synthetic diagnostic reruns.

The three inspected pilot proposals form a regression group: 27 observations,
nine reused and 18 new. The other 19 proposals from seven questions form an
expansion group: 171 new observations. Report these groups separately; both are
development material, and the inspected failures are not held-out evidence.

Reuse requires matching source call ID, exact request, independent labels,
returned provider/model, and a valid saved Boolean verdict. Frozen response
and grade hashes bind the reuse evidence. Changes invalidate the plan before
execution, and duplicate matching judgments are rejected as ambiguous. Reuse
creates no invented calls; historical cost is excluded from new spending.

## Authorized advance cost proposal

Purpose: measure whether recomputation improves verification, whether extra
reasoning allowance adds improvement, and how the resulting profiles behave
on more reviewed natural answers at an acceptable cost. Saved judgments can
answer unchanged requests, but cannot predict changed profiles' verdicts.

Prices come from the pinned endpoint snapshot fetched at
`2026-10-07T22:39:11.569577+00:00`. Reasoning capabilities were checked through
the free model catalog during preparation. Both snapshots must be within 24
hours at execution. Provider price ceilings constrain prompt/completion rates.

Each model has **32,200 estimated input tokens** across its 63 new calls:
8,790 baseline plus 11,705 for each new-prompt variant. Estimates use prompt
characters divided by three plus 96 framing tokens per request. Expected total
billed output is **12,576 tokens per model**: `19*32 + 22*32 + 22*512`.
Output includes reasoning, counted once. Reasoning usage under the changed
settings is untested, and no cache discount is assumed.

| Model / provider | New calls | Input / output USD per million | Estimated input cost | Estimated output cost | Estimated subtotal |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 2.5 Flash-Lite / Google AI Studio | 63 | $0.10 / $0.40 | $0.00322000 | $0.00503040 | $0.00825040 |
| Gemini 3.1 Flash-Lite / Google AI Studio | 63 | $0.25 / $1.50 | $0.00805000 | $0.01886400 | $0.02691400 |
| DeepSeek V3.2 / DeepInfra | 63 | $0.26 / $0.38 | $0.00837200 | $0.00477888 | $0.01315088 |
| Total | **189** | | $0.01964200 | $0.02867328 | **$0.04831528** |

Estimated costs by variant:

| Model | Baseline, 19 new | Recompute, 22 new | Recompute plus reasoning, 22 new |
| --- | ---: | ---: | ---: |
| Gemini 2.5 | $0.00112220 | $0.00145210 | $0.00567610 |
| Gemini 3.1 | $0.00310950 | $0.00398225 | $0.01982225 |
| DeepSeek | $0.00251644 | $0.00331082 | $0.00732362 |

Conservative reservations use full request UTF-8 bytes plus 256 framing tokens
and the entire combined output cap at the larger completion/reasoning rate.
Totals: Gemini 2.5 $0.02710700, Gemini 3.1 $0.16534925, DeepSeek $0.05603582;
**$0.24849207 overall**. These estimates do not guarantee provider billing.

Proposed limits: **$0.25 spending limit and 189 new requests maximum**, for this
comparison only. The original $0.00163967 pilot expense is historical and
separate. The user approved this numeric budget for the single frozen run.

The runner is serial and checks known spending plus the next reservation before
scheduling. Unknown cost/tokens, provider/model changes, inconsistent usage,
or exceeded reservations stop it. This experiment also stops at the first
technical/format error, including truncation, to avoid paying for repeated
configuration failures. Mathematical rejections remain valid observations.
Early stops can reduce the call count. No automatic retry, rerun, resume, or
scope expansion is allowed. Regression examples are scheduled first, with
question blocks and variants randomized using recorded seed 42.

## Reporting, decision, and verification

Report paired improvements/worsening for identical proposals within each model;
separate regression and expansion, false acceptances, false rejections,
technical errors, unknown labels, and incomplete coverage. Reused versus new
judgments and actual new spend remain explicit. Preserve raw responses,
reasoning measurements, and timing. Prefer fewer false acceptances, then fewer
false rejections/errors, and compare cost/latency at comparable coverage.
Do not freeze a profile with unresolved demonstrated false acceptances merely
because it is cheap or repairs the inspected failure. Zero observed errors
would make a profile promising, not prove it error-free. Eight questions with
related solver outputs do not establish a population error rate.

**82 offline tests passed**, including eleven new comparison checks covering
unchanged baselines, prompt isolation, reasoning controls, exact reuse,
response/label drift, stale metadata, historical cost exclusion, paired counts,
unknown labels, partial coverage, and stop-on-truncation. The preparation audit
validates this plan and the original pilot plan. At preparation time the database
was byte-for-byte unchanged, contained only the prior 36 paid calls, and passed
integrity/foreign-key checks. No schema upgrade was needed. After execution it
contains five additional calls; the results report records the post-run audit.

Artifacts:

- Plan: `results/workflow_previews/verifier-comparison-2026-10-07.json`.
- SHA-256: `a881986fca6e05dc0596aa00c618d986d6b6de2c282fa77338ef4e4b9a5038e9`.
- Capabilities: `results/workflow_previews/reasoning-metadata-2026-10-07.json`.
- Audit: `results/workflow_previews/verifier-comparison-2026-10-07-preparation-audit.json`.

Offline preparation command (use a new output filename if this plan exists):

```powershell
.\.venv\Scripts\python.exe scripts/mathqa_verifier_compare.py --metadata results/workflow_previews/provider-metadata-2026-10-07.json --reasoning-metadata results/workflow_previews/reasoning-metadata-2026-10-07.json --plan results/workflow_previews/verifier-comparison-2026-10-07.json
```

The existing screening runner executed this frozen plan after authorization
with explicit `--run`, numeric limits, and a new report destination. Generated
plans/reports remain ignored by Git; code, tests, and this proposal are reviewable
source files. Milestone 2 remains open; the LangGraph loop is still Milestone 3.

Primary references: [Google thinking budgets](https://ai.google.dev/gemini-api/docs/generate-content/thinking),
[OpenRouter reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens),
[public model catalog](https://openrouter.ai/api/v1/models), and pinned endpoint metadata for
[Gemini 2.5](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash-lite/endpoints),
[Gemini 3.1](https://openrouter.ai/api/v1/models/google/gemini-3.1-flash-lite/endpoints), and
[DeepSeek](https://openrouter.ai/api/v1/models/deepseek/deepseek-v3.2/endpoints).
