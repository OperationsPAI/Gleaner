#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
bash scripts/smoke_test.sh
bash scripts/run_rq1_sampling_quality.sh
bash scripts/run_rq2_rca_effectiveness.sh
bash scripts/run_rq3_ablation.sh
bash scripts/run_rq4_efficiency.sh
bash scripts/run_reduced_plots.sh
echo "[reduced] all reduced RQ scripts and plots completed"
