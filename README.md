# Empirical Evaluation of Mutation Testing for Regression-Test Fault Detection

This repository hosts the replication package, experimental testbed, and daily research logs for our empirical study:
**"Which Mutation Operators Track Real-Fault Detection? A Method-Level Isolation Protocol and Pilot Study on Apache Commons Lang"**

🔗 **GitHub Repository:** [https://github.com/Kanhaiya76618/java-mutation-testing-research](https://github.com/Kanhaiya76618/java-mutation-testing-research)

## Research Objectives
Building upon empirical literature (Papadakis et al. ICSE 2018, Just et al. FSE 2014, Zhao et al. ISSTA 2026) and industrial mutation testing (Foster et al. Meta FSE 2025), this study investigates the conditions under which mutation score increases predict real regression-fault detection:
- **RQ1:** In within-subject matched pairs, does $\Delta \text{MutationScore}$ correlate with real-fault detection when controlling for test-suite size?
- **RQ2:** Which PIT mutator groups (`CONDITIONALS_BOUNDARY`, `NEGATE_CONDITIONALS`, `MATH`, `VOID_METHOD_CALLS`, etc.) offer the highest predictive signal-to-cost ratio across Leave-One-Bug-Out cross-validation folds?
- **RQ3:** What are the computational overhead trade-offs of selective operator pruning for continuous integration pipelines?

## Key Empirical Findings
- **Within-Subject Matched Pairs:** In **8 of 9 bug fixes (88.9%)**, adding tests catching real regression defects strictly increased class mutation score (mean gain $\overline{\Delta MS} = +5.55\%$, **Wilcoxon signed-rank $W = 36.0, p = 0.0039$**; paired sign test $p = 0.0039$).
- **Unpaired Distribution Metrics:** Mann-Whitney $U = 55.5, p = 0.20$, Vargha-Delaney $\hat{A}_{12} = 0.685$ [95% CI: $0.43, 0.94$], Cliff's $\delta = 0.370$, and size-controlled partial rank correlation $r_{xy \cdot z} = 0.324$.
- **Mutator Sensitivity (LOBO):** `MATH` (+11.81% differential, 100% positive LOBO folds) and `CONDITIONALS_BOUNDARY` (+1.85%, 89% positive folds) provide the strongest discriminatory signals, while `VOID_METHOD_CALLS` is saturated by baseline smoke tests.
- **CI/CD Optimization:** Pruning to high-sensitivity operators reduces mutant generation by **63.4%** while preserving **91.2%** of fault-revealing score gains.

## Repository Structure
```text
├── DAILY_LOG.md               # Daily progress tracker, notes, and milestones
├── docs/                      # Theoretical framework, literature synthesis, and paper drafts
│   ├── PAPER_MANUSCRIPT_FULL.md          # Complete unified NIER paper manuscript
│   ├── PAPER_DRAFT_METHODOLOGY.md        # Empirical methodology draft (§3)
│   ├── PAPER_DRAFT_RESULTS.md            # Empirical results & analysis draft (§4)
│   ├── PAPER_DRAFT_THREATS_AND_CONCLUSION.md # Validity threats & conclusion (§5 & §6)
│   ├── REPLICATION_GUIDE.md              # Open-science replication instructions
│   ├── RESEARCH_BRIEF.md                 # Foundational literature synthesis (2023–2026)
│   └── RESEARCH_QUESTIONS.md             # Formal statistical hypotheses (RQ1, RQ2, RQ3)
├── figures/                   # High-resolution (300 DPI) publication figures
│   ├── rq1_mutation_vs_fault_detection.png
│   └── rq2_mutator_sensitivity.png
├── config/                    # PIT configuration profiles and mutator definitions
│   └── pit-mutators.json
├── harness/                   # Execution harnesses and log parsers
│   ├── pit_parser.py          # Extracts mutant kill statuses from PIT XML reports
│   └── git_miner.py           # Mines bug-fix commits and test delta from git history
├── scripts/                   # Automated experiment runners and analysis pipelines
│   ├── run_experiment.py      # Single bug-pair evaluation pipeline
│   ├── batch_runner.py        # Automated batch candidate evaluation
│   ├── analyze_results.py     # Statistical analysis engine (Spearman, Partial Corr, A12)
│   └── plot_results.py        # Publication chart generation pipeline
├── data/                      # Structured dataset for statistical evaluation
│   ├── mined_bugs_commons_lang.json      # Mined candidate bug-fixing commits
│   └── processed_results.csv             # 18 experimental records across 9 bug pairs
└── tests/                     # Unit test suite for miners and parsers
    ├── test_git_miner.py
    └── test_pit_parser.py
```

## Quick Start & Reproduction
1. **Python Environment:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Reproduce Statistical Analysis:**
   ```bash
   python3 scripts/analyze_results.py
   ```
3. **Regenerate Publication Figures:**
   ```bash
   python3 scripts/plot_results.py
   ```
4. **Full Artifact Guide:**
   See [`docs/REPLICATION_GUIDE.md`](./docs/REPLICATION_GUIDE.md) and [`docs/PAPER_MANUSCRIPT_FULL.md`](./docs/PAPER_MANUSCRIPT_FULL.md).
