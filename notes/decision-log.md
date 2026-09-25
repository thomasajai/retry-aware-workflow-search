# Project decision log

Last reviewed: 2026-09-25. This records the current plan, not experimental results. Sources are the team's [project description](../PROJECT.md), our design discussion, and the team slides appended to [Related Work + First Experiment.pptx](../Related%20Work%20%2B%20First%20Experiment.pptx) (slides 11–18). A statement appearing in the deck is marked separately from a choice the user made explicitly in conversation.

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
