# Live loop pilot results — October 7, 2026

The user requested a commit followed by the pilot. The screening/offline-loop
checkpoint is `0fc1d05`; the tested live adapter and advance cost proposal were
committed as `00453de` before execution. The pilot completed all **six executions**
with **twenty requests**, **$0.00249524** reported cost, and **zero unknown charges
or technical errors**. All six accepted final options match the independent
MathQA keys. The live graph naturally reached every attempt position.

This completes Milestone 3's integration check. It does not establish a best
sequence or a reliable verifier error rate: these are two already-exposed
development questions, evaluated under three related configurations once each.
Prior verifier false acceptances remain part of the evidence.

## Execution and routing

Run `c399547b-f47f-43d9-8578-11b3f257b2ff`, status `completed`, no stop reason.
UTC start/end: `2026-10-08T02:46:54.626818+00:00` /
`2026-10-08T02:47:53.753337+00:00` (October 7 in New York). Elapsed: **59.13 seconds**.
Executed clean commit `00453de7a8cfb21bed3d5e21ab29d1e0c936c22c`.
The [proposal](solver-verifier-loop-pilot-proposal.md) freezes scope, rates,
temperature 0.2, solver cap 512, and the fixed Gemini 2.5 reasoning verifier.

| Question | Sequence | Natural decisions | Final option | Independent score |
| --- | --- | --- | --- | ---: |
| Stations / `0002` | Qwen2.5 → Qwen3 → DeepSeek | Reject → reject → accept | c, 870 | 1 |
| Stations / `0002` | Qwen3 → DeepSeek → Qwen2.5 | Reject → accept | c, 870 | 1 |
| Stations / `0002` | DeepSeek → Qwen2.5 → Qwen3 | Accept | c, 870 | 1 |
| Distribution / `0047` | Qwen2.5 → Qwen3 → DeepSeek | Reject → accept | d, 5 | 1 |
| Distribution / `0047` | DeepSeek → Qwen2.5 → Qwen3 | Accept | d, 5 | 1 |
| Distribution / `0047` | Qwen3 → DeepSeek → Qwen2.5 | Accept | d, 5 | 1 |

There were ten usable solver answers, four verifier rejections, and six
acceptances. Three executions ended at slot one, two at slot two, and one at
slot three. Each rejection triggered a fresh request with the original
question/options only; every stored request exactly matches reconstruction
from its frozen profile, question and price limits. Acceptance scheduled no
later attempts. No unusable output, truncation, invalid verdict, provider error,
transport retry, fallback, rerun or synthetic verdict occurred.

All-rejected exhaustion and accepted-wrong scoring were demonstrated offline,
not encountered naturally here. First solver answers matched the key in three
of six executions; the final accepted answers matched in six of six. These
related observations are a routing illustration, not a general accuracy gain.

## Separate reasoning review

The assistant reviewed the saved calculations independently; these are not
human annotations. All six accepted calculations are valid, allowing correct
shortcuts, and all four rejected calculations are mathematically invalid:

- The ticket question has 28 intermediate stations plus two endpoints, so
  thirty origins each have twenty-nine other destinations: `30*29=870`.
  DeepSeek's three accepted proposals use that setup and arithmetic. Qwen2.5's
  `28*(28-1)/2=380` omits endpoints, uses unordered pairs, and actually equals
  378. Qwen3's two `30*29/2=380` proposals also use unordered pairs and actually
  equal 435. All three invalid proposals were rejected.
- The distribution question requires `gcd(1345,775)=5`. The remainders in
  Euclid's algorithm are 570, 205, 160, 45, 25, 20, 5 and 0. DeepSeek displays
  the valid chain; Qwen3's two accepted calculations state the correct GCD
  directly. Qwen2.5's `gcd(1345,775)=91` is false and was rejected.

Thus no false acceptance or false rejection was observed among these ten
reviewed proposals. This tiny, related sample cannot replace earlier screening
evidence or certify reliability. Database option grades remain separate from
verifier decisions; their `reasoning_valid` fields remain unknown. The review
above is separately recorded evidence, not inferred from key matching.

## Actual spend

| Role/model | Pinned provider | Calls | Cost | Input tokens | Output including reasoning | Reasoning subset |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Solver Qwen2.5 7B | Phala | 2 | $0.00006840 | 570 | 57 | 0 |
| Solver Qwen3 32B | SiliconFlow | 4 | $0.00021616 | 1,088 | 112 | 0 |
| Solver DeepSeek V3.2 | DeepInfra | 4 | $0.00028108 | 959 | 193 | 0 |
| Verifier Gemini 2.5 Flash-Lite | Google AI Studio | 10 | $0.00192960 | 2,924 | 4,093 | 4,067 |
| Total | | **20** | **$0.00249524** | **5,541** | **4,455** | **4,067** |

Actual spend was below the $0.00442248 expected estimate, $0.03480540
conservative reservation total, and $0.04 configured cap. Fewer calls and
shorter inputs/outputs reduced spend. Reported usage/cost includes cache effects;
reasoning is counted inside output, never added again. Verifier reasoning
usage ranged from 362 to 481 tokens; all total outputs stayed under 1,024.
The verifier accounted for about 77% of pilot cost. Average cost per finished
execution was approximately $0.000416. Total known workflow spend across the
three prior verifier runs and this pilot is **$0.01033542**, with 101 requests
and zero unknown costs.

## Audit and milestone checkpoint

All **123 offline tests** passed before execution; the eleven pilot tests also
passed after the last adapter edit. The post-run read-only audit confirms:

- All twenty calls completed with HTTP 200 and `stop`, the requested models,
  pinned providers, known usage/cost, and charges within per-call reservations.
- Stored requests reconstruct exactly, excluding feedback, answer keys and
  review labels. Independent attempt/final grades match the unchanged dataset.
- All six legacy tables and all prior workflow records are unchanged. Database
  integrity is `ok`; foreign-key checks have zero errors.
- The plan, bound source hashes and dataset checksum still validate. Execution
  used a clean committed checkout. No new migration or post-run API call ran.

Ignored artifacts under `results/workflow_previews/`:

- `loop-pilot-2026-10-07.json`, frozen SHA-256
  `52071be6332dd77d35cdc9c9f6639c91393bdc7371abf2e39b413c5ac5698023`.
- `loop-pilot-report-2026-10-07.json`, full measured summary.
- `loop-pilot-before-audit.json` and `loop-pilot-after-audit.json`, record
  fingerprints, request/grading checks and saved calculation traces.
- Raw call payloads and independent option grades: `results/mathqa_runs.sqlite3`.

Milestone 3 is complete. Next prepare a small balanced development evaluation
of all 27 sequences, with question IDs/repetitions, fresh rates, expected and
maximum calls, uncertainty, and a separate cost proposal. Keep the provisional
verifier fixed. No larger paid evaluation has been run or scheduled.
