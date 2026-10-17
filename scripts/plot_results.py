"""
scripts/plot_results.py

Draws the paper's figures from the measured results (never from typed-in numbers):
- figures/pitfall_placebo.(pdf|png): per pair, the mutation-score gain of the tests the
  fix added vs. removing the same number of random tests that do not reveal the bug.
- figures/a12_ms_vs_coverage.(pdf|png): per pair, A12 of mutation score vs. coverage
  for equal-size test subsets.

Inputs: data/v2/pitfall_analysis.csv and data/v2/subset_pairs.csv.
"""

from __future__ import annotations
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# Validated categorical slots 1-2 (dataviz reference palette) and text/grid inks
SERIES_1 = "#2a78d6"     # blue
SERIES_2 = "#eb6834"     # orange
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3de"


def set_paper_style() -> None:
    """IEEE single-column figures: 3.4 in wide, small sans text, recessive grid."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "axes.edgecolor": TEXT_SECONDARY,
        "axes.labelcolor": TEXT_PRIMARY,
        "xtick.color": TEXT_SECONDARY,
        "ytick.color": TEXT_PRIMARY,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
    })


def pair_label(row: pd.Series) -> str:
    return f"{row['class_name']} ({row['bug_id'][:7]})"


def save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    # No creation timestamp in the files, so regenerating them gives identical bytes
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight", metadata={"CreationDate": None})
    fig.savefig(out_dir / f"{name}.png", dpi=300, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    print(f"[✓] Saved figures/{name}.pdf and .png")


def plot_pitfall(pitfall: pd.DataFrame, out_dir: Path) -> None:
    df = pitfall.sort_values("delta_matrix").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    y = range(len(df))
    ax.hlines(y, df["placebo_p05"], df["placebo_p95"], color=SERIES_2, linewidth=2, zorder=2,
              label="Same number of random tests that reveal no bug (median, 5th–95th percentile)")
    ax.scatter(df["placebo_median"], y, marker="D", s=14, color=SERIES_2, edgecolor="white", linewidth=0.6, zorder=3)
    ax.scatter(df["delta_matrix"], y, marker="o", s=22, color=SERIES_1, edgecolor="white", linewidth=0.6, zorder=4,
               label="Tests the fix added")
    for i, row in df.iterrows():
        if row["placebo_ge_real"] < 0.05:
            ax.annotate(f"p={row['placebo_ge_real']:.3f}", (row["delta_matrix"], i), xytext=(5, -2),
                        textcoords="offset points", fontsize=6, color=TEXT_PRIMARY)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlim(-0.05, 40)
    ax.set_xticks([0, 0.5, 1, 2, 5, 10, 20])
    ax.set_xticklabels(["0", "0.5", "1", "2", "5", "10", "20"])
    ax.set_yticks(list(y))
    ax.set_yticklabels([pair_label(r) for _, r in df.iterrows()])
    ax.set_xlabel("Mutation-score gain ΔMS when tests are added (percentage points)")
    ax.grid(axis="x", color=GRID, linewidth=0.6, zorder=0)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.02, 1.0), frameon=False, handletextpad=0.4, borderaxespad=0.2)
    save(fig, out_dir, "pitfall_placebo")


def plot_a12(pairs: pd.DataFrame, pitfall: pd.DataFrame, out_dir: Path) -> None:
    df = pairs.merge(pitfall[["bug_id", "class_name"]], on="bug_id").dropna(subset=["a12_ms", "a12_cov"])
    df = df.sort_values("a12_ms").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    y = range(len(df))
    ax.hlines(y, df[["a12_ms", "a12_cov"]].min(axis=1), df[["a12_ms", "a12_cov"]].max(axis=1),
              color=GRID, linewidth=1.5, zorder=1)
    ax.scatter(df["a12_cov"], y, marker="D", s=14, color=SERIES_2, edgecolor="white", linewidth=0.6, zorder=3,
               label="Coverage")
    ax.scatter(df["a12_ms"], y, marker="o", s=22, color=SERIES_1, edgecolor="white", linewidth=0.6, zorder=4,
               label="Mutation score")
    ax.axvline(0.5, color=TEXT_SECONDARY, linestyle=(0, (3, 2)), linewidth=0.8, zorder=0)
    ax.text(0.505, len(df) - 0.4, "0.5 = no information beyond size", fontsize=6, color=TEXT_SECONDARY, va="bottom")
    ax.set_xlim(0.3, 1.0)
    ax.set_yticks(list(y))
    ax.set_yticklabels([pair_label(r) for _, r in df.iterrows()])
    ax.set_xlabel("A12: chance a bug-detecting subset outscores a non-detecting one of equal size")
    ax.grid(axis="x", color=GRID, linewidth=0.6, zorder=0)
    ax.legend(loc="lower right", frameon=False, handletextpad=0.4)
    save(fig, out_dir, "a12_ms_vs_coverage")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the paper figures from measured results.")
    parser.add_argument("--pitfall", default="data/v2/pitfall_analysis.csv", help="Output of pitfall_analysis.py")
    parser.add_argument("--pairs", default="data/v2/subset_pairs.csv", help="Output of subset_analysis.py")
    parser.add_argument("--outdir", default="figures", help="Output figures directory")
    args = parser.parse_args()

    set_paper_style()
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pitfall = pd.read_csv(args.pitfall, dtype={"bug_id": str})
    pairs = pd.read_csv(args.pairs, dtype={"bug_id": str})
    plot_pitfall(pitfall, out_dir)
    plot_a12(pairs, pitfall, out_dir)
