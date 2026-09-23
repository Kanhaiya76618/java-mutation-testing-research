# Empirical Evaluation of Mutation Testing for Regression-Test Fault Detection

This repository hosts the replication package, experimental testbed, and daily research logs for our empirical study:
**"When Does Raising Mutation Score Actually Raise Real-Fault Detection? An Empirical Investigation on Java Ecosystems"**

## Research Objectives
Building upon recent findings by Zhao, Zhou & Cohen (PACMSE/ISSTA 2026) and industrial mutation-guided testing (Meta FSE 2025), this study investigates the conditions under which mutation score increases predict real regression-fault detection:
- **RQ1:** Across historical bug fixes, does $\Delta \text{MutationScore}$ correlate with real-fault detection when controlling for test-suite size?
- **RQ2:** Which PIT mutator groups (`CONDITIONALS_BOUNDARY`, `NEGATE_CONDITIONALS`, `MATH`, `VOID_METHOD_CALLS`, etc.) offer the highest predictive signal-to-cost ratio?
- **RQ3:** How do these correlations behave across different project architectures (Defects4J benchmarks vs. modern production systems like JabRef/Jenkins)?

## Repository Structure
```text
├── DAILY_LOG.md               # Daily progress tracker, notes, and milestones
├── docs/                      # Theoretical framework, literature synthesis, and paper drafts
│   ├── RESEARCH_BRIEF.md      # Foundational 2023–2026 landscape
│   └── RESEARCH_QUESTIONS.md  # Formal hypotheses and statistical definitions
├── config/                    # PIT configuration profiles and mutator definitions
│   └── pit-mutators.json
├── harness/                   # Execution harnesses and log parsers
│   ├── pit_parser.py          # Extracts mutant kill statuses from PIT XML reports
│   └── git_miner.py           # Mines bug-fix commits and test delta from git history
├── scripts/                   # Automated experiment runners and analysis pipelines
│   └── run_experiment.py
├── data/                      # Structured dataset for statistical evaluation
│   ├── raw/                   # Raw XML/CSV mutation and coverage reports (ignored by git)
│   └── processed_results.csv  # Consolidated metrics across trials
└── requirements.txt           # Python dependencies for statistical analysis
```

## Quick Start
1. **Python Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Review Daily Progress:**
   Check [`DAILY_LOG.md`](./DAILY_LOG.md) for the active milestone and latest findings.
