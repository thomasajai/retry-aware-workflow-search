# Offline workflow search experiment specification

Algorithm versions: **vinelm-adapted-v1**, **agentopt-matrix-ucb-e-v1**,
**random-pair-search-v1**, **gittins-equal-cost-finite-v1**,
**sysrs-synchronized-v1**. Comparison formats: **workflow-search-comparison-v1**
(original three equal-length strategies), **workflow-search-comparison-v2**
(additional naturally terminating strategies), **workflow-search-budget-matched-v1**
(independent SySRs horizons, matched per-seed spend).
Updated October 8, 2026.

This is the controlling specification for the search comparison. Update this
document in the same change as any implementation change to sampling, scoring,
priors, smoothing, cost accounting, stopping, recommendation or aggregation.
Increment the algorithm version when those numerical semantics change. Record
implementation, specification and database hashes in every result. Record runs
and findings separately so adding a finding does not change the specification.

## Authorized scope and objective

Use **only data already saved in the database**. No OpenRouter requests, new
generations, paid calls, regrading, question/key edits, or database writes.
Installing local numerical/plotting dependencies does not acquire experiment
data. The experiment itself needs no API key or network connection.

Each strategy investigates question/configuration pairs to recommend **one fixed
configuration for all questions**. Maximize independent workflow accuracy among
the 27 ordered three-model sequences. There is no deployment cost or latency
constraint. Profiling spend is the horizontal axis, distinct from deployment
cost. All configurations tied for maximum recorded accuracy are optimal.

The implemented strategies are adapted VineLM, AgentOpt Matrix UCB-E, uniform
Random pair search, equal-cost Gittins, and synchronized successive rejects
(SySRs). They share the same source, independent final workflow
scores, full recorded costs and evaluator. The sections below define each.

## Frozen source and admission checks

Default database: `data/experiments/mathqa_runs.sqlite3` (frozen snapshot).
Default run: `f0c941bc-5479-4e86-ae2d-261b521a3317`.
Independent grader: `workflow-option-v1`.

Use only that run. Do not pool earlier runs or reserved held-out questions.
Read configuration snapshots, question identities, executions, reached attempts,
independent attempt/final grades, and the `workflow_billable_calls` view. The
view accounts for physical transport billing without counting a logical call
again when physical requests exist.

Open SQLite with `mode=ro`, `PRAGMA query_only=ON` and a read transaction. Validate
a complete cross product of scheduled questions and distinct three-position
model combinations, with exactly one saved execution per pair. The default run
has 20 questions, 27 configurations and 540 pairs. Validate matching shared solver
settings and verifier settings, contiguous attempt positions, actual model
identities, acceptance/termination consistency, grade provenance, completed
verification and known finite nonnegative billing. Reject incomplete,
duplicated, mismatched or ungraded records. Hash the database before/after
loading and reject a change rather than silently mixing snapshots.

Actual default exhaustive reference: **30.118175983 cents**, including all 2,194
solver/verifier requests, and **65% accuracy**. The four tied optimal sequences
are `deepseek-deepseek-deepseek`, `deepseek-deepseek-qwen25`,
`deepseek-qwen25-deepseek`, and `qwen3-qwen3-deepseek`. Recompute these values
from the selected database/run on every experiment; do not hard-code them into
the strategy.

## Reference and adaptations

Reference: [VineLM, Section 4.2 and Appendix A](https://arxiv.org/html/2605.23914v1#S4.SS2).
Use its trie representation, random cascade profiling, conditional decomposition
and rank-one smoothing of third-attempt conditional accuracy estimates.

Our interface samples complete question/configuration pairs uniformly without
replacement; each saved trace already executes its sequence as a cascade. This
differs from a profiler that independently samples stage actions or resumes
checkpoints. No outcome-dependent or UCB sampling rule is attributed to VineLM.

Share *statistical evidence* for prefixes, not exact cached outcomes. Independently
recorded executions sharing a question and model prefix can differ. Do not copy
a successful observed trace into unqueried database cells and do not subtract
their recorded prefix costs. Checkpoint reuse and VineLM's runtime re-rooting
controller are excluded. Label figures and outputs **VineLM adapted**.

The stopping signal is Gemini acceptance, while accuracy is independent key
agreement of the accepted answer. An accepted wrong answer terminates without
success; a rejected key-matching answer can continue. Therefore continuation
probability is not generally `1 - accuracy`. The decomposition below adapts the
paper's success/failure recursion to the actual workflow.

## Observation exposed by one query

For the requested pair, expose only its question identity, sequence, reached
attempt outcomes and full recorded cost. Do not expose any other pair's outcome,
cost, per-question difficulty, full-grid ranking, or held-out record to the
estimator. Public candidate identities and question identities are available.

Classify each reached solver/verifier attempt into exactly one category:

1. `correct_accept`: verifier accepted and independent option grade is correct.
2. `continue`: no acceptance and another attempt is permitted (position 1 or 2).
   Includes rejected correct answers and paid unusable/truncated solver attempts.
3. `incorrect_stop`: accepted wrong answer, or no acceptance at final position 3.

Only reached attempts generate observations. Early stopping generates no
observations for uncalled positions. A trace ending in `correct_accept` scores
one; all other terminal traces score zero. Check against its saved final grade.

## Algorithm, exactly

Defaults: 100 seeds starting at 0; all 540 pairs; pseudocount `alpha=0.5`;
third-stage smoothing enabled. Hyperparameters are fixed before viewing search
results. They are adaptation choices, not claimed paper defaults.

For each seed:

1. Sort question IDs and configuration tuples lexicographically. Construct the
   question-major Cartesian list of all pairs. Shuffle once with
   `random.Random(seed)`. Consume the resulting permutation without replacement.
   No observations influence this permutation.
2. Independently shuffle a sorted list of configurations with
   `random.Random(seed + 1_000_003)` to create a fixed recommendation tie priority.
   Recommendation ties never consume the sampling random stream.
3. Initialize prefix counts to zero and cumulative spend to zero. Record an
   initial recommendation based on the priors only, using the seeded tie priority.
   It is not a paid evaluation or a hidden-data warmup.
4. Reveal the next pair's saved trace. Add its full recorded solver and verifier
   cost, including rejected, truncated and unsuccessful attempts, exactly once.
   Add one categorical observation per reached prefix. For sequence `(a,b,c)`,
   the prefixes are `(a)`, `(a,b)` and `(a,b,c)`, only as far as actually reached.
   Independent executions contribute independent observations; querying the same
   saved pair twice is rejected.
5. Recompute the estimated configuration accuracies as specified below. Choose
   the highest estimated accuracy. Values within absolute tolerance `1e-12` of
   the maximum are tied; use the fixed tie priority. Do not use full-grid cost,
   full-grid accuracy or a cheapest-tie rule in recommendations.
6. The evaluator records the chosen configuration's full-grid accuracy and gap,
   without feeding either back to the estimator. Repeat through the selected
   number of pairs. Default: stop only after all pairs are revealed.

Optional `--max-pairs N` stops after N revealed pairs, including N=0. This is an
observation-count limit, not a cost-aware selection rule or hard spending gate.
Common-budget evaluation uses completed observations only; the strategy never
consults an unrevealed cost to decide what to sample.

### Prefix conditional probabilities

For each prefix p at depth 1 or 2, let n be its reached observation count,
S its `correct_accept` count, R its `continue` count, and W its
`incorrect_stop` count. Use a symmetric Dirichlet prior:

```
s(p) = (S + alpha) / (n + 3*alpha)
r(p) = (R + alpha) / (n + 3*alpha)
w(p) = (W + alpha) / (n + 3*alpha)
```

These are posterior means; they sum to one. A wholly unobserved shallow prefix
has s=r=w=1/3. At depth 3 there are only two terminal categories:

```
s(p) = (S + alpha) / (n + 2*alpha)
r(p) = 0
```

Without any depth-3 observation, its unsmoothed prior success probability is 1/2.
No category is assigned merely because a prefix was not reached.

### Third-attempt smoothing

Construct a matrix with the nine depth-2 prefixes as rows and the three final
models as columns. An observed cell contains its posterior conditional success
rate above. Initialize each unobserved cell to the arithmetic mean of observed
posterior rates in its final-model column (equal weight per observed cell).
If the entire column is unobserved, initialize it to 0.5.

Compute `U, singular, Vt = numpy.linalg.svd(matrix, full_matrices=False)` and
replace the matrix by `singular[0] * outer(U[:,0], Vt[0])`. This is a single
rank-one projection, not repeated matrix completion. Clip entries to [0,1].
Use these rates only at depth 3; do not smooth continuation rates or depths 1/2.
`--no-smoothing` uses the raw posterior depth-3 rates (including 0.5 for missing
cells) and is a decomposition ablation, not another headline strategy.

### Estimated accuracy and recommendation

For configuration `(a,b,c)`, the three ways to finish correctly are disjoint:

```
A_hat(a,b,c) = s(a) + r(a)*s(a,b) + r(a)*r(a,b)*s_smoothed(a,b,c)
```

Only queried-prefix statistics enter this calculation. Estimates stay in [0,1].
No override replaces these estimates with full-grid column means at the end.

## Evaluation and figure

Evaluator accuracy A(c) is saved final workflow scores summed across all 20
questions and divided by 20. Exhaustive accuracy A* is the maximum of these
column means. Report recommendation quality using:

```
gap_pp = 100 * (A* - A(current_recommendation))
cumulative_cost_cents = 100 * sum(recorded_USD_of_queried_pairs)
```

Use decimal arithmetic for accumulating recorded costs. Accuracy gaps are
percentage points, not relative percentages. Selecting any tied optimum gives
gap zero. The recommendation can change to a worse configuration, so the curve
may rise. Do not plot the evaluator's best-ever visited configuration instead.

Preserve every seed's full history, including selected pairs, cost,
recommendation, estimated accuracy, evaluator accuracy and gap. Generate 121
equally spaced budget points between zero and the minimum terminal spend across
seeds. At each budget, use the last completed observation whose cost is no
greater than that budget (rightmost if zero-cost observations share a cost).
Never interpolate per-seed gaps or use an observation from a future budget.
Never extrapolate beyond a seed's terminal spend.

At each common budget, report arithmetic mean gap, 10th and 90th percentiles
(linear quantiles at position `(number_of_seeds-1)*probability`), and the fraction
of seeds recommending an optimum. The band measures profiling-order randomness,
**not** confidence about accuracy on unseen questions. The figure joins the mean
values at these budget points and marks exhaustive evaluation at its total cost,
gap zero. Exhaustive has no invented intermediate search trajectory.

Export JSON (all histories/settings/provenance), CSV (budget-curve aggregates),
PNG and SVG (standalone scientific figure). Record Python, NumPy and Matplotlib
versions for environment provenance; dependencies are pinned in `uv.lock`.
The plotter defaults its font/configuration cache to a `.matplotlib` subdirectory
of the output directory (unless `MPLCONFIGDIR` was explicitly set).

## AgentOpt Matrix UCB-E: exact replay algorithm

Reference: [AgentOpt, Section 5.2, Algorithm 1](https://arxiv.org/html/2604.06296v2#S5.SS2).
The local reference checkout is `https://github.com/AgentOptimizer/agentopt.git`,
commit `08b2d2c7fe370c884d956afbe540a09abc163c27`, file
`src/agentopt/model_selection/matrix_ucb.py`. Its default exploration weight is
**a=1.0**. Use **batch size B=1**, pure accuracy (no cost/latency penalties), and
default observation budget fraction **1.0** to record a complete anytime history.
Do not use the package runtime, transport interceptors, model overrides or API
adapters. Implement only its selection rule against the frozen database.

1. Supply sorted public question IDs and configuration tuples. Initialize every
   configuration's success count and observation count to zero. Use the same
   fixed recommendation tie priority as VineLM: independently shuffle sorted
   configurations with `random.Random(seed + 1_000_003)`.
2. Before any observations, recommend the first configuration in that priority
   with `estimated_accuracy=null`. No observed accuracy or prior is fabricated.
3. For every configuration c with success count S and observation count n, set:

   ```
   UCB(c) = +infinity                         if n=0
          = -infinity                         if n=number_of_questions
          = S/n + sqrt(a/n)                   otherwise
   ```

   Fully observed configurations cannot be sampled again but remain eligible
   for recommendation. Choose the exact maximum UCB; ties use the fixed seeded
   priority. Thus every configuration receives one observation before any
   receives a second. This rule is not cost-aware: spend is measured afterward.
4. Make a sorted list of questions not yet observed for the selected
   configuration. Choose one uniformly with `random.Random(seed).choice(list)`.
   Keep this sampling RNG separate from recommendation ties.
5. Reveal that pair only. Its binary workflow score is one if its trace ends in
   independent `correct_accept`, zero otherwise. Increment S/n appropriately,
   mark the pair observed, and charge all its recorded solver/verifier costs.
   No prefix inference, outcome copying or discounts are applied.
6. Recommend the largest **raw empirical mean S/n among observed configurations**,
   not the largest UCB. Exclude unobserved configurations. Recommendation means
   within absolute tolerance `1e-12` are tied; use the common fixed priority.
7. Record the same history fields as VineLM. Only the evaluator computes the
   recommendation's complete-grid accuracy and accuracy gap. Repeat through
   the whole grid, or stop after explicit `--max-pairs N` observations.

The published argmax tie rule is unspecified. The local library uses first-row
ties and NumPy permutations; this replay uses seeded priorities and Python
uniform choices for reproducible, common comparison conventions. It reproduces
the UCB-E decision rule, not the library's bit-for-bit random sequences. The
fixed a=1.0 is chosen before examining results and is configurable with
`--exploration`; no tuning on the complete-grid oracle is performed. A=0 is
allowed as an explicit greedy ablation, not the default baseline.

## Random pair search: exact replay algorithm

This is the user's pair-at-a-time baseline. It differs from the AgentOpt paper's
Random variant that samples entire configurations and evaluates those fully.
Label this strategy **Random (pairs)** in figures.

1. Construct the same sorted, question-major Cartesian pair list as VineLM.
   Shuffle once with `random.Random(seed)` and consume without replacement.
   For a given seed, its queried pair sequence and cumulative costs exactly
   match VineLM's; only how observations are used for recommendations differs.
2. Initialize the common fixed recommendation priority. Before profiling,
   recommend its first candidate with null estimated accuracy.
3. Reveal one pair, update only that configuration's binary workflow successes
   and observation count, and charge its complete recorded cost.
4. Recommend the highest raw empirical accuracy among observed configurations,
   using the same `1e-12` recommendation tie tolerance and seeded priority as
   AgentOpt. No priors, prefix pooling or smoothing are used.
5. Record recommendation quality with the evaluator, never feeding oracle
   scores or hidden costs back into selection. Continue through the same
   observation limit as the other strategies.

## Preserved plot values and combined figures

Keep each strategy's JSON and CSV separately. The existing
`vinelm-adapted.json` and `vinelm-adapted.csv` are preserved unchanged for this
comparison. Their exact original specification and implementation are archived
as `vinelm-adapted.spec.md` and `vinelm-adapted.implementation.py`; historical
source hashes are not rewritten when this live specification is extended.
New strategy results archive their own specification, implementation and shared
helper implementation alongside their output JSON. Historical runs remain
associated with those snapshots.

All three CSVs have the same schema:

```
cost_cents, mean_gap_pp, p10_gap_pp, p90_gap_pp, optimal_fraction
```

All JSONs retain every per-seed history, allowing reaggregation at arbitrary
common budgets without rerunning a strategy or querying the database.

Before combining, require matching database/run/dataset/plan/grade provenance,
question/configuration counts, exhaustive reference, seed list and per-seed
number of observations. Fail on mismatches. Choose the smallest terminal cost
across **all strategies and all seeds** and generate 121 common budget points
from zero to that cost. Apply the same last-completed-observation lookup to each
strategy's saved histories. Explicit arbitrary budgets must be ordered,
nonnegative and within every included run's terminal cost. Existing VineLM
sampling, inference, defaults and standard 121-point curve are unchanged.

Export `search-comparison.json` with the three curves, strategy versions/settings
and source-result hashes. Export `search-comparison.csv` in long format, adding
a `strategy` column to the five shared curve fields. The chart can be reproduced
directly from that combined JSON, with no database access or simulations.

The default comparison shows three mean lines and the exhaustive endpoint.
Percentile bounds remain saved; optional `--bands` adds the three 10th-90th
profiling-order percentile bands. The same units and limitations apply.

Compact portable baseline copies are saved in `data/search_baselines/` (not
ignored by Git): all three curve CSVs, the combined long-format CSV, and the
combined JSON. They retain numerical values, strategy settings, source hashes
and original result hashes; machine-specific paths are replaced with relative
project paths. Each series also retains its generation specification and code
hashes. The portable JSON can be rendered without full histories or the database.
Only the full histories allow reaggregation to different arbitrary budgets.
Update portable baseline snapshots deliberately when experiment versions change.

## Equal-cost Gittins: exact replay algorithm

Version: **gittins-equal-cost-finite-v1**. Reference:
[BanditGittinsEval](https://github.com/QianJaneXie/BanditGittinsEval), pinned commit
`a4992e22a48e781327efd5411fb7d0921ad5ab61`, `src/gittins_policy.py`,
`src/gittins_shrinking_posterior.py`, `src/gittins_lookup.py`,
`src/q_estimation.py`, and `src/simple_regret_recommend.py`.
Attribution and MIT license are in `references/BanditGittinsEval-NOTICE.md`.

Use configurations as arms and questions as available observations. One step
reveals one binary final workflow score, sampled uniformly from unseen questions
on the configuration with the largest unfinished Gittins index. No prefix
pooling. Public identities are sorted; Python `Random(seed)` chooses unseen
questions. Use the existing independent `Random(seed+1_000_003)` configuration
priority for sampling and recommendation ties within absolute tolerance 1e-12.
RNG and ties differ from the reference's Torch RNG/first-index ties.

Fixed defaults, selected from the reference before the 100-seed experiment:
Gaussian latent prior mean **0.5**, variance **0.04**, per-cell observation noise
variance **0.25**, batch size **1**, no lower-confidence recommendation penalty,
**1,025** grid points, grid SD bound **5**, grid cost margin **0.01**. The Gaussian
model approximates binary scores; no data-specific prior is fitted to hidden
outcomes. Every arm uses the same numerical decision charge **1e-4**, equivalent
to reference unit charge 1 times its default scale 1e-4. This charge is part of
the exploration calculation, **not dollars or cents**. Actual recorded costs
never enter the policy. Cost-aware Gittins is excluded.

For N questions, n queried scores with sum S, compute:

```
v_n = 1 / (1/v_0 + n/tau_squared)
mu_n = v_n * (mu_0/v_0 + S/tau_squared)
M_n = (S + (N-n)*mu_n) / N
V_n = ((N-n)^2*v_n + (N-n)*tau_squared) / N^2
sigma_n = (1 + tau_squared/(N*v_0)) * v_n / sqrt(v_n + tau_squared)
```

`M_n` is the posterior mean of the **entire fixed question set**, distinct from
the latent population mean. At completion M=S/N and V=0 exactly. Recommend the
maximum M over all configurations, including unobserved and completed ones.
An unobserved configuration has mean 0.5, so it can be recommended. Do not clip
or substitute empirical means for incomplete rows.

Precompute a single shared root table for the N-observation horizon. On a
uniform float64 grid from `-5*sqrt(sum(sigma_n^2))` to
`1.01*N*1e-4 + 5*sqrt(sum(sigma_n^2))`, apply the reference backward recurrence:

```
Q_N(x) = x
Q_n(x) = E[max(Q_(n+1)(x + sigma_n*Z), 0)] - 1e-4
r_n = first grid x whose Q_n(x) >= 0
index_n = M_n - r_n
r_N = 0 exactly
```

Compute the Gaussian expectation of the piecewise-linear grid by the reference
`m_diff` method: slope changes convolved with Gaussian expected improvement,
left extrapolation slope zero and right slope one. Use NumPy FFT float64 and
standard-library erfc for the normal CDF. This ports the same grid/root algorithm;
it does not promise bitwise equality to reference JAX/Torch float32. Reject an
unbracketed/nonmonotone root. Roots are saved in the result JSON and depend only
on public question count and fixed parameters, never hidden scores.

Continue until every pair is revealed, as the reference fixed-budget runner
does with early stopping disabled. Keep completed configurations eligible for
recommendation but exclude them from sampling. Record first natural stopping
(a completed arm has the largest index) and first recommendation-aware stopping
(largest unfinished index below the recommended M) as diagnostics, without
truncating the anytime history. Actual cumulative cents and evaluator gap are
recorded after every queried pair. No additional dependencies beyond NumPy.

## SySRs: exact replay algorithm and planned horizon

Version: **sysrs-synchronized-v1**. Port the schedule and finite-question
reallocation from the pinned reference `src/sysrs_policy.py` (Smart-SR).
For K arms, the planned pair budget H must be at least K+1 (one arm: at least 1)
and no larger than K*N. This guard avoids the reference's H=K zero-observation
eliminations. Default H is `max(K+1, round(0.1*K*N))`, hence **54** in our grid.
An explicit horizon is prespecified, never chosen by oracle accuracy or costs.

The original cumulative per-active-arm schedule is:

```
logbar = 0.5 + sum(1/j for j=2..K)
n_0 = 0
n_k = ceil((H-K)/(logbar*(K+1-k))), k=1..K-1
```

Copy the reference's iterative reallocation when n_k>N: mark saturated phases,
cap them at N, and rescale unsaturated original cumulative targets using the
remaining planned budget and reference boundary/saturated-round terms. Apply
ceil and cumulative maximum after convergence or K iterations. Do not replace
it with a new clipping-only schedule. The code is the controlling arithmetic
for these terms; the deterministic schedule is saved in every seed's result.

Use NumPy `default_rng(seed)` to choose `min(N,n_(K-1))` distinct shared questions
in one random order, with the same generator later breaking elimination ties.
Every active configuration sees that shared order. In phase k, evaluate the next
`n_k - n_(k-1)` shared questions on every active configuration. Serialize each
shared-question batch into individual pairs using the existing independent
seeded configuration priority. **No elimination occurs until every scheduled
pair in that phase is observed.** Costs are paid independently for all pairs.

After a complete phase, eliminate one arm with the smallest raw observed mean.
For worst-arm ties use reference NumPy `isclose` defaults and uniform random
choice. Zero-extra phases eliminate without another query. Eliminated arms are
never sampled or recommended again. During serial batches, recommend the
largest raw mean among observed active arms; with no observations recommend the
first active arm in the seeded priority and estimate null. Recommendation ties
use absolute tolerance 1e-12 and that fixed priority (a replay adaptation).

Stop upon H queried pairs, one survivor, finished schedule, or exhausted shared
questions. H is a strict **pair cap**: unlike reference whole-batch budget
overshoot, a final synchronized batch may be only partly revealed. Do not
eliminate based on that incomplete phase. Do not force extra observations to
match another strategy's run length. Save every queried pair plus zero-cost
recommendation changes caused by eliminations. Zero-cost records have no queried
question/configuration and retain the previous cumulative step and spend;
budget lookup uses the last such state. Save schedules, shared question order,
elimination events, survivors, and stop reason for audit.

With H=540 and N=20 the reference reallocation gives `[0,20,20,...,20]`: the first
phase reveals the entire grid. That endpoint is effectively exhaustive search,
not evidence that elimination improved search. The default 54-pair trace is
saved separately, alongside independently rerun horizons
**54,108,162,216,270,324,378,432,486,540**, each using seeds **0..99**. These are
not prefixes of a single larger-horizon search. Rounding and early termination
can leave some of H unused; charge only actual queried pairs. The sweep summary
reports terminal recommendation gaps, optimal fractions, actual pair counts,
and actual costs with ranges. Complete sweep histories and code/spec snapshots
are saved locally under `results/workflow_search/sysrs-horizons/`.

## Five-strategy figures and budget matching

Preserve all original VineLM/AgentOpt/Random histories and portable values.
Do not rerun or overwrite them when adding these methods. No generation or DB
writes are permitted in either new experiment.

Two distinct five-line comparisons are saved:

1. `search-comparison-extended.json`, format **workflow-search-comparison-v2**:
   the four full-horizon anytime histories and SySRs's **planned 54-pair** history.
   Each uses its own 121-point grid ending at that strategy's minimum terminal
   spend across seeds. The short SySRs line stops there, without carrying a
   stopped policy into imaginary later spend. This format validates the same
   frozen source, exhaustive reference, seed set and common public grid limit;
   naturally different history lengths are allowed. The original v1 overlay
   retains its stricter equal-history-length validation.
2. `search-comparison-budget-matched.json`, format
   **workflow-search-budget-matched-v1**: the **main comparison**, using independent
   SySRs horizons and equal seed-specific monetary budgets. For horizon H and
   seed s, let B(H,s) be actual SySRs terminal spend. Use SySRs's terminal
   recommendation and each other strategy's **last completed observation at or
   below B(H,s)** in its saved full history. Do not interpolate, look ahead, or
   use the mean spend as an individual seed's cap. Reject unsupported budgets.
   Plot the mean gaps against `mean_s B(H,s)`, saving p10/p90 and optimal fractions.
   Include the common zero-spend recommendation and ten horizon endpoints.
   X is labeled **Mean profiling budget (cents; matched within each seed)**.
   Joining those points does not imply one continuous SySRs search. For other
   strategies a small residual cap can be unspent because a pair is indivisible.

The second comparison is a cost-matched evaluation of search policies, not a
claim that all methods spent exactly the same money or that the horizon was
known as a dollar amount in advance. The evaluator selects the caps after the
offline runs; the policies never receive future costs. Saved budget anchors
retain every seed's actual cap for recomputation and auditing. The zero-spend
origin uses the same seeded configuration priority for all methods.

Save both comparisons in JSON/CSV and PNG/SVG, along with separate `gittins.csv`,
`sysrs.csv`, and `sysrs-budget-sweep.csv`. Compact portable copies live in
`data/search_baselines/`, preserving settings, reference commit, result/code/spec
hashes and relative paths. Full histories remain in ignored results. The saved
comparison JSON alone redraws the plot without a database, search or network.

Reproduce the two new methods and ten independent SySRs horizons:

```powershell
uv run --locked --extra profiling python scripts/mathqa_bandits.py --budget-sweep --plot
uv run --locked --extra profiling python scripts/mathqa_search_plot.py data/search_baselines/search-comparison-budget-matched.json --output results/workflow_search/search-comparison-budget-matched.png
```

This requires the original three full-history files for recomputing the overlay,
but the portable chart JSON needs none of them for redraw. To reaggregate saved
histories alone use `save_extended_comparison` or `save_budget_matched_comparison`
in `mathqa_bandits.py`; neither function reads the database or executes policies.
Add `--portable-dir data/search_baselines` to explicitly export the eight new
compact files. This never rewrites the original three-strategy snapshots.
The budget-matched and sweep JSONs also retain hashes/paths of each horizon's
full-history file. Portable exports include the current plotter hash.

## Limits and validation (all strategies)

Prefix pooling and regularization estimate expected behavior; they can differ
from individual frozen configuration means even at complete exposure. Thus an
adapted VineLM endpoint is allowed to have a nonzero gap. Full exposure makes
prefix counts independent of sampling order; the final choice should agree
across seeds unless estimated accuracies tie and the tie priorities differ.

There is one saved realization per pair: seeds vary profiling order, not model
generation, routing or verifier behavior. Twenty questions give 5-percentage-point
accuracy increments. Preserve original keys and quality flags; do not remove
the six known problematic questions after inspecting performance. Results are
development-data search baselines, not held-out deployment guarantees.

Validate false acceptance/rejection, paid truncations, no fabricated uncalled
observations, no pair reuse, oracle separation, reproducible seeds, proper
budget lookup, and smoothing bounds/missing-column behavior. Validate real-grid
cost/score reconciliation, unchanged database bytes, and rejection of bad or
incomplete data. Run the existing offline regression suite. Inspect the rendered
figure for labels, units, uncertainty meaning and readability.

## Reproduction

```
uv sync --extra profiling
uv run --locked --extra profiling python scripts/mathqa_vinelm.py --plot
uv run --locked --extra profiling python scripts/mathqa_search.py --plot
uv run --locked --extra profiling python scripts/mathqa_search_plot.py results/workflow_search/search-comparison.json
uv run --locked --extra profiling python -m unittest discover -s tests
```

The first command installs numerical/plotting packages only. The latter experiment
reads the frozen database and writes ignored artifacts under
`results/workflow_search/`. To study sparse decomposition without SVD, use
`--no-smoothing`; it can run without NumPy when no plot is requested.

`mathqa_search.py --plot` executes only AgentOpt and Random, reusing the saved
VineLM result. `mathqa_search_plot.py` redraws from saved values only. To
regenerate a comparison's values from saved strategy histories without running
any search, call `mathqa_search.save_comparison([...result paths...], output)`.

## Change history

- `vinelm-adapted-v1`: initial approved adaptation. Random unseen-pair replay,
  prefix statistics, continuation-aware decomposition, fixed symmetric priors,
  third-stage SVD smoothing, full recorded costs, and evaluator-only gap curves.
- `agentopt-matrix-ucb-e-v1`, `random-pair-search-v1`: add the approved UCB-E and
  Random pair baselines. Preserve original VineLM histories and values. Add
  optional explicit budgets to the shared aggregator without changing its
  existing defaults or VineLM numerical semantics, and add saved-data overlays.
- `gittins-equal-cost-finite-v1`, `sysrs-synchronized-v1`: add the approved
  equal-decision-cost Gittins and SySRs policies. Preserve previous results.
  Document reference numerical defaults, serial synchronized phases, strict
  planned pair caps, finite-set recommendations, 10% default SySRs horizon,
  ten independent horizons, and seed-specific cost matching. Add extended
  anytime and budget-matched comparisons without changing original v1 semantics.
