#!/usr/bin/env python3
"""
scripts/pitfall_analysis.py

Demonstrates the base-vs-augmented pitfall on the measured data.

1. Naive design (the one the first version of this study used): for each pair,
   dMS = MS(T_aug) - MS(T_base), tested across pairs with a two-sided sign test.
   T_aug is T_base plus the added tests, so every mutant that T_base kills is still
   killed by T_aug: dMS >= 0 for every pair, whatever the added tests are.
2. Placebo: on the kill matrix of T_aug, remove the same number of random tests that do
   NOT reveal the bug (instead of the tests the fix added) and compute the same dMS.
   If the placebo also gives positive dMS and a "significant" sign test, the naive
   design cannot tell bug-revealing tests from any other tests.

Inputs come only from measured data: data/v2/runs.csv and data/raw/<bug_id>/.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import binomtest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.kill_matrix import load_pair, random_subsets
from harness.paper_numbers import write_macros


def sign_test(deltas: np.ndarray) -> float:
    """Two-sided exact sign test on the non-zero differences."""
    pos, neg = int((deltas > 0).sum()), int((deltas < 0).sum())
    return binomtest(pos, pos + neg, 0.5, alternative="two-sided").pvalue if pos + neg > 0 else 1.0


def placebo_deltas(pair: Dict[str, Any], draws: int, rng: np.random.Generator) -> np.ndarray:
    """dMS when |added| random tests that do not reveal the bug are removed instead of the added tests."""
    km = pair["matrix"]
    n_tests = len(km.tests)
    candidates = np.flatnonzero(~km.mask(pair["fault_revealing"]))
    picks = random_subsets(len(candidates), len(pair["added"]), draws, rng)
    subsets = np.ones((draws, n_tests), dtype=bool)
    rows, cols = np.nonzero(picks)
    subsets[rows, candidates[cols]] = False
    full = km.scores(np.ones((1, n_tests), dtype=bool))[0]
    return full - km.scores(subsets)


def short_name(target_classes: str) -> str:
    return target_classes.split(";")[0].rsplit(".", 1)[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Naive base-vs-augmented analysis and its placebo.")
    parser.add_argument("--runs", default="data/v2/runs.csv", help="runs.csv written by run_experiment.py")
    parser.add_argument("--raw-dir", default="data/raw", help="Raw archive written by run_experiment.py")
    parser.add_argument("--draws", type=int, default=1000, help="Placebo draws per pair")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed (results are reproducible)")
    parser.add_argument("--out", default="data/v2/pitfall_analysis.csv", help="Per-pair results CSV")
    parser.add_argument("--report", default="docs/PITFALL_ANALYSIS.md", help="Markdown report path")
    args = parser.parse_args()

    runs = pd.read_csv(args.runs, dtype={"bug_id": str})
    rng = np.random.default_rng(args.seed)
    rows: List[Dict[str, Any]] = []
    placebo_by_pair: List[np.ndarray] = []
    for bug_id in runs["bug_id"].drop_duplicates():
        pair = load_pair(Path(args.raw_dir) / bug_id)
        if not pair["fault_revealing"]:
            continue
        r = runs[runs["bug_id"] == bug_id].set_index("suite_type")
        km = pair["matrix"]
        n_tests = len(km.tests)
        base_mask = ~km.mask(pair["added"])
        real = km.scores(np.ones((1, n_tests), dtype=bool))[0] - km.scores(base_mask[None, :])[0]
        placebo = placebo_deltas(pair, args.draws, rng)
        placebo_by_pair.append(placebo)
        rows.append({
            "bug_id": bug_id,
            "class_name": short_name(r.loc["augmented", "target_classes"]),
            "tests": n_tests,
            "added": len(pair["added"]),
            "fault_revealing": len(pair["fault_revealing"]),
            "delta_pit": float(r.loc["augmented", "mutation_score"] - r.loc["base", "mutation_score"]),
            "delta_matrix": float(real),
            "placebo_median": float(np.median(placebo)),
            "placebo_p05": float(np.percentile(placebo, 5)),
            "placebo_p95": float(np.percentile(placebo, 95)),
            "placebo_positive": float((placebo > 0).mean()),
            "placebo_ge_real": float((placebo >= real).mean()),
        })

    df = pd.DataFrame(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    # Across pairs
    naive_p = sign_test(df["delta_pit"].to_numpy())
    matrix_p = sign_test(df["delta_matrix"].to_numpy())
    replicate_p = np.array([sign_test(col) for col in np.vstack(placebo_by_pair).T])
    sig_share = float((replicate_p < 0.05).mean())
    beats_placebo = int((df["placebo_ge_real"] < 0.05).sum())

    report = []
    report.append("# The base-vs-augmented pitfall: naive analysis vs. placebo\n")
    report.append(f"Generated by `scripts/pitfall_analysis.py` from `data/v2/runs.csv` and `data/raw/` "
                  f"({args.draws} placebo draws per pair, seed {args.seed}).\n")
    report.append("dMS is in percentage points. 'PIT runs' = the two separate PIT runs (timeouts count as detected); "
                  "'matrix' = recomputed from the T_aug kill matrix (killed mutants with a named test).\n")
    report.append("## 1. Naive analysis (T_aug vs. T_base)\n")
    report.append("| Pair | Class | Tests | Added | Fault-revealing | dMS PIT runs | dMS matrix |")
    report.append("|---|---|---|---|---|---|---|")
    for x in df.itertuples():
        report.append(f"| `{x.bug_id}` | {x.class_name} | {x.tests} | {x.added} | {x.fault_revealing} | "
                      f"{x.delta_pit:+.2f} | {x.delta_matrix:+.2f} |")
    report.append(f"\nPositive in {int((df['delta_pit'] > 0).sum())} of {len(df)} pairs, negative in "
                  f"{int((df['delta_pit'] < 0).sum())}; two-sided sign test p = {naive_p:.4f} "
                  f"(matrix: p = {matrix_p:.4f}). A negative dMS is impossible by construction, up to timeout noise.\n")
    report.append("## 2. Placebo: remove the same number of random tests that do not reveal the bug\n")
    report.append("| Pair | Class | Added | dMS matrix (real) | Placebo dMS median [5th, 95th] | Placebo dMS > 0 | P(placebo >= real) |")
    report.append("|---|---|---|---|---|---|---|")
    for x in df.itertuples():
        report.append(f"| `{x.bug_id}` | {x.class_name} | {x.added} | {x.delta_matrix:+.2f} | "
                      f"{x.placebo_median:+.2f} [{x.placebo_p05:+.2f}, {x.placebo_p95:+.2f}] | "
                      f"{x.placebo_positive:.0%} | {x.placebo_ge_real:.3f} |")
    report.append(f"\nIn {sig_share:.1%} of {args.draws} placebo replicates (one draw per pair), the naive two-sided "
                  f"sign test is 'significant' at 0.05 although the removed tests reveal no bug. "
                  f"The real added tests raise MS more than at least 95% of placebo draws in {beats_placebo} of {len(df)} pairs.\n")
    Path(args.report).write_text("\n".join(report) + "\n", encoding="utf-8")

    skipped_path = Path(args.runs).parent / "skipped.csv"
    skipped = len(pd.read_csv(skipped_path)) if skipped_path.exists() else 0
    write_macros("pitfall_numbers.tex", {
        "CandidatesMined": str(len(df) + skipped),
        "CandidatesSkipped": str(skipped),
        "PitfallPairs": str(len(df)),
        "NaivePositivePairs": str(int((df["delta_pit"] > 0).sum())),
        "NaiveNegativePairs": str(int((df["delta_pit"] < 0).sum())),
        "NaiveSignP": f"{naive_p:.3f}",
        "NaiveMedianDelta": f"{df['delta_pit'].median():.2f}",
        "NaiveMinDelta": f"{df['delta_pit'].min():.2f}",
        "NaiveMaxDelta": f"{df['delta_pit'].max():.2f}",
        "PlaceboDraws": f"{args.draws:,}".replace(",", "{,}"),
        "PlaceboSigShare": f"{sig_share * 100:.1f}\\%",
        "PlaceboMedianPValue": f"{np.median(replicate_p):.3f}",
        "RealBeatsPlaceboPairs": str(beats_placebo),
        "TotalTests": str(int(df["tests"].sum())),
        "TotalAdded": str(int(df["added"].sum())),
        "TotalFaultRevealing": str(int(df["fault_revealing"].sum())),
    }, "scripts/pitfall_analysis.py")

    print("\n".join(report))
    print(f"[✓] Report saved -> {args.report}; CSV -> {out}; LaTeX -> paper/generated/pitfall_numbers.tex")


if __name__ == "__main__":
    main()
