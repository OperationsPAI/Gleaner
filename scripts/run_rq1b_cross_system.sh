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

DATASET="${GLEANER_RQ1B_DATASET:-tracepicker_lite}"
RATES_CSV="${GLEANER_RQ1B_RATES:-0.1}"
MODE="${GLEANER_RQ1B_MODE:-offline}"
CPUS="${GLEANER_REDUCED_CPUS:-}"
CLEAR_FLAG="${GLEANER_RQ1B_CLEAR:+--clear}"
SKIP_FLAG="${GLEANER_RQ1B_NO_SKIP:-0}"
SYSTEMS_CSV="${GLEANER_RQ1B_SYSTEMS:-trainticket,media}"
SAMPLERS_CSV="${GLEANER_RQ1B_SAMPLERS:-gleaner_no_logs_no_ad}"

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
IFS=',' read -r -a SAMPLERS <<< "${SAMPLERS_CSV}"
batch_rate_args=(); report_rate_args=(); summary_rate_args=()
for rate in "${RATES[@]}"; do
  batch_rate_args+=(--rate "$rate")
  report_rate_args+=(--sampling-rates "$rate")
  summary_rate_args+=(--sampling-rate "$rate")
done
batch_sampler_args=(); report_sampler_args=(); summary_sampler_args=()
for sampler in "${SAMPLERS[@]}"; do
  batch_sampler_args+=(--sampler "$sampler")
  report_sampler_args+=(--samplers "$sampler")
  summary_sampler_args+=(--sampler "$sampler")
done
batch_mode_args=(--mode "${MODE}")
IFS=',' read -r -a SYSTEMS <<< "${SYSTEMS_CSV}"
summary_system_args=()
for system in "${SYSTEMS[@]}"; do
  summary_system_args+=(--system "$system")
done
skip_args=()
if [[ "${SKIP_FLAG}" == "1" ]]; then skip_args+=(--no-skip-finished); fi

echo "[rq1b] running Dataset B sampling for paper metric Trace Pattern Coverage: dataset=${DATASET} systems=${SYSTEMS_CSV} samplers=${SAMPLERS_CSV} rates=${RATES_CSV}"
"${PY[@]}" scripts/full/platform_cli.py sample batch \
  -d "${DATASET}" \
  "${batch_sampler_args[@]}" \
  "${batch_rate_args[@]}" \
  "${batch_mode_args[@]}" \
  --use-cpus "${CPUS}" \
  ${CLEAR_FLAG:-} \
  "${skip_args[@]}" \
  --no-ignore-exceptions

echo "[rq1b] generating Dataset B sampler performance report"
"${PY[@]}" scripts/full/platform_cli.py sample perf-report \
  -d "${DATASET}" \
  "${report_sampler_args[@]}" \
  "${report_rate_args[@]}" \
  --modes "${MODE}" \
  --warn-missing

"${PY[@]}" scripts/artifact/rq1b_tracepicker_cross_system.py \
  --input-parquet "output/rcabench-platform-v2/sampler_reports/${DATASET}/detailed_perf.parquet" \
  --mode "${MODE}" \
  "${summary_sampler_args[@]}" \
  "${summary_rate_args[@]}" \
  "${summary_system_args[@]}" \
  "$@"

test -s output/artifact/reduced/rq1_cross_system/rq1b_tracepicker_cross_system.png
