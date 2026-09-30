# Empirical Evaluation Results: Mutation Score vs. Real-Fault Detection

**Dataset Summary:** 18 total records across 9 distinct bug fixes in Apache Commons Lang.

## Matched Paired Analysis (Within-Subject Unit of Inference: 9 Bug Pairs)

- Total Matched Pairs: 9
- Positive Score Gains ($MS_{aug} > MS_{base}$): **8 of 9** (88.9%)
- Neutral Differences ($MS_{aug} == MS_{base}$): 1 of 9
- Negative Differences ($MS_{aug} < MS_{base}$): **0 of 9** (0.0%)
- Mean Within-Pair Gain ($\overline{\Delta MS}$): **+5.55%** (Median: +0.73%)
- **Wilcoxon Signed-Rank Test:** $W = 36.0, p = 0.0039$ (Statistically significant)
- **Paired Sign Test:** $p = 0.0039$

## RQ1: Distribution Metrics & Rank Correlation (Unpaired Perspective: 81 Pair Combinations)

| Metric | Value | p-value | Exact Interpretation |
|---|---|---|---|
| **Mann-Whitney U** | 55.5 (81 comparisons) | 0.2002 | Unpaired rank sum comparison |
| **Vargha-Delaney ($\hat{A}_{12}$)** | 0.685 [95% CI: 0.43, 0.94] | — | Medium effect; CI spans 0.5 (pilot sample) |
| **Cliff's Delta ($\delta$)** | 0.370 | — | Identically $2\hat{A}_{12} - 1$ |
| **Spearman Rank ($\rho$)** | 0.321 | 0.1934 | Moderate rank correlation |
| **Kendall Tau ($\tau$)** | 0.270 | 0.1851 | Concordant with Mann-Whitney U |
| **Partial Correlation ($r_{xy \cdot z}$)** | 0.324 | 0.2039 | Controlled for test count |

*Note on sample power:* The 95% CI around $\hat{A}_{12}$ spans $[0.43, 0.94]$ across the 81 cross-bug pairings due to cross-class baseline variance. Confirmatory claims at $\alpha = 0.05$ with 80% power require $N \approx 77$–$134$ records (Noether's approximation).

## RQ2: Mutator Operator Efficiency Breakdown

| Mutator Operator | Mean Score (Detected) | Mean Score (Undetected) | Differential ($\Delta$) | Signal Stability (LOBO Positive Freq) |
|---|---|---|---|---|
| **Conditionals Boundary** | 49.63% | 47.78% | **+1.85%** | 8/9 (89%) |
| **Negate Conditionals** | 8.93% | 8.93% | **+0.00%** | 0/9 (0%) |
| **Math / Arithmetic** | 59.51% | 47.70% | **+11.81%** | 9/9 (100%) |
| **Void Method Calls** | 60.56% | 60.56% | **+0.00%** | 0/9 (0%) |
| **Invert Negatives** | 16.67% | 16.67% | **+0.00%** | 0/9 (0%) |