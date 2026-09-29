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

---

## Day 4 — Incremental Dataset Scaling, Visualizations & Paper Drafting (2026-09-28)

### Objectives
- Follow structured, batch-by-batch execution and incremental GitHub delivery.
- **Batch 1:** Mine and evaluate time and character utility modules (`DurationFormatUtils`, `Conversion`, `CharRange`).
- **Batch 2:** Mine and evaluate core string and timestamp modules (`StringUtils`, `Instants`).
- **Batch 3:** Build automated publication plotting pipeline (`scripts/plot_results.py`) and generate figures for RQ1 and RQ2.
- **Batch 4:** Draft Section 3 (Empirical Study Design & Methodology) for our NIER paper submission.
- **Batch 5:** Draft Section 4 (Empirical Results & Analysis) answering RQ1, RQ2, and RQ3.
- **Batch 6:** Draft Sections 5 & 6 (Threats to Validity & Conclusion) and write Open Science `REPLICATION_GUIDE.md`.
- **Batch 7:** Assemble unified full paper manuscript (`docs/PAPER_MANUSCRIPT_FULL.md`) and update project README.

### Completed Work
- [x] **Executed Batch 1:**
  - `DurationFormatUtils`: $\Delta MS = +0.40\%$ ($79.52\% \rightarrow 79.92\%$).
  - `Conversion`: $\Delta MS = +0.34\%$ ($89.23\% \rightarrow 89.57\%$, 3 extra mutants killed).
  - `CharRange.contains`: $\Delta MS = +23.08\%$ ($69.23\% \rightarrow 92.31\%$, 24 extra boundary mutants killed!).
  - Committed & Pushed: `fc588e8`.
- [x] **Executed Batch 2:**
  - `StringUtils`: 2,187 mutants evaluated; $\Delta MS = +0.73\%$ ($5.58\% \rightarrow 6.31\%$, 16 extra mutants killed).
  - `Instants`: $\Delta MS = +21.43\%$ ($71.43\% \rightarrow 92.86\%$, 3 extra mutants killed).
  - Scaled dataset to **18 records across 9 distinct bug pairs**.
  - Committed & Pushed: `20e31b8`.
- [x] **Statistical Evolution:**
  - **Controlled Partial Correlation ($r_{xy \cdot z}$):** Increased from $0.170 \rightarrow 0.285 \rightarrow \mathbf{0.324}$.
  - **Vargha-Delaney Effect Size ($\hat{A}_{12}$):** Increased from $0.594 \rightarrow 0.663 \rightarrow \mathbf{0.685}$ (Medium effect approaching large effect threshold).
  - **Cliff's Delta ($\delta$):** Rose to $\mathbf{0.370}$.
  - **Math/Arithmetic Mutators:** Confirmed strong predictive signal ($\Delta > +10\%$ mean score for fault-detecting suites).
- [x] **Executed Batch 3 (Visualizations):**
  - Built `scripts/plot_results.py` using `seaborn` and `matplotlib`.
  - Generated high-resolution publication charts:
    - `figures/rq1_mutation_vs_fault_detection.png` (Boxplot of mutation distributions with strip overlays).
    - `figures/rq2_mutator_sensitivity.png` (Horizontal grouped bar chart of individual mutator sensitivities).
  - Committed & Pushed: `e5c133c`.
- [x] **Executed Batch 4 (Paper Methodology):**
  - Drafted comprehensive methodology section in `docs/PAPER_DRAFT_METHODOLOGY.md` covering inclusion criteria, annotation isolation, mutator operator taxonomy, and non-parametric statistical metrics.
  - Committed & Pushed: `a95f9e2`.
- [x] **Executed Batch 5 (Paper Results & Discussion):**
  - Drafted Section 4 in `docs/PAPER_DRAFT_RESULTS.md` with detailed statistical analysis tables, operator kill rate decompositions, and practical CI/CD pruning trade-offs.
  - Committed & Pushed: `35eca19`.
- [x] **Executed Batch 6 (Threats, Conclusion & Replication Guide):**
  - Drafted Section 5 (Threats to Validity) and Section 6 (Conclusion & Artifacts) in `docs/PAPER_DRAFT_THREATS_AND_CONCLUSION.md`.
  - Authored comprehensive artifact replication guide in `docs/REPLICATION_GUIDE.md`.
  - Committed & Pushed: `d2d54e9`.
- [x] **Executed Batch 7 (Unified Manuscript & Project Index):**
  - Assembled complete 6-section conference manuscript in `docs/PAPER_MANUSCRIPT_FULL.md`.
  - Updated `README.md` with key findings summary, publication figures index, and artifact reproduction instructions.
  - Committed & Pushed: `e0fbe1e`.

---

## Day 5 — Camera-Ready LaTeX Manuscript, CI Replication & Zenodo Packaging (2026-09-29)

### Objectives
- Follow incremental batch delivery to GitHub for all Day 5 research deliverables.
- **Batch 1:** Format camera-ready two-column IEEE/ACM LaTeX conference manuscript (`paper/main.tex`, `paper/references.bib`).
- **Batch 2:** Build automated end-to-end replication script (`scripts/reproduce_all.sh`) and GitHub Actions CI workflow.
- **Batch 3:** Author Zenodo open-science DOI archive metadata (`zenodo.json`) and packaging script.
- **Batch 4:** Draft conference submission checklist (`docs/SUBMISSION_CHECKLIST.md`) for ICSE NIER / ISSTA Workshop.

### Completed Work
- [x] **Executed Batch 1 (LaTeX Manuscript):**
  - Authored standard IEEEtran two-column conference paper in `paper/main.tex`.
  - Authored complete BibTeX references in `paper/references.bib` covering 2024–2026 literature.
  - Embedded empirical tables (RQ1 statistical summary, RQ2 mutator decomposition), formulas, and methodology descriptions.
  - Committed & Pushed: `d5c0d9c`.
- [x] **Executed Batch 2 (Automated Replication Script & CI):**
  - Built `scripts/reproduce_all.sh` orchestrating unit test execution, statistical analysis, and 300 DPI chart generation.
  - Verified local end-to-end execution.
  - Authored GitHub Actions workflow `.github/workflows/reproduce_and_test.yml` to automatically verify replication on Ubuntu runners on every commit.
  - Committed & Pushed: `90adc4b`.
- [x] **Executed Batch 3 (Zenodo Open-Science Archiving):**
  - Authored MIT `LICENSE` ensuring open replication rights for ACM/IEEE badges.
  - Authored `zenodo.json` archive descriptor with DOI metadata, keywords, and publication links.
  - Built and verified automated standalone bundle packager `scripts/package_zenodo_artifact.sh`.

### Next Steps (Day 5 Batches)
- Draft submission checklist and finalize Day 5 review (Batch 4).
