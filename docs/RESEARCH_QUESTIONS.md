# Research Questions

Revised in October 2026, after the re-measurement (see `DATA_V1_VS_V2.md`). The unit of analysis
is the bug pair; every test is two-sided.

## RQ1: Does the base-vs-augmented design distinguish bug-revealing tests from any other tests?
> Comparing MS(T_aug) with MS(T_base) is a common way to ask whether tests that catch a real bug
> raise the mutation score. Because T_aug is T_base plus tests, the difference can never be negative.

- **Naive analysis:** dMS = MS(T_aug) - MS(T_base) per pair; sign test across pairs.
- **Placebo:** on the kill matrix of T_aug, remove the same number of random tests that do not
  reveal the bug and compute the same dMS (1,000 draws per pair).
- **Outputs:** share of placebo replicates in which the naive sign test is significant; per pair,
  the chance that a placebo removal costs at least as much mutation score as removing the added tests.
- **Script:** `scripts/pitfall_analysis.py` -> `PITFALL_ANALYSIS.md`.

## RQ2: At equal suite size, does mutation score rank bug-detecting suites higher, and more than coverage does?
- Random test subsets of exactly k tests (5% to 90% of the suite), 1,000 per size, scored from
  PIT's kill matrix without re-running PIT.
- **Effect size:** Vargha-Delaney A12 between subsets that contain a fault-revealing test and those
  that do not; per pair, the median over sizes.
- **Baseline:** the same A12 for coverage (share of mutants executed by at least one test of the subset).
- **Script:** `scripts/subset_analysis.py` -> `SUBSET_ANALYSIS.md`.

## RQ3: Which mutation operators carry that signal?
- Same subsets, scored on the mutants of one operator (or a group of operators) at a time.
- Includes the MATH + CONDITIONALS_BOUNDARY selection that the naive analysis singled out.
- An operator is scored in a pair only if it has at least 3 mutants that some test kills.
