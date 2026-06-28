#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

uv run --package Gleaner python scripts/artifact/make_reduced_sampler_reports.py \
  --input-detailed data/artifact/reduced/rq1/gleaner_source.detailed_perf.parquet \
  --output-dir output/rcabench-platform-v2/sampler_reports/gleaner_reduced20 \
  --subset-size 20 \
  --manifest configs/reduced/reduced20_datapacks.json
