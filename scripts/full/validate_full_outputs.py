#!/usr/bin/env python3
"""Validate full reproduction output postconditions without trusting logs."""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset-a", default="gleaner")
    p.add_argument("--dataset-b", default="tracepicker")
    p.add_argument("--rates", default="0.005,0.01,0.1")
    p.add_argument("--modes", default="offline")
    return p.parse_args()


def require(path: Path) -> Path:
    if not path.exists() or path.stat().st_size == 0:
        raise SystemExit(f"ERROR: missing/non-empty output: {path}")
    return path


def require_cols(path: Path, cols: set[str]) -> pl.DataFrame:
    df = pl.read_parquet(require(path))
    missing = cols - set(df.columns)
    if missing:
        raise SystemExit(f"ERROR: {path} missing columns: {sorted(missing)}")
    if df.height == 0:
        raise SystemExit(f"ERROR: {path} has zero rows")
    return df


def main() -> None:
    args = parse_args()
    expected_rates = {float(x) for x in args.rates.split(",") if x}
    expected_modes = {x for x in args.modes.split(",") if x}

    a_sampler = require_cols(Path(f"output/rcabench-platform-v2/sampler_reports/{args.dataset_a}/aggregated_perf.parquet"), {"sampler", "dataset", "sampling_rate", "mode", "datapack_count"})
    b_sampler = require_cols(Path(f"output/rcabench-platform-v2/sampler_reports/{args.dataset_b}/aggregated_perf.parquet"), {"sampler", "dataset", "sampling_rate", "mode", "datapack_count"})
    rca = require_cols(Path(f"output/rcabench-platform-v2/meta/{args.dataset_a}/sampler.grouped.perf.parquet"), {"algorithm", "dataset", "AC@1", "AC@3"})

    missing_rates = expected_rates - set(float(x) for x in a_sampler["sampling_rate"].unique().to_list())
    if missing_rates:
        raise SystemExit(f"ERROR: Dataset A sampler report missing rates: {sorted(missing_rates)}")
    missing_modes = expected_modes - set(str(x) for x in a_sampler["mode"].unique().to_list())
    if missing_modes:
        raise SystemExit(f"ERROR: Dataset A sampler report missing modes: {sorted(missing_modes)}")

    required_a_samplers = {"gleaner", "random", "tracepicker", "trastrainer", "trastrainer_no_metrics", "sifter", "sieve"}
    missing_samplers = required_a_samplers - set(str(x) for x in a_sampler["sampler"].unique().to_list())
    if missing_samplers:
        raise SystemExit(f"ERROR: Dataset A report missing required samplers: {sorted(missing_samplers)}")
    required_b_samplers = {"gleaner_no_logs_no_ad", "random", "tracepicker", "trastrainer_no_metrics", "sifter", "sieve"}
    missing_b_samplers = required_b_samplers - set(str(x) for x in b_sampler["sampler"].unique().to_list())
    if missing_b_samplers:
        raise SystemExit(f"ERROR: Dataset B report missing required samplers: {sorted(missing_b_samplers)}")

    required_algs = {"microrca", "shapleyiq", "nezha"}
    missing_algs = required_algs - set(str(x) for x in rca["algorithm"].unique().to_list())
    if missing_algs:
        raise SystemExit(f"ERROR: RCA report missing algorithms: {sorted(missing_algs)}")

    for path in [
        Path("output/full/REPORT.md"),
        Path("output/full/tables/rq1_dataset_a_sampling_quality.csv"),
        Path("output/full/tables/rq1_dataset_b_cross_system.csv"),
        Path("output/full/tables/rq2_ablation_sampling.csv"),
        Path("output/full/tables/rq3_rca_effectiveness.csv"),
        Path("output/full/tables/rq4_efficiency.csv"),
        Path("output/full/figures/fig4_dataset_a_sampling_quality.png"),
        Path("output/full/figures/fig5_dataset_b_cross_system.png"),
        Path("output/full/figures/fig6_7_ablation.png"),
        Path("output/full/figures/table8_efficiency.png"),
    ]:
        require(path)

    print("[full:validate] full output postconditions passed")


if __name__ == "__main__":
    main()
