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

"${PY[@]}" scripts/artifact/rq1_sampling_quality.py "$@"

if [[ "${GLEANER_COMPARE_EXPECTED:-0}" == "1" && -d artifact_expected/reduced/rq1 ]]; then
  "${PY[@]}" scripts/compare_expected.py \
    --expected artifact_expected/reduced/rq1 \
    --actual output/artifact/reduced/rq1 \
    --file rq1_sampling_quality_results.md \
    --file rq1_sampling_quality_summary.csv \
    --file rq1_sampling_quality_summary.json
fi

"${PY[@]}" scripts/artifact/print_reduced_tables.py rq1
