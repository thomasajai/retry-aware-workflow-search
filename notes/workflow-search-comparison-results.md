# Offline search comparison results

Completed October 8, 2026. All experiment observations came from the frozen
database; no OpenRouter/model calls, credit spending, regrading or database
writes. [Exact maintained specification](workflow-search-experiment-spec.md).

## Methods and scope

Source: `data/experiments/mathqa_runs.sqlite3`; run
`f0c941bc-5479-4e86-ae2d-261b521a3317`; grader `workflow-option-v1`.
20 questions, 27 fixed solver sequences, one stored execution per pair.
100 seeds (0-99), up to all 540 pairs per strategy.

- **VineLM adapted v1**: preserve/reuse its original saved histories and curve
  values; no rerun. Random pair sampling, prefix pooling, continuation-aware
  decomposition, pseudocount 0.5 and third-attempt rank-one smoothing.
- **AgentOpt Matrix UCB-E v1**: a=1.0, batch size one, select by observed mean
  plus `sqrt(a/n)`, uniformly sample an unseen question for that configuration.
  Recommend by observed empirical mean, with no cost/latency penalties.
- **Random pair search v1**: uniformly shuffle unseen pairs, then recommend
  by observed empirical mean. Its per-seed pairs and cumulative costs exactly
  match VineLM's, allowing comparison of how each uses the same observations.

Every queried pair incurs its entire recorded solver/verifier cost, including
unsuccessful attempts. Recommendations use revealed observations only; the
evaluator's complete-grid accuracy and hidden pair costs do not affect decisions.
All methods use the same independent key-based workflow score and common seeded
recommendation tie priority. These are offline replay baselines, not full runtime
reproductions of the VineLM or AgentOpt systems.

## Results at exact common budgets

Use the last completed observation at or below each budget for each seed. Each
entry is the mean percentage-point gap from the best recorded fixed sequence.

| Profiling budget (cents) | VineLM adapted | AgentOpt Matrix UCB-E | Random pairs |
| ---: | ---: | ---: | ---: |
| 5 | 4.25 | 4.75 | 7.60 |
| 10 | 2.55 | 3.45 | 4.90 |
| 15 | 2.30 | 0.60 | 4.00 |
| 20 | 1.30 | 0.20 | 3.00 |
| 25 | 0.40 | 0.05 | 2.00 |
| 30.118175983 | 0.00 | 0.00 | 0.00 |

At 20 cents, the fractions recommending any tied optimum are **79%**, **98%**,
and **50%**, respectively. At 25 cents they are **93%**, **99%**, and **65%**.
At exhaustive spend all 100 seeds of each strategy recommend an optimum.

The exhaustive reference is **65% (13/20)** at **30.118175983 cents**, with four
sequences tied. VineLM has the smaller mean gap at 5/10 cents; AgentOpt has the
smaller mean gap at 15/20/25 cents in this run. Random's mean gap is higher at
these reported intermediate budgets. This is descriptive evidence for this
frozen dataset and parameter setting, not a claim of universal superiority or
statistical significance. No search hyperparameter was tuned against the oracle.

## Saved values and reproduction

Each strategy saves full histories in a separate JSON and its 121-point
aggregate curve in CSV under `results/workflow_search/`. Historical exact
specifications and code are archived alongside those JSONs. The original
VineLM files are preserved rather than overwritten.

`search-comparison.json`/`.csv` combine the three curves at the same 121 budget
points, using saved histories only. Compact portable copies are in
[`data/search_baselines/`](../data/search_baselines/README.md), including the
unchanged VineLM CSV. The combined PNG/SVG and all curves use cents and
percentage-point gaps. Optional percentile bands describe profiling-order
variation, not uncertainty on unseen questions.

Regenerate AgentOpt and Random and combine with the existing VineLM histories:

```powershell
uv run --locked --extra profiling python scripts/mathqa_search.py --seeds 100 --plot
```

Redraw from the saved portable values only:

```powershell
uv run --locked --extra profiling python scripts/mathqa_search_plot.py data/search_baselines/search-comparison.json --output results/workflow_search/search-comparison.png
```

## Validation and limits

**210 offline tests passed**, including 13 new AgentOpt/Random/comparison tests
and the 16 adapted VineLM tests. No OpenRouter calls or credits were consumed.

Focused checks validate UCB arithmetic, exploration of every configuration before
revisits, exclusion of completed configurations from sampling, empirical rather
than UCB recommendations, Random/VineLM pair identity, no repeated cells,
hidden-oracle and hidden-cost isolation, exact costs, seed reproducibility,
explicit-budget lookups, source/scope compatibility and saved-data plot reuse.
Runtime network access is prohibited in replay isolation tests. Real-run audits
confirm original database bytes, matching archived spec/code hashes, matching
source-result hashes and identical VineLM/Random query sequences and costs for
all 100 seeds. The three-line scientific figure was rendered and inspected.

Keep the original question keys and recorded verifier errors. One saved
realization per pair means seeds vary search order, not model-generation noise.
Twenty questions give coarse 5-point per-configuration accuracy increments.
The comparison is a development-data baseline and does not establish held-out
performance. The Random variant evaluates pairs, rather than the AgentOpt
paper's subset-of-complete-configurations variant. Prefix reuse is statistical;
none of the curves claims cache/checkpoint cost savings.
