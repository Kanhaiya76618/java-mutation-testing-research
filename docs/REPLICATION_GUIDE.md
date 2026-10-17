# Artifact Replication Guide

This guide details how to reproduce all empirical experiments, statistical analyses, and publication figures from our research study.

---

## 1. Prerequisites & Environment Setup

- **Operating System:** macOS (Apple Silicon / Intel) or Linux (Ubuntu 22.04+).
- **Java:** OpenJDK 21 LTS (`/opt/homebrew/opt/openjdk@21` on macOS or `openjdk-21-jdk` on Ubuntu).
  - Check with: `java -version` (must report version 21.x).
- **Maven:** Apache Maven 3.9+.
- **Python:** Python 3.10+ with scientific computing libraries:
  ```bash
  pip install pandas scipy seaborn matplotlib
  ```

---

## 2. Repository Structure

```
├── config/
│   └── pit-mutators.json               # Operator groups (STRONGER, DEFAULTS, ALL)
├── data/
│   ├── mined_bugs_commons_lang.json    # Mined candidate bug-fixing commits
│   └── processed_results.csv           # 18 experimental records across 9 bug pairs
├── docs/
│   ├── RESEARCH_BRIEF.md               # Theoretical foundation and literature synthesis
│   ├── RESEARCH_QUESTIONS.md           # Formal hypothesis definitions (RQ1, RQ2, RQ3)
│   ├── PAPER_DRAFT_METHODOLOGY.md      # Section 3 draft
│   ├── PAPER_DRAFT_RESULTS.md          # Section 4 draft
│   └── PAPER_DRAFT_THREATS_AND_CONCLUSION.md # Sections 5 & 6 draft
├── figures/
│   ├── rq1_mutation_vs_fault_detection.png # High-res RQ1 boxplot
│   └── rq2_mutator_sensitivity.png         # High-res RQ2 operator bar chart
├── harness/
│   ├── git_miner.py                    # Mining engine for atomic bug fixes
│   └── pit_parser.py                   # PITest mutations.xml extraction engine
├── scripts/
│   ├── run_experiment.py               # Single bug-pair evaluation pipeline
│   ├── batch_runner.py                 # Multi-candidate automated runner
│   ├── analyze_results.py              # Statistical computing engine
│   └── plot_results.py                 # Publication chart generation pipeline
└── tests/
    ├── test_git_miner.py               # Unit tests for mining engine
    └── test_pit_parser.py              # Unit tests for PITest XML parser
```

---

## 3. Reproduction Steps

### Step 1: Verify Test Suite
Ensure all parser and mining components function properly:
```bash
python3 -m unittest discover -s tests -v
```

### Step 2: Reproduce Non-Parametric Statistical Analysis
To re-run the statistical engine (Spearman $\rho$, Kendall $\tau$, controlled partial correlation $r_{xy \cdot z}$, Vargha-Delaney $\hat{A}_{12}$, Cliff's $\delta$, and operator breakdown):
```bash
python3 scripts/analyze_results.py
```
This generates a markdown summary at `docs/LATEST_STATISTICAL_REPORT.md` and prints the analysis to stdout.

### Step 3: Reproduce Publication Figures
To regenerate the 300 DPI publication figures in the `figures/` directory:
```bash
python3 scripts/plot_results.py
```

### Step 4: Run Mutation Analysis on a Bug Pair
To run the full end-to-end pipeline on one mined candidate (here index 12 of the mined list):
```bash
python3 scripts/run_experiment.py \
  --repo benchmarks/commons-lang \
  --mined-bugs data/mined_bugs_commons_lang.json \
  --index 12 \
  --mutators STRONGER
```
To run a range of candidates:
```bash
python3 scripts/batch_runner.py --repo benchmarks/commons-lang --start 0 --limit 14
```
Outputs:
- `data/v2/runs.csv`: one row per bug and suite (`base`, `augmented`) with Surefire test counts, PIT counts and scores, timings, and the tests that fail on the buggy version.
- `data/v2/operators.csv`: one row per bug, suite and PIT mutator, with raw counts.
- `data/v2/skipped.csv`: candidates that could not be evaluated, with the reason.
- `data/raw/<bug_id>/`: the raw PIT report (`mutations.xml.gz`, with the full kill matrix), PIT's console output, and the Surefire reports for the buggy version and both suites.

### Step 5: Equal-size Test-Subset Analysis (RQ1, RQ2)
Uses the kill matrices from Step 4 to score thousands of random equal-size test subsets, without re-running PIT:
```bash
python3 scripts/subset_analysis.py --subsets 1000 --seed 2026
```
Outputs `docs/SUBSET_ANALYSIS.md` (sanity check against PIT, per-pair A12 for mutation score and coverage, per-operator A12) and the raw numbers in `data/v2/subset_analysis.csv` and `data/v2/subset_operators.csv`. The seed makes the results reproducible.
