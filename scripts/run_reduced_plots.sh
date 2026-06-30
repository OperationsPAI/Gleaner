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

"${PY[@]}" scripts/artifact/plot_reduced_rq_figures.py "$@"

required_pngs=(
  output/artifact/reduced/figures/rq1_sampling_quality_metrics.png
  output/artifact/reduced/figures/rq2_ablation_metrics.png
  output/artifact/reduced/figures/rq3_rca_effectiveness_ac.png
  output/artifact/reduced/figures/rq4_efficiency_metrics.png
)
for png in "${required_pngs[@]}"; do
  test -s "$png"
done

test -s output/artifact/reduced/REPORT.md

echo "[plots] reduced plot/report generation completed"
