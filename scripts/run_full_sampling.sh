#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

DATASET_A="${GLEANER_FULL_DATASET_A:-gleaner}"
DATASET_B="${GLEANER_FULL_DATASET_B:-tracepicker}"
RATES_CSV="${GLEANER_FULL_RATES:-0.001,0.01,0.025,0.05,0.075,0.1}"
MODES_CSV="${GLEANER_FULL_MODES:-offline,online}"
CPUS="${GLEANER_FULL_CPUS:-}"
SAMPLE_DATAPACKS="${GLEANER_FULL_SAMPLE_DATAPACKS:-}"
CLEAR_FLAG="${GLEANER_FULL_CLEAR:+--clear}"
SKIP_FLAG="${GLEANER_FULL_NO_SKIP:-0}"
TRACEPICKER_ENV="${GLEANER_TRACEPICKER_ENV:-third_party/TracePicker/.venv}"
TRASTRAINER_ENV="${GLEANER_TRASTRAINER_ENV:-third_party/TraStrainer/.venv}"

IFS=',' read -r -a RATES <<< "${RATES_CSV}"
IFS=',' read -r -a MODES <<< "${MODES_CSV}"

stage() { printf '\n[full:sampling] == %s ==\n' "$1"; }
require_file() { [[ -f "$1" ]] || { echo "[full:sampling] ERROR: missing required file: $1" >&2; exit 1; }; }
require_dir() { [[ -d "$1" ]] || { echo "[full:sampling] ERROR: missing required directory: $1" >&2; exit 1; }; }

rate_args=()
report_rate_args=()
for rate in "${RATES[@]}"; do
  rate_args+=(--rate "$rate")
  report_rate_args+=(--sampling-rates "$rate")
done
mode_args=()
report_mode_args=()
for mode in "${MODES[@]}"; do
  mode_args+=(--mode "$mode")
  report_mode_args+=(--modes "$mode")
done
cpu_args=()
if [[ -n "${CPUS}" ]]; then cpu_args+=(--use-cpus "${CPUS}"); fi
sample_args=()
if [[ -n "${SAMPLE_DATAPACKS}" ]]; then sample_args+=(--sample-datapacks "${SAMPLE_DATAPACKS}"); fi
skip_args=()
if [[ "${SKIP_FLAG}" == "1" ]]; then skip_args+=(--no-skip-finished); fi

stage "preflight"
require_file "data/rcabench-platform-v2/meta/${DATASET_A}/index.parquet"
require_dir "data/rcabench-platform-v2/data/${DATASET_A}"
require_file "data/rcabench-platform-v2/meta/${DATASET_B}/index.parquet"
require_dir "data/rcabench-platform-v2/data/${DATASET_B}"
if [[ ! -x "${TRACEPICKER_ENV}/bin/python" ]]; then
  echo "[full:sampling] ERROR: TracePicker env not found at ${TRACEPICKER_ENV}/bin/python" >&2
  echo "[full:sampling] Build it with: GLEANER_SETUP_TRACEPICKER_ENV=1 bash scripts/full/setup_baseline_envs.sh" >&2
  exit 1
fi
if [[ ! -x "${TRASTRAINER_ENV}/bin/python" ]]; then
  echo "[full:sampling] ERROR: TraStrainer env not found at ${TRASTRAINER_ENV}/bin/python" >&2
  echo "[full:sampling] Build it with: GLEANER_SETUP_TRASTRAINER_ENV=1 bash scripts/full/setup_baseline_envs.sh" >&2
  exit 1
fi

stage "Dataset A Gleaner variants and random baseline"
uv run --all-packages python scripts/full/platform_cli.py sample batch \
  -d "${DATASET_A}" \
  -s gleaner \
  -s gleaner_no_ad \
  -s gleaner_no_dpp \
  -s gleaner_no_logs \
  -s gleaner_no_logs_no_ad \
  -s gleaner_pure_diversity \
  -s gleaner_top_score \
  -s gleaner_anomaly_pure_diversity \
  -s gleaner_wl_kernel \
  -s random \
  "${rate_args[@]}" "${mode_args[@]}" "${cpu_args[@]}" "${sample_args[@]}" ${CLEAR_FLAG:-} "${skip_args[@]}"

stage "Dataset A TraStrainer/Sifter/Sieve isolated baselines"
"${TRASTRAINER_ENV}/bin/python" scripts/full/platform_cli.py sample batch \
  -d "${DATASET_A}" \
  -s trastrainer \
  -s trastrainer_no_metrics \
  -s sifter \
  -s sieve \
  "${rate_args[@]}" "${mode_args[@]}" "${cpu_args[@]}" "${sample_args[@]}" ${CLEAR_FLAG:-} "${skip_args[@]}"

stage "Dataset B Gleaner and random cross-system baselines"
uv run --all-packages python scripts/full/platform_cli.py sample batch \
  -d "${DATASET_B}" \
  -s gleaner_no_logs_no_ad \
  -s random \
  "${rate_args[@]}" "${mode_args[@]}" "${cpu_args[@]}" "${sample_args[@]}" ${CLEAR_FLAG:-} "${skip_args[@]}"

stage "Dataset B TraStrainer/Sifter/Sieve isolated baselines"
"${TRASTRAINER_ENV}/bin/python" scripts/full/platform_cli.py sample batch \
  -d "${DATASET_B}" \
  -s trastrainer_no_metrics \
  -s sifter \
  -s sieve \
  "${rate_args[@]}" "${mode_args[@]}" "${cpu_args[@]}" "${sample_args[@]}" ${CLEAR_FLAG:-} "${skip_args[@]}"

stage "Dataset A/B TracePicker isolated sampler"
(
  cd third_party/TracePicker
  export DATA_ROOT="${ROOT}/data/rcabench-platform-v2"
  export OUTPUT_ROOT="${ROOT}/output/rcabench-platform-v2"
  "${ROOT}/${TRACEPICKER_ENV}/bin/python" "${ROOT}/scripts/full/tracepicker_platform_sample.py" batch \
    -d "${DATASET_A}" -d "${DATASET_B}" "${rate_args[@]}" "${mode_args[@]}" "${sample_args[@]}" ${CLEAR_FLAG:-} "${skip_args[@]}"
)

stage "sampler performance reports"
uv run --all-packages python scripts/full/platform_cli.py sample perf-report \
  -d "${DATASET_A}" -d "${DATASET_B}" \
  --samplers gleaner --samplers gleaner_no_ad --samplers gleaner_no_dpp \
  --samplers gleaner_no_logs --samplers gleaner_no_logs_no_ad --samplers gleaner_pure_diversity \
  --samplers gleaner_top_score --samplers gleaner_anomaly_pure_diversity --samplers gleaner_wl_kernel \
  --samplers random --samplers trastrainer --samplers trastrainer_no_metrics \
  --samplers sifter --samplers sieve \
  "${report_rate_args[@]}" "${report_mode_args[@]}" --warn-missing
(
  cd third_party/TracePicker
  export DATA_ROOT="${ROOT}/data/rcabench-platform-v2"
  export OUTPUT_ROOT="${ROOT}/output/rcabench-platform-v2"
  "${ROOT}/${TRACEPICKER_ENV}/bin/python" "${ROOT}/scripts/full/tracepicker_platform_sample.py" perf-report \
    -d "${DATASET_A}" -d "${DATASET_B}" "${rate_args[@]}" "${mode_args[@]}"
)

echo "[full:sampling] sampling phase completed"
