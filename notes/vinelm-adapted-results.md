# Adapted VineLM baseline results

Completed October 8, 2026, using only the frozen experiment database. Algorithm:
`vinelm-adapted-v1`; see the controlling
[experiment specification](workflow-search-experiment-spec.md).

## Experiment

- Source run: `f0c941bc-5479-4e86-ae2d-261b521a3317`.
- Source: `data/experiments/mathqa_runs.sqlite3`, opened read-only.
- 20 questions, all 27 ordered configurations, 540 saved pairs.
- 100 profiling orders, seeds 0 through 99, without replacement.
- Fixed pseudocount 0.5; third-attempt rank-one SVD smoothing enabled.
- Full recorded solver/verifier cost for every query; no checkpoint discounts.
- One configuration recommended at each step, using revealed prefix evidence.
- Python dependency versions: NumPy 2.5.3, Matplotlib 3.11.2; see `uv.lock`.
- No new model requests, OpenRouter calls, credit consumption or database edits.

Exhaustive reference: **30.118175983 cents**, best recorded independent workflow
accuracy **65% (13/20)**, four tied configurations.

## Recommendation quality at equal profiling spend

The table uses the last completed observation at or below each exact budget,
separately for each seed. Gaps use full-dataset accuracy of the *current*
recommendation; the evaluator never feeds this accuracy back to the strategy.

| Profiling budget (cents) | Mean accuracy gap (percentage points) | Seeds recommending a tied optimum |
| ---: | ---: | ---: |
| 5 | 4.25 | 42/100 |
| 10 | 2.55 | 59/100 |
| 15 | 2.30 | 60/100 |
| 20 | 1.30 | 79/100 |
| 25 | 0.40 | 93/100 |
| 30.118175983 | 0.00 | 100/100 |

At full exposure, all 100 seeds recommended **DeepSeek -> Qwen2.5 -> DeepSeek**,
one of the four 65% configurations. All final prefix counts match across seeds,
as expected when the entire grid has been revealed. Earlier recommendations may
change to a worse configuration: this is not a monotone best-ever discovery curve.

The figure's 10th-90th percentile band describes randomness of profiling order,
not confidence about generalization. Prefix pooling/smoothing is an adaptation
and can leave a nonzero final gap on other datasets. These results do not show
checkpoint savings, compare against AgentOpt/Random yet, or validate accuracy on
held-out questions. Preserve the known question/key and verifier quality issues.

## Outputs and validation

Generated artifacts (ignored locally):

- `results/workflow_search/vinelm-adapted.json`: all 100 full histories,
  prefix counts, settings, Python/package versions, and database/code/spec hashes.
- `results/workflow_search/vinelm-adapted.csv`: 121 common-budget summaries.
- `results/workflow_search/vinelm-adapted.png` and `.svg`: scientific figure.

**197 offline tests passed**, including 16 new search tests. Checks cover false
acceptance/rejection, truncations, no fabricated uncalled prefixes, duplicate
pair rejection, hidden-oracle/cost isolation, seed reproducibility, posterior
decomposition, SVD missing-data handling, budget lookup, source admission,
known-cost and grade reconciliation, and unchanged source bytes. Result
database, implementation and specification hashes match their final files.
The PNG was rendered and visually inspected for axes, cents/percentage-point
units, percentile labeling, exhaustive reference and readability.

Reproduce this experiment:

```powershell
uv run --locked --extra profiling python scripts/mathqa_vinelm.py --seeds 100 --plot
```

Future implementation changes must update the controlling specification in the
same change. Keep this results note tied to v1; do not overwrite its conclusions
with a different method without recording the new version and run.
