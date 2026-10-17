#!/usr/bin/env python3
"""
scripts/subset_analysis.py

Equal-size test-subset analysis (RQ1 and RQ2, following Papadakis et al. ICSE 2018).

For every bug pair, the pool is every test method of the augmented suite T_aug, and the
fault-revealing tests are those that fail on the buggy version V_bug. For several subset
sizes k, random subsets of exactly k tests are drawn. A subset "detects the bug" if it
contains a fault-revealing test. Using PIT's kill matrix, each subset gets a mutation
score (MS), a coverage score (COV, the baseline) and one score per mutation operator.

Because all subsets in a comparison have the same size, suite size cannot explain the
result. A12 = chance that a random bug-detecting subset scores higher than a random
non-detecting subset of the same size (0.5 = the score tells nothing beyond size).

Inputs come only from measured data: data/v2/runs.csv and data/raw/<bug_id>/.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.kill_matrix import KillMatrix, a12, random_subsets
from harness.pit_parser import PitMutationReport
from harness.surefire_parser import SurefireResults

SIZE_FRACTIONS = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
MIN_GROUP = 10          # both detecting and non-detecting subsets needed at a size
MIN_KILLABLE = 3        # an operator needs this many killable mutants in a pair to be scored

# Operator groups scored besides the full mutation score
OPERATOR_GROUPS: Dict[str, set] = {
    "MATH + CONDITIONALS_BOUNDARY (paper's selection)": {"MATH", "CONDITIONALS_BOUNDARY"},
    "REMOVE_CONDITIONALS (all 4 variants)": {
        "REMOVE_CONDITIONALS_EQUAL_IF", "REMOVE_CONDITIONALS_EQUAL_ELSE",
        "REMOVE_CONDITIONALS_ORDER_IF", "REMOVE_CONDITIONALS_ORDER_ELSE",
    },
    "RETURNS (5 return-value mutators)": {
        "EMPTY_RETURNS", "FALSE_RETURNS", "TRUE_RETURNS", "NULL_RETURNS", "PRIMITIVE_RETURNS",
    },
}


def load_pair(raw_dir: Path, bug_id: str) -> Dict[str, Any]:
    """Loads the measured data of one bug pair from its raw archive."""
    pair_dir = raw_dir / bug_id
    aug = SurefireResults.from_files(sorted((pair_dir / "augmented" / "surefire").glob("TEST-*.xml")))
    base = SurefireResults.from_files(sorted((pair_dir / "base" / "surefire").glob("TEST-*.xml")))
    bug = SurefireResults.from_files(sorted((pair_dir / "v_bug" / "surefire").glob("TEST-*.xml")))
    pool = sorted(aug.keys())
    report = PitMutationReport(pair_dir / "augmented" / "mutations.xml.gz")
    return {
        "pool": pool,
        "added": sorted(set(pool) - base.keys()),
        "fault_revealing": sorted(bug.keys(("failed", "error")) & set(pool)),
        "matrix": KillMatrix.from_report(report, pool),
        "pit_killed_aug": report.summary()["killed"],
    }


def subset_sizes(n_tests: int) -> List[int]:
    return sorted({max(1, round(f * n_tests)) for f in SIZE_FRACTIONS} - {n_tests})


def analyze_pair(bug_id: str, pair: Dict[str, Any], n_subsets: int, rng: np.random.Generator):
    km: KillMatrix = pair["matrix"]
    n = len(km.tests)
    fr_mask = km.mask(pair["fault_revealing"])
    groups = {name: km.operator_rows(ops) for name, ops in OPERATOR_GROUPS.items()}
    groups.update({op: km.operator_rows({op}) for op in sorted(set(km.operators))})
    killable = km.kills.any(axis=1)

    size_rows, op_rows = [], []
    for k in subset_sizes(n):
        subsets = random_subsets(n, k, n_subsets, rng)
        detects = (subsets & fr_mask).any(axis=1)
        ms = km.scores(subsets)
        cov = km.scores(subsets, matrix="covers")
        evaluable = detects.sum() >= MIN_GROUP and (~detects).sum() >= MIN_GROUP
        size_rows.append({
            "bug_id": bug_id, "k": k, "fraction": round(k / n, 3), "n_tests": n, "subsets": n_subsets,
            "detecting": int(detects.sum()), "evaluable": int(evaluable),
            "ms_detecting": float(ms[detects].mean()) if detects.any() else np.nan,
            "ms_not": float(ms[~detects].mean()) if (~detects).any() else np.nan,
            "a12_ms": a12(ms[detects], ms[~detects]) if evaluable else np.nan,
            "cov_detecting": float(cov[detects].mean()) if detects.any() else np.nan,
            "cov_not": float(cov[~detects].mean()) if (~detects).any() else np.nan,
            "a12_cov": a12(cov[detects], cov[~detects]) if evaluable else np.nan,
        })
        if not evaluable:
            continue
        for name, rows in groups.items():
            if (rows & killable).sum() < MIN_KILLABLE:
                continue
            s = km.scores(subsets, rows=rows)
            op_rows.append({
                "bug_id": bug_id, "k": k, "group": name,
                "mutants": int(rows.sum()), "killable": int((rows & killable).sum()),
                "share": float(rows.sum() / len(km.operators)),
                "a12": a12(s[detects], s[~detects]),
            })
    return size_rows, op_rows


def sanity_row(bug_id: str, pair: Dict[str, Any], runs: pd.DataFrame) -> Dict[str, Any]:
    km: KillMatrix = pair["matrix"]
    base_mask = ~km.mask(pair["added"])
    base_run = runs[(runs["bug_id"] == bug_id) & (runs["suite_type"] == "base")].iloc[0]
    return {
        "bug_id": bug_id,
        "tests": len(km.tests),
        "added": len(pair["added"]),
        "fault_revealing": len(pair["fault_revealing"]),
        "mutants_used": len(km.operators),
        "left_out": km.unattributed,
        "pit_killed_aug": pair["pit_killed_aug"],
        "matrix_killed_aug": int(km.kills.any(axis=1).sum()),
        "pit_killed_base": int(base_run["killed"]),
        "matrix_killed_base": int(km.kills[:, base_mask].any(axis=1).sum()),
    }


def fmt(x: Optional[float], digits: int = 2) -> str:
    return "—" if x is None or pd.isna(x) else f"{x:.{digits}f}"


def build_report(sanity: pd.DataFrame, sizes: pd.DataFrame, ops: pd.DataFrame, n_subsets: int, seed: int) -> str:
    out: List[str] = []
    out.append("# Equal-size test-subset analysis\n")
    out.append(f"Generated by `scripts/subset_analysis.py` from `data/v2/runs.csv` and `data/raw/` "
               f"({n_subsets} random subsets per size, seed {seed}).\n")
    out.append("**How to read A12:** for subsets of the same size, A12 is the chance that a random subset that "
               "catches the bug scores higher than a random subset that does not. 0.5 means the score tells "
               "nothing beyond size; Vargha-Delaney thresholds are 0.56 small, 0.64 medium, 0.71 large.\n")

    out.append("## 1. Sanity check: the kill matrix reproduces PIT\n")
    out.append("Killed counts from PIT's own runs vs. counts recomputed from the kill matrix. T_aug must match exactly. "
               "T_base comes from a separate PIT run, so a mutant that timed out in one run and was killed in the other "
               "can make it differ by a few mutants. 'Left out' = detected mutants PIT reports without a test (timeouts, memory errors).\n")
    out.append("| Pair | Tests | Added | Fault-revealing | Mutants used | Left out | Killed T_aug PIT / matrix | Killed T_base PIT / matrix |")
    out.append("|---|---|---|---|---|---|---|---|")
    for r in sanity.itertuples():
        out.append(f"| `{r.bug_id}` | {r.tests} | {r.added} | {r.fault_revealing} | {r.mutants_used} | {r.left_out} | "
                   f"{r.pit_killed_aug} / {r.matrix_killed_aug} | {r.pit_killed_base} / {r.matrix_killed_base} |")

    out.append("\n## 2. RQ1: does mutation score rank bug-detecting suites higher at equal size?\n")
    out.append("Median A12 over the evaluable subset sizes of each pair (sizes where both groups have at least "
               f"{MIN_GROUP} subsets). Coverage is the baseline.\n")
    out.append("| Pair | Sizes evaluated | A12 mutation score | A12 coverage | MS detecting vs. not (at ~50% size) |")
    out.append("|---|---|---|---|---|")
    ev = sizes[sizes["evaluable"] == 1]
    per_pair = []
    for bug_id, g in sizes.groupby("bug_id", sort=False):
        e = g[g["evaluable"] == 1]
        mid = g.iloc[(g["fraction"] - 0.5).abs().argsort().iloc[0]]
        med_ms = e["a12_ms"].median() if not e.empty else np.nan
        med_cov = e["a12_cov"].median() if not e.empty else np.nan
        per_pair.append((bug_id, med_ms, med_cov))
        out.append(f"| `{bug_id}` | {len(e)} of {len(g)} | {fmt(med_ms)} | {fmt(med_cov)} | "
                   f"{fmt(mid['ms_detecting'])}% vs. {fmt(mid['ms_not'])}% |")
    pp = pd.DataFrame(per_pair, columns=["bug_id", "ms", "cov"]).dropna()
    if not pp.empty:
        out.append(f"\nAcross {len(pp)} pairs: median A12 mutation score {fmt(pp['ms'].median())} "
                   f"(above 0.5 in {int((pp['ms'] > 0.5).sum())}), median A12 coverage {fmt(pp['cov'].median())} "
                   f"(above 0.5 in {int((pp['cov'] > 0.5).sum())}); mutation score beats coverage in "
                   f"{int((pp['ms'] > pp['cov']).sum())} of {len(pp)} pairs.\n")
        # Unit of analysis = bug pair; two-sided tests
        if len(pp) >= 5:
            p_ms = wilcoxon(pp["ms"] - 0.5, alternative="two-sided").pvalue
            p_cov = wilcoxon(pp["cov"] - 0.5, alternative="two-sided").pvalue
            p_diff = wilcoxon(pp["ms"] - pp["cov"], alternative="two-sided").pvalue
            out.append("Wilcoxon signed-rank tests across pairs (one value per pair, two-sided): "
                       f"A12 mutation score vs. 0.5: p = {p_ms:.3f}; A12 coverage vs. 0.5: p = {p_cov:.3f}; "
                       f"mutation score vs. coverage: p = {p_diff:.3f}.")

    out.append("\n## 3. RQ2: which operators' scores rank bug-detecting suites higher?\n")
    out.append(f"Per pair: median A12 over evaluable sizes; an operator is scored in a pair only if it has at least "
               f"{MIN_KILLABLE} killable mutants there. 'Mutant share' is the operator's share of all mutants "
               "(its real cost if you ran only this operator).\n")
    out.append("| Operator / group | Pairs scored | Mean mutant share | Median A12 | Pairs with A12 > 0.5 |")
    out.append("|---|---|---|---|---|")
    if not ops.empty:
        per = ops.groupby(["group", "bug_id"]).agg(a12=("a12", "median"), share=("share", "first")).reset_index()
        summary = per.groupby("group").agg(
            pairs=("bug_id", "nunique"), share=("share", "mean"), a12=("a12", "median"),
            above=("a12", lambda s: int((s > 0.5).sum())),
        ).sort_values("a12", ascending=False)
        for name, r in summary.iterrows():
            pairs, above = int(r["pairs"]), int(r["above"])
            out.append(f"| {name} | {pairs} | {r['share'] * 100:.1f}% | {fmt(r['a12'])} | {above} of {pairs} |")

    out.append("\n## 4. Limits of this pilot\n")
    out.append("- 10 bug pairs from one project; per-pair A12 values describe how scores rank random subsets, not a population effect.")
    out.append("- The test pool is the changed test class(es) only, as in the PIT runs.")
    out.append("- Mutants detected only by timeout or memory error are left out (see section 1).")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Equal-size test-subset analysis on the kill matrix.")
    parser.add_argument("--runs", default="data/v2/runs.csv", help="runs.csv written by run_experiment.py")
    parser.add_argument("--raw-dir", default="data/raw", help="Raw archive written by run_experiment.py")
    parser.add_argument("--subsets", type=int, default=1000, help="Random subsets per size")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed (results are reproducible)")
    parser.add_argument("--out-dir", default="data/v2", help="Where to write the CSV results")
    parser.add_argument("--report", default="docs/SUBSET_ANALYSIS.md", help="Markdown report path")
    args = parser.parse_args()

    runs = pd.read_csv(args.runs, dtype={"bug_id": str})
    rng = np.random.default_rng(args.seed)
    sanity, sizes, ops = [], [], []
    for bug_id in runs["bug_id"].drop_duplicates():
        pair = load_pair(Path(args.raw_dir), bug_id)
        if not pair["fault_revealing"]:
            print(f"[-] {bug_id}: no test fails on V_bug, skipped")
            continue
        sanity.append(sanity_row(bug_id, pair, runs))
        s, o = analyze_pair(bug_id, pair, args.subsets, rng)
        sizes += s
        ops += o
        print(f"[✓] {bug_id}: {len(pair['pool'])} tests, {len(pair['fault_revealing'])} fault-revealing")

    sanity_df, sizes_df, ops_df = pd.DataFrame(sanity), pd.DataFrame(sizes), pd.DataFrame(ops)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sizes_df.to_csv(out_dir / "subset_analysis.csv", index=False)
    ops_df.to_csv(out_dir / "subset_operators.csv", index=False)
    report = build_report(sanity_df, sizes_df, ops_df, args.subsets, args.seed)
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    print(f"[✓] Report saved -> {args.report}; CSVs -> {out_dir}/subset_analysis.csv, subset_operators.csv")


if __name__ == "__main__":
    main()
