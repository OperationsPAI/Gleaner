#!/usr/bin/env python3
"""Print compact reviewer-facing tables for reduced RQ outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

BASE = Path("output/artifact/reduced")


def fmt(value: object, percent: bool = False) -> str:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{x:.2%}" if percent else f"{x:.4f}"


def print_table(rows: list[dict[str, object]], columns: list[str]) -> None:
    if not rows:
        print("(no rows)")
        return
    widths = {col: max(len(col), *(len(str(row.get(col, ""))) for row in rows)) for col in columns}
    print("  ".join(col.ljust(widths[col]) for col in columns))
    print("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))


def rq1() -> None:
    df = pd.read_csv(BASE / "rq1/rq1_sampling_quality_summary.csv")
    view = df[["sampler", "datapack_count", "avg_api_coverage", "avg_path_coverage_dedup", "avg_proportion_anomaly"]]
    view = view.sort_values(["avg_api_coverage", "avg_path_coverage_dedup"], ascending=False).head(5)
    rows = [
        {
            "sampler": r.sampler,
            "datapacks": int(r.datapack_count),
            "api_cov": fmt(r.avg_api_coverage),
            "path_cov": fmt(r.avg_path_coverage_dedup),
            "anom_prop": fmt(r.avg_proportion_anomaly),
        }
        for r in view.itertuples()
    ]
    print("[rq1] top sampling-quality rows")
    print_table(rows, ["sampler", "datapacks", "api_cov", "path_cov", "anom_prop"])


def rq2() -> None:
    df = pd.read_csv(BASE / "rq2/rq2_rca_effectiveness_summary.csv")
    avg = df.groupby("sampler_name", as_index=False)[["ac_at_1_mean", "ac_at_3_mean"]].mean()
    avg = avg.sort_values(["ac_at_3_mean", "ac_at_1_mean"], ascending=False).head(5)
    rows = [
        {"sampler": r.sampler_name, "ac@1": fmt(r.ac_at_1_mean), "ac@3": fmt(r.ac_at_3_mean)}
        for r in avg.itertuples()
    ]
    print("[rq2] top averaged RCA rows")
    print_table(rows, ["sampler", "ac@1", "ac@3"])


def rq3() -> None:
    df = pd.read_csv(BASE / "rq3/rq3_ablation_summary.csv")
    view = df[["sampler", "avg_api_coverage", "avg_unique_trace_coverage", "avg_benefit_cost_ratio"]]
    view = view.sort_values("avg_benefit_cost_ratio", ascending=False).head(5)
    rows = [
        {
            "sampler": r.sampler,
            "api_cov": fmt(r.avg_api_coverage),
            "uniq_cov": fmt(r.avg_unique_trace_coverage),
            "bcr": fmt(r.avg_benefit_cost_ratio),
        }
        for r in view.itertuples()
    ]
    print("[rq3] top ablation rows by benefit-cost")
    print_table(rows, ["sampler", "api_cov", "uniq_cov", "bcr"])


def rq4() -> None:
    df = pd.read_csv(BASE / "rq4/rq4_efficiency_summary.csv")
    view = df[["sampler", "avg_runtime_per_trace_ms", "avg_benefit_cost_ratio", "avg_actual_sampling_rate"]]
    view = view.sort_values("avg_runtime_per_trace_ms", ascending=True).head(5)
    rows = [
        {
            "sampler": r.sampler,
            "ms/trace": f"{float(r.avg_runtime_per_trace_ms):.3f}",
            "bcr": fmt(r.avg_benefit_cost_ratio),
            "actual_rate": fmt(r.avg_actual_sampling_rate, percent=True),
        }
        for r in view.itertuples()
    ]
    print("[rq4] fastest efficiency rows")
    print_table(rows, ["sampler", "ms/trace", "bcr", "actual_rate"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rq", choices=["rq1", "rq2", "rq3", "rq4", "all"])
    args = parser.parse_args()
    funcs = {"rq1": rq1, "rq2": rq2, "rq3": rq3, "rq4": rq4}
    if args.rq == "all":
        for name in ["rq1", "rq2", "rq3", "rq4"]:
            funcs[name]()
    else:
        funcs[args.rq]()


if __name__ == "__main__":
    main()
