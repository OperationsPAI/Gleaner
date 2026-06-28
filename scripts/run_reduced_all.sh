#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

stage() { printf '\n[reduced] == %s ==\n' "$1"; }

stage "smoke test"
bash scripts/smoke_test.sh
stage "prepare fault-balanced reduced20 sampler reports"
bash scripts/prepare_reduced_reports.sh
stage "RQ1 sampling quality"
bash scripts/run_rq1_sampling_quality.sh
stage "RQ1-B Dataset B cross-system evidence"
bash scripts/run_rq1b_cross_system.sh
stage "RQ2 downstream RCA effectiveness"
bash scripts/run_rq2_rca_effectiveness.sh
stage "RQ3 ablation"
bash scripts/run_rq3_ablation.sh
stage "RQ4 efficiency"
bash scripts/run_rq4_efficiency.sh
stage "plots and final report"
bash scripts/run_reduced_plots.sh
printf '\n[reduced] all reduced RQ scripts and plots completed\n'
