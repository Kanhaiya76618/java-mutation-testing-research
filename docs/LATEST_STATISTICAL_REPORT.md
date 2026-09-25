# Empirical Evaluation Results: Mutation Score vs. Fault Detection

**Dataset Summary:** 8 total experiment records.

- Real Fault Detected: 4 trials
- Real Fault Not Detected: 4 trials

## RQ1: Predictive Power of Mutation Score Gains
| Metric | Value | p-value | Interpretation |
|---|---|---|---|
| **Spearman Rank ($\rho$)** | 0.165 | 0.6968 | Not Significant |
| **Kendall Tau ($\tau$)** | 0.144 | 0.6631 | Rank concordant association |
| **Partial Correlation ($r_{xy \cdot z}$)** | 0.170 | 0.7152 | Controlled for Test-Suite Size |
| **Vargha-Delaney ($\hat{A}_{12}$)** | 0.594 | — | Small/Negligible |
| **Cliff's Delta ($\delta$)** | 0.188 | — | Non-parametric dominance |

## RQ2: Mutator Operator Efficiency Breakdown
| Mutator Operator | Mean Score (Detected) | Mean Score (Undetected) | Predictive Signal |
|---|---|---|---|
| **Conditionals Boundary** | 49.81% | 49.81% | Neutral/Low |
| **Negate Conditionals** | 20.09% | 20.09% | Neutral/Low |
| **Math / Arithmetic** | 64.45% | 63.76% | Moderate |
| **Void Method Calls** | 61.25% | 61.25% | Neutral/Low |
| **Invert Negatives** | 37.50% | 37.50% | Neutral/Low |