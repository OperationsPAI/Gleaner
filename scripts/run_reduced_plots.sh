#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

uv run python scripts/artifact/plot_reduced_rq_figures.py "$@"

required_pngs=(
  output/artifact/reduced/figures/rq1_sampling_quality_metrics.png
  output/artifact/reduced/figures/rq2_rca_effectiveness_ac.png
  output/artifact/reduced/figures/rq3_ablation_metrics.png
  output/artifact/reduced/figures/rq4_efficiency_metrics.png
)
for png in "${required_pngs[@]}"; do
  test -s "$png"
done

test -s output/artifact/reduced/REPORT.md

if [[ -d artifact_expected/reduced/figures ]]; then
  compare_dir="$(mktemp -d)"
  trap 'rm -rf "$compare_dir"' EXIT
  mkdir -p "$compare_dir/expected_plots" "$compare_dir/actual_plots" "$compare_dir/expected_report" "$compare_dir/actual_report"
  comparable_files=(
    rq1_sampling_quality_plot_data.csv
    rq2_rca_effectiveness_plot_data.csv
    rq3_ablation_plot_data.csv
    rq4_efficiency_plot_data.csv
    plot_data_summary.csv
    plot_manifest.json
  )
  for file in "${comparable_files[@]}"; do
    cp "artifact_expected/reduced/figures/$file" "$compare_dir/expected_plots/$file"
    cp "output/artifact/reduced/figures/$file" "$compare_dir/actual_plots/$file"
  done
  uv run python scripts/compare_expected.py \
    --expected "$compare_dir/expected_plots" \
    --actual "$compare_dir/actual_plots" \
    --file rq1_sampling_quality_plot_data.csv \
    --file rq2_rca_effectiveness_plot_data.csv \
    --file rq3_ablation_plot_data.csv \
    --file rq4_efficiency_plot_data.csv \
    --file plot_data_summary.csv \
    --file plot_manifest.json

  cp artifact_expected/reduced/figures/REPORT.md "$compare_dir/expected_report/REPORT.md"
  cp output/artifact/reduced/REPORT.md "$compare_dir/actual_report/REPORT.md"
  uv run python scripts/compare_expected.py \
    --expected "$compare_dir/expected_report" \
    --actual "$compare_dir/actual_report" \
    --file REPORT.md
fi

echo "[plots] reduced plot/report generation completed"
