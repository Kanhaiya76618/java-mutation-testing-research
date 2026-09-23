# Research Questions & Statistical Formulation

## RQ1: Predictive Power of Mutation Score Gains
> *Across historical bug-fix commits, does the increase in mutation score ($\Delta MS = MS_{aug} - MS_{base}$) correlate with whether the augmented test suite detects the regression bug?*

- **Hypothesis $H_0$:** There is no statistically significant correlation between $\Delta MS$ and real-fault detection ($p \ge 0.05$) when controlling for test-suite size.
- **Statistical Tests:**
  - Non-parametric: Spearman's rank correlation ($\rho$) and Kendall's $\tau$.
  - Partial correlation controlling for suite size ($\Delta \text{TestCount}$).
  - Logistic regression: $\text{logit}(P(\text{Detected})) = \beta_0 + \beta_1 \Delta MS + \beta_2 \Delta Cov + \beta_3 \Delta \text{Size}$.
  - Effect size: Vargha-Delaney $\hat{A}_{12}$ and Cliff's $\delta$.

---

## RQ2: Dissecting Mutator Operator Efficacy
> *Which PIT mutator groups (`CONDITIONALS_BOUNDARY`, `NEGATE_CONDITIONALS`, `MATH`, `VOID_METHOD_CALLS`, `INVERT_NEGS`) yield the highest predictive signal-to-cost ratio for regression faults?*

- **Metric:** Fault-to-Mutant Efficiency:
  $$\text{Efficiency}(M_k) = \frac{\text{Killed Mutants in } M_k \text{ by Fault-Detecting Tests}}{\text{Total Mutants in } M_k \times \text{Execution Time}}$$
- **Outcome:** Identifying mutator subsets that provide $\ge 85\%$ fault-detection prediction with $\le 40\%$ execution overhead.

---

## RQ3: Architectural & Project-Specific Generalizability
> *How consistent are the mutation-score-to-fault-detection relationships between classical algorithmic libraries (Defects4J: Commons-Lang/Math) and complex modern event/GUI/network-driven systems (JabRef / Jenkins)?*

- **Comparison:**
  - Benchmark vs. In-the-wild OSS commits.
  - Unit tests vs. integration tests.
