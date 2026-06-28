#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/aggregated_perf.parquet ]]; then
  bash scripts/prepare_reduced_reports.sh
fi

uv run --package Gleaner python scripts/artifact/rq4_efficiency.py "$@"

if [[ -d artifact_expected/reduced/rq4 ]]; then
  uv run --package Gleaner python scripts/compare_expected.py \
    --expected artifact_expected/reduced/rq4 \
    --actual output/artifact/reduced/rq4 \
    --file rq4_efficiency_results.md \
    --file rq4_efficiency_summary.csv \
    --file rq4_efficiency_summary.json
fi

uv run --package Gleaner python scripts/artifact/print_reduced_tables.py rq4
