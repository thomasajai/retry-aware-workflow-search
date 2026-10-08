# Meeting before the September 18 pitch

The exact meeting date and speaker identities are not established. This summary captures research discussion and tentative ideas.

## Main points

1. **Research problem.** Evaluating every model combination on every benchmark question is expensive. AgentOpt uses search methods, including bandit-style approaches, to reduce the number of evaluations. The proposed extension asks how to search when an execution may retry and incur costs before eventual success.
2. **Define the retry event before the algorithm.** The team asked whether a failure is detected at an individual stage or only after the full planner/executor/verifier workflow, whether a verifier gives ground-truth correctness or partial/noisy feedback, and whether a retry repeats the same model or changes it. Different workflows may retry the solver/executor without rerunning the planner. These choices change the search problem.
3. **Search space and novelty.** Model choices multiply across roles; the example of six choices at each of three roles yields 216 fixed assignments before retry choices are added. A finite retry cap makes the larger space definable, but allowing a different model at each attempt grows it quickly. One concern was that a naive retry extension may simply create more independent bandit arms, without a new search insight.
4. **Keep two costs distinct.** *Search/profiling cost* is the cumulative expense of testing candidates on benchmark questions. *Deployment cost* is the expense of running the chosen configuration after search. The amount worth spending on search depends partly on expected deployment volume.
5. **Start with a manageable objective.** The advisor recommended starting with a **single-objective, retry-aware** formulation, rather than combining retries and full multi-objective Pareto-frontier search at once. AgentOpt's weighted objective, quality/cost constraints in VineLM and SCOPE, and Pareto-frontier recovery were discussed as alternative formulations. SCOPE was described as a relevant no-retry paper, whereas VineLM includes retries.
6. **Evaluation ideas.** For a single objective, plot simple regret—the gap between the selected combination and an exhaustive/oracle reference—against cumulative search cost. Random search is an important baseline and can be hard to beat. Multi-objective evaluation would require additional measures, such as frontier coverage or hypervolume, and explicit uncertainty for partially evaluated points.
7. **Ground the system in real workflows.** Survey retry patterns in database, math, software, and tool-use agents before picking a narrow testbed. BFCL/tool calling, MathQA with an answer/critic pattern, and HotpotQA with planner/solver were discussed as possible starting points or examples. One external benchmark name was unclear and needs verification. A one-model workflow can still support model switching between retries.
8. **Instrumentation may be part of the contribution.** Inspect AgentOpt's open-source implementation and record the feedback, model choice, and number/cost of attempts needed for retry-aware analysis. The speaker said an earlier BFCL data collection did not retain retry counts. Model switching may also affect cache-related cost; its importance needs measurement.

## Follow-ups raised in the meeting

- Survey practical retry workflows and classify trigger, feedback, return stage, stop rule, and whether model switching is allowed.
- Inspect AgentOpt and VineLM, including what AgentOpt already logs and what extra per-attempt fields are needed.
- Choose a small, concrete workflow and benchmark with a usable success signal; check the data-collection cost before expanding.
- Use exhaustive evaluation on a small search space and random search as reference curves for the first result.

No owner or deadline was assigned to these research follow-ups in the discussion. The later discussion concerned the **past September 18 pitch**: explain retry scenarios and challenges, show workflow figures, and use AgentOpt, VineLM, and SCOPE as related papers. It also included slide-copying logistics. A later team idea about launching a stronger run in parallel and stopping a weak one was exploratory and was recognized as distinct from retries.

## Still open after this meeting

- What exactly counts as a failed attempt, and which feedback is available to the search procedure?
- Which stage is rerun, how many attempts are allowed, and can each attempt use a different model?
- Which workflow, benchmark, and metric can support a clear first experiment?
- Does switching models materially change caching cost or latency in the chosen system?
