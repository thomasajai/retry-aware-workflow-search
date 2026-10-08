# Project decision log

Last reviewed: 2026-09-25. This records the current plan, not experimental results. Sources are the team's [project description](../PROJECT.md), our design discussion, and the team slides appended to [Related Work + First Experiment.pptx](../Related%20Work%20%2B%20First%20Experiment.pptx) (slides 11–18). A statement appearing in the deck is marked separately from a choice the user made explicitly in conversation.

## October 6 planning update

Latest October 8 execution checkpoint: the user approved the routed development
comparison. It [stopped](solver-verifier-routed-development-results.md) after
223 requests/$0.0284535204 reported cost, with no new unknown billing. Fifty-nine
executions were graded (46 accepted key matches, 13 exhausted), one incomplete,
480 unreached; two complete question blocks and no full ranking. DeepSeek's
fully billed HTTP 200 output hit 512 tokens in slot three; v4 treated that as a
global gateway failure. The spend cap was not reached. Record the independent
geometry/option-key inconsistency in `mathqa_test_0187`, preserving the selected
dataset and grading key pending separate adjudication.

An [opt-in v5 amendment](solver-verifier-routed-development-v5-proposal.md)
counts this narrow known-cost solver truncation as unusable within the existing
three-attempt allowance. No verification of partial text or extra HTTP retry;
all identity/usage/price/billing/budget guards remain. All 174 offline tests pass,
prior configuration policies/records stay intact, and no migration/dependency
change is required. A separate fresh 540-execution run retains the original
questions, model controls and costs: $0.48995280 estimate, $3.75507954 stress
reservations, $4.25 cap, maximum 3,240 gateway requests. Its frozen plan binds
the amended policy and migration hashes. Fresh paid approval is pending;
the previous run's approval is consumed. No automatic continuation occurred.

Latest October 8 checkpoint: the user requested preparation of the balanced
27-configuration comparison after the routed check. The
[routed development proposal](solver-verifier-routed-development-proposal.md)
freezes the same twenty questions, shuffled schedule and one repetition: 540
executions. Expected new cost $0.48995280, conservative reservations $3.75507954,
proposed cap $4.25, at most 3,240 gateway HTTP requests; no client network retries
or automatic follow-up. Metadata refreshed at 18:57:33 UTC. Provider status had
changed since the check, so allow known compatible metadata providers to return
after temporary inactivity while preserving the outgoing routing/price policy;
require at least one active compatible provider at preflight. This changes only
response recognition. All 166 offline tests and the read-only scope, arithmetic,
frozen-plan and database audit pass; preparation consumed no credits. This
single paid run was subsequently approved and stopped as recorded above.
Historical runs remain separate.

Latest October 8 checkpoint: the user proposed keeping DeepSeek without a
provider pin and authorized implementation, offline tests, a commit, and a
fresh small-check proposal. The
[routing proposal](solver-verifier-routing-proposal.md) replaces the earlier
recommendation to find another solver. The `auto` workflow profile uses default
OpenRouter routing, provider fallbacks, required parameter support, and fixed
$0.60/$1.70 per-million input/output price ceilings. Freeze eligible identities
for response audits and record actual providers; reserve at ceiling prices.
No client network retries or unknown-billing exception in this profile. The
small check is six executions, expected $0.0079968, $0.07 cap, at most 36 gateway
HTTP requests. Internal provider attempts are unobserved. Implementation and
free metadata preparation consumed no credits; this paid scope awaits approval.
Keep Gemini, original-only mathematical retries, independent grading, the
twenty-question development selection, and all 27 model sequences fixed.
All 165 offline tests pass. Legacy profiles/pinned configuration snapshots match
the prior commit, the frozen routed plan validates, and read-only database
integrity checks pass. The main database was not modified during preparation.

The user approved this single $0.07 / 36-request check. Its
[routing results](solver-verifier-routing-results.md) show six completed
executions, fourteen requests, four DeepSeek providers, and $0.00199989274
reported cost with no new unknown billing. All six final options match the
independent keys; one first answer was rejected and the exact original solver
request was repeated. Assistant review finds that rejected calculation valid,
so record a false rejection rather than claiming a perfect verifier. The
read-only historical-row/request/grade/budget audit passes. No broad run
followed. Keep DeepSeek routing and Gemini provisionally; prepare a separate
frozen development plan and cost notice before further paid work.

Latest implementation checkpoint on October 8: the user requested bounded
cooldown/retry handling and a small provider diagnostic. The
[availability proposal](solver-verifier-availability-proposal.md) records the
offline implementation, additive physical-call storage, explicit unknown-cost
exception, 153 passing offline tests across full/focused runs, and migration
rehearsal. The live database and old reports remain intact. New six-execution
diagnostic: expected $0.00491167056, $0.05 cap, 38 maximum physical requests,
with two shared transport retries and up to $0.002 held unknown-cost reservations
inside the cap. Its numeric scope and billing exception await paid approval.

The user then approved that single check. Its
[availability results](solver-verifier-availability-results.md) show the bounded
retry mechanism exercised live: three DeepSeek/Venice 429s despite 30/60-second
waits, with all three transmissions in the same mathematical slot. Seven total
requests, two completed key-matching executions, one incomplete; $0.00055315773
known new spend plus three unresolved charges, with $0.00120554892 authorized
holds. The additive migration and physical-call/grade/budget audit pass and old
rows are preserved. A free key-limit check found the configured spending cap
unexhausted. No paid continuation; prepare a replacement third solver as the
recommended next checkpoint while holding Gemini and workflow rules fixed.

Latest October 8 checkpoint: following the stopped development run, the user
requested a DeepSeek provider change. The [Venice proposal](solver-verifier-venice-proposal.md)
freezes the new pin while preserving Gemini and the same twenty questions and
twenty-seven sequences. All 136 offline tests pass; legacy profiles, old workflow
builders and the real database are unchanged. No paid calls during preparation.
The new 540-execution run proposes approximately $0.398 expected spend, $3.50
cap and 3,240 maximum requests. The user approved that single run. The
[Venice results](solver-verifier-venice-results.md) record another upstream 429
after six successful DeepSeek calls: 29 total requests, ten finished executions,
one incomplete, $0.00379209782 known additional spend plus one unresolved charge.
No complete question block or ranking; no automatic retry or further provider
change. The prior run's $0.00555908 known spend and one unresolved charge remain
preserved separately. Rate-limit handling and a small availability diagnostic
are recommended before another broad run, each with an explicit budget policy.

The user requested an explicit [solver-verifier implementation and experiment
plan](solver-verifier-plan.md). It records the newly agreed rules: fresh solver
requests with small non-zero temperature, acceptance requiring correct reasoning
and option, local rejection only for unusable output, and score zero after three
rejected attempts. Verifier approval remains separate from offline correctness.
The plan includes verifier experiments before configuration comparison and uses
LangGraph with additive SQLite storage and numbered migrations. Creating this
plan does not authorize paid calls or implement the workflow. Earlier deck
choices and open decisions below retain their historical context; use the new
plan for the current workflow milestones and unresolved live-stage settings.

Following the user's authorization to begin, [Milestone 1](solver-verifier-milestone-1.md)
was completed offline on October 6. The plan was committed first as `5bcac0e`.
Storage, read-only verifier previews, and synthetic reviewed cases are available;
the paid runner, verifier selection, and LangGraph retry loop are still pending.
No OpenRouter credits were consumed. Work stops at this milestone boundary for review.

## October 7 implementation update

Milestone 1 is committed as `c25aa92`.
The [Milestone 2 preparation report](solver-verifier-milestone-2-preparation.md)
records the guarded screening runner and a concrete 36-call pilot proposal:
estimated $0.00789713, conservative reservations $0.03450510, proposed scheduling
limit $0.05. The user approved the pilot, which subsequently completed with
36 calls and $0.00163967 in reported cost. [Results](solver-verifier-pilot-results.md)
show one incorrect natural solution accepted by each candidate, despite success
on the eight labeled synthetic diagnostics. No verifier is selected. The full
screening comparison and LangGraph retry loop remain subsequent checkpoints;
additional paid experiments require a new proposal and authorization.

Following the user's instruction to continue, the
[recomputation comparison](solver-verifier-comparison-proposal.md) was prepared
offline: unchanged baseline, prompt-only recomputation, and recomputation plus
reasoning allowance, across eight reviewed questions. Nine pilot verdicts are
reused; 189 new calls are proposed. Estimated cost is $0.04831528 and the proposed
$0.25 spending limit was approved. All 82 offline tests passed before execution.
The [comparison stopped](solver-verifier-comparison-results.md) after five new
calls costing $0.00136376: DeepSeek with reasoning enabled returned no verdict
and inconsistent reasoning/output counts. A free metadata lookup confirmed its
reported charge. No expansion question was reached; no verifier is selected.
Known verifier-selection spend is $0.00300343 across both runs. Recommended next
checkpoint: prepare an amended comparison without that failing profile and
reuse all thirteen valid matching natural verdicts. No paid continuation or
larger token allowance is authorized automatically.

Following the user's instruction to proceed, the [amended comparison](solver-verifier-comparison-amended-proposal.md)
was implemented and prepared offline. Version 2 plans explicitly name multiple
finished reuse sources and excluded profiles; duplicate judgments and evidence
drift are rejected. Thirteen natural verdicts are reused, including mathematical
errors, and DeepSeek's failing reasoning profile is excluded. The remaining
eight profiles require 163 new requests, estimated at $0.03962351 from refreshed
provider metadata, with $0.21356408 in conservative reservations and proposed
$0.22 cap. All 89 offline tests pass; original plans still validate and the real
database is unchanged. The new numeric cost proposal awaits approval; no paid
continuation occurred during preparation. The user then approved the $0.22 cap
and 163-request maximum. The [amended run](solver-verifier-comparison-amended-results.md)
stopped after forty new calls costing $0.00483675: DeepSeek recompute produced
prose and exhausted its output cap without a verdict. Thirteen saved judgments
were reused; 123 new requests were unreached. All costs are known, database
checks pass, and total verifier-selection spend is $0.00784018. Every tested
profile has an observed false acceptance. Gemini 2.5 with reasoning has the
strongest partial common-coverage result (four correct out of five labeled
proposals), insufficient for selection. Proposed next checkpoint: a small
stronger-reference-verifier comparison on saved failures, with a fresh model,
provider, scope, and cost proposal. No automatic continuation or token-cap
increase occurred.

## October 7 provisional verifier and offline loop

The user chose to proceed with Gemini 2.5 rather than extend verifier selection.
Use `flashlite25__reasoning`: Gemini 2.5 Flash-Lite, the recomputation prompt,
Google AI Studio pin, temperature zero, 512 reasoning tokens, and 1,024 total
output tokens. This is a provisional user choice; the observed false acceptance
remains in the record. Further verifier-selection experiments are deferred.

The [offline Milestone 3 work](solver-verifier-milestone-3-offline.md) implements
the three-slot LangGraph with durable call records, no feedback/key leakage,
unusable-answer/error routing, run-wide spending gates, and independent atomic
option grades. One graph supports all 27 ordered solver triples. Proposed
workflow sampling uses temperature 0.2 and 512 total output tokens, preserving
legacy batch defaults. All 112 offline tests pass. A separate controlled demo
uses sixteen simulated calls to demonstrate early acceptance, third acceptance,
exhaustion, and an accepted wrong option scored zero. No OpenRouter credits were
consumed, and the real database still contains 81 prior verifier calls costing
$0.00784018. Next prepare a separately costed live loop pilot; no stronger
verifier experiment or live workflow run is automatically authorized.

## October 7 live loop pilot preparation

The user instructed us to commit and then run the pilot. Milestone 2 and the
offline loop were committed as `0fc1d05`. The [live loop proposal](solver-verifier-loop-pilot-proposal.md)
freezes two development questions, three cyclic solver sequences, one repetition,
six executions, temperature 0.2, and the provisional Gemini 2.5 verifier.
Fresh free provider metadata confirms the requested controls. Estimated cost is
$0.00442248 for 24 requests; full-cap reservations total $0.03480540. The pilot
uses a $0.04 spending limit and 36-request maximum, with no transport retries or
provider fallback. The separate HTTP adapter and provider price ceilings pass
123 offline tests. Commit this preparation before live execution; report actual
coverage/cost and checkpoint afterward. Larger evaluation is a later scope.

## October 7 completed live loop pilot

The tested pilot adapter/proposal was committed as `00453de` before execution.
The [live pilot completed](solver-verifier-loop-pilot-results.md): six executions,
twenty calls, $0.00249524 known cost, zero technical errors or unknown charges,
59.13 seconds. All six final options match independent keys. Natural routing
demonstrated first-, second-, and third-attempt acceptance; four wrong proposals
were rejected. Separate assistant review finds valid accepted calculations and
invalid rejected calculations. This is two exposed development questions, not
a verifier reliability estimate or a ranking of 27 sequences. Audits confirm
exact original-input request reconstruction, independent grading, intact prior
records and clean code provenance. Milestone 3 is complete. Total known workflow
spend is $0.01033542 across 101 calls. Checkpoint before Milestone 4; its larger
evaluation needs a separate scope/cost proposal.

## October 7 development evaluation preparation

After the user asked to move ahead, the [first development evaluation](solver-verifier-development-proposal.md)
was prepared offline. Use twenty seeded development questions (excluding the
two loop-pilot questions), all twenty-seven ordered triples, one repetition:
540 executions. Keep solver/verifier profiles and graph behavior fixed. Recorded
exposure is confined to the first hundred dataset questions; reserve the last
hundred. Shuffle configuration order within each question with a saved seed.
Reuse fresh first-slot observations for matching one-attempt baselines without
additional calls or execution prefix sharing.

Fresh free provider metadata gives an expected $0.39651192 / 2,160 requests,
conservative full-cap reservations $3.12607080, proposed cap $3.50 / 3,240
requests. This larger paid scope awaits numeric budget approval. Preparation
adds a guarded runner, per-sequence comparisons, Wilson accuracy intervals,
paired question-block bootstrap diagnostics, recovery/repeat metrics, and no
ranking for incomplete coverage. No automatic finalist or held-out run.
The full suite passed 132 offline tests; evaluation checks are repeated after
the final interval safeguard. Real database unchanged, four existing runs,
101 calls / $0.01033542 known spend, no new paid evaluation. Milestone 4 remains
open pending comparable results and separate held-out confirmation.

## October 8 development evaluation approval

The user explicitly approved the $3.50 cap and 3,240-request maximum. Public
prices/controls were refreshed at 17:01 UTC without credits; the selected twenty
questions, 27 profiles, schedule, $0.39651192 estimate and $3.12607080 stress
reservations are unchanged. The refreshed approved plan hash is
`9e80da128d3b2f2894d62b1fccd50d918df22c6edc2637774b83f09e00699588`.
Commit the tested checkpoint, then execute once with no transport retries,
provider fallback, automatic resume or held-out run. Report measured coverage,
cost, technical errors and independent scores before deciding the next stage.

## October 8 partial development run and reporter repair

The tested evaluation was committed as `203e79b` before the authorized run.
The [run stopped](solver-verifier-development-results.md) at a DeepInfra
`engine_overloaded` HTTP 429 without usage/cost/generation ID. Forty-five
requests were recorded (44 completed, one failed), fourteen executions finished,
one is incomplete, and no question completed all 27 sequences. Known new spend
is $0.00555908 plus one unknown charge; total known workflow spend is $0.01589450
across 146 requests. No retry, resume, fallback or further paid call occurred.

The post-stop repeat-answer exporter attempted to index decoded JSON null
fields. Restricting that metric to usable attempts fixes the exporter; the
partial report was recovered offline. A mocked upstream-429 regression covers
this exact case. All 133 offline tests pass. Read-only audits independently
recompute grades/summary counts, reconstruct requests, and confirm prior records
and database integrity. The full comparison remains incomplete with no ranking.

All 22 usable proposals selected the key's correct option for the only reached
question, but Gemini rejected nine. Profit-to-investment proportionality is an
unstated assumption there; preserve this ambiguity rather than turning key
matching into reasoning labels or silently changing the question/verifier.
Gemini stays provisional. Address DeepInfra capacity and billing evidence before
a newly costed/authorized continuation, potentially using another explicit
provider pin. Milestone 4 remains open; no new continuation is scheduled.

## Project scope

- Search model assignments for agent workflows that can retry. Evaluate task success, deployment cost, and latency, and account for failed attempts and paths that stop early. Report the cost of finding a configuration separately from the cost of running it. (Project description.)
- Use AgentOpt and VineLM as starting points. Prefix reuse, selective profiling, and early elimination are possible research directions, not selected methods yet. (Project description.)

## Explicit choices for the first experiment

- The initial question is: **Can a search method find a good sequence with fewer evaluations?** (User's wording.)
- Use MathQA questions with a solver and a verifier. The verifier may request **up to two retries**, for at most three solver attempts. Keep the verifier fixed and choose the solver model separately for each attempt. (User's design choice.)
- Design the experiment collaboratively for now. **Do not run model calls or implement the experiment yet.** (User's instruction.)
- A result in which random search finds equally good sequences at the same profiling budget would make us reconsider whether a specialized search method is needed. (User's stated disconfirming outcome.)

## Current presentation choices

These reflect the September 25 deck and remain the presentation's stated plan until the team changes it.

| Topic | Current deck position |
| --- | --- |
| Related work | AgentOpt, VineLM, SCOPE, GittinsEval, and SySRs. |
| Strongest baselines | Matrix UCB-E from AgentOpt and GittinsEval. |
| First experiment comparison | Matrix UCB-E versus random search at matched cumulative profiling cost. GittinsEval is discussed as a broader baseline but is not in this first comparison. |
| Small search space | Three candidate solver models across three attempt positions: **3³ = 27** model sequences. The candidate models have not been named. |
| Reference | Exhaustively evaluate the small set of sequences to estimate the best sequence on a fixed question set. The search methods do not receive that answer during search. |
| Data | Use labeled MathQA questions during search and separate questions to assess each selected sequence. |
| Controls | Hold the verifier, prompts, and retry rule fixed. Vary the solver sequence and search method. |
| Main figure | Cumulative profiling cost in USD versus the selected sequence's accuracy gap from the exhaustive reference, in percentage points. Lower gap is better. Compare Matrix UCB-E with random search and show a zero-gap reference line. |
| Other measures | Deployment cost, latency, and retry count. Record each attempt and score final answers using MathQA labels. |
| Interpretation | An earlier near-best result for Matrix UCB-E supports adaptive search. Similar performance from random search, or nearly identical sequences, challenges the need for specialized search in this setting. |

The [illustrative graph](../figures/expected-figure-illustrative.png) contains invented points and dollar amounts. It shows the intended figure layout and is **not a result**.

The local AgentOpt checkout comes from `https://github.com/AgentOptimizer/agentopt.git` at commit `08b2d2c7fe370c884d956afbe540a09abc163c27`. It is an external source checkout and is excluded from this project's Git history.

## Definitions to keep consistent

- The **verifier** decides whether the solver retries. The independent MathQA answer key determines whether the final answer is correct; verifier acceptance is not the accuracy metric.
- A **sequence** specifies a model for each of the three possible solver attempts. Later models are called only if the verifier requests those retries.
- **Profiling cost** is the money spent evaluating candidate sequences while searching. **Deployment cost** is the money required to run the chosen sequence on new questions.
- The exhaustive reference identifies the best sequence **on the evaluated question set**. It does not establish the best sequence for all possible MathQA questions. Held-out questions test whether the selected sequence generalizes.
- “Fewer evaluations” and “less profiling cost” are related but distinct. The main planned graph uses dollars because evaluations can have different costs; evaluation count should also be recorded to answer the stated question directly.

## Open decisions before running anything

1. Which three solver models and which fixed verifier model to use, including their prices and access constraints.
2. Exact solver prompt, verifier prompt, acceptance rule, and handling of malformed answers or missing verifier responses.
3. MathQA question counts and split, whether every sequence is scored on the same reference questions, and the number of repeated search runs or random seeds.
4. What counts as one evaluation: a full question run through a sequence, a solver attempt, or an individual model call. Also choose the profiling budgets and stopping rule.
5. How to calculate and display accuracy gap and uncertainty when answers vary across runs; when and how held-out accuracy is measured.
6. Whether and when GittinsEval joins the experiment, since the baseline slide proposes a comparison against both papers while the first-experiment slides compare only Matrix UCB-E and random search.

## Deck items to review

- Slide 12's VineLM paragraph contains merged text beginning `modelinSCOPE...`, and a SCOPE description appears inside that paragraph. Check it in PowerPoint before presenting.
- Slide 13 is still an unfilled template slide. Slides 14 and 15 contain the two baseline discussions. Decide whether slide 13 should be removed or filled.
- Slide 16 says the exhaustive evaluation will reveal the “true best sequence.” More precise wording is **best on the evaluated question set**.
