# Paper Draft: Empirical Study Design & Methodology (§3)

*Working draft for short paper submission (ICSE NIER / ISSTA Workshop).*

---

## 3. Empirical Study Design

To investigate whether proxy mutation score improvements translate into real regression fault detection, we design a controlled empirical experiment evaluating real-world bug-fixing commits in Java production systems.

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

### 3.1 Subject Mining & Selection Protocol
We mine historical bug-fixing commits from active Java ecosystems (e.g., Apache Commons Lang). A commit is selected as a candidate bug fix if and only if it satisfies four inclusion criteria:
1. **Keyword-anchored issue resolution:** The commit message matches regular expressions for bug resolution (`fix`, `bug`, `issue`, `defect`, `patch`).
2. **Dual modification scope:** The commit concurrently modifies production source files (`src/main/java`) and unit test files (`src/test/java`).
3. **Atomic change containment:** Total files modified $\le 10$ to exclude large architectural refactorings and dependency bumps.
4. **Reproducible Regression Assertion:** The added test methods fail on the pre-fix state ($V_{bug}$) and pass on the fixed state ($V_{fix}$).

### 3.2 Method-Level Test Isolation
A critical methodological constraint identified by recent work (Zhao et al., ISSTA 2026) is that mutation analysis requires a completely green test suite. Directly executing PIT on buggy code causes false mutant kills or premature abortion. Furthermore, simply checking out the pre-fix test file can introduce compilation incompatibilities against the fixed production API.

To resolve this, we implement **Method-Level Test Annotation Isolation**:
* For the **Base Test Suite ($T_{base}$)**: We parse the post-fix test suite and comment out the test annotations (`/* @Test */`, `/* @ParameterizedTest */`) corresponding to the newly added regression test methods. The remaining suite compiles cleanly and executes 100% green against $V_{fix}$, yielding the baseline mutation score:
  $$MS_{base} = \frac{\text{Mutants Killed by } T_{base}}{\text{Total Valid Mutants}} \times 100$$
* For the **Augmented Test Suite ($T_{aug}$)**: Test annotations are restored, recompiling the entire test suite including the bug-detecting tests, yielding:
  $$MS_{aug} = \frac{\text{Mutants Killed by } T_{aug}}{\text{Total Valid Mutants}} \times 100$$
* The differential mutation gain is computed as:
  $$\Delta MS = MS_{aug} - MS_{base}$$

### 3.3 Mutation Testing Configuration
Bytecode mutation testing is conducted using **PITest (PIT) v1.16.0** executed on **OpenJDK 21 (LTS)**. We evaluate the `STRONGER` mutator group comprising 14 operator classes:
* *Conditional Operators:* `CONDITIONALS_BOUNDARY`, `NEGATE_CONDITIONALS`, `REMOVE_CONDITIONALS_EQUAL_IF/ELSE`, `REMOVE_CONDITIONALS_ORDER_IF/ELSE`.
* *Arithmetic & Value Operators:* `MATH`, `INCREMENTS`, `INVERT_NEGS`.
* *Return & Call Operators:* `VOID_METHOD_CALLS`, `NULL_RETURNS`, `PRIMITIVE_RETURNS`, `BOOLEAN_TRUE/FALSE_RETURNS`, `EMPTY_OBJECT_RETURNS`.

### 3.4 Statistical Procedures
To avoid spurious correlation inflated by test suite expansion, we employ non-parametric rank statistics:
1. **Controlled Partial Rank Correlation ($r_{xy \cdot z}$):** Measures the correlation between mutation score gain ($x$) and real-fault detection ($y$) while controlling for test-suite size ($z$):
   $$r_{xy \cdot z} = \frac{r_{xy} - r_{xz} r_{yz}}{\sqrt{(1 - r_{xz}^2)(1 - r_{yz}^2)}}$$
2. **Vargha-Delaney Effect Size ($\hat{A}_{12}$):** Quantifies the probability that an augmented suite detecting a real bug achieves a higher mutation score than an undetected suite.
3. **Cliff’s Delta ($\delta$):** Assesses non-parametric dominance in $[-1, +1]$.
