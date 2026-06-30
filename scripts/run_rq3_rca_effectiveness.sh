#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -n "${GLEANER_PYTHON:-}" ]]; then
  read -r -a PY <<< "${GLEANER_PYTHON}"
elif [[ -x .venv/bin/python ]]; then
  PY=(.venv/bin/python)
else
  PY=(uv run --all-packages python)
fi

DATASET="${GLEANER_REDUCED_DATASET:-gleaner_lite}"
RATES_CSV="${GLEANER_REDUCED_RATES:-}"
MODES_CSV="${GLEANER_REDUCED_MODES:-}"
CPUS="${GLEANER_REDUCED_CPUS:-}"
CLEAR_FLAG="${GLEANER_REDUCED_RCA_CLEAR:+--clear}"
SKIP_FLAG="${GLEANER_REDUCED_RCA_NO_SKIP:-0}"
SAMPLE_DATAPACKS="${GLEANER_REDUCED_RCA_SAMPLE_DATAPACKS:-}"

if [[ -z "${CPUS}" ]]; then
  CPUS="$("${PY[@]}" - <<'PY'
import os
try:
    available = len(os.sched_getaffinity(0))
except AttributeError:
    available = os.cpu_count() or 1
print(max(1, available // 2))
PY
)"
fi

rate_args=()
summary_rate_args=()
mode_args=()
summary_mode_args=()
if [[ -n "${RATES_CSV}" ]]; then
  IFS=',' read -r -a RATES <<< "${RATES_CSV}"
  for rate in "${RATES[@]}"; do
    rate_args+=(--sampling-rate "$rate")
    summary_rate_args+=(--sampling-rate "$rate")
  done
fi
if [[ -n "${MODES_CSV}" ]]; then
  IFS=',' read -r -a MODES <<< "${MODES_CSV}"
  for mode in "${MODES[@]}"; do
    mode_args+=(--sampling-mode "$mode")
    summary_mode_args+=(--sampling-mode "$mode")
  done
fi
skip_args=()
if [[ "${SKIP_FLAG}" == "1" ]]; then skip_args+=(--no-skip-finished); fi
sample_args=()
if [[ -n "${SAMPLE_DATAPACKS}" ]]; then sample_args+=(--sample "${SAMPLE_DATAPACKS}"); fi

if [[ ! -f "output/rcabench-platform-v2/sampler_reports/${DATASET}/aggregated_perf.parquet" ]]; then
  bash scripts/prepare_reduced_reports.sh
fi

samplers=(
  gleaner
  gleaner_no_logs
  gleaner_no_ad
  gleaner_no_logs_no_ad
  gleaner_wl_kernel
  gleaner_pure_diversity
  gleaner_top_score
  gleaner_no_dpp
  gleaner_anomaly_pure_diversity
  random
)
sampler_args=()
for sampler in "${samplers[@]}"; do
  sampler_args+=(--sampler "$sampler")
done

algorithms=(microrca shapleyiq nezha)
algorithm_args=()
for algorithm in "${algorithms[@]}"; do
  algorithm_args+=(--algorithms "$algorithm")
done

echo "[rq3] running unsampled full-input RCA on dataset=${DATASET} with cpus=${CPUS}"
"${PY[@]}" scripts/full/platform_cli.py eval batch \
  -d "${DATASET}" \
  "${algorithm_args[@]}" \
  "${sample_args[@]}" \
  --use-cpus "${CPUS}" ${CLEAR_FLAG:-} "${skip_args[@]}"

echo "[rq3] running live sampled RCA on dataset=${DATASET} with cpus=${CPUS}"
"${PY[@]}" scripts/full/platform_cli.py eval batch \
  -d "${DATASET}" \
  "${algorithm_args[@]}" \
  --include-sampled \
  "${sample_args[@]}" \
  "${sampler_args[@]}" \
  "${rate_args[@]}" "${mode_args[@]}" \
  --use-cpus "${CPUS}" ${CLEAR_FLAG:-} "${skip_args[@]}"

echo "[rq3] generating live RCA performance report for dataset=${DATASET}"
"${PY[@]}" scripts/full/platform_cli.py eval perf-report "${DATASET}" --include-sampled --warn-missing

rca_parquet="output/rcabench-platform-v2/meta/${DATASET}/sampler.grouped.perf.parquet"
"${PY[@]}" scripts/artifact/rq3_rca_effectiveness.py \
  --shapleyiq-microrca-parquet "${rca_parquet}" \
  --nezha-parquet "${rca_parquet}" \
  "${summary_rate_args[@]}" "${summary_mode_args[@]}" "$@"

"${PY[@]}" scripts/artifact/print_reduced_tables.py rq3
