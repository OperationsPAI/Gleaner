#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DEFAULT_SHAPLEYIQ_MICRORCA_PATHS=(
  "output/artifact/reduced/rq2/rca/shapleyiq_microrca/sampler.grouped.perf.parquet"
  "output/rca/shapleyiq_microrca/sampler.grouped.perf.parquet"
  "output/rca/shapleyiq/sampler.grouped.perf.parquet"
  "data/artifact/reduced/rq2/shapleyiq_microrca/sampler.grouped.perf.parquet"
)
DEFAULT_NEZHA_PATHS=(
  "output/artifact/reduced/rq2/rca/nezha/sampler.grouped.perf.parquet"
  "output/rca/nezha/sampler.grouped.perf.parquet"
  "data/artifact/reduced/rq2/nezha/sampler.grouped.perf.parquet"
)

shapleyiq_microrca_path="${RQ2_SHAPLEYIQ_MICRORCA_PARQUET:-}"
nezha_path="${RQ2_NEZHA_PARQUET:-}"
has_shapleyiq_arg=0
has_nezha_arg=0

args=("$@")
for ((i = 0; i < ${#args[@]}; i++)); do
  case "${args[$i]}" in
    --shapleyiq-microrca-parquet)
      has_shapleyiq_arg=1
      if (( i + 1 < ${#args[@]} )); then
        shapleyiq_microrca_path="${args[$((i + 1))]}"
      fi
      ;;
    --shapleyiq-microrca-parquet=*)
      has_shapleyiq_arg=1
      shapleyiq_microrca_path="${args[$i]#*=}"
      ;;
    --nezha-parquet)
      has_nezha_arg=1
      if (( i + 1 < ${#args[@]} )); then
        nezha_path="${args[$((i + 1))]}"
      fi
      ;;
    --nezha-parquet=*)
      has_nezha_arg=1
      nezha_path="${args[$i]#*=}"
      ;;
  esac
done

find_first_existing() {
  local candidate
  for candidate in "$@"; do
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

if [[ -z "$shapleyiq_microrca_path" ]]; then
  shapleyiq_microrca_path="$(find_first_existing "${DEFAULT_SHAPLEYIQ_MICRORCA_PATHS[@]}" || true)"
fi
if [[ -z "$nezha_path" ]]; then
  nezha_path="$(find_first_existing "${DEFAULT_NEZHA_PATHS[@]}" || true)"
fi

if [[ -z "$shapleyiq_microrca_path" || -z "$nezha_path" ]]; then
  {
    echo "[rq2] ERROR: current artifact is missing RQ2 RCA reduced evidence."
    echo "[rq2] Missing required RCA parquet input(s); refusing to report a successful RQ2 run."
    echo "[rq2] Default ShapleyIQ/MicroRCA lookup paths:"
    printf '  - %s\n' "${DEFAULT_SHAPLEYIQ_MICRORCA_PATHS[@]}"
    echo "[rq2] Default Nezha lookup paths:"
    printf '  - %s\n' "${DEFAULT_NEZHA_PATHS[@]}"
    echo "[rq2] Provide inputs with CLI arguments:"
    echo "  bash scripts/run_rq2_rca_effectiveness.sh --shapleyiq-microrca-parquet PATH --nezha-parquet PATH"
    echo "[rq2] Or set environment variables:"
    echo "  RQ2_SHAPLEYIQ_MICRORCA_PARQUET=PATH RQ2_NEZHA_PARQUET=PATH bash scripts/run_rq2_rca_effectiveness.sh"
  } >&2
  exit 1
fi

run_args=("$@")
if [[ "$has_shapleyiq_arg" -eq 0 ]]; then
  run_args+=("--shapleyiq-microrca-parquet" "$shapleyiq_microrca_path")
fi
if [[ "$has_nezha_arg" -eq 0 ]]; then
  run_args+=("--nezha-parquet" "$nezha_path")
fi

uv run python scripts/artifact/rq2_rca_effectiveness.py "${run_args[@]}"

if [[ -d artifact_expected/reduced/rq2 ]]; then
  uv run python scripts/compare_expected.py \
    --expected artifact_expected/reduced/rq2 \
    --actual output/artifact/reduced/rq2 \
    --file rq2_rca_effectiveness_results.md \
    --file rq2_rca_effectiveness_summary.csv \
    --file rq2_rca_effectiveness_summary.json
fi
