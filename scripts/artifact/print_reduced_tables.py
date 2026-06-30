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
    view = df[["sampler", "datapack_count", "avg_api_coverage", "avg_path_coverage_dedup", "avg_event_coverage", "avg_proportion_anomaly", "avg_proportion_rare"]]
    view = view.sort_values(["avg_event_coverage", "avg_api_coverage"], ascending=False).head(5)
    rows = [
        {
            "sampler": r.sampler,
            "datapacks": int(r.datapack_count),
            "api_cov": fmt(r.avg_api_coverage),
            "path_cov": fmt(r.avg_path_coverage_dedup),
            "trace_pattern_cov": fmt(r.avg_event_coverage),
            "anom_prop": fmt(r.avg_proportion_anomaly),
            "rare_prop": fmt(r.avg_proportion_rare),
        }
        for r in view.itertuples()
    ]
    print("[rq1] top sampling-quality rows")
    print_table(rows, ["sampler", "datapacks", "api_cov", "path_cov", "trace_pattern_cov", "anom_prop", "rare_prop"])


def rq2() -> None:
    df = pd.read_csv(BASE / "rq2/rq2_ablation_summary.csv")
    view = df[["sampler", "avg_api_coverage", "avg_event_coverage", "avg_shannon_entropy", "avg_proportion_anomaly"]]
    view = view.sort_values("avg_event_coverage", ascending=False).head(5)
    rows = [
        {
            "sampler": r.sampler,
            "api_cov": fmt(r.avg_api_coverage),
            "trace_pattern_cov": fmt(r.avg_event_coverage),
            "entropy": fmt(r.avg_shannon_entropy),
            "anom_prop": fmt(r.avg_proportion_anomaly),
        }
        for r in view.itertuples()
    ]
    print("[rq2] top ablation rows by trace pattern coverage")
    print_table(rows, ["sampler", "api_cov", "trace_pattern_cov", "entropy", "anom_prop"])


def rq3() -> None:
    df = pd.read_csv(BASE / "rq3/rq3_rca_effectiveness_summary.csv")
    avg = df.groupby("sampler_name", as_index=False)[["accuracy_at_1_mean", "accuracy_at_3_mean"]].mean()
    avg = avg.sort_values(["accuracy_at_3_mean", "accuracy_at_1_mean"], ascending=False).head(5)
    rows = [
        {"sampler": r.sampler_name, "acc@1": fmt(r.accuracy_at_1_mean), "acc@3": fmt(r.accuracy_at_3_mean)}
        for r in avg.itertuples()
    ]
    print("[rq3] top averaged RCA rows")
    print_table(rows, ["sampler", "acc@1", "acc@3"])


def rq4() -> None:
    df = pd.read_csv(BASE / "rq4/rq4_efficiency_summary.csv")
    view = df[["sampler", "avg_runtime_per_trace_ms", "avg_actual_sampling_rate", "avg_benefit_cost_ratio"]]
    view = view.sort_values("avg_runtime_per_trace_ms", ascending=True).head(5)
    rows = [
        {
            "sampler": r.sampler,
            "ms/trace": f"{float(r.avg_runtime_per_trace_ms):.3f}",
            "actual_rate": fmt(r.avg_actual_sampling_rate, percent=True),
            "bcr": fmt(r.avg_benefit_cost_ratio),
        }
        for r in view.itertuples()
    ]
    print("[rq4] Gleaner efficiency rows")
    print_table(rows, ["sampler", "ms/trace", "actual_rate", "bcr"])


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
