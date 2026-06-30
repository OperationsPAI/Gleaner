#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

stage() { printf '\n[reduced] == %s ==\n' "$1"; }

wait_stage() {
  local name="$1"
  local pid="$2"
  local log_file="$3"

  if wait "${pid}"; then
    printf '[reduced] %s completed; log: %s\n' "${name}" "${log_file}"
    return 0
  fi

  printf '[reduced] ERROR: %s failed; tail of %s follows:\n' "${name}" "${log_file}" >&2
  tail -n 80 "${log_file}" >&2 || true
  return 1
}

stage "smoke test"
bash scripts/smoke_test.sh

stage "prepare live reports and RQ1-B in parallel"
mkdir -p output/artifact/reduced/logs
PREP_LOG="output/artifact/reduced/logs/prepare_reduced_reports.log"
RQ1B_LOG="output/artifact/reduced/logs/rq1b_cross_system.log"

bash scripts/prepare_reduced_reports.sh >"${PREP_LOG}" 2>&1 &
prep_pid=$!
bash scripts/run_rq1b_cross_system.sh >"${RQ1B_LOG}" 2>&1 &
rq1b_pid=$!

failed=0
wait_stage "prepare live gleaner_lite sampler reports" "${prep_pid}" "${PREP_LOG}" || failed=1
wait_stage "RQ1-B Dataset B cross-system evidence" "${rq1b_pid}" "${RQ1B_LOG}" || failed=1
if [[ "${failed}" != "0" ]]; then
  exit 1
fi

stage "RQ1 sampling quality"
bash scripts/run_rq1_sampling_quality.sh
stage "RQ2 ablation"
bash scripts/run_rq2_ablation.sh
stage "RQ3 downstream RCA effectiveness"
bash scripts/run_rq3_rca_effectiveness.sh
stage "RQ4 efficiency"
bash scripts/run_rq4_efficiency.sh
stage "plots and final report"
bash scripts/run_reduced_plots.sh
printf '\n[reduced] all reduced RQ scripts and plots completed\n'
