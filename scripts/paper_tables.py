#!/usr/bin/env python3
"""
scripts/paper_tables.py

Writes the paper's tables as LaTeX (paper/generated/table_*.tex) from the measured results:
- table_pairs.tex: per bug pair, the suite, the naive mutation-score gain, its placebo
  p-value and A12 for mutation score and coverage at equal suite size.
- table_operators.tex: per mutation operator (scored in at least 7 pairs, plus the naive pick), A12 at equal
  suite size and the operator's share of all mutants.

Inputs: data/v2/pitfall_analysis.csv, data/v2/subset_pairs.csv,
data/v2/subset_operator_summary.csv (written by pitfall_analysis.py and subset_analysis.py).
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

import pandas as pd

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.paper_numbers import tex_escape, write_lines

MIN_PAIRS_FOR_TABLE = 7
# Always shown: the operators the naive analysis singled out
ALWAYS_SHOWN = {"MATH", "CONDITIONALS_BOUNDARY", "MATH + CONDITIONALS_BOUNDARY (paper's selection)"}

# Short operator names for a single-column table; the caption explains RC and CB.
OPERATOR_LABELS = {
    "REMOVE_CONDITIONALS (all 4 variants)": "RC (all 4 variants)",
    "MATH + CONDITIONALS_BOUNDARY (paper's selection)": "MATH + CB (naive pick)",
    "RETURNS (5 return-value mutators)": "RETURNS (5 mutators)",
    "CONDITIONALS_BOUNDARY": "CB",
}


def operator_label(group: str) -> str:
    label = OPERATOR_LABELS.get(group, group.replace("REMOVE_CONDITIONALS_", "RC_"))
    return f"\\texttt{{{tex_escape(label)}}}"


def pairs_table(pitfall: pd.DataFrame, pairs: pd.DataFrame) -> list:
    df = pitfall.merge(pairs[["bug_id", "a12_ms", "a12_cov"]], on="bug_id").sort_values("delta_matrix", ascending=False)
    lines = [
        r"\begin{tabular}{@{}lrrrrrr@{}}",
        r"\toprule",
        r"Class (commit) & Tests & Added & $\Delta$MS & $p_{\mathrm{pl}}$ & \multicolumn{2}{c}{$\hat{A}_{12}$} \\",
        r"\cmidrule(l){6-7}",
        r" & & (rev.) & (pp) & & MS & Cov. \\",
        r"\midrule",
    ]
    for r in df.itertuples():
        a12_ms = "--" if pd.isna(r.a12_ms) else f"{r.a12_ms:.2f}"
        a12_cov = "--" if pd.isna(r.a12_cov) else f"{r.a12_cov:.2f}"
        lines.append(
            f"{tex_escape(r.class_name)} ({r.bug_id[:7]}) & {r.tests} & {r.added} ({r.fault_revealing}) & "
            f"{r.delta_matrix:.2f} & {r.placebo_ge_real:.3f} & {a12_ms} & {a12_cov} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    return lines


def operators_table(ops: pd.DataFrame) -> list:
    df = ops[(ops["pairs"] >= MIN_PAIRS_FOR_TABLE) | ops["group"].isin(ALWAYS_SHOWN)].sort_values("a12", ascending=False)
    lines = [
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"Operator & Pairs & Share & $\hat{A}_{12}$ & $>0.5$ \\",
        r"\midrule",
    ]
    for r in df.itertuples():
        lines.append(f"{operator_label(r.group)} & {int(r.pairs)} & {r.share * 100:.1f}\\% & {r.a12:.2f} & {int(r.above)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write the paper's LaTeX tables from measured results.")
    parser.add_argument("--pitfall", default="data/v2/pitfall_analysis.csv")
    parser.add_argument("--pairs", default="data/v2/subset_pairs.csv")
    parser.add_argument("--operators", default="data/v2/subset_operator_summary.csv")
    args = parser.parse_args()

    pitfall = pd.read_csv(args.pitfall, dtype={"bug_id": str})
    pairs = pd.read_csv(args.pairs, dtype={"bug_id": str})
    ops = pd.read_csv(args.operators)
    p1 = write_lines("table_pairs.tex", pairs_table(pitfall, pairs), "scripts/paper_tables.py")
    p2 = write_lines("table_operators.tex", operators_table(ops), "scripts/paper_tables.py")
    print(f"[✓] Tables written -> {p1.relative_to(PROJECT_ROOT)}, {p2.relative_to(PROJECT_ROOT)}")
