"""Standalone scientific figures regenerated from saved search result values."""

import argparse
import json
import os
from pathlib import Path


def plot_result(result, output):
    output = Path(output).resolve()
    if output.suffix.lower() != ".png":
        raise ValueError("Choose a .png output.")
    output.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(output.parent / ".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    curve = result["curve"]
    x = [float(p["cost_cents"]) for p in curve]
    mean = [p["mean_gap_pp"] for p in curve]
    low = [p["p10_gap_pp"] for p in curve]
    high = [p["p90_gap_pp"] for p in curve]
    exhaustive = result["exhaustive"]
    total = float(exhaustive["cost_cents"])
    fig, ax = plt.subplots(figsize=(10.5, 6.3), layout="constrained")
    color = "#2563eb"
    smoothing = result["settings"]["depth3_rank_one_smoothing"]
    label = "VineLM adapted" if smoothing else "VineLM adapted (no smoothing)"
    ax.fill_between(x, low, high, color=color, alpha=.16, label="10th-90th percentile of profiling orders")
    ax.plot(x, mean, color=color, linewidth=2.4, label=label + " - mean")
    ax.axhline(0, color="#94a3b8", linewidth=1)
    ax.scatter([total], [0], color="#111827", s=55, marker="D", zorder=5,
               label=f"Exhaustive: {total:.4f} cents, {100 * exhaustive['accuracy']:.0f}% accuracy")
    ax.set(xlabel="Cumulative profiling cost (cents)",
           ylabel="Accuracy gap from best fixed sequence (percentage points)",
           title=f"Finding one configuration across {result['source']['question_count']} questions",
           xlim=(0, total * 1.045),
           ylim=(-1, max(high + [5]) * 1.08))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.2)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    fig.suptitle(f"{result['source']['configuration_count']} configurations | {result['settings']['seeds']} random seeds | "
                 "full recorded costs, no checkpoint discounts", fontsize=10, color="#475569")
    fig.text(.01, -.025, "Gap uses full frozen-grid accuracy of the current recommendation; estimates use queried traces only.\n"
             "Band measures profiling-order variation, not uncertainty on new questions. Prefix pooling may leave a nonzero final gap.",
             fontsize=8.5, color="#475569")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    fig.savefig(output.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return output


LABELS = {"vinelm": "VineLM adapted", "agentopt": "AgentOpt (Matrix UCB-E)", "random": "Random (pairs)",
          "gittins": "Gittins (equal decision costs)", "sysrs": "SySRs"}
COLORS = {"vinelm": "#2563eb", "agentopt": "#d97706", "random": "#059669",
          "gittins": "#9333ea", "sysrs": "#dc477c"}
STYLES = {"vinelm": "-", "agentopt": "--", "random": ":", "gittins": "-.", "sysrs": (0, (5, 1, 1, 1))}


def plot_comparison(comparison, output, *, bands=False):
    output = Path(output).resolve()
    if output.suffix.lower() != ".png":
        raise ValueError("Choose a .png output.")
    output.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(output.parent / ".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10.5, 6.3), layout="constrained")
    upper = [5]
    for series in comparison["series"]:
        strategy, curve = series["strategy"], series["curve"]
        x = [float(p["cost_cents"]) for p in curve]
        means = [p["mean_gap_pp"] for p in curve]
        color, label = COLORS[strategy], LABELS[strategy]
        if strategy == "sysrs":
            label += (" (budget-specific runs)" if series["settings"].get("curve_semantics") == "independent-horizon"
                      else f" (planned {series['settings']['planned_budget']} pairs)")
        if bands:
            low = [p["p10_gap_pp"] for p in curve]
            high = [p["p90_gap_pp"] for p in curve]
            ax.fill_between(x, low, high, color=color, alpha=.09)
            upper.extend(high)
        upper.extend(means)
        ax.plot(x, means, color=color, linewidth=2.4, linestyle=STYLES[strategy], label=label,
                marker="o" if comparison.get("version") == "workflow-search-budget-matched-v1" else None,
                markersize=3.5)
    exhaustive = comparison["exhaustive"]
    total = float(exhaustive["cost_cents"])
    ax.axhline(0, color="#94a3b8", linewidth=1)
    ax.scatter([total], [0], color="#111827", marker="D", s=50, zorder=5,
               label=f"Exhaustive: {total:.4f} cents, {100 * exhaustive['accuracy']:.0f}% accuracy")
    ax.set(xlabel="Cumulative profiling cost (cents)",
           ylabel="Mean accuracy gap from best fixed sequence (percentage points)",
           title="Finding one configuration: profiling cost versus accuracy gap",
           xlim=(0, total * 1.045), ylim=(-.3, max(upper) * 1.08))
    if comparison.get("version") == "workflow-search-budget-matched-v1":
        ax.set_xlabel("Mean profiling budget (cents; matched within each seed)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.2)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    source = comparison["source"]
    seeds = comparison["series"][0]["settings"]["seeds"]
    fig.suptitle(f"{source['question_count']} saved questions | {source['configuration_count']} configurations | "
                 f"{seeds} random seeds | full recorded costs", fontsize=10, color="#475569")
    footer = "Each curve assesses the current recommendation using the frozen dataset; search sees queried observations only.\n"
    footer += ("Shaded bands: 10th-90th percentiles of profiling orders, not confidence on new questions." if bands else
               "Profiling-order percentiles and per-seed histories are saved separately. No cache or checkpoint discounts.")
    if comparison.get("version") == "workflow-search-comparison-v2":
        footer += "\nEach line ends at its supported spend range; SySRs is one planned-horizon trace, not independent smaller-budget runs."
    if comparison.get("version") == "workflow-search-budget-matched-v1":
        footer += "\nSySRs is rerun for each planned pair budget; other methods use their last affordable observation at that seed's SySRs spend."
    fig.text(.01, -.06, footer, fontsize=8.5, color="#475569", va="top")
    fig.savefig(output, dpi=180, bbox_inches="tight")
    fig.savefig(output.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="Saved single-strategy or comparison JSON.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bands", action="store_true", help="Show saved percentile bands in comparison plots.")
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    if "series" in result:
        plot_comparison(result, args.output or args.result.with_suffix(".png"), bands=args.bands)
    else:
        plot_result(result, args.output or args.result.with_suffix(".png"))


if __name__ == "__main__":
    main()
