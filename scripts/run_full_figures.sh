#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
DATASET_A="${GLEANER_FULL_DATASET_A:-gleaner}"
DATASET_B="${GLEANER_FULL_DATASET_B:-tracepicker}"

printf '\n[full:figures] == generating paper figures/tables from full reports ==\n'
uv run --package Gleaner python scripts/artifact/full_paper_outputs.py \
  --dataset-a "${DATASET_A}" \
  --dataset-b "${DATASET_B}" \
  --figure-dir output/full/figures \
  --table-dir output/full/tables

test -s output/full/REPORT.md
test -s output/full/tables/rq1_dataset_a_sampling_quality.csv
test -s output/full/tables/rq3_rca_effectiveness.csv
echo "[full:figures] figure/table phase completed"
