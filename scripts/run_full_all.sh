#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

cat <<'MSG'
[full] Gleaner full paper reproduction setting
[full] Config: configs/full/experiment_setting.yaml
[full] Scope:
[full]   - Dataset A full Gleaner/RCAbench sampler quality, ablations, RCA, efficiency
[full]   - Dataset B TracePicker cross-system evaluation over 5 systems
[full]   - Baseline samplers: random, TracePicker, TraStrainer, Sifter, Sieve
[full]   - RCA algorithms: MicroRCA, ShapleyIQ, Nezha
[full]   - Sampler rates: 0.1%, 1%, 2.5%, 5%, 7.5%, 10%; RCA rates: 1%, 10%
[full]   - Gleaner ablations: Table 5 variants only
[full]   - Paper figures/tables: RQ1 Fig.4/Fig.5, RQ2 Fig.6/Fig.7/Table5, RQ3 Table6/Table7, RQ4 Table8
[full] Expected runtime: long-running; depending on CPU count and baseline environments, this may take multiple days.
MSG

if [[ -n "${GLEANER_FULL_ALLOW_PLACEHOLDER:-}" ]]; then
  echo "[full] ERROR: GLEANER_FULL_ALLOW_PLACEHOLDER is forbidden; full mode must not fake success." >&2
  exit 2
fi

if [[ "${GLEANER_RUN_FULL:-0}" != "1" ]]; then
  cat <<'MSG'
[full] Refusing to start long-running full reproduction by default.
[full] Use the reduced AE path for fast validation:
[full]   bash scripts/run_reduced_all.sh
[full] To intentionally launch the full pipeline:
[full]   GLEANER_RUN_FULL=1 bash scripts/run_full_all.sh
[full] If TracePicker's Python 3.12 env is missing, first run or combine with:
[full]   GLEANER_SETUP_TRACEPICKER_ENV=1 bash scripts/full/setup_baseline_envs.sh
MSG
  exit 2
fi

mkdir -p output/full/figures output/full/tables

printf '\n[full] == environment preflight ==\n'
GLEANER_SYNC_BASELINE_WORKSPACE=1 bash scripts/full/setup_baseline_envs.sh

printf '\n[full] == sampling ==\n'
bash scripts/run_full_sampling.sh

printf '\n[full] == RCA ==\n'
bash scripts/run_full_rca.sh

printf '\n[full] == figures and tables ==\n'
bash scripts/run_full_figures.sh

printf '\n[full] == postcondition validation ==\n'
uv run --package Gleaner python scripts/full/validate_full_outputs.py \
  --dataset-a "${GLEANER_FULL_DATASET_A:-gleaner}" \
  --dataset-b "${GLEANER_FULL_DATASET_B:-tracepicker}" \
  --rates "${GLEANER_FULL_RATES:-0.001,0.01,0.025,0.05,0.075,0.1}" \
  --rca-rates "${GLEANER_FULL_RCA_RATES:-0.01,0.1}" \
  --modes "${GLEANER_FULL_MODES:-offline,online}"

echo "[full] full reproduction pipeline finished"
