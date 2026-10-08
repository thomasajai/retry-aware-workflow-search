# Verifier pilot results — 2026-10-07

The user approved the 36-call pilot with a $0.05 spending limit. All 36 calls
completed in **28.57 seconds**, with **$0.00163967** in reported OpenRouter cost,
zero unknown cost measurements, and zero transport, provider, or verdict-format
errors. No extra calls, solver generations, retries, or reruns were made.

The screening integration works, but **no candidate is ready to freeze**:
each accepted one demonstrably incorrect natural solution. All passed the eight
binary-labeled synthetic diagnostics. The one uncertain synthetic diagnostic is
excluded from quality denominators. These results show why reviewed natural
answers matter; simple synthetic success did not predict flawless verification.

## Scope and execution evidence

Run ID: `090a84fd-9ef1-43fc-9663-178e7c042765`.
Start/end: `2026-10-07T22:58:43.381804+00:00` /
`2026-10-07T22:59:11.951994+00:00`.
Status: `completed`, with no budget-stop reason.

The unchanged, approved plan has SHA-256
`06abbdfd5f247872bc0727e11c5ade202ea3c808022cede217cd75c6a73701e3`.
It reused three saved solver answers to development question
`mathqa_test_0002`, plus nine usable synthetic diagnostics, once per verifier.
All calls used the requested model and pinned provider, returned HTTP 200 with
`stop`, and supplied the required single-Boolean JSON verdict. Every request
contained only the question, options, and solver proposal; answer-key and review
labels remained outside the runtime input.

## Actual cost and tokens

| Verifier / provider | Calls | Reported cost | Input tokens | Total billed output tokens | Reasoning tokens within output |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 2.5 Flash-Lite / Google AI Studio | 12 | $0.00029350 | 2,687 | 62 | 2 |
| Gemini 3.1 Flash-Lite / Google AI Studio | 12 | $0.00076175 | 2,687 | 60 | 0 |
| DeepSeek V3.2 / DeepInfra | 12 | $0.00058442 | 2,637 | 84 | 0 |
| Total | 36 | **$0.00163967** | 8,011 | 206 | 2 |

Actual reported cost was below the $0.00789713 expected estimate, the
$0.03450510 conservative reservations, and the $0.05 approved limit. The
estimate allowed larger input framing and substantially more output/reasoning
than was billed. Some DeepSeek responses reported cached prompt tokens; the
estimate assumed no cache discount. Actual costs include reported reasoning
and cache effects; reasoning is not charged a second time in these totals.

Gemini 2.5 reported two reasoning tokens in one response despite the request's
`reasoning.enabled=false`. Gemini 3.1 reported zero reasoning tokens with
`reasoning.effort=minimal`. We verified routing, output shape, and reported
usage, but this does not establish that every provider applied every internal
reasoning control exactly as intended. Preserve this observation when designing
the next profiles; do not assume a reasoning setting alone guarantees a specific
amount of mathematical checking.

## Verification judgments, kept separate from option grading

| Verifier | Natural invalid solutions accepted | Natural valid solutions rejected | Synthetic invalid solutions accepted | Synthetic valid solutions rejected |
| --- | ---: | ---: | ---: | ---: |
| Gemini 2.5 Flash-Lite | 1 / 2 | 0 / 1 | 0 / 4 | 0 / 4 |
| Gemini 3.1 Flash-Lite | 1 / 2 | 0 / 1 | 0 / 4 | 0 / 4 |
| DeepSeek V3.2 | 1 / 2 | 0 / 1 | 0 / 4 | 0 / 4 |

The natural sample consists of three outputs from **one question**, so its
observations are related and cannot establish a population error rate or rank
these models reliably. The assistant independently reviewed the labels; they
are not human annotations. All three accepted the valid natural solution and
rejected the uncertain synthetic rounding case. The uncertain case has no
binary quality label and does not count as a demonstrated correct rejection.

For the natural ticket question, there are 28 intermediate stations plus two
endpoints. Thirty origins each have 29 other destinations, so the intended
answer is **30 * 29 = 870, option c**.

| Saved proposal | Independently checked problem | Gemini 2.5 | Gemini 3.1 | DeepSeek |
| --- | --- | --- | --- | --- |
| `28*(28-1)/2=380`, option e | Excludes endpoints and uses unordered pairs; the displayed expression is 378, not 380. | **Accept — incorrect** | Reject | Reject |
| `(28+2)*(28+1)/2=380`, option e | Uses unordered pairs; the displayed expression is 435, not 380. | Reject | **Accept — incorrect** | **Accept — incorrect** |
| `stations=28+2=30, tickets=30*29=870`, option c | Valid setup, arithmetic, and option mapping. | Accept | Accept | Accept |

These mistakes are independently verifiable arithmetic errors as well as
wrong-option acceptances. They are not just disagreements over the answer key
or a formatting rule. The Boolean responses contain no explanation, so we
cannot identify the internal cause of the mistakes from this pilot.

The synthetic cases include a correct option with invalid reasoning; all
candidates rejected that case. Natural and synthetic outcomes remain separate,
and verifier decisions never overwrite independent correctness labels. These
are screening executions, not three-attempt workflow runs; no deployment
workflow score was assigned.

## Records and validation

- Raw responses, request snapshots, usage, timing, and review labels are saved in
  `results/mathqa_runs.sqlite3`.
- Summary: `results/workflow_previews/verifier-pilot-2026-10-07-results.json`.
- Offline audit, including the three false-acceptance traces:
  `results/workflow_previews/verifier-pilot-2026-10-07-audit.json`.
- The source database's legacy rows still match the pre-screening backup.
  Integrity is `ok`, with zero foreign-key errors or unfinished calls.
- Workflow records now contain one run, three configurations, and 36 executions,
  attempts, verifier calls, and independent grades. There are zero new paid
  solver calls.
- The runner had 71 passing offline tests before execution. The audit reused
  saved responses and made zero additional generation requests.

Generated plans, raw reports, database, and backups remain ignored by Git. This
results note records the durable conclusion alongside source-controlled code.

## Recommendation and checkpoint

Keep Milestone 2 open. Do not select a verifier solely from these twelve trials
per model, and do not launch the larger screen with an assumption that the
current profiles are reliable. The integration and cost accounting have been
demonstrated, but the natural false acceptances need attention.

The next experiment should compare a profile that explicitly recomputes the
solution independently with a modest reasoning allowance against the unchanged
baseline. Include these failures as development regression cases and more
reviewed natural answers; do not treat the already inspected failures as fresh
held-out evidence. Separate prompt/settings effects from model differences.
More reasoning is a hypothesis to test, not a guarantee of correctness.

Prepare exact follow-up requests and a new cost proposal before running them.
Reuse existing judgments for unchanged requests and avoid automatically
repeating the successful synthetic diagnostics. No additional paid run has been
authorized or scheduled. The LangGraph retry-loop demonstration remains
Milestone 3, after a verifier is chosen and frozen.
