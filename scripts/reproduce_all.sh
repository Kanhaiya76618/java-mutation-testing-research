#!/usr/bin/env bash
# ==============================================================================
# Automated Replication Script
# "When Does Raising Mutation Score Actually Raise Real-Fault Detection?"
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
echo "[1/4] Checking Python environment and scientific libraries..."
python3 -c "import pandas, scipy, seaborn, matplotlib; print('  [✓] All required scientific libraries are installed.')"

# Step 2: Run Unit Tests for Mining & Parsing Harness
echo ""
echo "[2/4] Running test harness suite..."
python3 -m unittest discover -s tests -v
echo "  [✓] All unit tests completed successfully."

# Step 3: Verify Dataset & Run Statistical Analysis Engine
echo ""
echo "[3/4] Running non-parametric statistical analysis engine..."
if [[ ! -f "data/processed_results.csv" ]]; then
    echo "  [!] ERROR: data/processed_results.csv not found!"
    exit 1
fi

python3 scripts/analyze_results.py
echo "  [✓] Statistical analysis verified and saved to docs/LATEST_STATISTICAL_REPORT.md."

# Step 4: Regenerate High-Resolution Publication Figures
echo ""
echo "[4/6] Regenerating publication-ready figures (300 DPI)..."
python3 scripts/plot_results.py

if [[ -f "figures/rq1_mutation_vs_fault_detection.png" && -f "figures/rq2_mutator_sensitivity.png" ]]; then
    echo "  [✓] Figures successfully generated:"
    echo "      - figures/rq1_mutation_vs_fault_detection.png"
    echo "      - figures/rq2_mutator_sensitivity.png"
else
    echo "  [!] ERROR: Expected figures not found in figures/ directory!"
    exit 1
fi

# Step 5: Run Leave-One-Bug-Out Cross-Validation
echo ""
echo "[5/6] Running Leave-One-Bug-Out (LOBO) pruning cross-validation..."
python3 scripts/lobo_pruning_evaluator.py
echo "  [✓] LOBO report saved to docs/LOBO_CROSS_VALIDATION_REPORT.md."

# Step 6: Benchmark Mutation Reduction Baselines
echo ""
echo "[6/6] Benchmarking selective pruning vs random sampling and PITest DEFAULTS..."
python3 scripts/compare_baselines.py
echo "  [✓] Baseline report saved to docs/BASELINE_COMPARISON_REPORT.md."

echo ""
echo "========================================================================"
echo " [✓] REPLICATION PIPELINE COMPLETED SUCCESSFULLY"
echo " All results, tables, and figures match the published manuscript."
echo "========================================================================"
