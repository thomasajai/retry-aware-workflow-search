# Routed development comparison v5 — completed October 8, 2026

The approved comparison finished **all 540 executions: 20 development questions
× 27 ordered solver configurations × one repetition**. Reported cost was
**$0.30118175983**, below the $0.48995280 estimate and approved $4.25 cap.
It used **2,194 gateway requests**, below the 3,240 maximum. No new unknown
charges, client transport retries, guard stop, rerun or held-out evaluation.

The solver-verifier loop and truncation amendment worked. Gemini remains an
imperfect verifier, and several selected questions have option/key or
specification issues. Treat the ranking as a development comparison under the
original answer keys, not a deployment recommendation.

## Execution record

- Run: `f0c941bc-5479-4e86-ae2d-261b521a3317`.
- Approved [fresh-run proposal](solver-verifier-routed-development-v5-proposal.md).
- Clean execution revision: `45170b0664bec9a4dd7e331603104eddeb4b6c87`.
- Plan: `results/workflow_previews/routed-development-v5-plan-2026-10-08.json`.
- Plan SHA-256: `c8afff2663e82c7d58476d567134eb1945215200707161173d413acef6fcf365`.
- Start: `2026-10-08T19:45:00.086808+00:00` (3:45 p.m. EDT).
- Finish: `2026-10-08T21:25:14.374086+00:00` (5:25 p.m. EDT).
- Duration: 6,014.29 seconds, about 1 hour 40 minutes.
- Status: `completed_with_errors`; score coverage and billing comparison complete.

The status preserves **70 failed DeepSeek generations**, all HTTP 200,
`IncompleteGeneration`, `finish_reason=length`, with fully reported usage/cost.
Each was marked unusable, retained its request/cost/raw partial response,
consumed one of the three mathematical slots, and received no verifier call.
The run continued through them under the frozen v5 policy. The other 2,124
requests completed. There were no failed gateway/transport responses or verifier
truncations. Output caps, prompts, sampling, models and routing remained fixed.

All 540 executions have independent final grades: **294 accepted, 246 exhausted**.
Of the accepted final options, **292 match the key and two disagree**. The mean
over all configuration/question executions is **292/540 = 54.07%**. That pooled
mean describes this comparison, not a single configuration's deployment
accuracy. Acceptance coverage is 54.44%. Acceptance occurred at slots one,
two and three in 224, 40 and 30 executions respectively.

## Reported cost and providers

Output counts include reasoning once; do not add reasoning tokens again.

| Role/model | Requests | Input tokens | Output tokens | Reported USD |
| --- | ---: | ---: | ---: | ---: |
| Qwen2.5 7B / Phala | 377 | 113,105 | 11,317 | $0.01357390 |
| Qwen3 32B / SiliconFlow | 380 | 108,976 | 18,610 | $0.02586434 |
| DeepSeek V3.2 / automatic routing | 375 | 96,827 | 58,058 | $0.05475371983 |
| Gemini 2.5 Flash-Lite / Google AI Studio | 1,062 | 340,638 | 432,315 | $0.20698980 |
| **Total** | **2,194** | **659,546** | **520,300** | **$0.30118175983** |

Gemini output includes 429,129 reasoning tokens. There were 1,132 solver
attempts (2.096 per execution); 70 were unusable truncations, leaving 1,062
verifier requests. Average reported cost across all configurations is about
$0.000558 per execution, including unsuccessful attempts. Actual spend was
about 61.5% of the estimate; actual routing and outputs account for the
difference. The cap was a scheduling limit, not a spending target.

| DeepSeek provider | Calls | Reported USD |
| --- | ---: | ---: |
| Baidu | 222 | $0.027487068 |
| DigitalOcean | 82 | $0.02084850 |
| GMICloud | 43 | $0.0043050312 |
| DeepInfra | 20 | $0.00145728 |
| AtlasCloud | 5 | $0.00039812 |
| SiliconFlow | 2 | $0.000154868 |
| Venice | 1 | $0.00010285263 |

These observations describe the frozen automatic routing/price policy, not a
fixed-provider benchmark or future availability guarantee. Internal OpenRouter
provider attempts are not separately counted by the gateway counter. Across
the six development/availability runs, reported costs total **$0.34153950852
plus the same five older unresolved charges**, kept separately. This is not a
whole-project/account total.

## Configuration comparison

Every configuration was evaluated on all twenty questions. Score one requires
an accepted option matching the original independent key; exhausted executions
and accepted wrong options score zero. Reasoning validity remains separate and
has not been comprehensively labeled. No question/key was changed or removed
after observing results; no earlier run was pooled.

Four configurations tied at **13/20 (65%)**. The cheapest tied configuration
was **DeepSeek → DeepSeek → Qwen2.5**, with total reported cost $0.0103176936,
about $0.000516 per question, and mean execution latency 10.07 seconds.
Its Wilson 95% interval is approximately **43.3%–81.9%**; the question bootstrap
interval is 40%–85%. Twenty questions and one sequence observation per question
provide limited evidence. Sorting ties by observed cost does not establish a
statistically better or generally best sequence.

The descriptive accuracy/cost frontier contains
`deepseek-deepseek-qwen25` (65%, $0.000516/question) and
`deepseek-qwen25-qwen25` (60%, $0.000497/question). It uses accuracy and cost,
not latency. Full paired differences, Wilson intervals and 1,000 paired
question-block bootstrap results are in the local JSON report. There is no
selection/multiple-comparison correction or automatic finalist selection.

Aliases: `deepseek` = DeepSeek V3.2; `qwen25` = Qwen2.5 7B;
`qwen3` = Qwen3 32B. Total cost covers all solver/verifier attempts on twenty
questions; latency includes unsuccessful attempts.

| Solver sequence | Key score | Total USD | USD/question | Mean seconds | Solver attempts | Requests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deepseek → deepseek → qwen25 | 13/20 (65%) | $0.010317694 | $0.000515885 | 10.07 | 34 | 61 |
| deepseek → qwen25 → deepseek | 13/20 (65%) | $0.010929181 | $0.000546459 | 12.69 | 38 | 71 |
| deepseek → deepseek → deepseek | 13/20 (65%) | $0.010944969 | $0.000547248 | 12.71 | 36 | 66 |
| qwen3 → qwen3 → deepseek | 13/20 (65%) | $0.012058981 | $0.000602949 | 13.02 | 43 | 82 |
| deepseek → qwen25 → qwen25 | 12/20 (60%) | $0.009938588 | $0.000496929 | 11.62 | 36 | 69 |
| qwen25 → deepseek → qwen25 | 12/20 (60%) | $0.010461028 | $0.000523051 | 8.33 | 42 | 83 |
| qwen3 → deepseek → qwen3 | 12/20 (60%) | $0.010914188 | $0.000545709 | 11.91 | 40 | 78 |
| deepseek → deepseek → qwen3 | 12/20 (60%) | $0.010922650 | $0.000546132 | 14.62 | 37 | 68 |
| qwen3 → qwen25 → deepseek | 12/20 (60%) | $0.011422468 | $0.000571123 | 10.15 | 44 | 86 |
| deepseek → qwen3 → deepseek | 12/20 (60%) | $0.011517971 | $0.000575899 | 15.21 | 38 | 71 |
| qwen25 → deepseek → deepseek | 12/20 (60%) | $0.011524068 | $0.000576203 | 11.65 | 43 | 80 |
| qwen3 → deepseek → deepseek | 12/20 (60%) | $0.012005393 | $0.000600270 | 12.87 | 40 | 75 |
| deepseek → qwen3 → qwen25 | 11/20 (55%) | $0.010709296 | $0.000535465 | 10.76 | 38 | 73 |
| deepseek → qwen3 → qwen3 | 11/20 (55%) | $0.010747947 | $0.000537397 | 12.16 | 38 | 73 |
| deepseek → qwen25 → qwen3 | 11/20 (55%) | $0.011060835 | $0.000553042 | 10.81 | 42 | 84 |
| qwen25 → deepseek → qwen3 | 11/20 (55%) | $0.011617343 | $0.000580867 | 11.37 | 44 | 85 |
| qwen25 → qwen3 → deepseek | 11/20 (55%) | $0.011885428 | $0.000594271 | 11.40 | 46 | 90 |
| qwen25 → qwen3 → qwen25 | 10/20 (50%) | $0.010541490 | $0.000527074 | 8.42 | 44 | 88 |
| qwen3 → deepseek → qwen25 | 10/20 (50%) | $0.011371543 | $0.000568577 | 11.84 | 43 | 82 |
| qwen25 → qwen25 → qwen3 | 10/20 (50%) | $0.011460650 | $0.000573032 | 8.93 | 48 | 96 |
| qwen25 → qwen25 → deepseek | 10/20 (50%) | $0.012087408 | $0.000604370 | 9.76 | 48 | 93 |
| qwen3 → qwen25 → qwen3 | 9/20 (45%) | $0.010858500 | $0.000542925 | 10.76 | 43 | 86 |
| qwen3 → qwen3 → qwen3 | 9/20 (45%) | $0.011376650 | $0.000568832 | 11.55 | 43 | 86 |
| qwen25 → qwen3 → qwen3 | 9/20 (45%) | $0.011405030 | $0.000570252 | 10.12 | 46 | 92 |
| qwen3 → qwen25 → qwen25 | 8/20 (40%) | $0.010669840 | $0.000533492 | 8.75 | 44 | 88 |
| qwen3 → qwen3 → qwen25 | 8/20 (40%) | $0.011502420 | $0.000575121 | 10.58 | 46 | 92 |
| qwen25 → qwen25 → qwen25 | 6/20 (30%) | $0.010930200 | $0.000546510 | 7.60 | 48 | 96 |

## First-attempt diagnostics and retries

These reuse fresh calls from this run with **zero additional paid requests**.
Each solver has nine first-slot observations per question, 180 over twenty
questions. Raw key matching counts usable solver options; verified key matching
also requires first-attempt acceptance. Neither labels reasoning validity, and
bad keys affect both.

| First-slot solver | Raw option/key matches | Accepted key matches in one attempt |
| --- | ---: | ---: |
| Qwen2.5 | 58.89% | 30.00% |
| Qwen3 | 76.67% | 38.89% |
| DeepSeek | 76.67% | 55.56% |

Verifier rejection reduces first-attempt key matching substantially here. That
gap is not a false-rejection rate: some rejected key-matching calculations are
invalid and some keys are problematic. Among 294 finished executions whose
first answer was rejected, 68 eventually reached an accepted key match. Of
544 usable retries, 294 repeated a prior option/value. There were **404 rejected
key-matching attempts**, pending reasoning review.

## Question-quality flags and verifier examples

These are assistant mathematical reviews of specific observed development
records, not a preselected labeling study. They do not modify the dataset, keys
or stored scores. Automated reasoning-validity labels remain unreviewed; key
agreement does not establish valid reasoning and a key-matching rejection does
not automatically establish a verifier error.

| Question | Independent finding | Original key / consequence |
| --- | --- | --- |
| `mathqa_test_0187` | Spiral path: six turns, 18 feet vertically and 18 horizontally; distance `18*sqrt(2)` ≈ 25.46 feet. No option matches. | Key: 18 feet. |
| `mathqa_test_0237` | With `x/y=59.60`, remainder `r=3y/5`; for positive integer division the possible two-digit remainders are 12, 15, …, 99. Their sum is 1,665, absent from choices. | Key: 315. |
| `mathqa_test_0515` | Color/shape marginals do not determine the joint probability. Yellow-and-straight can range from 3/8 to 1/2; independence would give 7/16, absent from choices. | Key: 4/9 is possible but not uniquely implied. |
| `mathqa_test_0284` | Consecutive integers are coprime; the even one must be divisible by 32. Qualifying `n`: 31, 32, 63, 64, 95, 96. Probability 6/100 = 3/50, absent from choices. | Key: 1/16 is the repeating long-run fraction, not the finite 1–100 probability. |
| `mathqa_test_1455` | Dimensions in meters give volume 1,568 m³ and surface area 868 m². The keyed area is labeled cm²; a “none of them” option exists. | Key: 868 cm²; unit and answer-contract issue. |
| `mathqa_test_0383` | Combined rate `1/5+1/4=9/20` jobs/day gives 20/9 days, absent from choices. | Key: 2/9. |

All six flagged questions had zero accepted answers across all 27 configurations
(162 exhausted executions). This concentration materially limits absolute
accuracy interpretation. It does not justify deleting them after observing
performance or claiming every other question is clean. The earlier profit/
investment assumption ambiguity in `mathqa_test_0435` remains recorded in the
[first development results](solver-verifier-development-results.md).

The asteroid question, `mathqa_test_0902`, has a consistent mathematical answer:
`v_y=3*v_x` and `v_y-v_x=1000` imply `v_x=500`. Equal x/z speeds and z's
fivefold distance give `t+2=5t`, hence `t=0.5` and x's distance **250**, option a,
agreeing with the key. Three executions were accepted; only one matches the
key. Specific assistant-reviewed examples:

- **False rejections:** attempts `a53b3d59-7796-4e55-aaea-fe7cdb37e4f6` and
  `6047edbf-fd3c-4fc8-8a40-dd2f25cb115c` have valid equations yielding
  250/option a; Gemini returned false. These establish observed errors, not a
  population false-rejection rate. Do not infer its cause from the Boolean.
- **False acceptance:** attempt `901981fb-a8bb-4285-ba2a-de847deb94f6`, in
  `deepseek-deepseek-qwen3`, incorrectly replaces speed 500 with `500*t` in z's
  distance equation, yielding 1,500/option d. Gemini accepted it.
- **False acceptance:** attempt `b37dee44-f672-4cf8-9ba9-c861af277a40`, in
  `qwen3-qwen3-deepseek`, states distance/time equations but incorrectly concludes
  2,500/option e. Gemini accepted it.

The latter two are all accepted wrong final options in this run; independent
grading keeps both at zero. Prior verifier errors remain preserved separately.
Gemini remains provisional; other accepted key matches are not certified to
have valid reasoning by this targeted review.

## Audit, artifacts and next checkpoint

The read-only audit independently reconstructs every solver/verifier request,
configuration and scheduled question; checks original-only retries, three-slot
limits, final/attempt grades, chronological spend/request gates, reservations,
usage, prices and actual providers; recomputes role/provider and configuration
costs, baselines, ranking and frontier; and confirms no truncated output was
verified. SQLite integrity is `ok`, foreign-key errors are zero, all prior rows
are preserved, and the audit leaves the database unchanged. Reserved held-out
records remain unexposed by recorded calls.

Local artifacts are ignored by Git; raw calls remain in `results/mathqa_runs.sqlite3`:

- `results/workflow_previews/routed-development-v5-report-2026-10-08.json`.
- `results/workflow_previews/routed-development-v5-after-audit-2026-10-08.json`.
- `results/workflow_previews/routed-development-v5-summary-2026-10-08.json`.
- Pre-run backup: `results/backups/routed-development-v5-before-2026-10-08.sqlite3`.
- Post-run database SHA-256:
  `bb2c9e8bbb911ddc08957c744d2a73a74864deb99b504fc7c5a304d7a6cdeb64`.

The execution source passed **174 offline tests** before the run and was not
changed afterward. Historical stopped runs remain separate. This completes the
development comparison stage of Milestone 4; finalist/held-out assessment is
pending. Recommended next work is an **offline review of question quality and
saved verifier decisions**, agreeing how to adjudicate ambiguous records and
assess verifier reliability before further spending. Do not silently relabel
or recompute this run under revised policies. Any further paid run needs its
own purpose, scope, cost breakdown and fresh approval.
