#!/usr/bin/env python3
"""
scripts/compare_v1_v2.py

Compares the original dataset (data/processed_results.csv, "v1") with the data
re-measured by the corrected runner (data/v2/runs.csv, operators.csv and
skipped.csv, "v2"), bug by bug, so that every change to a reported number can
be traced to raw data.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# v1 columns that tracked single operators -> the PIT mutator class they were meant to measure
V1_OPERATOR_COLUMNS = {
    "cond_boundary_score": "ConditionalsBoundaryMutator",
    "negate_cond_score": "NegateConditionalsMutator",
    "math_score": "MathMutator",
    "void_call_score": "VoidMethodCallMutator",
    "invert_negs_score": "InvertNegsMutator",
}


def fmt(value: Any, digits: int = 2, signed: bool = False) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"


def v1_commit_prefix(bug_id: str, mined: List[Dict[str, Any]]) -> str:
    """v1 used either a commit prefix or an issue key (e.g. 'LANG-1834') as bug_id."""
    for c in mined:
        if c["commit_hash"].startswith(bug_id) or c["message"].startswith(bug_id + " "):
            return c["commit_hash"][:8]
    return bug_id


def suite_value(df: pd.DataFrame, bug: str, suite: str, col: str) -> Optional[float]:
    rows = df[(df["bug"] == bug) & (df["suite_type"] == suite)]
    if rows.empty or pd.isna(rows.iloc[0][col]):
        return None
    return float(rows.iloc[0][col])


def compare(v1_csv: Path, v2_dir: Path, mined_json: Path) -> str:
    mined = json.loads(mined_json.read_text(encoding="utf-8"))
    v1 = pd.read_csv(v1_csv)
    v1["bug"] = v1["bug_id"].map(lambda b: v1_commit_prefix(str(b), mined))
    runs = pd.read_csv(v2_dir / "runs.csv", dtype={"bug_id": str})
    runs["bug"] = runs["bug_id"]
    ops = pd.read_csv(v2_dir / "operators.csv", dtype={"bug_id": str})
    skipped_path = v2_dir / "skipped.csv"
    skipped = pd.read_csv(skipped_path, dtype={"bug_id": str}) if skipped_path.exists() else pd.DataFrame(columns=["bug_id", "reason"])

    out: List[str] = []
    out.append("# Data comparison: original CSV (v1) vs. re-measured data (v2)\n")
    out.append(f"- v1: `{v1_csv}` ({v1['bug'].nunique()} bug pairs)")
    out.append(f"- v2: `{v2_dir}/runs.csv` ({runs['bug'].nunique()} bug pairs), `operators.csv`, `skipped.csv`")
    out.append("- v2 mutation score = PIT's own definition (detected / total, timeouts count as detected); "
               "killed-only = KILLED / total, the v1 definition.\n")

    # ------------------------------------------------------------------
    # 1. Which candidates are in which dataset
    # ------------------------------------------------------------------
    out.append("## 1. Candidates\n")
    out.append("| # | Commit | Change | In v1 | In v2 | v2 skip reason |")
    out.append("|---|---|---|---|---|---|")
    for i, c in enumerate(mined):
        bug = c["commit_hash"][:8]
        reason = skipped.loc[skipped["bug_id"] == bug, "reason"]
        out.append(
            f"| {i} | `{bug}` | {c['message'][:55]} | {'yes' if bug in set(v1['bug']) else 'no'} | "
            f"{'yes' if bug in set(runs['bug']) else 'no'} | {reason.iloc[0] if not reason.empty else ''} |"
        )

    # ------------------------------------------------------------------
    # 2. Suite size and mutation score per pair
    # ------------------------------------------------------------------
    out.append("\n## 2. Suite size and mutation score per pair\n")
    out.append("| Commit | Tests base→aug (v1) | Tests base→aug (v2) | MS base→aug (v1) | MS base→aug (v2) | ΔMS v1 | ΔMS v2 | ΔMS v2 killed-only | Added tests failing on V_bug |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    bugs = sorted(set(v1["bug"]) | set(runs["bug"]))
    for bug in bugs:
        tb1, ta1 = suite_value(v1, bug, "base", "test_count"), suite_value(v1, bug, "augmented", "test_count")
        tb2, ta2 = suite_value(runs, bug, "base", "test_count"), suite_value(runs, bug, "augmented", "test_count")
        mb1, ma1 = suite_value(v1, bug, "base", "mutation_score"), suite_value(v1, bug, "augmented", "mutation_score")
        mb2, ma2 = suite_value(runs, bug, "base", "mutation_score"), suite_value(runs, bug, "augmented", "mutation_score")
        kb2, ka2 = suite_value(runs, bug, "base", "killed_only_score"), suite_value(runs, bug, "augmented", "killed_only_score")
        aug = runs[(runs["bug"] == bug) & (runs["suite_type"] == "augmented")]
        if aug.empty:
            revealing = "—"
        else:
            failing = str(aug.iloc[0]["fault_revealing_tests"]) if pd.notna(aug.iloc[0]["fault_revealing_tests"]) else ""
            revealing = f"{len([t for t in failing.split(';') if t])} of {int(aug.iloc[0]['added_tests'])}"
        out.append(
            f"| `{bug}` | {fmt(tb1, 0)} → {fmt(ta1, 0)} | {fmt(tb2, 0)} → {fmt(ta2, 0)} | "
            f"{fmt(mb1)} → {fmt(ma1)} | {fmt(mb2)} → {fmt(ma2)} | "
            f"{fmt(None if mb1 is None or ma1 is None else ma1 - mb1, signed=True)} | "
            f"{fmt(None if mb2 is None or ma2 is None else ma2 - mb2, signed=True)} | "
            f"{fmt(None if kb2 is None or ka2 is None else ka2 - kb2, signed=True)} | {revealing} |"
        )

    # ------------------------------------------------------------------
    # 3. Operators: what v1 reported vs what PIT actually generated
    # ------------------------------------------------------------------
    out.append("\n## 3. Operator columns of v1 vs. mutants that exist in v2 (augmented suite)\n")
    out.append("v1 wrote 0.00 when a class had no mutants of an operator. v2 counts only mutants that exist.\n")
    out.append("| Commit | " + " | ".join(V1_OPERATOR_COLUMNS.values()) + " |")
    out.append("|---|" + "---|" * len(V1_OPERATOR_COLUMNS))
    for bug in bugs:
        cells = []
        for col, mutator in V1_OPERATOR_COLUMNS.items():
            v1_val = suite_value(v1, bug, "augmented", col)
            row = ops[(ops["bug_id"] == bug) & (ops["suite_type"] == "augmented") & (ops["mutator"] == mutator)]
            v2_val = f"{int(row.iloc[0]['detected'])}/{int(row.iloc[0]['total'])}" if not row.empty else "none"
            cells.append(f"v1 {fmt(v1_val, 1)} · v2 {v2_val}")
        out.append(f"| `{bug}` | " + " | ".join(cells) + " |")

    out.append("\n## 4. Mutators PIT generated in v2 (all bugs, augmented suite)\n")
    out.append("| Mutator | Operator | Mutants | Detected | Bugs with this mutator |")
    out.append("|---|---|---|---|---|")
    aug_ops = ops[ops["suite_type"] == "augmented"]
    for mutator, g in aug_ops.groupby("mutator"):
        out.append(f"| {mutator} | {g['operator'].iloc[0]} | {int(g['total'].sum())} | {int(g['detected'].sum())} | {g['bug_id'].nunique()} |")

    # ------------------------------------------------------------------
    # 5. Which mutants do the added (bug-revealing) tests newly detect?
    # ------------------------------------------------------------------
    out.append("\n## 5. Mutants newly detected by the added tests (T_aug minus T_base), per operator\n")
    out.append("Raw counts summed over all v2 pairs. This is descriptive: adding tests can only add detections.\n")
    out.append("| Operator | Mutants (all pairs) | Newly detected | Pairs with ≥1 newly detected | Newly detected per pair |")
    out.append("|---|---|---|---|---|")
    wide = ops.pivot_table(index=["bug_id", "operator"], columns="suite_type", values="detected", aggfunc="sum").fillna(0)
    totals = ops[ops["suite_type"] == "augmented"].groupby("operator")["total"].sum()
    gains = (wide["augmented"] - wide["base"]).rename("gain").reset_index()
    for operator, g in gains.groupby("operator"):
        per_pair = ", ".join(f"{b}: {int(v)}" for b, v in zip(g["bug_id"], g["gain"]) if v != 0)
        out.append(f"| {operator} | {int(totals.get(operator, 0))} | {int(g['gain'].sum())} | {int((g['gain'] > 0).sum())} | {per_pair} |")

    return "\n".join(out) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare the v1 CSV with the re-measured v2 data.")
    parser.add_argument("--v1", default="data/processed_results.csv", help="Original results CSV")
    parser.add_argument("--v2-dir", default="data/v2", help="Directory with runs.csv, operators.csv, skipped.csv")
    parser.add_argument("--mined-bugs", default="data/mined_bugs_commons_lang.json", help="Mined bugs JSON")
    parser.add_argument("--output", default="docs/DATA_V1_VS_V2.md", help="Markdown report path")
    args = parser.parse_args()

    report = compare(Path(args.v1), Path(args.v2_dir), Path(args.mined_bugs))
    print(report)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"[✓] Comparison report saved -> {out_path}")
