# Agentic Systems weekly update: background notes

Companion to the five existing slide drafts and the [speaker script](weekly-update-2026-10-09-speaker-script.md). These notes explain the implementation and prepare the team for questions. They are not intended to be read aloud within the ten-minute presentation.

All findings refer to the completed October 8, 2026 development run and its saved offline searches. Later experiments discussed here are proposed work.

## Slide 1 — Experiment: question + hypothesis

### Purpose and connection to last week

Keep the original hypothesis: Matrix UCB-E will approach the best sequence at lower profiling cost than random search. Adding baselines broadens the test but does not retroactively change the prediction. The experiment tests search over a fixed recorded grid. It does not yet test our proposed method against all baselines or establish held-out accuracy.

### Vocabulary

- **Configuration / sequence:** A fixed ordered triple of solver models. Repetition is allowed. For example, DeepSeek, DeepSeek, Qwen2.5 uses DeepSeek in the first two slots and Qwen2.5 in the third if those slots are reached.
- **Candidate arm:** One whole configuration when described using bandit terminology. There are 27 arms in this experiment.
- **Observation / pair:** One recorded execution of one configuration on one question. This is the unit revealed to the search, not one individual model call.
- **Profiling cost:** Recorded cost of the observations revealed while searching for a configuration.
- **Deployment cost:** Cost of using the chosen configuration on subsequent questions. This is a separate quantity and is not the objective being optimized here.
- **Exhaustive reference:** Best recorded mean workflow score among all 27 configurations on the 20 questions. It is a finite-data reference, not proof of the best configuration for future questions.
- **Accuracy gap:** Reference accuracy minus the current recommendation's recorded accuracy, expressed in percentage points. It is a simple-regret measure for this grid.

### Why the small test is useful

Three models in three positions give 3^3 = 27 configurations, and 20 questions give 540 pairs. We can compute recommendation quality exactly on the recorded grid and test whether a search strategy approaches its optimum before revealing the whole grid. Exhaustive evaluation is the scoring reference, not an adaptive competitor with an invented intermediate curve.

### Scope of the claim

“Near-best” in last week's hypothesis did not specify a numerical tolerance. Present the gap curve and quoted points. Do not invent a preregistered threshold or claim a measured percentage of budget saved to a convergence criterion that we have not defined and evaluated. A future experiment can specify a gap tolerance and whether it must be retained at subsequent observations.

**Likely question: Are we building an algorithm that picks a different model for each question?**

No. These searches recommend one fixed ordered configuration for the whole question set. A question-adaptive deployment router would be a different problem.

## Slide 2 — Experimental setup

### A. The executed workflow

The source is run `f0c941bc-5479-4e86-ae2d-261b521a3317`, independently graded with `workflow-option-v1`. Earlier pilots and interrupted runs are not pooled into it. Reserved held-out questions are not included.

| Component | Frozen setting |
| --- | --- |
| Solvers | Qwen2.5 7B, Qwen3 32B, DeepSeek V3.2 |
| Verifier | Gemini 2.5 Flash-Lite, Google AI Studio |
| Solvers' sampling/output controls | Temperature 0.2, output cap 512 tokens |
| Verifier controls | Temperature 0, reasoning budget 512 tokens, total output cap 1,024 tokens including reasoning |
| Retry input | Original question and choices only |
| Maximum solver slots | Three, including rejected or unusable attempts |
| Early termination | Verifier acceptance |
| Final score | One for an accepted option matching the original independent key; zero for an accepted wrong option or exhaustion |

The retry does not receive the previous answer, verifier criticism, or an attempt number. This experiment studies ordered independent attempts with verification. It does not study iterative revision from feedback.

The verifier assesses the response without access to the independent answer key. The independent grader checks option/key agreement after execution. It does not comprehensively certify mathematical reasoning. A correct option produced by invalid reasoning can still receive a key score of one if the verifier accepts it.

The completed grid contains 540 executions, 1,132 solver attempts, and 1,062 verifier calls: 2,194 gateway requests in total. The reported spend is $0.30118175983, or 30.118175983 cents. The original paid data collection incurred that spend. Offline search replay incurred no additional model-call spend; its horizontal axis represents the recorded costs of revealing selected executions.

There were 70 paid unusable DeepSeek outputs truncated at the output limit. The v5 policy retains each cost, consumes a solver slot, and skips verification of the partial response. It advances if a slot remains. It does not add an extra fourth attempt or a client transport retry. This narrowly defined handling differs from earlier stopped runs and is part of the frozen experiment policy.

### B. What the offline search sees

The loader verifies the complete 20-by-27 grid, consistent settings, grading, and billing, and reads the frozen database without writing to it. An observation reveals the requested pair's reached attempts, outcome, and complete recorded cost. Every pair can be revealed only once in a given search run.

The algorithms have public candidate and question identities. They do not receive unqueried outcomes, hidden costs, full-grid rankings, or held-out records. For a queried observation, independent scores are available to update their estimates. The separate evaluator can look up the recommended configuration's full recorded accuracy to draw the gap curve. That full accuracy is not fed back into search decisions.

### C. Algorithms and our adaptations

#### Random (pairs)

Shuffle all 540 pairs uniformly and reveal them without replacement. Track successes and sample counts separately for each configuration. Recommend the highest observed raw success fraction, breaking ties with a fixed seeded priority.

This is pair-at-a-time random sampling. The AgentOpt paper's random baseline samples complete configurations for full evaluation, so our label explicitly says **Random (pairs)**. This baseline uses neither prefix pooling nor a Bayesian prior. It is not “choose a random final configuration.”

#### AgentOpt Matrix UCB-E

Each configuration is an arm. For a partially observed configuration with S successes and n observations, its sampling index is:

`UCB = S/n + sqrt(a/n)`, with `a = 1.0`.

An unobserved arm has an infinite index, so all 27 receive one observation before any receives a second. Fully observed arms are excluded from further sampling. On the chosen arm, select an unseen question uniformly. Batch size is one.

**Sampling and recommendation differ:** sample by the exploration index, but recommend by the largest raw observed mean S/n among observed arms. Completed arms remain eligible for recommendation.

We port the selection rule to saved observations rather than run the full AgentOpt runtime. We use pure accuracy, with no monetary-cost or latency penalty. The exploration weight is fixed before inspecting search results. Seeded tie priorities and Python random choices replace the reference library's tie/RNG conventions, so this is not a bit-for-bit reproduction of its random traces.

#### VineLM adapted

Use the **same shuffled pair sequence and cumulative costs as Random for each seed**. Its different behavior comes from how it estimates configuration quality, not adaptive choice of the next observation.

Group reached attempts by model prefix: `(a)`, `(a,b)`, `(a,b,c)`. For a shallow prefix, distinguish correct acceptance, continuation, and incorrect termination. With pseudocount alpha = 0.5, estimate the correct-acceptance and continuation probabilities as:

`s(p) = (correct_accepts + alpha)/(reached_count + 3*alpha)`

`r(p) = (continuations + alpha)/(reached_count + 3*alpha)`

At depth three, use two terminal categories, so the success denominator is `reached_count + 2*alpha`. There is no continuation beyond the final slot. Estimate a configuration's probability of final success using:

`A_hat(a,b,c) = s(a) + r(a)*s(a,b) + r(a)*r(a,b)*s_smoothed(a,b,c)`.

The three terms represent correct acceptance at the first, second, or third attempt. Continuation is not generally one minus accuracy: acceptance of a wrong answer stops incorrectly, while rejection of a key-matching answer can continue.

Third-attempt rates form a 9-by-3 matrix, with two-model prefixes as rows and final models as columns. Fill missing cells from observed posterior rates in the same model column, or 0.5 if that column has none. Apply a single rank-one SVD projection and clip to [0,1]. Shallow rates are not smoothed. The prior and missing-cell handling are documented local adaptation choices.

**Statistical reuse:** separate observed executions sharing a prefix contribute evidence to shared estimates. They can have different outcomes. We do not copy an observed outcome into an unqueried pair, invent an uncalled attempt, or discount recorded prefix cost. Checkpoint reuse and the paper's runtime re-rooting controller are excluded. Use the label **VineLM adapted**.

#### Gittins with equal decision costs

Treat configurations as separate Bayesian arms and sample an unseen question on the unfinished arm with the largest Gittins-style index. The model approximates binary scores with a Gaussian prior and observation model. Defaults are prior mean 0.5, prior variance 0.04, observation-noise variance 0.25, and batch size one.

Its estimate targets the mean score across the **entire fixed set of 20 questions**. If n scores with sum S have been observed, and mu_n is the updated latent mean, the recommendation estimate is:

`M_n = (S + (20-n)*mu_n)/20`.

At full observation it equals S/20 exactly. Recommend the largest M_n across all arms. Unlike Matrix UCB-E and Random, Gittins can recommend an unobserved arm because that arm has prior mean 0.5.

The exploration index is `M_n - r_n`, where a backward Gaussian-expectation recurrence computes r_n on a 1,025-point numerical grid. It models the value of additional observations for the finite question horizon. Our port uses NumPy float64 rather than the reference JAX/Torch numerical path and uses local sampling/tie conventions.

Every arm has the same numerical decision charge, 0.0001. **This is not a dollar price. Actual recorded monetary costs do not enter selection.** Therefore, this run does not implement the cost-aware Gittins baseline described broadly last week.

The plotted runs continue through all pairs. Natural stopping conditions are recorded as diagnostics, including first occurrences between 364 and 450 queried pairs across seeds. They do not demonstrate actual stopping savings or recommendation quality after a deployed stopping policy.

#### SySRs: synchronized successive rejects

Active configurations receive observations on a shared shuffled question order. After a complete synchronized phase, eliminate one configuration with the lowest observed mean. Recommend the largest raw mean among observed active configurations. An eliminated arm cannot return, so early elimination can discard a true winner.

The schedule depends on the planned pair horizon H. Before finite-question reallocation, the cumulative phase target is:

`n_k = ceil((H-K)/(logbar*(K+1-k)))`, with `K=27` and `logbar=0.5+sum(1/j, j=2..K)`.

We port the reference's iterative reallocation for targets exceeding 20 questions. We serialize synchronized observations into individual pairs to account for their costs, enforce a strict pair cap, and perform no elimination based on an incomplete phase. Some elimination steps can change the recommendation without an additional paid observation. Recommendation ties use our common seeded priority; elimination ties use the reference NumPy closeness rule and random tie-breaking.

The default horizon is 54 pairs. The main plot uses ten **independently rerun** horizons: 54, 108, 162, 216, 270, 324, 378, 432, 486, and 540. They are not prefixes of one search. The 540-pair schedule reveals the full grid before elimination, so its zero-gap endpoint is effectively exhaustive evaluation.

### D. Shared controls and differences

All methods use the same candidate grid, frozen outcomes, recorded costs, seeds 0–99, and initial seeded recommendation priority. Their actual observation orders differ, except that Random and VineLM deliberately share an order. No hidden-oracle tuning is performed. Different priors, estimators, sampling rules, and elimination rules are part of the methods being compared. Their outcomes therefore do not isolate one particular mechanism without an ablation.

**Likely question: Does putting dollars on the x-axis make every method cost-aware?**

No. Accounting for actual costs in evaluation is different from using predicted costs to choose the next observation. None of these runs establishes the performance of a monetary-cost-aware Gittins variant or our proposed cost-informed acquisition rule.

## Slide 3 — Full plot

### Read the correct figure

Use [the main budget-matched comparison](../results/workflow_search/search-comparison-budget-matched.png). The extended anytime plot has a short default-54-pair SySRs trace and answers a different comparison question. Do not combine its endpoint interpretation with the horizon-sweep results.

Accuracy for configuration c is its sum of final binary scores divided by 20. The reference A* is 0.65. The plotted gap is:

`gap_pp = 100 * (A* - A(current_recommendation))`.

For example, recommending a 60% configuration gives a five-percentage-point gap. It does not give a relative five-percent error. Individual configurations move in five-point increments, but averaging over 100 seeds produces smaller fractional mean gaps.

Four configurations tie at 13/20 (65%): DeepSeek/DeepSeek/DeepSeek, DeepSeek/DeepSeek/Qwen2.5, DeepSeek/Qwen2.5/DeepSeek, and Qwen3/Qwen3/DeepSeek. Any of them gives zero gap. Search recommendations do not break those ties using hidden full-grid deployment cost.

### Budget matching

For a given SySRs horizon and seed, take its actual terminal cost as the budget cap. Evaluate each other method at its last completed observation no more expensive than that cap. Then average gaps across the seeds and average the caps for the x-coordinate.

We do not apply the mean cap to every seed, interpolate individual outcomes, consult future observations, or extend a stopped trace beyond its supported spend. Because a pair is indivisible, another method can have a small unspent residual. The phrase “matched budget” describes the common seed-specific cap, not exactly identical dollars spent by every method.

### Numbers worth knowing

| Mean matched budget, cents | VineLM adapted gap | Matrix UCB-E gap | Random gap | Gittins gap | SySRs gap |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2.21 | 5.00 | 8.40 | 9.30 | 6.80 | 5.50 |
| 5.07 | 3.95 | 5.20 | 7.65 | 4.80 | 3.25 |
| 8.30 | 3.30 | 3.45 | 6.75 | 3.20 | 1.20 |
| 12.31 | 2.60 | 2.15 | 5.30 | 2.85 | 0.40 |
| 15.30 | 2.15 | 0.75 | 4.50 | 1.85 | 0.40 |
| 18.26 | 1.60 | 0.05 | 3.75 | 0.65 | 0.40 |
| 21.24 | 0.80 | 0.10 | 2.40 | 0.05 | 0.25 |
| 24.18 | 0.55 | 0.05 | 2.15 | 0.00 | 0.00 |
| 27.13 | 0.05 | 0.00 | 1.45 | 0.00 | 0.00 |
| 30.12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

All gaps are mean percentage points. Rounded budget labels describe different exact caps from the earlier three-method figure's fixed 5/10/15/20/25-cent budgets. Do not mix their numerical tables.

At 15.30 cents, optimum-selection frequencies are Matrix UCB-E 87/100, Random 36/100, and SySRs 92/100. At 18.26 cents, Matrix UCB-E is 99/100 and Random is 48/100. Frequencies describe the saved search seeds, not confidence levels.

### Why lines can rise

The plot measures the current recommendation, not the best configuration ever discovered with hindsight. Another observation can change an estimate or recommendation and increase its true recorded gap. This is valid behavior. The connecting lines show measured anchor values, not observations at every interpolated location, and the SySRs connections span different horizon runs.

Saved 10th–90th percentiles describe variation across search seeds on fixed outcomes. They are not confidence intervals for generalization to new questions. The main plot does not display these bands. Endpoint agreement does not imply equal efficiency at intermediate budgets.

## Slide 4 — What the result means

### Supported conclusion

Matrix UCB-E has a smaller mean gap than Random at each reported positive intermediate anchor in the main plot. Both tie at exhaustive exposure. Other methods lead in different budget regions. This is descriptive support for the original hypothesis on one recorded dataset and fixed parameter settings. We have not established a statistically significant universal ranking.

Averaging across 100 seeds stabilizes the summary of search randomness conditional on these outcomes. It does not increase the underlying question sample from 20 to 2,000, account for fresh-generation noise, or provide an independent held-out test. The recommendation is scored on the same finite question set from which search observations are drawn, with unrevealed cells hidden from selection.

### Data and workflow limitations

- Six questions have identified option/key, units, or under-specification issues. All six have zero accepted answers across the 27 configurations. Their 162 executions materially affect absolute accuracy. This does not certify the other questions as clean or justify retrospectively deleting the six.
- Targeted saved-record review found valid solutions rejected by the verifier and invalid solutions accepted. Key matching alone does not establish reasoning validity. An aggregate count of rejected key-matching answers is not a measured false-rejection rate.
- Of 294 accepted final responses, 292 match the key and two do not. There are 246 exhausted executions. The pooled 292/540 = 54.07% score averages over configurations and is not the deployment accuracy of one selected sequence.
- Seventy DeepSeek truncations consume slots and contribute paid costs. The ranking includes their consequences under the fixed 512-token cap.
- DeepSeek uses recorded automatic provider routing, while the two Qwen solvers and verifier use their recorded provider controls. We fixed the routing policy, not DeepSeek's realized provider. This is not a controlled fixed-provider model benchmark.

A problematic question on which every configuration scores zero can limit absolute accuracy without changing a particular ordering, but it is not safe to conclude that grading and verifier issues cannot affect relative rankings. Corrected grading or a different verifier can change observations, continuation, costs, and recommendations.

### Recommended next work

First review question/key quality and a consistently selected set of saved verifier decisions. Agree an adjudication policy before using corrected outcomes for comparisons. Preserve the original run and its scores; a revised scoring analysis needs a separate version. This saved-record review can proceed without new model calls.

Then assess whether the search advantage persists with a larger independent question set and repeated generations. Future evaluation should define the search data, held-out evaluation data, parameters, gap tolerance, and cost accounting in advance. The present presentation reports a recommendation for this work, not its completion or authorization.

**Likely question: Have we found the best sequence to deploy?**

We found four tied best recorded sequences on this development grid. DeepSeek/DeepSeek/Qwen2.5 is the cheapest of those ties in the recorded workflow results, but small-sample ranking and observed cost do not establish a generally best deployment choice. The search objective here maximizes accuracy without a deployment-cost or latency constraint.

## Slide 5 — From result to motivation

### What the result adds to the research story

The experiment shows that the configuration recommendation obtained from partial profiling depends on the search method. Existing methods already improve on Random on this dataset. The remaining research question is the incremental value of explicit retry structure compared with those stronger baselines.

Potential mechanisms include conditional reachability of later attempts, evidence pooled across shared prefixes, and differences in the cost of revealing whole workflow outcomes. These are candidate mechanisms, not established causes of the plotted advantages. In particular, SySRs's observed advantage cannot be attributed to retry-specific modeling.

### What has already been tested versus what remains proposed

| Component | Current evidence |
| --- | --- |
| Adaptive configuration sampling | Matrix UCB-E and Gittins implemented and compared |
| Shared-question elimination | SySRs implemented across separate planned horizons |
| Shared-prefix statistical estimation | VineLM adapted implemented with prior and smoothing |
| Monetary-cost-aware Gittins | Not implemented in this comparison |
| Cache/checkpoint execution discounts | Excluded from every curve |
| Actual early stopping for Gittins | Diagnostics saved, but plotted runs continue |
| Our proposed method's improvement | Not demonstrated by these baseline comparisons |
| Held-out deployment performance | Pending |

### A useful sequence of future experiments

1. Audit the evaluation data and verifier behavior before interpreting a new search mechanism.
2. On a documented scoring version, disable VineLM's third-stage smoothing while keeping its sampled pairs, costs, and remaining estimator fixed. This tests the smoothing contribution. A no-smoothing option exists, but its comparative results are not reported here.
3. To isolate prefix pooling, compare the adapted prefix estimator with the flat Random estimator on their already shared pair order. Recognize that the current difference also includes priors and smoothing. Additional controls are required to attribute the difference to pooling alone.
4. Specify a reachability- or cost-informed acquisition rule before running it. Pair it with an otherwise comparable rule that omits that information. Predicted costs must come only from allowable revealed evidence, not hidden future database costs.
5. Compare the completed method with Matrix UCB-E, SySRs, and appropriately specified Gittins, then evaluate generalization independently.

This separates estimation improvements from sampling improvements. It also avoids attributing a method-level difference to a single component without controlling the others.

### Suggested research-story sentence

“Existing methods reduce the accuracy gap during profiling, and our task is to determine whether retry structure can deliver further savings while maintaining recommendation quality.”

This is suitable as the current motivation for the October 16 research story. It does not predict that the proposed method will win. If the strongest existing method remains equally effective, using or adapting that method may be the right outcome.

**Likely question: Why study search when the whole experiment cost only thirty cents?**

This is a small controlled development test, not evidence of a large current financial burden. More candidate models, more attempt positions, more questions, and repeated executions increase profiling requirements. This run establishes a way to measure search efficiency; actual scaling benefits still need measurement. Do not extrapolate a quantified large-scale saving from this grid.

## Source and implementation map

The [controlling experiment specification](workflow-search-experiment-spec.md) documents algorithm semantics and adaptations. The [five-method results](workflow-search-bandit-results.md) and [portable numerical values](../data/search_baselines/search-comparison-budget-matched.csv) support the main figure. The [recorded workflow results](solver-verifier-routed-development-v5-results.md) document calls, costs, grading, truncations, and quality flags. The [v5 workflow proposal](solver-verifier-routed-development-v5-proposal.md) records the frozen execution policy.

For code questions, start with these files and functions:

| File | What to inspect |
| --- | --- |
| [mathqa_workflow.py](../scripts/mathqa_workflow.py) | Workflow configuration, request construction, solver/verifier progression, usability handling |
| [mathqa_workflow_grading.py](../scripts/mathqa_workflow_grading.py) | Independent option/key grading |
| [mathqa_vinelm.py](../scripts/mathqa_vinelm.py) | `load_dataset`, prefix estimator, `rank_one_rates`, `simulate`, `aggregate` |
| [mathqa_search.py](../scripts/mathqa_search.py) | UCB and empirical recommendation rules, Random sampling, simulations |
| [mathqa_bandits.py](../scripts/mathqa_bandits.py) | `finite_roots`, Gittins, `sysrs_schedule`, SySRs, `save_budget_matched_comparison` |

The maintained specification and each result's archived code/settings govern the historical run. Avoid inferring the run's provider or policy solely from current function defaults. Full histories retain per-seed selections and recommendations; portable plot values suffice to redraw the figure but do not replace histories for arbitrary reaggregation.
