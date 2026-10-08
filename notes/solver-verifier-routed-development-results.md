# Routed development comparison — partial results, October 8, 2026

The user approved one 540-execution comparison with a $4.25 cap and at most
3,240 gateway requests. It stopped after **223 requests and $0.0284535204
reported spend**, with no new unknown charges. A fully billed DeepSeek solver
response hit its 512-token output limit; the frozen v4 policy treated this as a
global gateway failure. The spending cap was not exhausted. No rerun, resume,
token increase or held-out evaluation followed.

## Execution and coverage

- Run: `d26ac343-7c1d-4369-91d1-f54a96dffb00`.
- Clean execution revision: `ab02535994a1f7a0e864897f13aee1d8a74fa3ae`.
- Approved [proposal](solver-verifier-routed-development-proposal.md).
- Frozen plan: `results/workflow_previews/routed-development-final-plan-2026-10-08.json`.
- Plan SHA-256: `c4b21c8648a92095120120b97822b5c75c75a38380dc703041e9e7edcf4e1581`.
- Start/end: 19:11:28–19:18:48 UTC (3:11:28–3:18:48 p.m. EDT); 440.17 seconds.
- Requests: 222 completed, one failed; zero client transport retries.
- Executions: 59 independently graded, one incomplete, 480 unreached out of 540.
- Finished outcomes: 46 accepted final options matching the key, 13 exhausted
  executions scoring zero. No accepted final option disagreed with the key.
- Complete question blocks: `mathqa_test_0435` (20 accepted, seven exhausted)
  and `mathqa_test_0661` (26 accepted, one exhausted), 27 configurations each.
- `mathqa_test_0187`: five exhausted executions, then one incomplete execution.

The completed-only answer-key mean is 46/59 (77.97%). This partial coverage is
not the twenty-question comparison. No full ranking or accuracy/cost Pareto
frontier is emitted, no missing scores are imputed, and earlier runs are not
pooled. Automated reasoning-validity labels remain unreviewed; accepted key
matches do not establish valid reasoning.

## Reported spend

| Role/model | Observed provider(s) | Requests | Reported USD |
| --- | --- | ---: | ---: |
| Qwen2.5 7B solver | Phala | 39 | $0.00133780 |
| Qwen3 32B solver | SiliconFlow | 36 | $0.00211561 |
| DeepSeek V3.2 solver | DigitalOcean, GMICloud, Baidu | 37 | $0.0038872104 |
| Gemini 2.5 Flash-Lite verifier | Google AI Studio | 111 | $0.02111290 |
| **Total** | | **223** | **$0.0284535204** |

DeepSeek's provider breakdown is DigitalOcean: 24 calls/$0.00287520; GMICloud:
seven/$0.0004475304; Baidu: six/$0.00056448. Total input/output tokens were
62,921/49,364. Verifier output includes 44,218 reasoning tokens once, not as
additional billed output. All new costs are reported; there are no held
unknown-cost reservations or 429/503 responses in this run.

Across the five development/availability runs, reported costs now total
**$0.04035774869 plus the same five previously unresolved charges**. This is
not a whole-project/account total. The new run does not reconcile those old
failed-request charges.

## Stop and data issue

The last call, `8892c469-c785-4265-97f1-a919a9a667ca`, was DeepSeek/DigitalOcean
in mathematical slot three of `qwen3-qwen25-deepseek`, on `mathqa_test_0187`.
It returned HTTP 200, `finish_reason=length`, 254 input tokens, 512 output
tokens, zero reasoning tokens, and $0.00054084 reported cost. Model/provider,
usage, price and reservation checks passed. Its unfinished calculation had no
usable final option; no verifier request was sent. The runner classified
`IncompleteGeneration` as `gateway_failure` and halted before grading this
execution. The stored status `budget_stopped` is a generic guard-stop status,
not evidence that the $4.25 cap was reached.

This question describes a squirrel spiraling around a post, rising three feet
per circuit, with height eighteen feet and circumference three feet. Unrolling
the cylinder gives eighteen feet horizontally and eighteen vertically, so the
path is `18 * sqrt(2)`, about **25.46 feet**. None of the five options (10, 12,
13, 15, 18 feet) matches; the MathQA key is 18 feet. This is an independently
identified option/key inconsistency. Preserve and flag the record: do not
replace the selected question or silently change the grading key after seeing
performance. Dataset adjudication is a separate later decision.

There were 45 rejected attempts whose selected option matched the key. They
are not automatically false rejections: their reasoning has not all been
reviewed, and the key can be problematic. Of 51 usable retries, 37 repeated a
previous option/value; 19 of 32 finished executions with a first rejection
eventually obtained an accepted key match. These are descriptive partial-run
diagnostics, not verifier-reliability estimates.

## Audit and next checkpoint

The read-only audit reconstructs exact frozen solver/verifier requests,
configuration/schedule identities, independent grades, request counts, slot
limits, chronological budget gates, provider/usage/price checks, role/provider
sums and completed-only reporting. SQLite integrity is `ok`, foreign-key errors
are zero, and fingerprints confirm all prior rows are preserved. The audit
leaves the database unchanged. A pre-run SQLite backup is saved at
`results/backups/routed-development-before-2026-10-08.sqlite3`.

Local artifacts (ignored by Git):

- `results/workflow_previews/routed-development-report-2026-10-08.json`.
- `results/workflow_previews/routed-development-after-audit-2026-10-08.json`.
- Database SHA-256 after the run:
  `51caacf0dba973ed0f654a19491d9666ede8d8cbe4ce081abea8074ebc2b6514`.

An offline, opt-in v5 amendment now treats a fully reconciled, length-truncated
solver answer as unusable within the existing three-attempt allowance. It
preserves the failed call and its cost, skips verification of partial output,
and keeps all billing/identity/usage/price guards. All **174 offline tests pass**
(137.015 seconds). Original v1–v4 configurations retain their behavior. No
migration, dependency or token-limit change is required.

The [v5 rerun proposal](solver-verifier-routed-development-v5-proposal.md)
required fresh approval; the user subsequently approved it and the separate
[run completed](solver-verifier-routed-development-v5-results.md). This
historical run stays partial under its original policy, with no retroactive
regrading, resumed calls or pooled observations. Milestone 4 remains open for
finalist assessment; no further paid run is authorized.
