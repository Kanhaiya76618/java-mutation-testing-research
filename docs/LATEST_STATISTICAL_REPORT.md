# Empirical Evaluation Results: Mutation Score vs. Fault Detection

**Dataset Summary:** 14 total experiment records.

- Real Fault Detected: 7 trials
- Real Fault Not Detected: 7 trials

## RQ1: Predictive Power of Mutation Score Gains
| Metric | Value | p-value | Interpretation |
|---|---|---|---|
| **Spearman Rank ($\rho$)** | 0.284 | 0.3254 | Not Significant |
| **Kendall Tau ($\tau$)** | 0.241 | 0.3062 | Rank concordant association |
| **Partial Correlation ($r_{xy \cdot z}$)** | 0.285 | 0.3447 | Controlled for Test-Suite Size |
| **Vargha-Delaney ($\hat{A}_{12}$)** | 0.663 | — | Medium effect |
| **Cliff's Delta ($\delta$)** | 0.327 | — | Non-parametric dominance |

## RQ2: Mutator Operator Efficiency Breakdown
| Mutator Operator | Mean Score (Detected) | Mean Score (Undetected) | Predictive Signal |
|---|---|---|---|
| **Conditionals Boundary** | 63.13% | 60.75% | Moderate |
| **Negate Conditionals** | 11.48% | 11.48% | Neutral/Low |
| **Math / Arithmetic** | 75.37% | 60.64% | Strong ($\Delta > +10\%$) |
| **Void Method Calls** | 77.86% | 77.86% | Neutral/Low |
| **Invert Negatives** | 21.43% | 21.43% | Neutral/Low |