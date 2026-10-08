# Amended verifier comparison — October 7, 2026, New York

The user approved the frozen comparison with a **$0.22 cap and 163 requests
maximum**. It stopped after forty new calls costing **$0.00483675**, when the
DeepSeek recompute profile returned prose and truncated before a Boolean
verdict. See the [partial results and audit](solver-verifier-comparison-amended-results.md).
Thirteen saved verdicts were reused, including mathematical errors. **89
offline tests passed** before execution. The original proposal below preserves
the approved scope; no automatic continuation is authorized.

## Purpose and fixed scope

Measure how independent recomputation and extra reasoning allowance affect
false acceptances, false rejections, completeness, cost, and latency on the
same eight reviewed development questions. Live calls are needed for previously
unobserved profile/proposal pairs. Saved evidence supplies unchanged requests.

The three Google variants remain baseline, recompute, and recompute plus
reasoning. DeepSeek retains baseline and recompute with reasoning disabled.
The third variant changes both reasoning allowance and total output cap;
comparisons do not isolate reasoning effort alone. Prompts, provider pins,
temperature zero, token limits, serial scheduling, and seed 42 are unchanged.

| Profile / pinned provider | New calls | Reasoning setting | Total output cap |
| --- | ---: | --- | ---: |
| Gemini 2.5 Flash-Lite baseline / `google-ai-studio` | 19 | Disabled | 256 |
| Gemini 2.5 Flash-Lite recompute / `google-ai-studio` | 21 | Disabled | 256 |
| Gemini 2.5 Flash-Lite recompute plus reasoning / `google-ai-studio` | 21 | Budget 512 | 1,024 |
| Gemini 3.1 Flash-Lite baseline / `google-ai-studio` | 19 | Minimal effort | 1,024 |
| Gemini 3.1 Flash-Lite recompute / `google-ai-studio` | 22 | Minimal effort | 1,024 |
| Gemini 3.1 Flash-Lite recompute plus reasoning / `google-ai-studio` | 21 | Low effort | 2,048 |
| DeepSeek V3.2 baseline / `deepinfra/fp4` | 19 | Disabled | 256 |
| DeepSeek V3.2 recompute / `deepinfra/fp4` | 21 | Disabled | 256 |
| Total | **163** | | |

Providers allow no fallback and require the requested controls; the frozen
requests contain explicit price ceilings. There are **zero solver calls, zero
transport retries, and zero synthetic reruns**. No solver feedback enters any
verifier input; reference labels remain offline.

Use the original first eight development questions from solver batch
`6e8ba4fd-3f6d-41f9-9522-23c84e0d332d`: `mathqa_test_0002`,
`mathqa_test_0013`, `mathqa_test_0026`, `mathqa_test_0047`,
`mathqa_test_0079`, `mathqa_test_0102`, `mathqa_test_0108`, `mathqa_test_0122`.
Their 24 outputs contain 22 usable proposals: ten reviewed valid, eleven
invalid, one unknown. Reviews are independent assistant annotations, not human
labels. The two unusable outputs receive no verifier request.

`22 usable proposals * 8 profiles = 176` planned observations. Nine original
baseline judgments and four valid Boolean verdicts from the stopped run supply
thirteen observations, leaving **163 new expected/maximum calls**. Valid here
means a usable verifier response, not a mathematically correct judgment.

The inspected first question is the regression group: 24 observations, thirteen
reused and eleven new. The other seven questions form the expansion group:
152 new observations. Both groups are development evidence, not held-out data.
Regression goes first; question blocks and variants use the frozen seed.

## Reuse safeguards and offline validation

Reuse sources are explicitly named, with no broad database search or selection
by outcome: pilot `090a84fd-9ef1-43fc-9663-178e7c042765` and stopped comparison
`f551e8d9-e2b1-4214-b17b-03c520cb25fc`. Source runs must be finished on the same
dataset and solver batch, with no unfinished calls. Only completed calls with
usable verdicts and complete, consistent billing/usage measurements qualify.
The failed DeepSeek response supplies no reused observation.

Exact source-call/request matching, response/grade hashes, independent labels,
and returned model/provider bind each observation. Conflicting duplicate
judgments are rejected rather than chosen. False acceptances and false
rejections remain in the evidence. Historical charges are excluded from the
new run's spend. A changed response, cost, label, profile, or request invalidates
the frozen plan before execution.

Comparison plan version 2 records the explicit reuse list and excluded
profiles. Original version 1 screening/comparison plans still validate against
the actual saved pilot and stopped run. Tests cover partial reuse, excluded
profile coverage, duplicate judgments, unfinished sources, inconsistent
measurements, evidence drift before scheduling, and mathematical errors kept
in reuse. All **89 tests pass**, using disposable databases and mocked HTTP.
The real database is byte-for-byte unchanged, with 41 prior paid calls totaling
$0.00300343, no unknown costs or active calls, and passing integrity/foreign-key
checks. No schema change was needed.

## Approved advance cost breakdown

Provider metadata was refreshed through free public GETs at
`2026-10-08T01:28:49.627400+00:00` (October 7, 9:28 p.m. New York).
The free model catalog confirmed controls for the selected reasoning profiles.
Both snapshots must be within 24 hours when executing; stale or changed
metadata requires a new validated proposal.

Expected input uses prompt characters divided by three plus 96 framing tokens.
Expected billed output includes reasoning once: 32 tokens per baseline or
recompute call, 512 per reasoning-enabled Google call. These are planning
assumptions, not a billing guarantee. No cache discount is assumed.

| Verifier model / provider | New calls | Input / output tokens estimated | Input / output USD per million | Input cost | Output cost | Subtotal |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| Gemini 2.5 Flash-Lite / Google AI Studio | 61 | 31,148 / 12,032 | $0.10 / $0.40 | $0.00311480 | $0.00481280 | $0.00792760 |
| Gemini 3.1 Flash-Lite / Google AI Studio | 62 | 31,679 / 12,064 | $0.25 / $1.50 | $0.00791975 | $0.01809600 | $0.02601575 |
| DeepSeek V3.2 / DeepInfra | 40 | 19,976 / 1,280 | $0.26 / $0.38 | $0.00519376 | $0.00048640 | $0.00568016 |
| Total | **163** | 82,803 / 25,376 | | **$0.01622831** | **$0.02339520** | **$0.03962351** |

| Model | Baseline estimate | Recompute estimate | Recompute plus reasoning estimate | Conservative reservation |
| --- | ---: | ---: | ---: | ---: |
| Gemini 2.5 | $0.00112220 | $0.00138670 | $0.00541870 | $0.02614480 |
| Gemini 3.1 | $0.00310950 | $0.00398225 | $0.01892400 | $0.16171850 |
| DeepSeek | $0.00251644 | $0.00316372 | Excluded | $0.02570078 |
| Total | | | | **$0.21356408** |

Reservations use the full request's UTF-8 bytes plus 256 framing tokens and the
entire total output cap at the larger completion/reasoning rate. The proposed
**$0.22 spending cap and 163 new requests maximum** apply to this single amended
run; the user approved these limits and prior spend is separate. The lower estimate depends on actual reasoning
usage. Responses can still truncate or take longer than expected.

The runner checks known spending plus the next reservation before each serial
request. Unknown cost/tokens, inconsistent usage, provider/model changes,
reservation overruns, and the first technical/format error stop scheduling.
Mathematical rejections remain observations. No automatic retry, rerun, resume,
scope expansion, or token-cap increase is authorized. The 60-second HTTP timeout
bounds inactivity, not total elapsed time; record actual latency and retain
incomplete outcomes. This proposal makes no absolute wall-time guarantee.

Report actual new charges after execution, paired verdict changes only for
selected arms, partial coverage, technical errors, and unknown labels. Keep
regression and expansion separate. Do not select a verifier merely because it
fixes an inspected failure or is cheap. Even a completed eight-question
comparison cannot establish an error-free verifier.

## Frozen artifacts and execution

- Plan: `results/workflow_previews/verifier-comparison-amended-2026-10-07.json`.
- SHA-256: `c029aabf8ac09935f7a50cf855b33cd209e45dce8abacc070a06146c58643e4f`.
- Provider metadata: `results/workflow_previews/provider-metadata-amended-2026-10-07.json`.
- Reasoning metadata: `results/workflow_previews/reasoning-metadata-amended-2026-10-07.json`.
- Audit: `results/workflow_previews/verifier-comparison-amended-2026-10-07-preparation-audit.json`.

The following command consumed credits and was run once after approval. Do not
rerun or resume this frozen plan:

```powershell
.\.venv\Scripts\python.exe scripts/mathqa_verifier_screen.py --run --plan results/workflow_previews/verifier-comparison-amended-2026-10-07.json --budget-usd 0.22 --max-requests 163 --report results/workflow_previews/verifier-comparison-amended-2026-10-07-results.json
```

The preparation CLI itself remains offline; repeated `--reuse-run` selects
explicit sources and `--exclude-candidate deepseek__reasoning` prepares this
subset. Plans and reports stay ignored by Git. Milestone 2 is still open; the
LangGraph solver/retry loop remains Milestone 3.
