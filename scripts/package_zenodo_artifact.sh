#!/usr/bin/env bash
# ==============================================================================
# Packaging script for Zenodo Open Science Artifact Archive
# Generates a standalone replication zip archive
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ARCHIVE_NAME="mutation-testing-research-zenodo-artifact.zip"
OUTPUT_PATH="${REPO_ROOT}/${ARCHIVE_NAME}"

echo "Packaging Zenodo artifact: ${ARCHIVE_NAME}..."

cd "${REPO_ROOT}"

# Remove existing archive if present
rm -f "${OUTPUT_PATH}"

# Create zip archive excluding git history, virtual environments, cache, and raw logs
zip -r "${OUTPUT_PATH}" \
  README.md \
  LICENSE \
  DAILY_LOG.md \
  zenodo.json \
  requirements.txt \
  config/ \
  data/*.json \
  data/processed_results.csv \
  docs/ \
  figures/ \
  harness/ \
  paper/ \
  scripts/ \
  tests/ \
  -x "*.DS_Store" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "data/raw/*" \
  -x ".git/*" \
  -x ".venv/*"

echo "[✓] Archive created successfully: ${OUTPUT_PATH}"
ls -lh "${OUTPUT_PATH}"
