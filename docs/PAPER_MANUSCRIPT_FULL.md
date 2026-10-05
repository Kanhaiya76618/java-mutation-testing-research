# Which Mutation Operators Track Real-Fault Detection? A Method-Level Isolation Protocol and Pilot Study on Apache Commons Lang

**Author:** Kanhaiya Mehta  
**Target Venues:** IEEE/ACM Software Engineering Conferences (ICSE NIER / AST / ICST 2027)  
**Replication Package:** [https://github.com/Kanhaiya76618/java-mutation-testing-research](https://github.com/Kanhaiya76618/java-mutation-testing-research)

---

## Abstract

Mutation testing is widely regarded as the gold standard for assessing test suite adequacy. However, empirical debates persist regarding whether mutation score gains reliably predict real regression fault detection once test-suite size is accounted for, and which specific operators provide actionable defect-revealing signals. In this paper, we introduce **Method-Level Test Annotation Isolation**, an empirical protocol that evaluates pre-fix baseline suites and bug-detecting augmented suites under identical, 100% green production bytecode without classpath incompatibilities or assertion contamination. We evaluate this protocol in an empirical pilot study across 9 historical regression bug-fixing pairs (18 experimental records) in Apache Commons Lang using PITest v1.16 on OpenJDK 21.

Our pilot findings demonstrate:
1. **Within-Subject Predictive Power:** In matched-pair analysis, augmented suites exhibit strictly higher mutation scores than baseline suites in **8 of 9 bug fixes** (mean gain $\overline{\Delta MS} = +5.55\%$, Wilcoxon signed-rank $W = 36.0, p = 0.0039$), while unpaired cross-bug comparisons yield $\hat{A}_{12} = 0.685$ [95% CI: $0.43, 0.94$] ($U = 55.5, p = 0.20$).
2. **Operator Discriminatory Power:** Mutator operators differ markedly in diagnostic sensitivity: `MATH` (+11.81% differential kill rate, 100% positive Leave-One-Bug-Out folds) and `CONDITIONALS_BOUNDARY` (+1.85%, 89% positive folds) provide robust discriminatory signals, whereas `VOID_METHOD_CALLS` is saturated by baseline smoke tests.
3. **Actionable CI/CD Subsetting:** Selective operator pruning reduces total mutant evaluation volume by **63.4%** while retaining **91.2%** of fault-revealing score gains. We formalize sample-size power requirements ($N \approx 77$–$134$) for confirmatory multi-project scale-up.

---

## 1. Introduction

Software testing research has long sought objective, automated criteria to determine whether a test suite is adequate. While code coverage metrics remain the ubiquitous industrial standard, empirical studies have established that high coverage is an insufficient condition for defect detection (Inozemtseva & Holmes, ICSE 2014). Mutation testing addresses this limitation by systematically injecting syntactic faults (mutants) into source code or bytecode, evaluating whether test suites detect and kill them (Coles et al., ISSTA 2016).

While foundational studies demonstrated that mutants are coupled to real faults (Just et al., FSE 2014), recent empirical investigations and industrial experiences have raised critical caveats:
1. **Test Suite Size Confounding:** Papadakis et al. (ICSE 2018) demonstrated that reported correlations between mutation score and real-fault detection are often driven by test-suite size ($SLOC_{test}$), weakening once size is controlled.
2. **Targeted vs. Combinatorial Mutation:** Industrial reports from Meta's Automated Code Health tool ACH (Foster et al., FSE 2025) show that modern practice favors small, targeted mutant subsets tailored to specific health concerns rather than exhaustive combinatorial mutation.
3. **Methodological Baseline Contamination:** Directly executing mutation tools on buggy revisions ($V_{bug}$) aborts pre-scans or yields false mutant kills due to pre-existing assertion failures, while rolling back full test files introduces compilation incompatibilities against updated production APIs (Zhao et al., ISSTA 2026).

To overcome these methodological challenges, this paper introduces **Method-Level Test Annotation Isolation**, an automated protocol that evaluates base and augmented test suites against identical, 100% green production bytecode, and reports an empirical pilot study on Apache Commons Lang.

---

## 2. Empirical Methodology

```
          +---------------------------------------------------------+
          |           Historical Bug-Fix Commit (V_bug, V_fix)      |
          +---------------------------------------------------------+
                                       |
              +------------------------+------------------------+
              |                                                 |
     [Pre-Fix State: V_bug]                           [Post-Fix State: V_fix]
              |                                                 |
   Verify Fault Detection:                             Evaluate Mutation Score:
   Apply added tests T_aug.                             (Must run on 100% green suite)
   Does T_aug fail on V_bug?                                    |
   -> Record Fault Detected (0 or 1).          +----------------+---------------+
                                               |                                |
                                     [Base Suite: T_base]            [Augmented Suite: T_aug]
                                      (Added tests masked)            (Full test suite)
                                               |                                |
                                          Run PITest                       Run PITest
                                               |                                |
                                         MS_base (%)                       MS_aug (%)
                                               +----------------+---------------+
                                                                |
                                                      Compute Delta MS (%)
```

### 2.1 Subject Mining & Selection Protocol
We mine historical bug-fixing commits from Apache Commons Lang satisfying four inclusion criteria:
1. Keyword-anchored issue resolution regex (`fix`, `bug`, `issue`, `defect`, `patch`).
2. Concurrent dual modifications to production code (`src/main/java`) and unit test code (`src/test/java`).
3. Atomic change containment ($\le 10$ files modified) to isolate unit regression logic.
4. Reproducible failure: added test methods fail deterministically on $V_{bug}$ and pass on $V_{fix}$.

### 2.2 Method-Level Test Annotation Isolation
To guarantee that PITest executes on a 100% green baseline without classpath contamination:
- **Base Suite ($T_{base}$):** We parse the post-fix test suite and comment out JUnit annotations (`/* @Test */`, `/* @ParameterizedTest */`) on newly added regression test methods. The remaining suite compiles cleanly and runs green on $V_{fix}$, producing $MS_{base}$.
- **Augmented Suite ($T_{aug}$):** Annotations are restored and recompiled, executing the complete suite against $V_{fix}$ to produce $MS_{aug}$.
- **Differential Gain:** $\Delta MS = MS_{aug} - MS_{base}$.

### 2.3 Mutation Setup
Bytecode mutation testing is conducted using PITest v1.16.0 under OpenJDK 21 LTS with the `STRONGER` operator group (14 operator classes).

---

## 3. Empirical Results & Discussion

### 3.1 RQ1: Predictive Power of Mutation Score Gains

Our pilot dataset contains 9 matched bug pairs (18 records total).

#### Within-Subject Matched Paired Analysis
| Metric | Observed Value |
|---|---|
| Total Matched Bug Pairs | 9 |
| Positive Score Gains ($MS_{aug} > MS_{base}$) | **8 of 9** (88.9%) |
| Neutral Differences ($MS_{aug} == MS_{base}$) | 1 of 9 (11.1%) |
| Negative Differences ($MS_{aug} < MS_{base}$) | **0 of 9** (0.0%) |
| Mean Within-Pair Gain ($\overline{\Delta MS}$) | **+5.55%** (Median: +0.73%) |
| **Wilcoxon Signed-Rank Test** | $W = 36.0, \mathbf{p = 0.0039}$ |
| **Paired Sign Test** | $\mathbf{p = 0.0039}$ |

In 8 of the 9 bug fixes, adding the test method that catches the regression bug strictly increased the mutation score. The Wilcoxon signed-rank test confirms statistical significance ($W = 36.0, p = 0.0039$).

#### Unpaired Cross-Bug Distribution Comparison (81 Pairwise Comparisons)
| Metric | Value | p-value | Exact Interpretation |
|---|---|---|---|
| **Mann-Whitney $U$** | 55.5 | 0.2002 | Unpaired rank sum comparison |
| **Vargha-Delaney ($\hat{A}_{12}$)** | **0.685** | — | Medium effect [95% CI: 0.43, 0.94] |
| **Cliff’s Delta ($\delta$)** | **0.370** | — | Identically $2\hat{A}_{12} - 1$ |
| **Spearman Rank ($\rho$)** | **0.321** | 0.1934 | Moderate rank correlation |
| **Kendall’s Tau ($\tau$)** | **0.270** | 0.1851 | Concordant with Mann-Whitney $U$ |
| **Partial Correlation ($r_{xy \cdot z}$)** | **0.324** | 0.2039 | Controlled for test count |

The point estimate $\hat{A}_{12} = 0.685$ indicates a medium effect size favoring fault-detecting suites. However, its Hanley-McNeil 95% confidence interval spans $[0.43, 0.94]$, illustrating that cross-class baseline variance requires matched pairing.

### 3.2 RQ2: Mutator Operator Sensitivity Breakdown & LOBO Cross-Validation

To prevent circular evaluation, we performed Leave-One-Bug-Out (LOBO) cross-validation across the 9 bug fixes.

| Operator Category | Mean Score ($FD=1$) | Mean Score ($FD=0$) | Differential ($\Delta$) | LOBO Fold Stability |
|---|---|---|---|---|
| **Math / Arithmetic (`MATH`)** | **59.51%** | **47.70%** | **+11.81%** | **9/9 (100%)** |
| **Conditionals Boundary (`CONDITIONALS_BOUNDARY`)** | **49.63%** | **47.78%** | **+1.85%** | **8/9 (89%)** |
| **Negate Conditionals (`NEGATE_CONDITIONALS`)** | 8.93% | 8.93% | +0.00% | 0/9 (0%) |
| **Void Method Calls (`VOID_METHOD_CALLS`)** | 60.56% | 60.56% | +0.00% | 0/9 (0%) |
| **Invert Negatives (`INVERT_NEGS`)** | 16.67% | 16.67% | +0.00% | 0/9 (0%) |

`MATH` operators demonstrated the strongest discriminatory power (+11.81% higher kill rate for fault-detecting suites, 100% LOBO folds). Boundary mutators remained positive in 89% of folds. In contrast, `VOID_METHOD_CALLS` was saturated at 60.56% across both base and augmented suites.

### 3.3 RQ3: Cost vs. Detection Trade-offs and Baseline Comparison

Evaluating all 2,187 mutants in large classes (e.g., `StringUtils`) required over 2.2 minutes per evaluation. We benchmark selective operator pruning against uniform random sampling and standard PITest `DEFAULTS`:

| Reduction Policy | Mutant Budget | Mean $\overline{\Delta MS}$ | Sensitivity Retained (LOBO) |
|---|---|---|---|
| **Full Suite (`STRONGER`)** | 100.0% | +5.55% | 100.0% (Baseline) |
| **Selective (`MATH` + `BOUNDARY`)** | **36.6%** | **+6.83%** | **92.4%** |
| **Random Sampling ($N=1000$)** | 36.6% | +5.58% | 90.1% |
| **PITest `DEFAULTS`** | 68.2% | +0.62% | 46.2% |

Pruning mutators to `MATH` + `CONDITIONALS_BOUNDARY`:
- **63.4% reduction in total mutant generation.**
- **65.8% reduction in execution latency** (from 132s to under 45s).
- **92.4% retention of cross-validated sensitivity in Leave-One-Bug-Out evaluation.**
- While random sampling provides strong theoretical guarantees (Gopinath et al., ICSE 2016), selective mutation guarantees deterministic, reproducible CI execution and substantially outperforms standard PITest `DEFAULTS`.

---

## 4. Threats to Validity & Power Analysis

### 4.1 Sample Size & Power Analysis
While our pilot ($N=18$ records, 9 matched pairs) yields statistically significant within-pair results ($p = 0.0039$), confirmatory unpaired population-level claims require larger samples. Applying Noether's sample size approximation for Mann-Whitney tests ($\alpha = 0.05$ two-sided, 80% power):
$$N \approx \frac{7.85}{3 \cdot (\hat{A}_{12} - 0.5)^2}$$

| Target True Effect ($\hat{A}_{12}$) | Classification | Total Records Needed ($N$) |
|---|---|---|
| **0.685** | Pilot Point Estimate | $\approx 77$ |
| **0.640** | Vargha-Delaney Medium | $\approx 134$ |
| **0.600** | Small-to-Moderate | $\approx 262$ |

Our study provides an initial validated protocol and empirical pilot, establishing the foundation for scale-up across Defects4J 2.0.

### 4.2 Construct, Internal & External Validity
- **Construct Validity:** Controlled for test-suite size via partial rank correlation ($r_{xy \cdot z}$) following Papadakis et al. (ICSE 2018), and avoided baseline contamination via method-level annotation isolation.
- **Internal Validity:** Bytecode execution standardized on OpenJDK 21 LTS with deterministic execution timeout factors ($1.25\times$).
- **External Validity:** Evaluated in Apache Commons Lang. Future work will expand to state-machine, parsing (Commons CSV, Gson), and mock-heavy enterprise architectures.

---

## 5. Conclusion & Artifact Availability

This empirical pilot study demonstrates that bytecode mutation testing provides a statistically significant within-pair predictive signal for real regression fault detection ($W = 36.0, p = 0.0039$), and that `MATH` and `CONDITIONALS_BOUNDARY` operators provide the strongest discriminatory signal. Selective operator pruning reduces execution cost by over 60% while retaining >90% of predictive sensitivity.

All experimental code, datasets, plotting pipelines, and reproduction scripts are available at:
**[https://github.com/Kanhaiya76618/java-mutation-testing-research](https://github.com/Kanhaiya76618/java-mutation-testing-research)**
