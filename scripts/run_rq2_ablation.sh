#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -n "${GLEANER_PYTHON:-}" ]]; then
  read -r -a PY <<< "${GLEANER_PYTHON}"
elif [[ -x .venv/bin/python ]]; then
  PY=(.venv/bin/python)
else
  PY=(uv run --package Gleaner python)
fi

DATASET="${GLEANER_REDUCED_DATASET:-gleaner_lite}"
REPORT_DIR="output/rcabench-platform-v2/sampler_reports/${DATASET}"

if [[ ! -f "${REPORT_DIR}/aggregated_perf.parquet" ]]; then
  bash scripts/prepare_reduced_reports.sh
fi

"${PY[@]}" scripts/artifact/rq2_ablation.py "$@"

"${PY[@]}" scripts/artifact/print_reduced_tables.py rq2
