# Research Daily Log

Tracking daily progress, experimental findings, methodology updates, and decisions for the research paper.

---

## Day 1 — Repository Initialization & Environment Setup (2026-09-24)

### Objectives
- Initialize research repository and directory structure.
- Document baseline research questions (RQ1–RQ3) and 2026 literature anchors.
- Configure mutator group profiles for PIT.
- Implement the PIT XML parsing engine (`harness/pit_parser.py`) and CSV data schema.
- Outline dual-track setup: Option 1 (Defects4J standard benchmark) & Option 2 (GSoC target project mining).

### Completed Work
- [x] Initialized Git repository with clean directory hierarchy (`docs/`, `config/`, `harness/`, `scripts/`, `data/`).
- [x] Preserved literature context in `docs/RESEARCH_BRIEF.md`.
- [x] Defined statistical metrics and formal hypotheses in `docs/RESEARCH_QUESTIONS.md`.
- [x] Defined mutator subsets in `config/pit-mutators.json`.
- [x] Built core XML mutation parser (`harness/pit_parser.py`) to extract:
  - Mutant status (`KILLED`, `SURVIVED`, `NO_COVERAGE`, `TIMED_OUT`)
  - Mutator group mapping
  - Killing test identification
- [x] Initialized `data/processed_results.csv` with standard experiment schema.

### Observations & Methodological Decisions
1. **Controlling for Suite Size:** Standard Spearman correlation alone is insufficient because adding tests increases both size and the likelihood of killing mutants. We explicitly track `test_count_base` and `test_count_aug` so we can run partial rank correlation ($r_{xy \cdot z}$) and logistic regression.
2. **Mutator Granularity:** In addition to testing coarse-grained bundles (`DEFAULTS`, `STRONGER`), we track 5 isolated mutator classes (`CONDITIONALS_BOUNDARY`, `NEGATE_CONDITIONALS`, `MATH`, `VOID_METHOD_CALLS`, `INVERT_NEGS`) to determine which ones yield genuine predictive value vs. noise.

---

## Day 2 — Git Mining Pipeline & First End-to-End Real Bug Trial (2026-09-24)

### Objectives
- Build the automated Git Bug Miner (`harness/git_miner.py`) with unit test validation.
- Clone and configure our first target repository (`commons-lang`).
- Resolve Maven, JaCoCo, and JUnit 5 plugin dependencies for PIT bytecode mutation.
- Execute our very first end-to-end experiment trial on a live, real-world bug.
- Log metrics to `data/processed_results.csv` and push Day 2 progress to GitHub.

### Completed Work
- [x] Built `harness/git_miner.py` to identify regression bug fixes modifying both `src/main/java` and `src/test/java`, extracting $V_{bug}$, $V_{fix}$, target classes, and newly added test methods.
- [x] Added automated unit test `tests/test_git_miner.py` (passed in 0.21s).
- [x] Cloned Apache Commons Lang (`benchmarks/commons-lang`).
- [x] Mined candidate bug-fixing commits -> saved to `data/mined_bugs_commons_lang.json`.
- [x] Integrated `pitest-maven` 1.16.0 with `pitest-junit5-plugin` 1.2.1.
- [x] Verified fault detection on Bug `LANG-1834` (`FractionTest.testReducedFactoryIntegerMinValue`):
  - Fails on $V_{bug}$ (`real_bug_detected = 1`).
  - Passes on $V_{fix}$ with 38 test cases green.
- [x] Executed full PIT mutation testing on `org.apache.commons.lang3.math.Fraction`:
  - Mutators: `STRONGER` (14 operator classes).
  - Mutants generated: 350 | Killed: 280 (80.00% mutation score).
  - Line Coverage: 96% (262/272 lines).
  - Execution time: 64 seconds.
- [x] Verified `harness/pit_parser.py` on real PIT report, extracting complete operator breakdown:
  - `MathMutator`: 90% killed (66/73).
  - `NullReturnValsMutator`: 97% killed (32/33).
  - `ConditionalsBoundaryMutator`: 17% killed (5/30) — notable survivability.
- [x] Recorded first data points in `data/processed_results.csv`.

---

## Day 3 — Batch Execution Engine, Bytecode Architecture & Statistical Analysis (2026-09-25)

### Objectives
- Resolve OpenJDK 26 ASM bytecode compatibility by installing and binding OpenJDK 21 LTS.
- Solve the PIT green pre-scan requirement using method-level annotation commenting (`_disable_test_methods`).
- Build and verify automated batch runner (`scripts/batch_runner.py`).
- Implement statistical analysis engine (`scripts/analyze_results.py`) computing Spearman $\rho$, Kendall $\tau$, partial correlation, Vargha-Delaney $\hat{A}_{12}$, and Cliff's $\delta$.
- Scale dataset to multiple real bug commits and evaluate preliminary findings.

### Completed Work
- [x] Installed OpenJDK 21 LTS via Homebrew (`/opt/homebrew/opt/openjdk@21`) and configured runtime environment flags in `run_cmd`.
- [x] Implemented regex-based bytecode test annotation isolation:
  - For $T_{base}$: Comments out `@Test` and `@ParameterizedTest` for added methods, compiling a 100% green base suite.
  - For $T_{aug}$: Restores annotations, compiling the full augmented test suite.
- [x] Successfully evaluated 3 additional real bug fixes:
  - **`d8f4116d` (MethodUtils):** $MS_{base} = 80.60\% \rightarrow MS_{aug} = 83.19\%$ ($\Delta MS = +2.59\%$, 6 new mutants killed, detected real bug).
  - **`e213b85c` (Fraction.add/subtract):** $MS_{base} = 74.50\% \rightarrow MS_{aug} = 75.07\%$ ($\Delta MS = +0.57\%$, 2 new mutants killed, detected real bug).
  - **`df1e9189` (TypeUtils.isAssignable):** $MS_{base} = 67.72\% \rightarrow MS_{aug} = 68.54\%$ ($\Delta MS = +0.82\%$, 5 new mutants killed, detected real bug).
- [x] Scaled dataset to 8 experiment records in `data/processed_results.csv`.
- [x] Built `scripts/analyze_results.py` and generated preliminary statistical report in `docs/LATEST_STATISTICAL_REPORT.md`:
  - Spearman Rank Correlation: $\rho = 0.165$ ($p = 0.697$).
  - Partial Rank Correlation (size-controlled): $r_{xy \cdot z} = 0.170$.
  - Vargha-Delaney Effect Size: $\hat{A}_{12} = 0.594$.
  - Cliff's Delta: $\delta = 0.188$.
- [x] Operator breakdown indicates `Math / Arithmetic` and `Conditionals Boundary` mutators show higher sensitivity to regression test additions.

### Key Technical Insights
1. **PIT Bytecode Versioning Constraints:** PIT 1.16 is powered by ASM 9.x, which natively parses class files up to Java 21. Standardizing on OpenJDK 21 LTS eliminates all class file major version exceptions when testing classes that reflect on JDK internals (`java.util.Collections$EmptyList`).
2. **Annotation-Level Suite Isolation:** Completely commenting out the test annotation (`/* @Test */`) is superior to using `@Disabled` because PIT's bytecode test discoverer ignores `@Disabled` unless configured with specific runner engines. Commenting out ensures the test method does not exist in the test engine's execution graph.

### Next Steps (Day 4)
- Run remaining mined candidates in `data/mined_bugs_commons_lang.json` (target: $N \ge 10$ bug pairs, 20 total dataset rows).
- Generate publication-ready correlation and effect size charts (`matplotlib` / `seaborn`).
- Begin drafting Section 3 (Empirical Methodology) of the NIER paper.
