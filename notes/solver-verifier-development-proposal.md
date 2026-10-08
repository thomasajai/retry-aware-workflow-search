# First 27-sequence development evaluation — October 7, 2026

The user asked to move ahead after the successful live loop pilot. Prepare
**20 development questions × 27 sequences × one repetition = 540 executions**.
This expands beyond the completed $0.04 pilot, so this stage's numeric limits
need approval under the [spending rule](../README.md#openrouter-spending-rule).
Preparation and tests are offline; no new paid run has occurred.

## October 8 authorization

Subsequent status: the [authorized run stopped](solver-verifier-development-results.md)
after 45 requests at an upstream 429 with unknown billing. The report is
recovered and audited; no automatic continuation or configuration ranking.
The user subsequently requested a different DeepSeek provider; the
[Venice proposal](solver-verifier-venice-proposal.md) prepares that change and a
new cost notice. Additional paid execution requires its own authorization.

The user approved the $3.50 cap / 3,240-request maximum. Free public metadata
was refreshed at `2026-10-08T17:01:25.885118+00:00`; rates, requested controls,
question IDs, profiles, schedule, scope and cost estimates are unchanged.
The execution plan is `evaluation-development-approved-2026-10-08.json`, SHA-256
`9e80da128d3b2f2894d62b1fccd50d918df22c6edc2637774b83f09e00699588`.
The original proposal plan is preserved. Commit this reviewed preparation before
the authorized single run; no automatic rerun or held-out stage is authorized.

## Scope and question selection

Measure each sequence's independent answer-key accuracy, acceptance coverage,
cost, latency and retries on the same questions. Keep the provisional Gemini
2.5 Flash-Lite reasoning verifier and pilot solver settings fixed. Every triple
allows up to three solver attempts; repetitions of models are allowed. Retries
receive the original question/options only, and rejected answers are not fallback
answers. Solvers use temperature 0.2 / max_tokens 512; verifier temperature zero,
reasoning cap 512 / total output cap 1,024. Retain all other prompts and controls.

Start with one repetition instead of the plan's earlier suggested three,
reducing 1,620 executions to 540. A single observation per sequence/question is
noisy. Close results or a tie do not establish a reliable winner. More repeats
and held-out confirmation remain later stages of Milestone 4.

Selection seed `20261007` samples uniformly from the first hundred dataset
records, excluding the two live-pilot questions. This broadens development
coverage without claiming unexposed data. Saved legacy calls cover the first
hundred; workflow history adds no exposure in the remaining hundred. Reserve
the last hundred for later finalist evaluation. The audit concerns recorded
calls, not a guarantee against unrecorded inspection. Exact selected IDs:

```text
mathqa_test_0435  mathqa_test_0661  mathqa_test_0187  mathqa_test_0566
mathqa_test_1092  mathqa_test_1096  mathqa_test_1292  mathqa_test_1076
mathqa_test_1408  mathqa_test_0237  mathqa_test_0515  mathqa_test_0284
mathqa_test_0952  mathqa_test_1029  mathqa_test_1455  mathqa_test_0260
mathqa_test_0902  mathqa_test_0013  mathqa_test_1105  mathqa_test_0383
```

Each question is a complete block of twenty-seven configurations, independently
shuffled with schedule seed `20261008`. No shared-prefix reuse: every sequence
gets fresh calls. Calls stay serial using the tested spending gate. Rough time
planning is one to two hours based on pilot timing, with substantial uncertainty
from provider latency and retry depth; this is not a total timeout guarantee.

Nine configurations start with each solver on every question. Reuse these
separate initial generations for raw one-attempt solver accuracy/cost and a
one-attempt solver-plus-verifier diagnostic. Each baseline has 180 first-slot
observations across twenty questions, with **zero additional paid calls**.
Those nine observations share a question; compare question-level means.
Historical batch responses have different sampling settings and are not reused
as workflow answers. Baseline reuse does not change sequence execution.

## Advance OpenRouter cost breakdown

Free public metadata was refreshed `2026-10-08T03:05:02.289672+00:00`. Active
pinned endpoints advertise the requested controls/output caps. Source URLs,
exact settings and provider price ceilings are frozen in the plan. Rates below
are USD per million input/output tokens; output includes reasoning once.

| Role/model | Provider pin | Input/output rates | Expected/max calls | Input/output tokens | Input cost | Output cost | Subtotal |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Solver Qwen2.5 7B | Phala `phala` | $0.10 / $0.20 | 360 / 540 | 140,652 / 34,560 | $0.01406520 | $0.00691200 | $0.02097720 |
| Solver Qwen3 32B | SiliconFlow `siliconflow/fp8` | $0.14 / $0.57 | 360 / 540 | 141,840 / 34,560 | $0.01985760 | $0.01969920 | $0.03955680 |
| Solver DeepSeek V3.2 | DeepInfra `deepinfra/fp4` | $0.26 / $0.38 | 360 / 540 | 140,652 / 34,560 | $0.03656952 | $0.01313280 | $0.04970232 |
| Verifier Gemini 2.5 Flash-Lite | Google AI Studio `google-ai-studio` | $0.10 / $0.40 | 1,080 / 1,620 | 650,916 / 552,960 | $0.06509160 | $0.22118400 | $0.28627560 |

Expected **$0.39651192 / 2,160 requests**. Maximum **3,240 requests**, including
all solver and verifier retries. Proposed cap **$3.50**. Conservative full-cap
reservations total **$3.12607080**: Qwen2.5 $0.13365810, Qwen3 $0.31114854,
DeepSeek $0.31441986 and verifier $2.36684430. The cap leaves a small margin
above this estimate; it is not an instruction to spend that amount.

Expected assumptions: two slots reached per execution, 96 solver output tokens
and 512 verifier output tokens including reasoning once, inputs from message
characters/3 plus 96 framing tokens, no cache discount. Pilot outputs were
shorter, but broader questions may need more output/retries. Gemini reasoning
uses the $0.40 output rate. Stress reservations use full UTF-8 request size plus
256 framing tokens, an 8,192-character calculation and full output caps.
These are not tokenizer or billing guarantees. Actual verifier inputs are
reserved before each call. Known spend plus the next reservation must fit the
approved cap. Unknown billing/usage, provider/model drift or overruns stop
scheduling. No transport retries, provider fallback, automatic rerun/resume,
token-cap increase, or follow-up evaluation.

## Reporting and selection

The primary score is one only for a final accepted option matching the
independent dataset key. Exhaustion/terminal known technical failures score
zero. Budget/infrastructure stops remain incomplete without invented grades.
Verifier acceptance is separate from correctness; option grades cannot establish
reasoning validity. Keep reasoning reviews separate.

The report contains all twenty-seven configurations' coverage, average accuracy,
acceptance, cost per execution, wall latency, attempts and requests, plus repeated
option/value answers and recovery after first rejection. Baselines include raw
solver and first-verification cost. Full rankings and the accuracy/cost Pareto
frontier require all 540 final scores. An incomplete run retains costs and
coverage with clearly labeled completed-only means and no final ranking.

Report Wilson intervals for each sequence's answer accuracy, alongside 1,000
paired question-block bootstrap resamples (seed `20261009`) for descriptive
accuracy intervals/differences from the observed top result. Bootstrap alone
can collapse at zero or perfect observed accuracy; Wilson retains finite-sample
uncertainty there (twenty correct answers still have a lower bound around 84%).
The reference is selected on this same sample and twenty-seven comparisons
share questions; these are not multiple-comparison significance tests or proof
of a universal winner. Report the frontier without automatically choosing a
finalist or running held-out questions. Review results before fixing the finalist
objective and proposing a separate held-out budget.

## Prepared implementation and checkpoint

New `scripts/mathqa_workflow_evaluation.py` reuses the unchanged graph, grading,
storage and pilot helpers. It adds free metadata fetching, read-only exposure
checks, source/data-bound balanced plans, explicit paid execution, progress after
each question block, and paired reporting. No dependencies or migrations change.
Existing pilot source/settings and historical plans remain intact.

Nine new offline tests cover balancing, held-out exposure, read-only preparation,
partial-score handling, complete paired summaries, zero-extra-call baselines,
mocked live recovery/repeated answers, duplicate plans, drift and budget guards.
All use disposable databases and simulated responses. The full suite passes
132 offline tests; the evaluation tests are rerun after the uncertainty safeguard.

Free preparation commands:

```powershell
.\.venv\Scripts\python.exe scripts/mathqa_workflow_evaluation.py --fetch-metadata results/workflow_previews/new-evaluation-metadata.json
.\.venv\Scripts\python.exe scripts/mathqa_workflow_evaluation.py --metadata results/workflow_previews/new-evaluation-metadata.json --plan results/workflow_previews/new-development-plan.json
```

Paid execution requires explicit `--run`, a frozen plan, approved numeric caps,
and a new report path. Metadata must be less than twenty-four hours old; refresh
and re-disclose changed costs if delayed. Commit reviewed preparation before
paid execution, then checkpoint with measured results and actual spend.

Ignored artifacts under `results/workflow_previews/`:

- `evaluation-provider-metadata-2026-10-07.json`.
- `evaluation-development-final-2026-10-07.json`, SHA-256
  `76b0ef4f679a2579a9e570ebd664d1f219a03d6f46e6353ac2f07a07ceab7014`.
- `evaluation-preparation-audit-2026-10-07.json`: unchanged database, integrity
  `ok`, zero foreign-key errors, four prior workflow runs / 101 calls /
  $0.01033542 known spend, zero new evaluation runs.
