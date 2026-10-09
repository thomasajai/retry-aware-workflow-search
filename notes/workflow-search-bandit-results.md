# Equal-cost Gittins and SySRs offline results

Completed October 8, 2026. Only the saved database supplied experiment observations;
no model calls, credit spending, regrading or database changes. The original
VineLM, AgentOpt and Random histories/portable values were reused unchanged.
See the [exact maintained specification](workflow-search-experiment-spec.md)
and [reference attribution](../references/BanditGittinsEval-NOTICE.md).

## Setup

Same frozen run `f0c941bc-5479-4e86-ae2d-261b521a3317`, grader
`workflow-option-v1`, 20 questions, 27 configurations and 540 saved pairs.
The exhaustive reference remains **65% accuracy**, four tied optimal sequences,
and **30.118175983 cents**. All methods use seeds **0 through 99**.

- **Gittins equal-cost finite v1**: batch size 1; Gaussian prior mean 0.5 and
  variance 0.04; cell noise variance 0.25; equal numerical transition charge
  1e-4; 1,025 grid points; full fixed-question-set acquisition/recommendation
  target. Continue through all pairs, retaining natural stop diagnostics.
  This is a NumPy float64 port, not bitwise JAX/Torch reproduction. Recorded
  monetary costs never enter selection. No cost-aware variant was implemented.
- **SySRs synchronized v1**: reference successive-rejects schedule and
  finite-question reallocation; shared question order; pairs serialized within
  synchronized phases; eliminate after complete phases; strict planned pair
  cap. Default planned budget 54. Independently rerun at
  54,108,162,216,270,324,378,432,486,540 pairs; preserve each history.

## Main cost-matched comparison

SySRs's schedule depends on its planned budget. Each plotted SySRs point comes
from a separate horizon run. For every seed, evaluate the other strategies at
the last completed observation affordable at that SySRs run's actual terminal
cost. Average the seed-specific cost caps and gaps. This matches budgets within
each seed; it does not use an average cap for all seeds or interpolate outcomes.
The x-axis is **mean profiling budget in cents**; y is mean percentage-point gap
from the best frozen configuration. Lines join discrete horizon points only.

| Mean matched budget (cents) | VineLM adapted | AgentOpt | Random pairs | Gittins | SySRs |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0000 | 9.20 | 9.20 | 9.20 | 9.20 | 9.20 |
| 2.2075 | 5.00 | 8.40 | 9.30 | 6.80 | 5.50 |
| 5.0690 | 3.95 | 5.20 | 7.65 | 4.80 | 3.25 |
| 8.3048 | 3.30 | 3.45 | 6.75 | 3.20 | 1.20 |
| 12.3079 | 2.60 | 2.15 | 5.30 | 2.85 | 0.40 |
| 15.2962 | 2.15 | 0.75 | 4.50 | 1.85 | 0.40 |
| 18.2574 | 1.60 | 0.05 | 3.75 | 0.65 | 0.40 |
| 21.2378 | 0.80 | 0.10 | 2.40 | 0.05 | 0.25 |
| 24.1762 | 0.55 | 0.05 | 2.15 | 0.00 | 0.00 |
| 27.1273 | 0.05 | 0.00 | 1.45 | 0.00 | 0.00 |
| 30.1182 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

SySRs has the lowest reported mean gap at the 5.0690, 8.3048, 12.3079 and
15.2962-cent anchors. AgentOpt is strongest at 18.2574 cents; Gittins is
strongest at 21.2378 cents. This describes these fixed parameters and this saved
dataset, not universal superiority or a statistically significant ranking.
No hyperparameter or prior was tuned against oracle accuracy.

SySRs's first three horizons terminate naturally at 39, 91 and 145 observations
per seed, leaving part of their nominal pair budget unused. Their terminal
optimal-selection fractions are **35%, 51%, 78%**. Planned budgets 216 and 270
both select an optimum in **92%** of seeds. The 432-pair horizon selects an
optimum in all seeds at mean **24.1762 cents**. At 540 pairs, the reference
reallocation evaluates the entire grid before elimination; it is effectively
exhaustive. Do not attribute that zero-gap endpoint to elimination savings.

All full-exposure Gittins runs recommend an optimum. Natural stop diagnostics
first occur between **364 and 450 queried pairs** across seeds, but the plotted
anytime runs continue. These diagnostics are not actual early-stop experiments.

## Saved artifacts

Local PNG/SVG figures:

- `results/workflow_search/search-comparison-budget-matched.*`: main five-line
  comparison above, independent SySRs horizons matched within each seed.
- `results/workflow_search/search-comparison-extended.*`: full anytime curves
  plus the short SySRs default 54-pair trace, with no extension past supported
  spend. Its SySRs aggregate ends at the minimum terminal spend across seeds,
  so that last point is not the all-seed mean terminal gap of 5.5 points.

Full Gittins/SySRs histories, code/spec snapshots and CSVs are local under
`results/workflow_search/`. Ten independent SySRs histories live in
`sysrs-horizons/`. Compact JSON/CSV values in
[`data/search_baselines/`](../data/search_baselines/README.md) recreate both
charts without the database, full histories or any simulation. The main JSON
retains each horizon's result hash and every seed's actual spend cap.

```powershell
uv run --locked --extra profiling python scripts/mathqa_bandits.py --budget-sweep --plot --portable-dir data/search_baselines
uv run --locked --extra profiling python scripts/mathqa_search_plot.py data/search_baselines/search-comparison-budget-matched.json --output results/workflow_search/search-comparison-budget-matched.png
```

## Validation and interpretation limits

The final full offline suite passed **230 tests**, including 20 new checks for
Gaussian expectation/analytic roots, finite-population
variance, grid refinement, synchronized phases, no post-elimination sampling,
strict pair caps, oracle/cost isolation, no network use, reproducible seeds,
recorded cost reconciliation, snapshot hashes, per-seed budget matching,
horizon provenance rejection and portable export preservation.

The final audit checks real-grid pair counts, no repeats, total actual recorded
cost, hidden-source isolation, archived code/spec hashes, horizon-file hashes,
unchanged database bytes and original baseline files. Both five-line charts were
rendered and visually inspected; distinct line styles supplement color, and
captions disclose horizon/cost semantics. Percentiles remain saved and optional
bands describe profiling randomness, not confidence on new questions.

The real-grid audit reconciled **12 saved result files, 1,200 archived seed runs,
and 350,000 queried pairs** (including the duplicate default 54-pair snapshot
also retained in the sweep). All pairs' actual cost, evaluator scores and saved
step counts reconcile. The NumPy schedule matches independently executed
reviewed upstream schedule functions for **all 513 valid horizons, 28-540**.
The saved portable JSON successfully redrew the main chart without a database
read or search run. The local machine-readable audit is
`results/workflow_search/bandit-audit.json`.

Original question-key issues and verifier errors remain in the frozen data.
One recorded realization per pair means seeds vary search order rather than
generation noise. Twenty questions give coarse 5-point accuracy increments for
individual configurations. These are development-data baselines, not held-out
deployment results. Gittins uses a Gaussian approximation for binary outcomes;
SySRs can permanently eliminate a true winner.
