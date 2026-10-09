# Saved offline search baseline values

Captured October 8, 2026, from the completed 20-question / 27-configuration
database run. All three strategies use seeds 0 through 99 and full recorded
solver/verifier profiling costs. These compact derived artifacts are not
ignored by Git, so they can travel with the project when changes are committed.

- `vinelm-adapted.csv`, `agentopt.csv`, `random.csv`: each has 121 budget rows,
  with cost in cents, mean gap in percentage points, 10th/90th profiling-order
  percentiles and the fraction recommending an optimum.
- `search-comparison.csv`: 363 rows in the same schema, plus `strategy`.
- `search-comparison.json`: portable three-series values, settings and source
  provenance for recreating the overlay. Paths are relative to the project.

VineLM values are copied unchanged from the previously saved baseline; they
were not rerun for the comparison. Complete pair-by-pair histories and exact
spec/code snapshots remain in ignored `results/workflow_search/` files. The
comparison JSON's result hashes refer to those original full-history files;
those files are not required to redraw the portable figure.

Redraw the three-line plot **from these saved values only**, without a database
read, simulation or model/API request:

```powershell
uv run --locked --extra profiling python scripts/mathqa_search_plot.py data/search_baselines/search-comparison.json --output results/workflow_search/search-comparison.png
```

Add `--bands` to display profiling-order percentile bounds. They are not
confidence intervals about new-question accuracy. For the exact algorithms,
see [the maintained specification](../../notes/workflow-search-experiment-spec.md);
for findings and validation, see [comparison results](../../notes/workflow-search-comparison-results.md).

If the experiment changes, regenerate values into a separate output directory
first. Update these portable baseline files deliberately, together with the
algorithm version, specification and results note; do not silently replace a
historical method's values with a new method.

## Equal-cost Gittins and SySRs extension

The additional methods use the same frozen grid and seeds 0-99. Original
three-strategy artifacts above are preserved byte-for-byte.

- `gittins.csv`, `sysrs.csv`: 121-point anytime curves. SySRs here is its default
  **54-pair planned horizon** and ends at the minimum supported seed spend;
  that curve's endpoint is not the mean terminal outcome of all seeds.
- `sysrs-budget-sweep.json`/`.csv`: terminal results from ten independent
  SySRs horizons, 54 through 540 pairs. Mean/min/max actual costs, pair counts,
  gaps, percentiles and optimal fractions are retained.
- `search-comparison-extended.json`/`.csv`: five anytime traces, with distinct
  supported spend domains. No stopped SySRs history is extended to later costs.
- `search-comparison-budget-matched.json`/`.csv`: **main five-method comparison**,
  with zero spend plus ten independent SySRs horizon endpoints. All other
  methods are evaluated at each seed's actual SySRs terminal cost, then the
  per-seed gaps and cost caps are averaged. These eleven points are not one
  continuous SySRs trajectory. Individual seed caps and source hashes are saved.

The new JSONs retain relative paths, code/spec hashes, pinned reference commit,
and plotter hash. Full source-result hashes refer to ignored local histories,
which are needed only to audit/reaggregate, not redraw.

```powershell
uv run --locked --extra profiling python scripts/mathqa_search_plot.py data/search_baselines/search-comparison-budget-matched.json --output results/workflow_search/search-comparison-budget-matched.png
```

Use `--bands` for saved profiling-order percentiles. To regenerate new policies,
horizons, figures and compact values deliberately:

```powershell
uv run --locked --extra profiling python scripts/mathqa_bandits.py --budget-sweep --plot --portable-dir data/search_baselines
```

This reuses the original three full-history JSONs in local results. It never
invokes a model API or changes the database. See
[bandit results](../../notes/workflow-search-bandit-results.md) and the maintained
specification for numerical defaults and budget-matching semantics.
