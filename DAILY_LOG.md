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

### Key Technical Insights
1. **PIT Requires a 100% Green Suite:** PIT will abort during its pre-scan if any test fails on the code under test. This validates our experimental methodology: mutation testing must be evaluated on the **bug-free fixed version** ($V_{fix}$) as formalized in Zhao et al. (ISSTA 2026), while real-fault detection is evaluated by checking if the augmented test fails on the **buggy version** ($V_{bug}$).
2. **Low Mutation Score in Conditionals Boundary:** Notice `ConditionalsBoundaryMutator` had an 83% survival rate (only 5 of 30 killed), despite high overall line coverage (96%). This provides early empirical support for RQ2 (boundary mutators expose test gaps that standard line coverage misses).

### Next Steps (Day 3)
- Batch-run the experiment pipeline across remaining mined bugs in `data/mined_bugs_commons_lang.json` (`NumberUtils`, `ConstructorUtils`, `AbstractFormatCache`).
- Mine 10 additional bug-fix commits to expand dataset to $N \ge 15$.
- Compute preliminary Spearman $\rho$ and delta mutation scores ($\Delta MS$).
