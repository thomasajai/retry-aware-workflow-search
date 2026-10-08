# Project decision log

Last reviewed: 2026-09-25. This records the current plan, not experimental results. Sources are the team's [project description](../PROJECT.md), our design discussion, and the team slides appended to [Related Work + First Experiment.pptx](../Related%20Work%20%2B%20First%20Experiment.pptx) (slides 11–18). A statement appearing in the deck is marked separately from a choice the user made explicitly in conversation.

## October 6 planning update

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
