#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
uv run --package Gleaner python scripts/artifact/rq1b_tracepicker_cross_system.py "$@"
test -s output/artifact/reduced/rq1_cross_system/rq1b_tracepicker_cross_system.png
if [[ -d artifact_expected/reduced/rq1_cross_system ]]; then
  compare_dir="$(mktemp -d)"
  trap 'rm -rf "$compare_dir"' EXIT
  mkdir -p "$compare_dir/expected" "$compare_dir/actual"
  for file in rq1b_tracepicker_cross_system_results.md rq1b_tracepicker_cross_system_summary.csv rq1b_tracepicker_cross_system_summary.json; do
    cp "artifact_expected/reduced/rq1_cross_system/$file" "$compare_dir/expected/$file"
    cp "output/artifact/reduced/rq1_cross_system/$file" "$compare_dir/actual/$file"
  done
  uv run --package Gleaner python scripts/compare_expected.py \
    --expected "$compare_dir/expected" \
    --actual "$compare_dir/actual" \
    --file rq1b_tracepicker_cross_system_results.md \
    --file rq1b_tracepicker_cross_system_summary.csv \
    --file rq1b_tracepicker_cross_system_summary.json
fi
