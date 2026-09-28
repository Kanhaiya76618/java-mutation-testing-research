# Empirical Evaluation Results: Mutation Score vs. Fault Detection

**Dataset Summary:** 18 total experiment records.

- Real Fault Detected: 9 trials
- Real Fault Not Detected: 9 trials

## RQ1: Predictive Power of Mutation Score Gains
| Metric | Value | p-value | Interpretation |
|---|---|---|---|
| **Spearman Rank ($\rho$)** | 0.321 | 0.1934 | Not Significant |
| **Kendall Tau ($\tau$)** | 0.270 | 0.1851 | Rank concordant association |
| **Partial Correlation ($r_{xy \cdot z}$)** | 0.324 | 0.2039 | Controlled for Test-Suite Size |
| **Vargha-Delaney ($\hat{A}_{12}$)** | 0.685 | — | Medium effect |
| **Cliff's Delta ($\delta$)** | 0.370 | — | Non-parametric dominance |

## RQ2: Mutator Operator Efficiency Breakdown
| Mutator Operator | Mean Score (Detected) | Mean Score (Undetected) | Predictive Signal |
|---|---|---|---|
| **Conditionals Boundary** | 49.63% | 47.78% | Moderate |
| **Negate Conditionals** | 8.93% | 8.93% | Neutral/Low |
| **Math / Arithmetic** | 59.51% | 47.70% | Strong ($\Delta > +10\%$) |
| **Void Method Calls** | 60.56% | 60.56% | Neutral/Low |
| **Invert Negatives** | 16.67% | 16.67% | Neutral/Low |