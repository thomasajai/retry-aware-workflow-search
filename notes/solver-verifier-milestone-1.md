# Milestone 1: offline foundation completed

Completed: 2026-10-06. OpenRouter requests: **0**. New OpenRouter cost: **USD 0**.
The planning documents were committed first as `5bcac0e` (`docs: plan solver-verifier workflow and budget controls`). Implementation changes are available for review; no paid stage has begun.

## What is available

- Additive workflow storage for experiments, configuration snapshots, per-question executions, reached attempts, actual API-call records, and independent grades. Numeric measurements preserve unknown values as `NULL`; historical saved solver calls are not counted as newly paid calls.
- Numbered, checksummed migrations with an automatic backup before upgrading an existing database. Workflow migrations apply in a transaction and repeated application is a no-op.
- An offline-only verifier-screening preview. It reads completed saved answers, verifies the dataset checksum, distinguishes usability from legacy formatting, and builds exact candidate requests using only the question, choices, and solver proposal. It never sends them.
- Proposed candidate profiles for Gemini 2.5 Flash-Lite, Gemini 3.1 Flash-Lite, and DeepSeek V3.2. Provider/control support and current pricing remain to be checked in Milestone 2. The preview reports future cost estimates as unknown, not free.
- Twelve hand-authored synthetic diagnostic cases with explicit assistant-review provenance. They test valid reasoning, valid shortcuts, cosmetic format violations, wrong options, correct options with false arithmetic, wrong problem interpretation, value conflicts, unusable output, and an uncertain rounding convention.

The reviewed cases are **assistant-reviewed synthetic diagnostics**, not human annotations or a representative natural-error dataset. They contain eight usable binary-labeled examples, one usable uncertain example, and three unusable examples. Unknown reasoning labels stay unknown. More independent review of natural responses is needed for verifier selection; no candidate verdict was used to create labels.

## Saved-answer preview result

Source: run `6e8ba4fd-3f6d-41f9-9522-23c84e0d332d`, first 20 selected questions, three solver models.

| Item | Count |
| --- | ---: |
| Saved source attempts | 60 |
| Usable natural answers | 56 |
| Unusable natural answers | 4 |
| Usable answers that failed legacy strict formatting | 24 |
| Reviewed synthetic diagnostics | 12 |
| Usable reviewed diagnostics (including one uncertain case) | 9 |
| Potential natural-answer calls across three candidates | 168 |
| Potential diagnostic calls across three candidates | 27 |
| Total potential verifier calls | 195 |
| Calls actually made | 0 |

The unusable natural answers are Qwen2.5's non-option `none` on question 0102 and three truncated DeepSeek generations on questions 0108, 0187, and 0237. They have no proposed verifier request. The 24 usable legacy format violations are retained for mathematical verification instead of rejected for cosmetic or calculation-length rules.

All 56 usable natural answers have answer-key comparisons and **unknown reasoning validity**. Their offline labels are separated from proposed requests. Diagnostic cases and natural answers are separate populations; the uncertain rounding case must be excluded from binary verifier-quality denominators.

Each proposed candidate would make 56 natural plus 9 diagnostic calls, or 65 calls. This is a request-count preview, **not a live-run authorization or a cost quote**. Reasoning/output usage and current provider rates must be checked before estimating or spending credits. The source calls' historical known cost, USD 0.00396901, is provenance only and was not spent again.

Full local preview: [milestone-1.json](../results/workflow_previews/milestone-1.json).

## Database upgrade verification

Applied migration `001_workflow.sql` to the local results database after creating a verified SQLite backup. Fingerprints of every pre-existing row matched before and after the upgrade, and matched the backup. SQLite integrity and foreign-key checks passed. All six new workflow tables are empty; no experimental executions or calls were inserted in the production results database.

| Existing table | Rows preserved |
| --- | ---: |
| `runs` | 17 |
| `calls` | 538 |
| `call_validations` | 475 |
| `run_gradings` | 2 |
| `call_gradings` | 360 |
| `model_gradings` | 6 |

Local backup: `results/backups/mathqa_runs_20261006T231105_3b3f72cd.sqlite3`.
Local verification report: [milestone-1-storage.json](../results/workflow_previews/milestone-1-storage.json).
Backups and preview artifacts are ignored by Git; they contain local experimental evidence.

## Verification and next milestone

All **53 offline tests passed**: 26 existing regression tests plus 27 new checks. Coverage includes fresh schema/upgrades, backup preservation, migration checksum/rollback, configuration and repetition identities, verdict/grade separation, unknown costs and reasoning tokens, saved-answer provenance, credential removal, input leakage, unusable-answer handling, and a CLI that rejects paid execution. HTTP activity in existing tests uses mocked transports; no OpenRouter request was sent.

The usability extractor intentionally permits readable prose, long calculations, one enclosing code fence, and explicitly logged option case/outer-whitespace normalization. It never infers a missing option from a value or repairs ambiguous JSON. A missing returned value does not hide an otherwise explicit option; a supplied conflicting value is retained for mathematical verification. These extraction settings should be reviewed and frozen before a live stage.

Work stops here for milestone review. Milestone 2 will finalize provider support, verifier settings, natural reasoning review, quality targets, and an explicitly disclosed cost breakdown/spend limit before any live verifier experiment. The paid runner and LangGraph retry loop have not been implemented or exercised yet.
