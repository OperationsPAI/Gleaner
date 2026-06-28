#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/aggregated_perf.parquet ]]; then
  bash scripts/prepare_reduced_reports.sh
fi

uv run --package Gleaner python scripts/artifact/rq1_sampling_quality.py "$@"

if [[ -d artifact_expected/reduced/rq1 ]]; then
  uv run --package Gleaner python scripts/compare_expected.py \
    --expected artifact_expected/reduced/rq1 \
    --actual output/artifact/reduced/rq1 \
    --file rq1_sampling_quality_results.md \
    --file rq1_sampling_quality_summary.csv \
    --file rq1_sampling_quality_summary.json
fi

uv run --package Gleaner python scripts/artifact/print_reduced_tables.py rq1
