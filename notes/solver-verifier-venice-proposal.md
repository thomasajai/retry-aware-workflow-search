# Development evaluation with Venice — October 8, 2026

Status: provider change prepared offline at the user's request; **new paid run
awaits approval**. DeepInfra's stopped run remains preserved in the
[partial results](solver-verifier-development-results.md). This proposal keeps
Gemini 2.5 Flash-Lite with reasoning as the verifier and changes only DeepSeek's
provider pin to Venice. No more verifier screening is proposed.

## Purpose and scope

Finish a comparable development evaluation of all **27 solver sequences × the
same 20 questions × one repetition = 540 fresh executions**. Saved responses
cannot complete this experiment: the previous run finished only 14 executions,
all on the first question, using a different DeepSeek provider. Preserve those
observations as diagnostics; do not combine them with this evaluation's scores.
The question IDs, shuffled schedule, prompts, sampling and acceptance/grading
rules remain exactly as in the [original proposal](solver-verifier-development-proposal.md).
Retain the ambiguous first question rather than changing selection after seeing
results. Reserved held-out questions remain outside this stage.

Run `scripts/mathqa_workflow_evaluation.py` once with the new frozen plan.
At most three attempts per execution, original question/options only on retries,
solver temperature 0.2 and output cap 512. Verifier temperature zero, reasoning
cap 512 and total output cap 1,024. Calls remain serial, with zero transport
retries and no provider fallback. No automatic restart, further paid diagnostic,
held-out evaluation or settings adjustment is included.

## Provider evidence and cost notice

Free public metadata fetched at `2026-10-08T17:20:52.307999+00:00` lists Venice
as active for [DeepSeek V3.2](https://openrouter.ai/api/v1/models/deepseek/deepseek-v3.2/endpoints)
with the requested reasoning, temperature and output controls. This metadata
check establishes advertised compatibility, not demonstrated live reliability.
The frozen snapshot includes all four endpoint source URLs and explicit price
ceilings. Models and provider pins:

| Role/model | Pin | USD per million input/output | Expected/max calls | Estimated input/output tokens | Input cost | Output cost | Subtotal |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Solver `qwen/qwen-2.5-7b-instruct` | `phala` | $0.10 / $0.20 | 360 / 540 | 140,652 / 34,560 | $0.01406520 | $0.00691200 | $0.02097720 |
| Solver `qwen/qwen3-32b` | `siliconflow/fp8` | $0.14 / $0.57 | 360 / 540 | 141,840 / 34,560 | $0.01985760 | $0.01969920 | $0.03955680 |
| Solver `deepseek/deepseek-v3.2` | `venice` | $0.26829 / $0.39024 | 360 / 540 | 140,652 / 34,560 | $0.03773552508 | $0.01348669440 | $0.05122221948 |
| Verifier `google/gemini-2.5-flash-lite` | `google-ai-studio` | $0.10 / $0.40 | 1,080 / 1,620 | 650,916 / 552,960 | $0.06509160 | $0.22118400 | $0.28627560 |

Expected additional spend **$0.39803181948**, approximately **$0.398**, for
**2,160 calls**. Maximum **3,240 calls**, including every solver/verifier attempt.
Proposed additional spending cap **$3.50**, unchanged from the previous cap but
applying to a **new run**. The previous cap was not a reusable authorization for
automatic reruns. Venice adds approximately $0.00152 to the expected estimate.

Expected assumptions: two attempts reached per execution; 96 solver output
tokens; 512 verifier output tokens including reasoning once; message
characters/3 plus 96 framing tokens for inputs; no cache discount. Reasoning
uses Gemini's $0.40 output rate. Stress reservations use full UTF-8 request size
plus 256 framing tokens, an 8,192-character solver calculation and full output
caps. Conservative total **$3.13543236069**: Qwen2.5 $0.13365810, Qwen3
$0.31114854, DeepSeek $0.32378142069, verifier $2.36684430. Neither estimate
guarantees actual billing. Each next call must fit the cap using recorded spend
and a fresh reservation. Unknown cost/usage, provider/model drift or reservation
overrun stop further calls, and incomplete executions remain ungraded.

Prior stopped run: **$0.00555908 known spend plus one unresolved charge** from
the DeepInfra 429. Preserve its unknown billing as unknown; this new plan does
not reconcile or erase it. Combined expected known spend for the stopped run
and this new run would be $0.40359089948, plus that unresolved charge.

## Implementation and offline verification

Add an explicit, allowlisted workflow-only `deepseek_provider` setting and new
version-two snapshots for Venice. Legacy batch profiles and all 27 default
version-one workflow configurations match their exact pre-change builders.
Every Venice DeepSeek slot has fallback disabled and required parameters enabled.
The runner reconstructs trusted profiles and rejects provider/profile tampering.
Execution cannot override a frozen plan using the preparation flag. No database
migration or dependency is needed.

The prepared plan is ignored local artifact
`results/workflow_previews/evaluation-development-venice-2026-10-08.json`, SHA-256
`a24147002ebe7f2205bcccf049db44c15caabf1b174507ec7227b21161c8ee08`.
Source hashes, data, metadata, provider choice and schedule are bound to it.
Metadata expires after 24 hours; refresh and disclose changed prices before
execution if delayed. Original plans and partial reports remain intact.

All **136 offline tests pass**. New tests cover compatible/incompatible Venice metadata, unchanged scope
and other profiles, checksummed provider tampering, and a simulated complete
27-sequence run using the Venice pin. The preparation audit confirms the real
database stayed unchanged, integrity is `ok`, zero foreign-key errors, and
zero generation requests. Commit reviewed preparation before any authorized
paid run; report actual spend and results at the next checkpoint.
