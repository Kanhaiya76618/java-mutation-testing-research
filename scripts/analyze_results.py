"""
scripts/analyze_results.py

Computes statistical significance, correlation, and effect sizes for the empirical study:
- Spearman's rho and Kendall's tau
- Partial correlation controlling for test-suite size
- Vargha-Delaney A12 effect size and Cliff's delta
- Mutator operator efficiency breakdown (RQ2)
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from scipy import stats


def vargha_delaney_a12(group1: np.ndarray, group2: np.ndarray) -> float:
    """Computes Vargha-Delaney A12 non-parametric effect size.
    A12 = (R1 / n1 - (n1 + 1) / 2) / n2
    """
    m = len(group1)
    n = len(group2)
    if m == 0 or n == 0:
        return 0.5
    r = stats.rankdata(np.concatenate([group1, group2]))
    r1 = np.sum(r[:m])
    return float((r1 / m - (m + 1.0) / 2.0) / n)


def cliffs_delta(group1: np.ndarray, group2: np.ndarray) -> float:
    """Computes Cliff's delta non-parametric effect size in [-1, 1]."""
    m = len(group1)
    n = len(group2)
    if m == 0 or n == 0:
        return 0.0
    greater = sum(1 for x in group1 for y in group2 if x > y)
    less = sum(1 for x in group1 for y in group2 if x < y)
    return float((greater - less) / (m * n))


def partial_corr(x: pd.Series, y: pd.Series, z: pd.Series) -> Tuple[float, float]:
    """Computes partial rank correlation between x and y controlling for z."""
    rx = stats.rankdata(x)
    ry = stats.rankdata(y)
    rz = stats.rankdata(z)

    # Correlation matrix
    df = pd.DataFrame({"x": rx, "y": ry, "z": rz})
    c = df.corr(method="pearson").to_numpy()
    r_xy, r_xz, r_yz = c[0, 1], c[0, 2], c[1, 2]

    denom = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
    if denom == 0:
        return 0.0, 1.0
    r_part = (r_xy - r_xz * r_yz) / denom

    # Degrees of freedom: n - 2 - k (k=1 controlling variable)
    n = len(x)
    df_resid = n - 3
    if df_resid <= 0 or abs(r_part) >= 1.0:
        return float(r_part), 1.0

    t_stat = r_part * np.sqrt(df_resid / (1 - r_part**2))
    p_val = float(2 * (1 - stats.t.cdf(abs(t_stat), df=df_resid)))
    return float(r_part), p_val


class EmpiricalAnalyzer:
    def __init__(self, csv_path: str | Path):
        self.csv_path = Path(csv_path).resolve()
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Results CSV not found: {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)

    def analyze(self) -> str:
        out = []
        out.append("# Empirical Evaluation Results: Mutation Score vs. Fault Detection\n")
        out.append(f"**Dataset Summary:** {len(self.df)} total experiment records.\n")

        # Separate into detected vs non-detected
        detected = self.df[self.df["real_bug_detected"] == 1]
        not_detected = self.df[self.df["real_bug_detected"] == 0]

        out.append(f"- Real Fault Detected: {len(detected)} trials")
        out.append(f"- Real Fault Not Detected: {len(not_detected)} trials\n")

        # ----------------------------------------------------
        # RQ1: Overall Correlation & Size Control
        # ----------------------------------------------------
        out.append("## RQ1: Predictive Power of Mutation Score Gains")
        ms = self.df["mutation_score"].to_numpy()
        fault = self.df["real_bug_detected"].to_numpy()
        tests = self.df["test_count"].to_numpy()

        if len(self.df) >= 3 and len(np.unique(fault)) > 1:
            spearman_rho, s_p = stats.spearmanr(ms, fault)
            kendall_tau, k_p = stats.kendalltau(ms, fault)
            part_r, p_p = partial_corr(self.df["mutation_score"], self.df["real_bug_detected"], self.df["test_count"])
            a12 = vargha_delaney_a12(detected["mutation_score"].to_numpy(), not_detected["mutation_score"].to_numpy())
            delta = cliffs_delta(detected["mutation_score"].to_numpy(), not_detected["mutation_score"].to_numpy())

            out.append("| Metric | Value | p-value | Interpretation |")
            out.append("|---|---|---|---|")
            out.append(f"| **Spearman Rank ($\\rho$)** | {spearman_rho:0.3f} | {s_p:0.4f} | {'Statistically Significant' if s_p < 0.05 else 'Not Significant'} |")
            out.append(f"| **Kendall Tau ($\\tau$)** | {kendall_tau:0.3f} | {k_p:0.4f} | Rank concordant association |")
            out.append(f"| **Partial Correlation ($r_{{xy \\cdot z}}$)** | {part_r:0.3f} | {p_p:0.4f} | Controlled for Test-Suite Size |")
            out.append(f"| **Vargha-Delaney ($\\hat{{A}}_{{12}}$)** | {a12:0.3f} | — | {'Large effect' if a12 >= 0.71 else 'Medium effect' if a12 >= 0.64 else 'Small/Negligible'} |")
            out.append(f"| **Cliff's Delta ($\\delta$)** | {delta:0.3f} | — | Non-parametric dominance |")
        else:
            out.append("*Note: Minimum of 3 varied records required for statistical correlation metrics. Run batch runner to populate records.*")

        # ----------------------------------------------------
        # RQ2: Mutator Group Breakdown
        # ----------------------------------------------------
        out.append("\n## RQ2: Mutator Operator Efficiency Breakdown")
        out.append("| Mutator Operator | Mean Score (Detected) | Mean Score (Undetected) | Predictive Signal |")
        out.append("|---|---|---|---|")

        mutator_cols = [
            ("Conditionals Boundary", "cond_boundary_score"),
            ("Negate Conditionals", "negate_cond_score"),
            ("Math / Arithmetic", "math_score"),
            ("Void Method Calls", "void_call_score"),
            ("Invert Negatives", "invert_negs_score"),
        ]

        for label, col in mutator_cols:
            if col in self.df.columns:
                mean_det = detected[col].mean() if len(detected) > 0 else 0.0
                mean_not = not_detected[col].mean() if len(not_detected) > 0 else 0.0
                diff = mean_det - mean_not
                signal = r"Strong ($\Delta > +10\%$)" if diff > 10 else "Moderate" if diff > 0 else "Neutral/Low"
                out.append(f"| **{label}** | {mean_det:0.2f}% | {mean_not:0.2f}% | {signal} |")

        report_str = "\n".join(out)
        print(report_str)
        return report_str


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze mutation experiment CSV.")
    parser.add_argument("--csv", default="data/processed_results.csv", help="Path to results CSV")
    parser.add_argument("--output-report", default="docs/LATEST_STATISTICAL_REPORT.md", help="Save markdown report")
    args = parser.parse_args()

    analyzer = EmpiricalAnalyzer(args.csv)
    report = analyzer.analyze()

    out_file = Path(args.output_report)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")
    print(f"\n[✓] Statistical report saved -> {out_file}")
