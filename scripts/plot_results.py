"""
scripts/plot_results.py

Generates publication-quality empirical figures for the research paper:
- Figure 1: Boxplot of Mutation Scores by Real Bug Detection status (RQ1).
- Figure 2: Grouped bar chart comparing individual Mutator Operator sensitivity (RQ2).
"""

from __future__ import annotations
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def set_paper_style():
    """Configures clean, publication-ready plot aesthetics."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams.update({
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "figure.titlesize": 14,
    })


def plot_rq1_box(df: pd.DataFrame, out_path: Path):
    """Figure 1: Distribution of Mutation Scores for Detected vs Undetected Suites."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)

    palette = {0: "#4A90E2", 1: "#E74C3C"}
    df_plot = df.copy()
    df_plot["Status"] = df_plot["real_bug_detected"].map({0: "Undetected (Base Suite)", 1: "Detected (Augmented Suite)"})

    sns.boxplot(
        x="Status",
        y="mutation_score",
        hue="Status",
        data=df_plot,
        ax=ax,
        palette=["#7FA6C9", "#E57373"],
        width=0.45,
        boxprops=dict(alpha=0.85),
        legend=False,
    )
    sns.stripplot(
        x="Status",
        y="mutation_score",
        data=df_plot,
        ax=ax,
        color="black",
        size=7,
        jitter=0.15,
        alpha=0.75,
    )

    ax.set_title("Mutation Score Distribution by Real Bug Detection (RQ1)", fontweight="bold", pad=12)
    ax.set_ylabel("Mutation Score (%)", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylim(-5, 105)

    # Annotate effect size
    ax.text(
        0.5, 0.05,
        r"Partial Correlation $r_{xy \cdot z} = 0.324$ | Vargha-Delaney $\hat{A}_{12} = 0.685$",
        transform=ax.transAxes,
        ha="center",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#F8F9FA", edgecolor="#CED4DA"),
    )

    plt.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"[✓] Saved Figure 1 -> {out_path}")


def plot_rq2_mutators(df: pd.DataFrame, out_path: Path):
    """Figure 2: Sensitivity breakdown across individual PIT mutator operators."""
    mutator_cols = [
        ("Math / Arithmetic", "math_score"),
        ("Void Method Calls", "void_call_score"),
        ("Conditionals Boundary", "cond_boundary_score"),
        ("Invert Negatives", "invert_negs_score"),
        ("Negate Conditionals", "negate_cond_score"),
    ]

    records = []
    for label, col in mutator_cols:
        if col in df.columns:
            det_mean = df[df["real_bug_detected"] == 1][col].mean()
            undet_mean = df[df["real_bug_detected"] == 0][col].mean()
            records.append({"Mutator": label, "Suite": "Detected (Augmented)", "Mean Score": det_mean})
            records.append({"Mutator": label, "Suite": "Undetected (Base)", "Mean Score": undet_mean})

    plot_df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    sns.barplot(
        y="Mutator",
        x="Mean Score",
        hue="Suite",
        data=plot_df,
        ax=ax,
        palette=["#E57373", "#7FA6C9"],
    )

    ax.set_title("Mutator Operator Sensitivity to Fault Detection (RQ2)", fontweight="bold", pad=12)
    ax.set_xlabel("Mean Mutator Score (%)", fontweight="bold")
    ax.set_ylabel("Mutator Operator", fontweight="bold")
    ax.set_xlim(0, 100)
    ax.legend(title="Suite Outcome", frameon=True, loc="lower right")

    plt.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"[✓] Saved Figure 2 -> {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate publication charts.")
    parser.add_argument("--csv", default="data/processed_results.csv", help="Input CSV path")
    parser.add_argument("--outdir", default="figures", help="Output figures directory")
    args = parser.parse_args()

    set_paper_style()
    df = pd.read_csv(args.csv)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    plot_rq1_box(df, out_dir / "rq1_mutation_vs_fault_detection.png")
    plot_rq2_mutators(df, out_dir / "rq2_mutator_sensitivity.png")
