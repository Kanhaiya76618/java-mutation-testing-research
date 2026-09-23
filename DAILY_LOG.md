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

### Next Steps (Day 2)
- Set up target project workspace for Option 2 (e.g., clone target repository or set up submodule).
- Validate PIT execution on a single small test case to verify end-to-end report generation and parsing.
- Implement `harness/git_miner.py` to identify candidates with both production code fixes and new test assertions.
