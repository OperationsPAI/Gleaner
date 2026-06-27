#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

uv run python scripts/artifact/rq1_sampling_quality.py "$@"

if [[ -d artifact_expected/reduced/rq1 ]]; then
  uv run python scripts/compare_expected.py \
    --expected artifact_expected/reduced/rq1 \
    --actual output/artifact/reduced/rq1 \
    --file rq1_sampling_quality_results.md \
    --file rq1_sampling_quality_summary.csv \
    --file rq1_sampling_quality_summary.json
fi
