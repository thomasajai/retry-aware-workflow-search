# Amended verifier comparison results — October 7, 2026, New York

The [approved amended comparison](solver-verifier-comparison-amended-proposal.md)
stopped after **40 new verifier calls**, costing **$0.00483675**, within its
$0.22 cap. The remaining 123 requests were not made. Thirteen saved verdicts
supplied additional observations without new charges. No solver calls,
transport retries, reruns, or automatic continuation occurred.

At this checkpoint every tested profile had an observed false acceptance and
none was selected. Subsequently the user chose Gemini 2.5 with reasoning
provisionally and instructed us to proceed; the
[offline loop is now implemented](solver-verifier-milestone-3-offline.md).
The observations below are unchanged, and further verifier experiments are
deferred in favor of a live loop pilot.

## Stop reason and billing

DeepSeek V3.2's recompute profile, pinned to `deepinfra/fp4` with reasoning
disabled, produced explanatory prose instead of the requested single-Boolean
JSON and exhausted its 256-token output cap. The response ended with `length`,
so it supplied no usable verdict. The runner stopped immediately under
`verifier_error_review_settings`, with run status `budget_stopped`. The numeric
budget was not exhausted; this status also covers guarded early stops.

The failed request concerned `mathqa_test_0047`, a maximum-equal-distribution
problem whose supplied proposal claims `gcd(1345,775)=91`, option a. The actual
GCD is 5. The response was cut off before a verdict; it is a technical error,
not a mathematical rejection or a false acceptance.

That request took 10.96 seconds, reported 273 input tokens, 256 output tokens,
zero reasoning tokens, and cost **$0.00014330**. Unlike the prior DeepSeek
reasoning-enabled failure, this response's reported token counts are internally
consistent. The strict requested output contract still failed in live use.
Increasing its cap or retrying it would be a new experiment, not an automatic
repair within this approval.

| Model / pinned provider | New calls | Input tokens | Output including reasoning | Reasoning subset | Actual new cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 2.5 Flash-Lite / Google AI Studio | 14 | 4,809 | 2,534 | 2,475 | $0.00149450 |
| Gemini 3.1 Flash-Lite / Google AI Studio | 15 | 5,105 | 822 | 747 | $0.00250925 |
| DeepSeek V3.2 / DeepInfra | 11 | 3,299 | 329 | 0 | $0.00083300 |
| Total | **40** | **13,213** | **3,685** | **3,222** | **$0.00483675** |

These are provider-reported charges, including the failed request. Reasoning is
part of output and is not charged a second time in this report. All costs are
known. Wall time was **73.65 seconds**. Known verifier-selection spend across
the pilot and both stopped comparisons is now **$0.00784018**.

## Coverage and observed quality

There are 53 observations out of 176 planned: thirteen reused and forty new.
The first inspected regression question, `mathqa_test_0002`, has all 24 planned
observations. Expansion question `mathqa_test_0026` also has all 24 observations.
Question `mathqa_test_0047` has five observations, including the failed request.
The other five planned questions were not reached. There are 52 usable Boolean
verdicts; eight concern an unknown acceptance label and are excluded from binary
quality calculations. Independent labels are assistant reviews, not human
annotations. No final workflow accuracy scores are assigned by this screen.

| Profile | Observed / planned | False acceptances / reviewed invalid | False rejections / reviewed valid | Technical errors |
| --- | ---: | ---: | ---: | ---: |
| Gemini 2.5 baseline | 6 / 22 | 3 / 4 | 0 / 1 | 0 |
| Gemini 2.5 recompute | 6 / 22 | 2 / 4 | 1 / 1 | 0 |
| Gemini 2.5 recompute plus reasoning | 7 / 22 | 1 / 5 | 0 / 1 | 0 |
| Gemini 3.1 baseline | 6 / 22 | 3 / 4 | 0 / 1 | 0 |
| Gemini 3.1 recompute | 6 / 22 | 2 / 4 | 0 / 1 | 0 |
| Gemini 3.1 recompute plus reasoning | 7 / 22 | 3 / 4 | 0 / 2 | 0 |
| DeepSeek baseline | 7 / 22 | 3 / 5 | 0 / 1 | 0 |
| DeepSeek recompute | 8 / 22 | 2 / 4 | 1 / 2 | 1 |

Coverage differs, so those raw counts are not a fair complete-model ranking.
For comparable coverage, all eight profiles produced verdicts on the same six
proposals from the first two reached questions. One proposal's label is unknown,
leaving only **five common labeled proposals**: four invalid and one valid.

| Profile | Correct verdicts on the five common labeled proposals |
| --- | ---: |
| Gemini 2.5 baseline | 2 / 5 |
| Gemini 2.5 recompute | 2 / 5 |
| Gemini 2.5 recompute plus reasoning | **4 / 5** |
| Gemini 3.1 baseline | 2 / 5 |
| Gemini 3.1 recompute | 3 / 5 |
| Gemini 3.1 recompute plus reasoning | 2 / 5 |
| DeepSeek baseline | 2 / 5 |
| DeepSeek recompute | 2 / 5 |

Gemini 2.5 with reasoning is the most promising partial signal, but it still
accepted an invalid solution. Its average observed cost, including historical
observations, was approximately $0.000196 per proposal and average call time
2.27 seconds across seven observations. Those costs describe reached examples,
not expected deployment expense over the full dataset.

Paired results keep regression and expansion separate. Relative to its own
baseline, Gemini 2.5's reasoning arm improved one labeled regression verdict
and one labeled expansion verdict, with no worsening among those five pairs.
Gemini 3.1's prompt-only arm improved one regression verdict; its reasoning arm
showed no improvement over baseline in the common pairs. DeepSeek recompute
improved one regression verdict but worsened another. The recorded pairs are
too few and related by question to establish population error rates or a
causal benefit from reasoning alone.

## Audit and recommended next checkpoint

The read-only audit confirmed forty finished new calls, no active calls, zero
new solver calls, and no final workflow scores. There are now 81 actual paid
verifier requests across three runs, all with known reported charges. Database
integrity and foreign-key checks pass; all six legacy batch tables exactly
match the pre-screening backup. The 89 offline tests passed before execution.
This checkpoint adds documentation and an ignored audit artifact only.

The initial recommendation was to address reliability rather than enlarge this
incomplete low-cost sweep blindly. Recommend setting aside the tested DeepInfra
profiles because both recomputation settings have now failed their output
contract, and preparing a small stronger-reference-verifier comparison on
saved failures alongside Gemini 2.5 with reasoning. Existing mathematical
mistakes remain in the record. Do not automatically select a verifier, increase
token caps, or resume the stopped plan. Model/provider choice and the exact
scope would require a fresh cost proposal before further paid calls. This
recommendation was superseded by the user's provisional selection above.

Verifier false acceptance stops the intended solver loop on a wrong answer,
so adding two retries cannot fix that path. A stronger verifier may reduce this
problem; it cannot be assumed error-free. Selection still needs independently
reviewed examples beyond the inspected failures.

Artifacts under ignored `results/workflow_previews/`:

- Run: `080d8889-63f7-4843-8b2f-9bcaa00ccd62`.
- Frozen plan: `verifier-comparison-amended-2026-10-07.json`.
- SHA-256: `c029aabf8ac09935f7a50cf855b33cd209e45dce8abacc070a06146c58643e4f`.
- Partial report: `verifier-comparison-amended-2026-10-07-results.json`.
- Billing/storage/common-coverage audit: `verifier-comparison-amended-2026-10-07-audit.json`.
