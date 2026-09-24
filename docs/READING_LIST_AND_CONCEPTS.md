# Essential Reading List & Study Guide for Java Mutation Testing Research

This guide outlines the foundational papers, theoretical concepts, and statistical methods you need to master to conduct this research and write an empirically rigorous paper.

---

## 1. Core Papers to Read (Priority Ranked)

### Must-Read #1: The Anchor Paper (Read This First)
* **Title:** *Do Coverage and Mutation Scores of LLM-Generated Test Suites Correlate with Their Effectiveness? (Replicability Study)*
* **Authors:** Chenyu Zhao, Yang Zhou, Myra B. Cohen (2026)
* **Venue:** *PACMSE* (ACM International Conference on Software Testing and Analysis / ISSTA 2026 track)
* **Links:** [arXiv:2607.22880](https://arxiv.org/html/2607.22880v1) | [DOI: 10.1145/3832093](https://doi.org/10.1145/3832093)
* **What to focus on:**
  - Section 3: Experimental Methodology on Defects4J.
  - Section 4: How they control for test-suite size using Kendall's $\tau$ and partial correlation.
  - Section 5 & 6: The "Open Problems" section — this is the exact justification for our research questions (RQ1–RQ3).

### Must-Read #2: The Classic Foundations
Before Zhao et al., these two seminal papers shaped the entire software engineering debate:
1. **Inozemtseva & Holmes (ICSE 2014):**
   * *Title:* "Coverage is not strongly correlated with test suite effectiveness."
   * *Key Takeaway:* Showed that when suite size is controlled, code coverage has only a low-to-moderate correlation with fault detection.
2. **Papadakis et al. (IEEE TSE 2018):**
   * *Title:* "Mutation testing versus code coverage in assessing test suite effectiveness: A large-scale empirical comparison."
   * *Key Takeaway:* Showed that mutation score correlates significantly better with real-fault detection than statement or branch coverage.

### Must-Read #3: Industrial Scale Application
* **Title:** *Mutation-Guided LLM-based Test Generation at Meta*
* **Authors:** Nadia Alshahwan et al. (Meta, FSE 2025)
* **Venue:** *ACM International Conference on the Foundations of Software Engineering (FSE 2025)*
* **Link:** [DOI: 10.1145/3696630.3728544](https://dl.acm.org/doi/10.1145/3696630.3728544)
* **What to focus on:**
  - How industrial pipelines use surviving mutants as prompt context to iteratively ask LLMs to generate tests that kill those mutants.

### Must-Read #4: Benchmark Foundation
* **Title:** *Defects4J: A Database of Existing Faults to Enable Controlled Testing Studies for Java*
* **Authors:** René Just, Darioush Jalali, Michael D. Ernst (ISSTA 2014)
* **What to focus on:**
  - How real-world bugs are structured ($V_{bug}$, $V_{fix}$, $T_{trigger}$ vs $T_{dev}$).

---

## 2. Core Concepts You Must Master

### A. The RIPR Model of Software Testing
For a test suite to detect a fault (or kill a mutant), four conditions must be met:
1. **R (Reachability):** The test execution must reach the mutated statement.
2. **I (Infection):** Execution of the mutated statement must produce an incorrect internal program state.
3. **P (Propagation):** The infected state must propagate through variables and method calls until it affects an observable output.
4. **R (Reveal):** The test must contain an assertion that checks the affected output and fails.
* *Why this matters for your paper:* Standard code coverage only measures **Reachability**. Mutation testing forces **Reachability + Infection + Propagation**.

### B. Fundamental Mutation Testing Hypotheses
1. **Competent Programmer Hypothesis (CPH):** Programmers generally write code that is close to correct; faults are typically small syntactic deviations rather than completely broken structures.
2. **Coupling Effect:** Complex faults are strongly coupled to simple faults; a test suite capable of catching all simple syntactic mutants will catch a high percentage of complex real-world bugs.
3. **Equivalent Mutants:** A syntactic mutant that behaves identically to the original program under all inputs. Equivalent mutants cannot be killed and artificially deflate mutation scores (a major threat to construct validity).

### C. Bytecode Mutation Testing (How PIT Works)
* Unlike source-level mutation tools that modify `.java` files and recompile (slow), PIT operates on Java bytecode in memory using the ASM library.
* **Minion Architecture:** PIT spins up child JVMs ("minions") and communicates over TCP localhost sockets to isolate timeouts, infinite loops, and `OutOfMemoryError`s from crashing the main runner.

---

## 3. Statistical Methods for Empirical Software Engineering

Reviewers in top software engineering venues (ICSE, ISSTA, FSE, EMSE) evaluate empirical papers on statistical rigor. You should understand:

### 1. Non-Parametric Rank Correlation
* **Why not Pearson $r$?** Test suite scores and bug detection rates are non-linear, bounded in $[0, 100]$, and violate normality assumptions.
* **Use Spearman’s $\rho$ and Kendall’s $\tau$:** Measure monotonic relationships based on ranked orders.

### 2. Partial Rank Correlation ($r_{xy \cdot z}$)
* Measures the correlation between $X$ ($\Delta \text{MutationScore}$) and $Y$ (Real Bug Detection) while removing the confounding effect of $Z$ (Test Suite Size / Assertion Count).
* Formula:
  $$r_{xy \cdot z} = \frac{r_{xy} - r_{xz} r_{yz}}{\sqrt{(1 - r_{xz}^2)(1 - r_{yz}^2)}}$$

### 3. Non-Parametric Effect Sizes
Do not rely solely on $p$-values (a tiny effect can have $p < 0.05$ if sample size is large).
* **Vargha-Delaney $\hat{A}_{12}$:** Probability that a randomly selected bug is more likely to be caught with a high mutation score than a low one. ($\hat{A}_{12} = 0.5$: no effect; $\ge 0.71$: large effect).
* **Cliff’s $\delta$:** Standardized measure of dominance between groups ($-1$ to $+1$).

---

## 4. Software Engineering Paper Anatomy (How to Write It)

A successful 4-page short/NIER paper follows a strict structure:
1. **Introduction (§1):**
   - Context: Testing is costly; coverage is the default proxy.
   - The Conflict: 2026 ISSTA paper found coverage/mutation are informative across models, but whether proxy gains translate to real fault detection remains an open question.
   - Contributions: State your 3 RQs and summarize key takeaways.
2. **Empirical Study Design (§2):**
   - Selection of subjects (Defects4J + real OSS commits from Apache Commons).
   - Execution pipeline (PIT configuration, test isolation).
   - Variables: Independent ($MS_{base}$, $MS_{aug}$, $\Delta MS$, mutator classes), Dependent (Real bug caught: 0/1), Control ($N_{tests}$).
3. **Results & Analysis (§3):**
   - Dedicate one subsection to each RQ (RQ1, RQ2, RQ3) with bold **"Key Finding"** callout boxes.
   - Tables reporting $\rho$, $p$, and effect sizes.
4. **Threats to Validity (§4):**
   - *Construct Validity:* Are PIT mutants representative of real regression faults?
   - *Internal Validity:* Execution timeouts, non-deterministic/flaky tests.
   - *External Validity:* Does the finding hold beyond utility libraries to enterprise systems?
5. **Replication Package:**
   - Link to Zenodo DOI containing your scripts, raw XML logs, and Python notebooks.
