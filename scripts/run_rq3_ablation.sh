#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/aggregated_perf.parquet ]]; then
  bash scripts/prepare_reduced_reports.sh
fi

uv run --package Gleaner python scripts/artifact/rq3_ablation.py "$@"

if [[ -d artifact_expected/reduced/rq3 ]]; then
  uv run --package Gleaner python scripts/compare_expected.py \
    --expected artifact_expected/reduced/rq3 \
    --actual output/artifact/reduced/rq3 \
    --file rq3_ablation_results.md \
    --file rq3_ablation_summary.csv \
    --file rq3_ablation_summary.json
fi

uv run --package Gleaner python scripts/artifact/print_reduced_tables.py rq3
