# Milestone 2 preparation — 2026-10-07

Milestone 1 is committed as `c25aa92` (`feat: add offline workflow storage and
verifier screening previews`). Milestone 2's offline preparation is complete.
At preparation time, no paid generation requests had been made. The user has
since approved the proposed pilot; [its results](solver-verifier-pilot-results.md)
record 36 completed calls costing $0.00163967. No verifier has been selected.
The work in this report is still uncommitted for review.

## Implemented

- Free public endpoint metadata lookup and a price/control preflight, with no
  API key or generation call. Candidate endpoints advertise the requested
  temperature, token limit, reasoning, and response-format controls. Live
  behavior is still untested.
- Strict Boolean JSON schema and pinned provider profiles for Gemini 2.5
  Flash-Lite, Gemini 3.1 Flash-Lite, and DeepSeek V3.2. No provider fallback;
  Gemini flexible/priority tiers are excluded. The frozen pilot requests also
  include provider price ceilings in dollars per million tokens.
- Assistant reviews of 22 usable natural outputs from the first eight
  development questions, independently calculated without candidate calls:
  ten valid, eleven invalid, and one unknown acceptance label. Exact answer
  hashes, source call IDs, and dataset checksum bind these labels to the saved
  evidence. These are assistant reviews, not human annotations or an unbiased
  estimate of production accuracy.
- A frozen, checksummed pilot plan containing exact requests and offline labels
  separately. Execution rebuilds the plan against current source evidence,
  review files, and request builders before making any paid call. Metadata
  expires after 24 hours; source/profile changes require a new plan and notice.
- A serial paid runner requiring explicit execution, spending limit, request
  cap, and a new report destination. It has zero client retries and no new
  solver calls. A unique plan hash in SQLite prevents automatic rerun/resume of
  the same plan in the same database.
- Durable responses, full raw payloads, token/cost measurements, elapsed time,
  review provenance, and outcomes. Missing or malformed cost measurements stay
  unknown and stop further scheduling. Provider/model drift, unknown token
  usage, inconsistent reasoning usage, or exceeded reservations also stop it.
- Reports separate natural and synthetic results, attempted versus planned
  coverage, wrong-option acceptance, invalid-reasoning acceptance, valid-solution
  rejection, technical/format errors, unknown labels, known cost, unreconciled
  reservations, and reasoning-token measurements. Quality denominators include
  binary-labeled valid verdicts; reviewed attempted counts and error coverage
  remain visible. Screening does not assign deployment workflow scores.

## First paid pilot proposal — subsequently approved and completed

Purpose: establish that the pinned providers honor controls and return usable
Boolean verdicts, inspect clear acceptance/rejection mistakes, and measure actual
usage/cost before the larger screening experiment. Offline checks establish
local behavior; they cannot establish live provider behavior or verifier judgment.

Scope: the first saved development question has three usable solver answers.
Add nine usable synthetic diagnostics (eight binary-labeled and one uncertain).
Each of the three verifier candidates receives all twelve proposals once:
**36 expected/maximum generation requests**, zero new solver requests, and zero
transport retries. Early budget/error stops can reduce the count. A pilot of
this size cannot establish reliability or select the final verifier.

Source batch: `6e8ba4fd-3f6d-41f9-9522-23c84e0d332d`.
Question: `mathqa_test_0002`. Saved solver responses are reused at no new charge.
Dataset SHA-256:
`07ec007c4ad73eb40b57d8b494429f73e37e0c2d79cf1c6b90debf3f05ebbaca`.

Public metadata was fetched at **2026-10-07 22:39:11 UTC** (18:39:11 New York).
Exact pinned endpoint prices:

| Candidate / provider pin | Calls | Input / output USD per million | Estimated input tokens, total | Assumed output per call / cap | Estimated subtotal |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 2.5 Flash-Lite / `google-ai-studio` | 12 | $0.10 / $0.40 | 4,901 | 32 / 256 | $0.00064370 |
| Gemini 3.1 Flash-Lite / `google-ai-studio` | 12 | $0.25 / $1.50 | 4,901 | 256 / 1,024 | $0.00583325 |
| DeepSeek V3.2 / `deepinfra/fp4` | 12 | $0.26 / $0.38 | 4,901 | 32 / 256 | $0.00142018 |
| Total | 36 | | 14,703 | | **$0.00789713** |

Input estimates use question/proposal/prompt characters divided by three plus
96 framing tokens per request. Total billed output includes reasoning, counted
once. Gemini 2.5 and DeepSeek request reasoning disabled; Gemini 3.1 requests
minimal effort, so it has a larger planning assumption and total output limit.
Expected input/output cost components are $0.00049010/$0.00015360,
$0.00122525/$0.00460800, and $0.00127426/$0.00014592 respectively. No cache
discount is assumed.

Conservative reservations use the full request's UTF-8 byte size plus 256 framing
tokens and the full output-token limit, at the larger completion/reasoning rate.
Subtotals are $0.00350580, $0.02413950, and $0.00685980:
**$0.03450510 total**. This is an intentionally generous scheduling estimate,
not a guaranteed bound on provider billing. The proposed scheduling spending
limit is **$0.05**, with a **36-request cap**. The user approved these limits
before execution; the completed run remained within them.
Before each request, known actual spending plus its reservation must fit the
limit. Unknown costs or actual usage exceeding reservations stop the run for
review; no follow-up or larger batch runs automatically.

Frozen pilot plan:
`results/workflow_previews/verifier-pilot-2026-10-07.json`.
SHA-256: `06abbdfd5f247872bc0727e11c5ade202ea3c808022cede217cd75c6a73701e3`.
Free metadata: `results/workflow_previews/provider-metadata-2026-10-07.json`.
These generated artifacts remain ignored by Git. The reviewed fixtures, runner,
tests, and this proposal are source-controlled files.

## Verification and storage

**71 offline tests passed**, including 18 new screening tests with mocked HTTP
and disposable databases. They cover caps before scheduling, missing/invalid
billing, partial results, no retries, cancellation, duplicate-run blocking,
request/label separation, source/hash drift, stale metadata, provider drift,
reasoning accounting, separate quality counts, and offline-source invariants.

Migration `002_screening.sql` was applied to the local results database after
backup at `results/backups/mathqa_runs_20261007T225436_efafda18.sqlite3`.
All legacy rows match their prior contents and the backup: 17 runs, 538 calls,
475 validations, two run gradings, 360 call gradings, and six model gradings.
SQLite integrity is `ok`, with zero foreign-key errors. All six workflow tables
remain empty, confirming zero paid screening calls. The verification artifact is
`results/workflow_previews/milestone-2-storage.json`.

## Next checkpoint

The approved pilot completed with no missing billing or technical errors, but
each candidate accepted one incorrect natural solution. See the
[results and next-experiment recommendation](solver-verifier-pilot-results.md).
The larger 195-call comparison remains unexecuted. Choosing and freezing a
verifier requires addressing these failures, a larger reviewed comparison, and
explicit reliability criteria. The LangGraph retry loop remains Milestone 3.

Primary references: [provider routing and price ceilings](https://openrouter.ai/docs/guides/routing/provider-selection),
[reasoning token controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens),
[Gemini 2.5 endpoint metadata](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash-lite/endpoints),
[Gemini 3.1 endpoint metadata](https://openrouter.ai/api/v1/models/google/gemini-3.1-flash-lite/endpoints),
and [DeepSeek endpoint metadata](https://openrouter.ai/api/v1/models/deepseek/deepseek-v3.2/endpoints).
