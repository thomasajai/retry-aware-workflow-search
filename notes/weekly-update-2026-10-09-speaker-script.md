# Agentic Systems weekly update: speaker script

For the five slides already drafted. Presentation target: ten minutes, approximately two minutes per slide. These are speaking notes, not additional slide text.

Suggested pace: approximately 115–125 spoken words per minute, with brief pauses and time to point at the plot. The timestamps below are rehearsal targets, not measured delivery times. Begin the introduction on slide 1 and include the closing on slide 5. Rehearse once with the actual plot before presenting.

## Slide 1 — Experiment: question + hypothesis

**Target: 0:00–2:00.**

### Spoken script

Last week, we asked whether adaptive search could find a strong solver sequence using less profiling money than random search. This week, we have results that let us test that prediction. A solver sequence specifies which model we use on the first attempt, which model we use if another attempt is needed, and which model we use on the final attempt.

The practical issue is that selecting these models also requires experimentation. Trying every sequence on every question gives us a reference, but it spends the full profiling budget. We want to know whether partial observations are enough to recommend a sequence close to that reference.

Our original hypothesis was specifically that Matrix UCB-E would reach near-best accuracy at lower profiling cost than random search. We kept that question and expanded the comparison to include three additional baselines.

This first test has a deliberately small search space: three models across three attempt positions give twenty-seven sequences. We evaluated all of them, so we know the best recorded sequence accuracy on this dataset. That is our reference, rather than an estimate supplied to the search algorithm.

If random search matched adaptive search, or if the sequences performed almost identically, that would weaken the case for specialized search. I will first explain how we collected and reused the observations, then walk through the comparison.

### Delivery cues

- By approximately 0:30: define a solver sequence.
- By approximately 1:00: explain profiling and state the original hypothesis.
- By approximately 1:30: explain the 27-sequence exhaustive reference.
- Finish by identifying the result that would challenge the hypothesis.

## Slide 2 — Experimental setup

**Target: 2:00–4:00.**

### Spoken script

There are two parts to this experiment: collecting workflow executions and searching over those saved executions. For data collection, we used twenty MathQA development questions and all twenty-seven ordered sequences of Qwen2.5, Qwen3, and DeepSeek. That produced five hundred and forty recorded executions.

Within an execution, a solver answers the question and Gemini Flash-Lite checks its response. Acceptance ends the execution. Otherwise, we advance to the next solver, up to three attempts. Each retry receives the original question and options, without the previous answer or verifier feedback. Separately, we score whether the accepted final option matches the answer key. Acceptance alone does not establish correctness.

For search, we replay these saved records. One observation reveals one question-and-sequence execution, including its outcome and full recorded cost. The search then recommends one fixed sequence for the question set. We repeat this with one hundred seeds, which vary search order rather than generate new answers.

Random search reveals pairs randomly. Matrix UCB-E adaptively chooses a configuration. VineLM adapted pools shared-prefix evidence. Gittins uses Bayesian estimates, and SySRs compares configurations on shared questions and eliminates weaker candidates.

All methods use the same saved data and grading rules. We evaluate recommendations against the full reference dataset, but that information stays hidden from the search. The reference best accuracy is sixty-five percent, and collecting the complete grid cost approximately thirty cents.

### Delivery cues

- Spend the first minute explaining the workflow and independent grading.
- Emphasize “search order rather than generate new answers.”
- Give each algorithm only the short introduction above. Use background notes for detailed questions.
- Point out that 540 executions contain multiple model requests.

## Slide 3 — Full plot

**Target: 4:00–6:00.**

### Spoken script

The horizontal axis shows mean profiling budget in cents. The vertical axis shows how far the current recommendation falls below the best recorded sequence, in percentage points. Lower is better. Zero means matching one of the four sequences tied at sixty-five percent accuracy on these twenty questions.

Start with the orange Matrix UCB-E line and the green random-search line. At approximately fifteen-point-three cents, Matrix UCB-E has a mean gap of zero-point-seven-five percentage points, compared with four-point-five for random search. At approximately eighteen-point-three cents, Matrix UCB-E is almost at the reference, while random search still has a mean gap of three-point-seven-five points.

But the comparison also shows that Matrix UCB-E does not lead at every budget. The pink SySRs line is strongest at several smaller budgets. At approximately twelve-point-three cents, its mean gap is zero-point-four points. Gittins becomes competitive later, while VineLM adapted performs well at the smallest positive budget shown.

There is an important plotting detail: each SySRs point comes from a separate run with its own planned observation budget. We compare the other methods at the affordable observations within each seed's actual SySRs cost cap. These points are not one continuous SySRs trajectory.

The main pattern is that informed use of partial observations improves recommendation quality over random pair search on this saved dataset.

### Delivery cues

- Point to the axes and zero-gap reference before discussing rankings.
- Point to orange and green near 15.30 cents, then near 18.26 cents.
- Point to pink near 12.31 cents and briefly acknowledge the other methods.
- Pause before the explanation of independent SySRs runs.
- Use the five-method **budget-matched** plot, not the extended anytime plot.

## Slide 4 — What the result means

**Target: 6:00–8:00.**

### Spoken script

The first conclusion is that our original hypothesis receives support within this experiment: Matrix UCB-E recommends better sequences than random pair search at the reported intermediate budgets. For example, around eighteen-point-three cents, it recommends an optimal sequence in ninety-nine of the one hundred search seeds. Random search does so in forty-eight.

SySRs performs particularly well at several smaller budgets, and Gittins becomes strong later. These results give our proposed method stronger baselines to beat.

We also need to be precise about the limits. These are twenty development questions, with one recorded execution per question and sequence. The one hundred search seeds measure variation in search decisions on those fixed outcomes. They do not measure variation from fresh model generations or establish performance on unseen questions.

The recorded workflow also contains question and answer-key issues, verifier errors, and seventy unusable DeepSeek generations. We retained their outcomes and costs. Consequently, the ranking describes this particular workflow and grading policy. We cannot assume the same ordering would hold after changing the verifier or correcting the benchmark.

The next step I recommend is to review question quality and saved verifier decisions, document a consistent evaluation policy, and test whether the search advantage persists on a larger independent set. That would address the uncertainty between a useful development result and a generalizable finding.

### Delivery cues

- Open with the answer to last week's hypothesis.
- Explain that 99/100 is a frequency across search seeds, not a 99% confidence level.
- Keep the limitations connected to what they change about the conclusion.
- Present future work as a recommendation, not an already completed or approved experiment.

## Slide 5 — From result to motivation

**Target: 8:00–10:00.**

### Spoken script

Choosing a workflow configuration is itself a resource-allocation problem: we spend money learning which sequence to use, and the quality of that decision depends on how we use partial observations. The plot shows that established search methods can already help with that problem.

Our remaining question is whether the structure of retries provides additional useful information. Later attempts only happen when an execution continues. Sequences can also share model prefixes, and the cost of observing a sequence depends on which attempts were actually reached. Those properties suggest ways to improve search, but this comparison has not established an improvement from our proposed method.

VineLM adapted already pools statistical evidence from shared prefixes. We therefore need a sharper claim than simply saying that prefix information is useful. Likewise, the Gittins baseline here uses equal numerical decision costs, so it does not answer whether using actual monetary costs would improve allocation.

I would approach the next research test by changing one component at a time. After reviewing the evaluation data, we can compare prefix pooling with and without smoothing, and separately test a specified rule that uses retry reachability or cost information.

For the research story, the evidence supports this motivation: existing methods reduce the accuracy gap during profiling, and our task is to determine whether retry structure can deliver further savings while maintaining recommendation quality.

### Delivery cues

- Connect the project to configuration-search spending, not just per-answer deployment cost.
- Distinguish observed results from candidate mechanisms.
- Make clear that the proposed ablations and cost-informed rule are future work.
- Deliver the final sentence slowly. It is the closing statement for the presentation.

## Plot and preparation sources

- [Main five-method budget-matched plot](../results/workflow_search/search-comparison-budget-matched.png)
- [Background notes for these five slides](weekly-update-2026-10-09-background-notes.md)
- [Controlling experiment specification](workflow-search-experiment-spec.md)
- [Five-method results](workflow-search-bandit-results.md)
- [Recorded workflow results and limitations](solver-verifier-routed-development-v5-results.md)

The scripts preserve the five-slide draft and its original hypothesis. The future experiments mentioned on slides 4 and 5 are recommendations, not records of completed work.
