#!/usr/bin/env python3
"""Generate full-paper setting tables and figures from full sampler/RCA reports."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import polars as pl


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset-a", default="gleaner")
    p.add_argument("--dataset-b", default="tracepicker")
    p.add_argument("--sampler-root", type=Path, default=Path("output/rcabench-platform-v2/sampler_reports"))
    p.add_argument("--rca-root", type=Path, default=Path("output/rcabench-platform-v2/meta"))
    p.add_argument("--figure-dir", type=Path, default=Path("output/full/figures"))
    p.add_argument("--table-dir", type=Path, default=Path("output/full/tables"))
    return p.parse_args()


def require(path: Path) -> Path:
    if not path.exists() or path.stat().st_size == 0:
        raise SystemExit(f"ERROR: missing/non-empty required full report: {path}")
    return path


def safe_float(v) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else 0.0
    except Exception:
        return 0.0


def write_csv(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(path)
    print(f"[full:figures] wrote {path}")


def plot_metric(df: pl.DataFrame, x: str, y: str, title: str, path: Path, *, top: int = 16) -> None:
    if y not in df.columns or x not in df.columns:
        return
    pdf = df.select([x, y]).drop_nulls().to_pandas()
    if pdf.empty:
        return
    pdf[y] = pdf[y].map(safe_float)
    pdf = pdf.sort_values(y, ascending=False).head(top)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(8, len(pdf) * 0.45), 4.5))
    ax.bar(range(len(pdf)), pdf[y], color="#2f6f73")
    ax.set_xticks(range(len(pdf)))
    ax.set_xticklabels(pdf[x].astype(str), rotation=35, ha="right", fontsize=8)
    ax.set_ylabel(y)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25, linestyle="--")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"[full:figures] wrote {path}")


def main() -> None:
    args = parse_args()
    args.figure_dir.mkdir(parents=True, exist_ok=True)
    args.table_dir.mkdir(parents=True, exist_ok=True)

    ds_a_sampler = pl.read_parquet(require(args.sampler_root / args.dataset_a / "aggregated_perf.parquet"))
    ds_b_sampler = pl.read_parquet(require(args.sampler_root / args.dataset_b / "aggregated_perf.parquet"))
    rca = pl.read_parquet(require(args.rca_root / args.dataset_a / "sampler.grouped.perf.parquet"))

    # Paper RQ1/Fig.4 style: Dataset A sampling quality summary.
    rq1_a = ds_a_sampler.select([c for c in [
        "sampler", "dataset", "sampling_rate", "mode", "datapack_count",
        "avg_api_coverage", "avg_path_coverage_dedup", "avg_unique_trace_coverage",
        "avg_shannon_entropy", "avg_benefit_cost_ratio", "avg_runtime_per_trace_ms",
    ] if c in ds_a_sampler.columns]).sort(["sampling_rate", "sampler"])
    write_csv(rq1_a, args.table_dir / "rq1_dataset_a_sampling_quality.csv")
    plot_metric(rq1_a.filter(pl.col("sampling_rate") == rq1_a["sampling_rate"].max()), "sampler", "avg_benefit_cost_ratio", "RQ1 Dataset A Sampling Quality", args.figure_dir / "fig4_dataset_a_sampling_quality.png")

    # Paper RQ1/Fig.5 style: Dataset B cross-system/cross-baseline sampler summary.
    rq1_b = ds_b_sampler.select([c for c in [
        "sampler", "dataset", "sampling_rate", "mode", "datapack_count",
        "avg_api_coverage", "avg_path_coverage", "avg_benefit_cost_ratio", "avg_runtime_per_trace_ms",
    ] if c in ds_b_sampler.columns]).sort(["sampling_rate", "sampler"])
    write_csv(rq1_b, args.table_dir / "rq1_dataset_b_cross_system.csv")
    plot_metric(rq1_b.filter(pl.col("sampling_rate") == rq1_b["sampling_rate"].max()), "sampler", "avg_benefit_cost_ratio", "RQ1 Dataset B Cross-System Sampling", args.figure_dir / "fig5_dataset_b_cross_system.png")

    # Paper RQ2 ablation/Fig.6-Fig.7/Table5 style.
    ablation_samplers = [s for s in rq1_a["sampler"].unique().to_list() if str(s).startswith("gleaner")]
    rq2 = rq1_a.filter(pl.col("sampler").is_in(ablation_samplers))
    write_csv(rq2, args.table_dir / "rq2_ablation_sampling.csv")
    plot_metric(rq2.filter(pl.col("sampling_rate") == rq2["sampling_rate"].max()), "sampler", "avg_benefit_cost_ratio", "RQ2 Gleaner Ablation", args.figure_dir / "fig6_7_ablation.png")

    # Paper RQ3/Table6-7 style RCA impact.
    rca_cols = [c for c in [
        "algorithm", "dataset", "sampler.name", "sampler.rate", "sampler.mode", "total",
        "MRR", "AC@1", "AC@3", "AC@5", "runtime.seconds:avg",
    ] if c in rca.columns]
    rq3 = rca.select(rca_cols).sort([c for c in ["algorithm", "sampler.rate", "sampler.name"] if c in rca_cols])
    write_csv(rq3, args.table_dir / "rq3_rca_effectiveness.csv")
    sampled = rq3.filter(pl.col("sampler.name").is_not_null()) if "sampler.name" in rq3.columns else rq3
    if "AC@3" in sampled.columns and "sampler.name" in sampled.columns:
        ac = sampled.group_by("sampler.name").agg(pl.col("AC@3").mean().alias("AC@3_mean")).rename({"sampler.name": "sampler"})
        plot_metric(ac, "sampler", "AC@3_mean", "RQ3 Downstream RCA AC@3", args.figure_dir / "table6_7_rca_effectiveness.png")

    # Paper RQ4/Table8 style efficiency.
    rq4 = rq1_a.select([c for c in ["sampler", "sampling_rate", "avg_runtime_per_trace_ms", "avg_benefit_cost_ratio"] if c in rq1_a.columns])
    write_csv(rq4, args.table_dir / "rq4_efficiency.csv")
    plot_metric(rq4.filter(pl.col("sampling_rate") == rq4["sampling_rate"].max()), "sampler", "avg_runtime_per_trace_ms", "RQ4 Efficiency", args.figure_dir / "table8_efficiency.png")

    report = args.table_dir.parent / "REPORT.md"
    report.write_text(
        "# Full Paper Reproduction Outputs\n\n"
        f"- Dataset A: `{args.dataset_a}`\n"
        f"- Dataset B: `{args.dataset_b}`\n"
        f"- Figures: `{args.figure_dir}`\n"
        f"- Tables: `{args.table_dir}`\n"
        "- Scope: generated from full sampler/RCA reports after `scripts/run_full_sampling.sh` and `scripts/run_full_rca.sh`.\n",
        encoding="utf-8",
    )
    print(f"[full:figures] wrote {report}")


if __name__ == "__main__":
    main()
