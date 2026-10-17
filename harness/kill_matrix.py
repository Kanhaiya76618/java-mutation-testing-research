"""
harness/kill_matrix.py

A kill matrix records, for every mutant, which tests kill it and which tests run it
without killing it (PIT fullMutationMatrix=true). With it, scores of any subset S of
the test suite can be computed without re-running PIT:

    mutation score  MS(S)  = share of mutants with at least one killing test in S
    coverage        COV(S) = share of mutants with at least one covering test in S
                             (covering = killing or succeeding)

Mutants that PIT counts as detected without naming a test (TIMED_OUT, MEMORY_ERROR,
RUN_ERROR) cannot be attributed to any subset, so they are left out and counted
separately in `unattributed`.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import numpy as np
from scipy.stats import rankdata

from harness.pit_parser import PitMutationReport, key_from_test_name
from harness.surefire_parser import SurefireResults


@dataclass
class KillMatrix:
    tests: List[str]            # test identifiers ('Class#method'), one column each
    operators: List[str]        # operator of each mutant, one row each
    kills: np.ndarray           # bool, shape (mutants, tests)
    covers: np.ndarray          # bool, shape (mutants, tests); kills implies covers
    unattributed: int = 0       # detected mutants without any named test (left out)

    @classmethod
    def from_lists(cls, tests: Sequence[str], killers: Sequence[Iterable[str]],
                   covering: Sequence[Iterable[str]], operators: Sequence[str], unattributed: int = 0) -> "KillMatrix":
        index = {t: i for i, t in enumerate(tests)}
        kills = np.zeros((len(killers), len(tests)), dtype=bool)
        covers = np.zeros_like(kills)
        for row, (k, c) in enumerate(zip(killers, covering)):
            for t in k:
                kills[row, index[t]] = True
                covers[row, index[t]] = True
            for t in c:
                covers[row, index[t]] = True
        return cls(list(tests), list(operators), kills, covers, unattributed)

    @classmethod
    def from_report(cls, report: PitMutationReport, pool: Sequence[str]) -> "KillMatrix":
        """Builds the matrix for a test pool (normally every test method of T_aug, from Surefire).

        Tests named in the report but missing from the pool raise an error: the pool and
        the report must describe the same suite.
        """
        if not report.has_full_matrix:
            raise ValueError("report has no full mutation matrix (run PIT with fullMutationMatrix=true)")
        pool_set = set(pool)
        killers, covering, operators = [], [], []
        unattributed = 0
        for m in report.mutations:
            k = {key_from_test_name(t) for t in m["killing_tests"]}
            s = {key_from_test_name(t) for t in (m["succeeding_tests"] or [])}
            if m["detected"] and not k:
                unattributed += 1
                continue
            unknown = (k | s) - pool_set
            if unknown:
                raise ValueError(f"tests in the PIT report are not in the pool: {sorted(unknown)[:3]}")
            killers.append(k)
            covering.append(s)
            operators.append(m["operator"])
        return cls.from_lists(pool, killers, covering, operators, unattributed)

    def mask(self, tests: Iterable[str]) -> np.ndarray:
        """Boolean column mask for a set of test identifiers."""
        wanted = set(tests)
        return np.array([t in wanted for t in self.tests], dtype=bool)

    def scores(self, subsets: np.ndarray, rows: Optional[np.ndarray] = None, matrix: str = "kills") -> np.ndarray:
        """Percentage of mutants (optionally only `rows`) hit by each subset.

        `subsets` is a bool array (n_subsets, n_tests). matrix='kills' gives the mutation score,
        matrix='covers' the coverage score.
        """
        m = self.kills if matrix == "kills" else self.covers
        if rows is not None:
            m = m[rows]
        if m.shape[0] == 0:
            return np.full(subsets.shape[0], np.nan)
        hit = (m.astype(np.int32) @ subsets.T.astype(np.int32)) > 0     # (mutants, n_subsets)
        return hit.mean(axis=0) * 100.0

    def operator_rows(self, operators: Set[str]) -> np.ndarray:
        return np.array([op in operators for op in self.operators], dtype=bool)


def random_subsets(n_tests: int, size: int, count: int, rng: np.random.Generator) -> np.ndarray:
    """`count` random subsets of exactly `size` tests each, as a bool array (count, n_tests)."""
    order = np.argsort(rng.random((count, n_tests)), axis=1)[:, :size]
    subsets = np.zeros((count, n_tests), dtype=bool)
    np.put_along_axis(subsets, order, True, axis=1)
    return subsets


def a12(positive: np.ndarray, negative: np.ndarray) -> Optional[float]:
    """Vargha-Delaney A12: chance that a random `positive` value beats a random `negative` one (ties count half)."""
    m, n = len(positive), len(negative)
    if m == 0 or n == 0:
        return None
    ranks = rankdata(np.concatenate([positive, negative]))
    return float((ranks[:m].sum() / m - (m + 1) / 2.0) / n)


def load_pair(pair_dir: Path) -> Dict[str, Any]:
    """Loads the measured data of one bug pair from its raw archive (data/raw/<bug_id>/).

    pool            every test method of T_aug ('Class#method'), from Surefire
    added           tests in T_aug but not in T_base
    fault_revealing tests of the pool that fail on the buggy version V_bug
    matrix          the kill matrix of T_aug
    """
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
