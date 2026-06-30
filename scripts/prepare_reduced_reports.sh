#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DATASET="${GLEANER_REDUCED_DATASET:-gleaner_lite}"
RATES_CSV="${GLEANER_REDUCED_RATES:-0.01,0.1}"
MODES_CSV="${GLEANER_REDUCED_MODES:-offline}"
ONLINE_RATES_CSV="${GLEANER_REDUCED_ONLINE_RATES:-0.05}"
ONLINE_MODES_CSV="${GLEANER_REDUCED_ONLINE_MODES:-online}"
ONLINE_SAMPLERS_CSV="${GLEANER_REDUCED_ONLINE_SAMPLERS:-gleaner,gleaner_wl_kernel}"
CPUS="${GLEANER_REDUCED_CPUS:-}"
CLEAR_FLAG="${GLEANER_REDUCED_CLEAR:+--clear}"
SKIP_FLAG="${GLEANER_REDUCED_NO_SKIP:-0}"
SAMPLE_DATAPACKS="${GLEANER_REDUCED_SAMPLE_DATAPACKS:-}"

if [[ -n "${GLEANER_PYTHON:-}" ]]; then
  read -r -a PY <<< "${GLEANER_PYTHON}"
elif [[ -x .venv/bin/python ]]; then
  PY=(.venv/bin/python)
else
  PY=(uv run --all-packages python)
fi

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

IFS=',' read -r -a RATES <<< "${RATES_CSV}"
IFS=',' read -r -a MODES <<< "${MODES_CSV}"
IFS=',' read -r -a ONLINE_RATES <<< "${ONLINE_RATES_CSV}"
IFS=',' read -r -a ONLINE_MODES <<< "${ONLINE_MODES_CSV}"
IFS=',' read -r -a ONLINE_SAMPLERS <<< "${ONLINE_SAMPLERS_CSV}"

rate_args=()
report_rate_args=()
for rate in "${RATES[@]}"; do
  rate_args+=(--rate "$rate")
  report_rate_args+=(--sampling-rates "$rate")
done
online_rate_args=()
for rate in "${ONLINE_RATES[@]}"; do
  online_rate_args+=(--rate "$rate")
  report_rate_args+=(--sampling-rates "$rate")
done
mode_args=()
report_mode_args=()
for mode in "${MODES[@]}"; do
  mode_args+=(--mode "$mode")
  report_mode_args+=(--modes "$mode")
done
online_mode_args=()
for mode in "${ONLINE_MODES[@]}"; do
  online_mode_args+=(--mode "$mode")
  report_mode_args+=(--modes "$mode")
done
cpu_args=(--use-cpus "${CPUS}")
skip_args=()
if [[ "${SKIP_FLAG}" == "1" ]]; then skip_args+=(--no-skip-finished); fi
sample_args=()
if [[ -n "${SAMPLE_DATAPACKS}" ]]; then sample_args+=(--sample-datapacks "${SAMPLE_DATAPACKS}"); fi

if [[ ! -f "data/rcabench-platform-v2/meta/${DATASET}/index.parquet" ]]; then
  echo "[reduced:reports] ERROR: missing reduced dataset meta: data/rcabench-platform-v2/meta/${DATASET}/index.parquet" >&2
  echo "[reduced:reports] Build it first with: ${PY[*]} scripts/data/make_gleaner_lite.py" >&2
  exit 1
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
report_sampler_args=()
for sampler in "${samplers[@]}"; do
  sampler_args+=(--sampler "$sampler")
  report_sampler_args+=(--samplers "$sampler")
done
online_sampler_args=()
for sampler in "${ONLINE_SAMPLERS[@]}"; do
  online_sampler_args+=(--sampler "$sampler")
  report_sampler_args+=(--samplers "$sampler")
done

echo "[reduced:reports] running offline sampler experiments on dataset=${DATASET} with cpus=${CPUS}"
"${PY[@]}" scripts/full/platform_cli.py sample batch \
  -d "${DATASET}" \
  "${sampler_args[@]}" \
  "${rate_args[@]}" "${mode_args[@]}" "${cpu_args[@]}" "${sample_args[@]}" ${CLEAR_FLAG:-} "${skip_args[@]}"

echo "[reduced:reports] running minimal online sampler experiments for RQ4 on dataset=${DATASET} with cpus=${CPUS}"
"${PY[@]}" scripts/full/platform_cli.py sample batch \
  -d "${DATASET}" \
  "${online_sampler_args[@]}" \
  "${online_rate_args[@]}" "${online_mode_args[@]}" "${cpu_args[@]}" "${sample_args[@]}" ${CLEAR_FLAG:-} "${skip_args[@]}"

echo "[reduced:reports] generating sampler performance report for dataset=${DATASET}"
"${PY[@]}" scripts/full/platform_cli.py sample perf-report \
  -d "${DATASET}" \
  "${report_sampler_args[@]}" \
  "${report_rate_args[@]}" "${report_mode_args[@]}" --warn-missing
