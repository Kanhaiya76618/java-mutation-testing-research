#!/usr/bin/env bash
# ==============================================================================
# Automated Replication Script
# Recomputes every analysis, table, figure and paper number from the committed
# measured data (data/v2/ and data/raw/). No Java or PIT is needed for this;
# re-measuring the data itself is described in docs/REPLICATION_GUIDE.md (step 4).
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

echo "========================================================================"
echo " Starting Full Artifact Replication Pipeline"
echo " Working Directory: ${REPO_ROOT}"
echo "========================================================================"

# Step 1: Verify Python Environment & Dependencies
echo ""
echo "[1/6] Checking Python environment and scientific libraries..."
python3 -c "import numpy, pandas, scipy, matplotlib; print('  [✓] All required scientific libraries are installed.')"

# Step 2: Run Unit Tests for Harness and Analyses
echo ""
echo "[2/6] Running test suite..."
python3 -m unittest discover -s tests -v
echo "  [✓] All unit tests completed successfully."

# Step 3: RQ1 - Naive base-vs-augmented analysis and its placebo
echo ""
echo "[3/6] Running the pitfall analysis (naive design vs. placebo)..."
python3 scripts/pitfall_analysis.py > /dev/null
echo "  [✓] docs/PITFALL_ANALYSIS.md, data/v2/pitfall_analysis.csv, paper/generated/pitfall_numbers.tex"

# Step 4: RQ2/RQ3 - Equal-size test-subset analysis on the kill matrix
echo ""
echo "[4/6] Running the equal-size test-subset analysis..."
python3 scripts/subset_analysis.py > /dev/null
echo "  [✓] docs/SUBSET_ANALYSIS.md, data/v2/subset_*.csv, paper/generated/subset_numbers.tex"

# Step 5: Figures and paper tables
echo ""
echo "[5/6] Regenerating figures and the paper's LaTeX tables..."
python3 scripts/plot_results.py
python3 scripts/paper_tables.py
for f in figures/pitfall_placebo.pdf figures/a12_ms_vs_coverage.pdf paper/generated/table_pairs.tex paper/generated/table_operators.tex; do
    if [[ ! -f "${f}" ]]; then
        echo "  [!] ERROR: expected output ${f} not found!"
        exit 1
    fi
done

# Step 6: Comparison of the original (v1) and re-measured (v2) data
echo ""
echo "[6/6] Comparing the original CSV with the re-measured data..."
python3 scripts/compare_v1_v2.py > /dev/null
echo "  [✓] docs/DATA_V1_VS_V2.md"

echo ""
echo "========================================================================"
echo " [✓] REPLICATION PIPELINE COMPLETED SUCCESSFULLY"
echo " Every report, figure, table and paper number was regenerated from data/v2 and data/raw."
echo " 'git status' shows whether anything differs from the committed versions."
echo "========================================================================"
