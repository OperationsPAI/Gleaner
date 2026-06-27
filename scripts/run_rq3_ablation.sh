#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

uv run python scripts/artifact/rq3_ablation.py "$@"

if [[ -d artifact_expected/reduced/rq3 ]]; then
  uv run python scripts/compare_expected.py \
    --expected artifact_expected/reduced/rq3 \
    --actual output/artifact/reduced/rq3 \
    --file rq3_ablation_results.md \
    --file rq3_ablation_summary.csv \
    --file rq3_ablation_summary.json
fi
