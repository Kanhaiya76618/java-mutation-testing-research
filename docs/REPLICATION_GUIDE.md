# Artifact Replication Guide

How to reproduce every analysis, figure, table and paper number, and how to re-measure the data itself.
The repository layout is described in the [README](../README.md).

---

## 1. Prerequisites

- **Analyses only (steps 2–4):** Python 3.10+ with `pip install -r requirements.txt`. No Java is needed;
  everything is computed from the committed measured data in `data/v2/` and `data/raw/`.
- **Re-measuring the data (step 5):** additionally OpenJDK 21 (`java -version` must report 21.x; on macOS
  the runner uses `/opt/homebrew/opt/openjdk@21` when present), Apache Maven 3.9+, and a clone of
  Apache Commons Lang in `benchmarks/commons-lang`.
- **Building the paper (step 6):** a LaTeX distribution with `latexmk` and BibTeX, or Overleaf.

---

## 2. Run the Unit Tests
```bash
python3 -m unittest discover -s tests -v
```

## 3. Recompute Everything from the Measured Data
```bash
./scripts/reproduce_all.sh
```
This runs the unit tests and steps 4a–4e below. Afterwards, `git status` shows whether any report,
figure, table or paper number differs from the committed version (the outputs are deterministic:
fixed seeds, no timestamps in figures).

## 4. Individual Analyses
**a. RQ1, the pitfall (naive comparison vs. placebo):**
```bash
python3 scripts/pitfall_analysis.py --draws 1000 --seed 2026
```
Writes `docs/PITFALL_ANALYSIS.md`, `data/v2/pitfall_analysis.csv` and `paper/generated/pitfall_numbers.tex`.

**b. RQ2/RQ3, equal-size test subsets on the kill matrix:**
```bash
python3 scripts/subset_analysis.py --subsets 1000 --seed 2026
```
Writes `docs/SUBSET_ANALYSIS.md` (with a sanity check of the kill matrix against PIT's own counts),
`data/v2/subset_*.csv` and `paper/generated/subset_numbers.tex`.

**c. Figures:** `python3 scripts/plot_results.py` writes `figures/pitfall_placebo.(pdf|png)` and
`figures/a12_ms_vs_coverage.(pdf|png)`.

**d. Paper tables:** `python3 scripts/paper_tables.py` writes `paper/generated/table_pairs.tex` and
`paper/generated/table_operators.tex`.

**e. Original vs. re-measured data:** `python3 scripts/compare_v1_v2.py` writes `docs/DATA_V1_VS_V2.md`.

## 5. Re-measure a Bug Pair (Java, Maven, PIT)
To measure one mined candidate (here index 12 of the mined list):
```bash
python3 scripts/run_experiment.py \
  --repo benchmarks/commons-lang \
  --mined-bugs data/mined_bugs_commons_lang.json \
  --index 12 \
  --mutators STRONGER
```
To measure a range of candidates:
```bash
python3 scripts/batch_runner.py --repo benchmarks/commons-lang --start 0 --limit 14
```
Outputs:
- `data/v2/runs.csv`: one row per bug and suite (`base`, `augmented`) with Surefire test counts, PIT counts
  and scores, timings, and the tests that fail on the buggy version.
- `data/v2/operators.csv`: one row per bug, suite and PIT mutator, with raw counts.
- `data/v2/skipped.csv`: candidates that could not be evaluated, with the reason.
- `data/raw/<bug_id>/`: the raw PIT report (`mutations.xml.gz`, with the full kill matrix), PIT's console
  output, and the Surefire reports for the buggy version and both suites.

With the full kill matrix, PIT runs every covering test against every mutant, so runs are slower than
normal PIT runs (up to about 15 minutes per suite for `DurationFormatUtils`). Timeouts can differ between
runs, so re-measured counts may differ from the committed ones by a few mutants.

## 6. Build the Paper
```bash
cd paper && latexmk -pdf main.tex
```
`paper/main.tex` includes `paper/generated/*.tex` and `figures/*.pdf`, so run step 3 first. Set
`\anonymousfalse` in `main.tex` for a non-anonymous build. The GitHub workflow
`.github/workflows/compile_paper.yml` builds the PDF on every push that changes `paper/`.
