# DeepSeek automatic routing results — October 8, 2026

The user approved the single check in the
[routing proposal](solver-verifier-routing-proposal.md): **$0.07 cap, at most 36
gateway HTTP requests**, six executions, no client transport retries. It
completed successfully. No additional paid run, automatic restart, or broad
evaluation followed.

## Outcome and cost

- Run: `f42737a8-799e-4c8d-b5e1-c7bb6406597c`.
- Code: `862938d3fdb1b0da0093b7a6a616e914fabf49dd`, clean at initiation.
- Frozen plan SHA-256:
  `7b57f9602545463503be34e0b6066690c4ad1f385b6a3cccfbba20400233ff59`.
- Started **2026-10-08 18:51:57 UTC (2:51:57 p.m. EDT)**; finished
  **18:52:34 UTC (2:52:34 p.m. EDT)**; wall time **37.254203 seconds**.
- **6/6 executions completed**, all accepted final options match the independent
  MathQA keys. This is two previously exposed questions, each repeated three
  times, not six independent questions or a general accuracy estimate.
- **14 requests**, seven solver and seven verifier; all HTTP 200 with complete
  outputs, reported usage and costs. Zero reported technical errors, unknown
  costs, held reservations, or client network retries.
- Reported new cost **$0.00199989274**, about **$0.002 / 0.2 cents**, below the
  $0.0079968 planning estimate and the $0.07 cap.

| Role/provider | Requests | Reported input/output tokens | Reported cost |
| --- | ---: | ---: | ---: |
| DeepSeek / AtlasCloud | 1 | 242 / 40 | $0.00007812000 |
| DeepSeek / DigitalOcean | 1 | 239 / 59 | $0.00012834000 |
| DeepSeek / Venice | 1 | 242 / 79 | $0.00009575514 |
| DeepSeek / GMICloud | 4 | 962 / 220 | $0.00026897760 |
| **DeepSeek subtotal** | **7** | **1,685 / 398** | **$0.00057119274** |
| Gemini / Google AI Studio | 7 | 2,227 / 3,015 | $0.00142870000 |
| **Total** | **14** | **3,912 / 3,413** | **$0.00199989274** |

Solver reasoning usage was zero. Gemini reported 2,997 reasoning tokens as a
subset of its 3,015 output tokens; they are counted once. Every reported provider
was in the frozen eligible set, all observed prices/usage fit the applicable
ceilings and reservations, and the original model IDs/settings were preserved.

The gateway request count cannot reveal individual internal provider attempts
or prove that no upstream provider encountered an error before a successful
gateway response. Every gateway request in this check has a reported charge;
there is no newly unresolved billing in the saved responses. The prior three
development/availability runs remain **$0.00990433555 known plus five unresolved
charges**. Across these four runs, known costs total **$0.01190422829 plus those
same five unresolved charges**; this is not all project/account spending.

## Loop behavior and verifier limitation

For `mathqa_test_0002`, the station-ticket problem, repetition one:

1. AtlasCloud returned `stations=28+2=30; total_pairs=30*29=870`, option `c`,
   value `870`. Gemini rejected it.
2. The solver received the exact original request again, without prior work,
   verifier feedback, answer key, or retry hint. DigitalOcean returned the same
   mathematical setup with a more explicit station/ticket calculation. Gemini
   accepted it; independent option-key grading scored one.

The remaining five executions were accepted on their first attempt. All three
ticket executions ended with `c / 870`; all three distribution executions ended
with `d / 5`, using the GCD of 1,345 and 775. There were zero unusable answers,
one verifier rejection and six acceptances. This check exercised a live
mathematical retry and early stopping. The third attempt was not reached here;
its behavior remains covered by prior live integration and offline tests.

**Assistant reasoning review:** all seven saved solver calculations are valid
for these questions. Thirty total stations yield `30*29=870` directed tickets;
the displayed Euclidean reductions correctly give `gcd(1345,775)=5`. The first
rejection is therefore an observed false rejection under our reasoning/option
acceptance contract, despite recovery on the next attempt. This review is
separate from the option-key grader: stored automatic `reasoning_valid` labels
remain `NULL`, and verifier acceptance alone does not establish reasoning
validity. The saved verdict does not establish the cause; no verifier prompt,
token budget or model was changed to address it. This tiny repeated sample
cannot estimate verifier error rates.

## Storage and audit

All 165 offline tests passed before execution. An independent read-only audit of
the live result passed:

- SQLite integrity and foreign-key checks; every pre-existing row's fingerprint
  matches the pre-run snapshot. Existing migrations are unchanged.
- Exact reconstruction of every solver/verifier request from frozen controls
  and current question/parsed proposal, including original-only mathematical
  retries, provider filters and price ceilings.
- Schedule/repetition/configuration identity, at most three mathematical slots,
  independent option grades, accepted-attempt identity and full coverage.
- Chronological request-count and pre-call spending gates; recomputed
  reservations, actual provider and token/cost limits, no unknown-billing
  continuation, no client transport retries or double counting.
- Role/provider subtotals equal the reported total, and the audit itself did
  not modify the database.

Local evidence, ignored by Git:

- `results/workflow_previews/routed-availability-report-2026-10-08.json`.
- `results/workflow_previews/routed-before-audit-2026-10-08.json`.
- `results/workflow_previews/routed-after-audit-2026-10-08.json`.
- Backup: `results/backups/routed-before-2026-10-08.sqlite3`.

## Next checkpoint

Keep DeepSeek with this routing policy and Gemini as the provisional verifier.
The successful small check supports preparing the balanced twenty-question,
27-sequence development comparison. It does not demonstrate sustained capacity
or resolve the verifier's observed false rejection. Keep the original question
selection, prompts and mathematical retry rules fixed, and report provider
variability and independent correctness separately.

Any broad run needs a new frozen plan and advance role-by-role cost notice with
explicit approval. No further model credits are authorized by this result.
Milestone 4 remains open.
