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
To run the full end-to-end pipeline on an individual mined candidate:
```bash
python3 scripts/run_experiment.py \
  --repo-path /path/to/commons-lang \
  --commit <commit_hash> \
  --target-class org.apache.commons.lang3.math.Fraction \
  --target-test org.apache.commons.lang3.math.FractionTest \
  --mutators STRONGER
```
