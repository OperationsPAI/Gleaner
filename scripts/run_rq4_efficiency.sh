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

DATASET="${GLEANER_REDUCED_DATASET:-gleaner_lite}"
REPORT_DIR="output/rcabench-platform-v2/sampler_reports/${DATASET}"

needs_reports=0
if [[ ! -f "${REPORT_DIR}/aggregated_perf.parquet" ]]; then
  needs_reports=1
else
  if ! "${PY[@]}" - "${REPORT_DIR}/aggregated_perf.parquet" <<'PY'
from pathlib import Path
import sys
import polars as pl
p = Path(sys.argv[1])
df = pl.read_parquet(p)
needed = df.filter(
    pl.col("sampler").is_in(["gleaner", "gleaner_wl_kernel"])
    & ((pl.col("sampling_rate") - 0.05).abs() < 1e-12)
    & (pl.col("mode") == "online")
)
seen = set(needed.get_column("sampler").to_list()) if needed.height else set()
raise SystemExit(0 if {"gleaner", "gleaner_wl_kernel"}.issubset(seen) else 1)
PY
  then
    needs_reports=1
  fi
fi

if [[ "${needs_reports}" == "1" ]]; then
  bash scripts/prepare_reduced_reports.sh
fi

"${PY[@]}" scripts/artifact/rq4_efficiency.py "$@"

"${PY[@]}" scripts/artifact/print_reduced_tables.py rq4
