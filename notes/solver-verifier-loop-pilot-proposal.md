# Live solver-verifier loop pilot — October 7, 2026

The user instructed: "sure commit and then do the pilot." Commit the tested
implementation before execution. This authorizes this small integration pilot;
it does not authorize a 27-sequence sweep or further verifier selection.

## Purpose and scope

Check actual solver generations, Gemini decisions, conditional retries, durable
call records, budget gates and independent option grading. Offline tests already
cover every slot, exhaustion and accepted wrong answers; live calls check the
provider integration. Use exposed development questions `mathqa_test_0002` and
`mathqa_test_0047`, one repetition each of Qwen2.5→Qwen3→DeepSeek,
Qwen3→DeepSeek→Qwen2.5, and DeepSeek→Qwen2.5→Qwen3. This is six executions.
Seed 17 shuffles sequences within each question. No synthetic answers, forced
verdicts, transport retries or provider fallback. At most eighteen solver and
eighteen verifier calls; acceptance stops early and unusable answers skip checks.

Solvers use temperature 0.2 and max_tokens 512 with existing prompts and other
controls. The fixed `flashlite25__reasoning` verifier uses temperature zero,
512 reasoning tokens and 1,024 total output tokens. Retries receive only the
original question/options. Independent keys never enter model requests.

## Advance cost disclosure

Free public endpoint/catalog metadata fetched `2026-10-08T02:32:48.602756+00:00`
confirms active pinned endpoints advertising requested controls. Rates are USD
per million input/output tokens; output includes reasoning once.

| Role/model | Provider pin | Rates input/output | Expected/max calls | Input/output tokens | Input cost | Output cost | Subtotal |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Solver Qwen2.5 7B | Phala `phala` | $0.10 / $0.20 | 4 / 6 | 1,584 / 384 | $0.00015840 | $0.00007680 | $0.00023520 |
| Solver Qwen3 32B | SiliconFlow `siliconflow/fp8` | $0.14 / $0.57 | 4 / 6 | 1,596 / 384 | $0.00022344 | $0.00021888 | $0.00044232 |
| Solver DeepSeek V3.2 | DeepInfra `deepinfra/fp4` | $0.26 / $0.38 | 4 / 6 | 1,584 / 384 | $0.00041184 | $0.00014592 | $0.00055776 |
| Verifier Gemini 2.5 Flash-Lite | Google AI Studio `google-ai-studio` | $0.10 / $0.40 | 12 / 18 | 7,296 / 6,144 | $0.00072960 | $0.00245760 | $0.00318720 |

Expected **$0.00442248 / 24 requests**, cap **$0.04 / 36 requests**. Assume two
slots per execution, solver output 96 tokens, verifier output 512 including
reasoning, input characters/3 plus framing, and no cache discounts. Gemini
reasoning has the same $0.40 output rate. Conservative reservations for full
caps total **$0.03480540**: Qwen2.5 $0.00149400, Qwen3 $0.00346968, DeepSeek
$0.00351672, verifier $0.02632500. Stress inputs use an 8,192-character calculation,
full UTF-8 request plus framing and full output caps. These are estimates,
not tokenizer/billing guarantees; actual verifier inputs are reserved before
each call. Price ceilings are sent to OpenRouter. Known spend plus the next
reservation must fit the cap. Unknown billing/usage, provider drift or overruns
stop scheduling. No automatic rerun or resume.

## Prepared checkpoint

The separate `scripts/mathqa_workflow_pilot.py` HTTP adapter requires explicit
`--run`, numeric limits and a fresh report. Frozen plans bind source hashes,
dataset checksum, profiles, schedule, metadata and price ceilings. Duplicate
plans cannot be rerun. Calls are serial, with no redirects and a 60-second
inactivity timeout. No new database migration is needed.

All **123 offline tests pass**, including eleven pilot tests covering balancing,
early acceptance, three rejections, wrong accepted options, invalid verdicts,
partial coverage, unknown billing, nonfinite JSON, duplicates, evidence drift,
provider controls and spending limits. Zero paid calls during preparation.

Plan: `results/workflow_previews/loop-pilot-2026-10-07.json`.
SHA-256: `52071be6332dd77d35cdc9c9f6639c91393bdc7371abf2e39b413c5ac5698023`.

Report actual cost, coverage, routing, errors and independent grades, then
checkpoint. This sample cannot rank 27 sequences or establish reliable accuracy.
Natural decisions may not reach every slot; report that beside offline coverage.
