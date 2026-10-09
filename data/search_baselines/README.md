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
