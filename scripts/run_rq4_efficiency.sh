#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

uv run python scripts/artifact/rq4_efficiency.py "$@"

if [[ -d artifact_expected/reduced/rq4 ]]; then
  uv run python scripts/compare_expected.py \
    --expected artifact_expected/reduced/rq4 \
    --actual output/artifact/reduced/rq4 \
    --file rq4_efficiency_results.md \
    --file rq4_efficiency_summary.csv \
    --file rq4_efficiency_summary.json
fi
