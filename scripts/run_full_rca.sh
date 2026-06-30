#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

DATASET_A="${GLEANER_FULL_DATASET_A:-gleaner}"
RATES_CSV="${GLEANER_FULL_RCA_RATES:-0.01,0.1}"
MODES_CSV="${GLEANER_FULL_MODES:-offline}"
CPUS="${GLEANER_FULL_CPUS:-}"
SAMPLE_DATAPACKS="${GLEANER_FULL_SAMPLE_DATAPACKS:-}"
CLEAR_FLAG="${GLEANER_FULL_CLEAR:+--clear}"
SKIP_FLAG="${GLEANER_FULL_NO_SKIP:-0}"

IFS=',' read -r -a RATES <<< "${RATES_CSV}"
IFS=',' read -r -a MODES <<< "${MODES_CSV}"
rate_args=(); for rate in "${RATES[@]}"; do rate_args+=(--sampling-rate "$rate"); done
mode_args=(); for mode in "${MODES[@]}"; do mode_args+=(--sampling-mode "$mode"); done
cpu_args=(); [[ -n "${CPUS}" ]] && cpu_args+=(--use-cpus "${CPUS}")
sample_args=(); [[ -n "${SAMPLE_DATAPACKS}" ]] && sample_args+=(--sample "${SAMPLE_DATAPACKS}")
skip_args=(); [[ "${SKIP_FLAG}" == "1" ]] && skip_args+=(--no-skip-finished)

printf '\n[full:rca] == preflight ==\n'
test -f "data/rcabench-platform-v2/meta/${DATASET_A}/index.parquet" || { echo "[full:rca] ERROR: missing Dataset A meta for ${DATASET_A}" >&2; exit 1; }

printf '\n[full:rca] == unsampled RCA ==\n'
uv run --all-packages python scripts/full/platform_cli.py eval batch \
  -d "${DATASET_A}" \
  -a microrca -a shapleyiq -a nezha \
  "${cpu_args[@]}" "${sample_args[@]}" ${CLEAR_FLAG:-} "${skip_args[@]}"

printf '\n[full:rca] == sampled RCA ==\n'
uv run --all-packages python scripts/full/platform_cli.py eval batch \
  -d "${DATASET_A}" \
  -a microrca -a shapleyiq -a nezha \
  --include-sampled \
  -s gleaner -s gleaner_no_ad -s gleaner_no_dpp \
  -s gleaner_no_logs -s gleaner_no_logs_no_ad -s gleaner_pure_diversity \
  -s gleaner_top_score -s gleaner_anomaly_pure_diversity -s gleaner_wl_kernel \
  -s random -s tracepicker -s trastrainer -s trastrainer_no_metrics \
  -s sifter -s sieve \
  "${rate_args[@]}" "${mode_args[@]}" "${cpu_args[@]}" "${sample_args[@]}" ${CLEAR_FLAG:-} "${skip_args[@]}"

printf '\n[full:rca] == performance report ==\n'
uv run --all-packages python scripts/full/platform_cli.py eval perf-report "${DATASET_A}" --include-sampled --warn-missing

echo "[full:rca] RCA phase completed"
