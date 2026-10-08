# Availability check exhausted bounded retries — October 8, 2026

The user approved the [six-execution check](solver-verifier-availability-proposal.md)
with a $0.05 cap, 38 maximum physical requests, and up to $0.002 of held
reservations for two eligible unreported 429 charges. The single run stopped
after **seven physical requests**: two completed executions followed by three
consecutive DeepSeek/Venice upstream 429s. The runner waited **30 seconds and
60 seconds**, used both approved transport retries, and stopped at the retry
limit. No restart, provider fallback or additional paid request occurred.

The bounded retry mechanism was exercised live and its safeguards passed the
postflight audit. It did not restore provider availability in this window.
The six-execution check and Milestone 4 remain incomplete.

## Frozen run and coverage

- Run `a9bec429-872a-4bce-bad9-f39dde9a1170`.
- Code `ea00f66112c3ee93c356ca083d91b3c0d9e27092`, clean at execution start.
- Plan SHA-256 `2ec0304ea57c393bbe8334bac301e1099b32d73b03709a40a5afab7c93f1f5e3`.
- Started `2026-10-08T18:14:43.379801+00:00`; stopped
  `2026-10-08T18:16:30.430959+00:00`; elapsed 107.051158 seconds.
- Status `budget_stopped`, reason `rate_limit_retry_limit`, well below the
  scheduling cap. This is an infrastructure stop, not dollar-cap exhaustion.
- Two of six executions finished, one incomplete, three unreached.

The first repetition of each question finished in its first mathematical slot:
`mathqa_test_0002` selected `c`, value `870`; `mathqa_test_0047` selected `d`,
value `5`. Gemini accepted both, and both independently matched the dataset
key. This is an integration observation on two previously used questions, not
evidence of general accuracy, reasoning validity or a best configuration.

The second repetition of `mathqa_test_0002` stopped in its **first mathematical
slot** after three physical HTTP transmissions of the exact same solver request.
It has no usable answer, verifier call or final grade. No second mathematical
solver slot was consumed by transport retries.

## Actual spending and unresolved billing

| Role/model | Physical requests | Known input tokens | Known output tokens | Reasoning within output | Known cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek V3.2 / Venice | 5: two successful, three 429s | 481 | 107 | 0 | $0.00016195773 |
| Gemini 2.5 Flash-Lite / Google AI Studio | 2 successful | 640 | 818 | 812 | $0.00039120 |
| Total | 7 | 1,121 | 925 | 812 | **$0.00055315773** |

All three 429s have **unreported charges and usage**. Token totals above exclude
their missing measurements. The first two failed calls each retain a
$0.00060277446 reservation, totaling **$0.00120554892 held inside the approved
cap**. Known spend plus these authorized holds is **$0.00175870665**. This is
budget-accounted exposure, not a settled bill or a guaranteed billing maximum.

The terminal third error has no authorized hold because recovery was exhausted;
no more requests followed it. Its saved pre-call reservation was also
$0.00060277446, an estimate rather than a charge. Do not classify any failed
call as free or infer its charge from a reservation. The partial run cannot
establish the proposed six-execution expected cost of $0.00491167056.

Together with the two prior development attempts, these three runs have
**$0.00990433555 known spend and five unresolved charges**. Other historical
project calls remain separate; this is not the account's total spend.

## Rate-limit evidence and free account check

Each failed response named Venice and
`limit_source=upstream_provider_shared_pool`, with a 30-second retry hint.
The second cooldown increased to 60 seconds under the frozen backoff policy.
No response supplied a generation ID for per-generation billing reconciliation.
The physical call IDs were `b4f12efd-57a6-4d02-a693-729cc1f232ac`,
`334ef1d2-e7e3-4666-be99-8cec423fcc43`, and
`4f8174c6-ae15-4424-9af8-0dd4042fbe58`, sharing logical solver call
`81ae8770-77e0-43c5-a0e2-6f4fb61e5b57`.

A free, authenticated read-only `GET /api/v1/key` at
`2026-10-08T18:18:17.873415+00:00` reported `is_free_tier=false`, key spending
limit $250, and $249.942368831 remaining under that limit. Aggregate key usage
was $0.057631169. This shows the key cap was not exhausted; it is not a statement
of prepaid wallet balance or a per-call bill. OpenRouter's
[limits documentation](https://openrouter.ai/docs/api_reference/limits) defines
these fields and distinguishes upstream 429s from credit-limit errors.
The key snapshot is consistent with the error's upstream-capacity classification,
but does not establish the provider's exact quota or resolve individual charges.
No model generation occurred during this additional check, and no credentials
or identifying key fields were included in its saved diagnostic.

## Audit and preservation

The preflight validated the approved source/data/migration-bound plan and backed
up the database to `results/backups/availability-before-2026-10-08.sqlite3`.
The runner then applied `003_transport.sql`, with the migration framework's
additional backup at
`results/backups/mathqa_runs_20261008T181443_945d79b3.sqlite3`.

The independent read-only audit confirms every old row is preserved, migration
checksums match, integrity is `ok`, and there are no foreign-key errors. Every
logical and physical request reconstructs exactly from the original question,
frozen profile, solver proposal and price ceilings. Physical ordinals, actual
cooldown intervals, two shared transport retries, held allowance and
chronological spending gates all satisfy the approved limits. Independent
attempt/final option grades match the dataset; incomplete work remains ungraded.
There is no double counting of logical and physical requests. Audit reads leave
the database unchanged. No code repair was needed; the prior 153 passing offline
checks remain applicable.

Ignored artifacts under `results/workflow_previews/`:

- `availability-retry-report-2026-10-08.json`.
- `availability-before-audit-2026-10-08.json` and `availability-after-audit-2026-10-08.json`.
- `availability-account-limits-2026-10-08.json`.
- `availability_preflight_20261008.py`, `availability_progress_20261008.py`,
  `availability_postflight_20261008.py`, and `availability_account_limits_20261008.py`.

## Next checkpoint

The implementation handled the expected failure safely, but this provider/model
setup remained throttled after the approved cooldowns. Do not repeat the broad
evaluation or expand retry limits automatically. I recommend preparing a
replacement third solver using free catalog/provider metadata while keeping
Gemini and the workflow rules fixed, then proposing a small costed live check.
Changing the solver changes the experiment definition and must be frozen
explicitly. These observations do not prove every other DeepSeek provider is
unavailable or that another solver will be more accurate. No replacement model,
additional paid diagnostic or broad evaluation is authorized by this single-run
approval.
