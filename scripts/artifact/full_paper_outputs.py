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

DISPLAY_NAMES = {
    "__full__": "Full (unsampled)",
    "gleaner": "Gleaner",
    "gleaner_no_logs": "Gleaner w/o Logs",
    "gleaner_no_ad": "Gleaner w/o Alarms",
    "gleaner_no_logs_no_ad": "Gleaner w/o Logs & Alarms",
    "gleaner_wl_kernel": "Gleaner WL Kernel",
    "gleaner_pure_diversity": "Gleaner Pure Diversity",
    "gleaner_top_score": "Gleaner Pure Anomaly",
    "gleaner_no_dpp": "Gleaner w/o Diversity",
    "gleaner_anomaly_pure_diversity": "Gleaner w/o Anomaly",
    "random": "Random",
    "tracepicker": "TracePicker",
    "trastrainer": "TraStrainer",
    "trastrainer_no_metrics": "TraStrainer w/o Metrics",
    "sifter": "Sifter",
    "sieve": "Sieve",
}

PAPER_ABLATION_SAMPLERS = [
    "gleaner",
    "gleaner_no_logs",
    "gleaner_no_ad",
    "gleaner_no_logs_no_ad",
    "gleaner_wl_kernel",
    "gleaner_pure_diversity",
    "gleaner_top_score",
    "gleaner_no_dpp",
    "gleaner_anomaly_pure_diversity",
]

PAPER_RCA_SAMPLERS = ["__full__", *PAPER_ABLATION_SAMPLERS, "random", "tracepicker", "trastrainer", "trastrainer_no_metrics", "sifter", "sieve"]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset-a", default="gleaner")
    p.add_argument("--dataset-b", default="tracepicker")
    p.add_argument("--sampler-root", type=Path, default=Path("output/rcabench-platform-v2/sampler_reports"))
    p.add_argument("--rca-root", type=Path, default=Path("output/rcabench-platform-v2/meta"))
    p.add_argument("--figure-dir", type=Path, default=Path("output/full/figures"))
    p.add_argument("--table-dir", type=Path, default=Path("output/full/tables"))
    p.add_argument("--rca-rate", type=float, action="append", default=None)
    p.add_argument("--efficiency-rate", type=float, default=0.05)
    p.add_argument("--efficiency-mode", default="online")
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


def add_sampler_display(df: pl.DataFrame, source: str = "sampler") -> pl.DataFrame:
    if source not in df.columns:
        return df
    mapping = pl.Series("sampler_key", list(DISPLAY_NAMES), dtype=pl.Utf8).to_frame()
    mapping = mapping.with_columns(
        pl.Series("Sampler", list(DISPLAY_NAMES.values()), dtype=pl.Utf8)
    )
    return (
        df.with_columns(pl.col(source).cast(pl.Utf8).alias("sampler_key"))
        .join(mapping, on="sampler_key", how="left")
        .with_columns(pl.coalesce(["Sampler", pl.col(source).cast(pl.Utf8)]).alias("Sampler"))
        .drop("sampler_key")
    )


def paper_sampler_table(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    selected = df.select([c for c in columns if c in df.columns])
    renamed = {}
    for old, new in {
        "sampling_rate": "Sampling Rate",
        "mode": "Mode",
        "datapack_count": "Datapacks",
        "avg_api_coverage": "API Coverage",
        "avg_path_coverage_dedup": "Path Coverage",
        "avg_event_coverage": "Trace Pattern Coverage",
        "avg_shannon_entropy": "Shannon Entropy",
        "avg_proportion_anomaly": "Proportion Anomaly",
        "avg_proportion_rare": "Proportion Rare",
        "avg_benefit_cost_ratio": "Benefit-Cost Ratio",
        "avg_actual_sampling_rate": "Actual Sampling Rate",
        "avg_runtime_per_trace_ms": "Runtime Per Trace (ms)",
    }.items():
        if old in selected.columns:
            renamed[old] = new
    selected = selected.rename(renamed)
    if "sampler" in selected.columns:
        selected = add_sampler_display(selected).drop("sampler")
    return selected


def rows_at_rate(df: pl.DataFrame, rate: float) -> pl.DataFrame:
    if "sampling_rate" not in df.columns:
        return df
    exact = df.filter((pl.col("sampling_rate") - rate).abs() < 1e-12)
    return exact if exact.height else df.filter(pl.col("sampling_rate") == df["sampling_rate"].max())


def require_rows_at_rate(df: pl.DataFrame, rate: float, label: str) -> pl.DataFrame:
    if "sampling_rate" not in df.columns:
        raise SystemExit(f"ERROR: {label} requires a sampling_rate column")
    exact = df.filter((pl.col("sampling_rate") - rate).abs() < 1e-12)
    if exact.height == 0:
        available = sorted(float(x) for x in df["sampling_rate"].drop_nulls().unique().to_list())
        raise SystemExit(f"ERROR: {label} missing required rate {rate}; available rates: {available}")
    return exact


def filter_rca_rates(df: pl.DataFrame, rates: list[float]) -> pl.DataFrame:
    if "sampler.rate" not in df.columns:
        return df
    rate_expr = pl.col("sampler.rate").cast(pl.Float64, strict=False)
    keep = pl.col("sampler.rate").is_null()
    for rate in rates:
        keep = keep | ((rate_expr - rate).abs() < 1e-12)
    filtered = df.filter(keep)
    sampled = filtered.filter(pl.col("sampler.rate").is_not_null())
    present = set(float(x) for x in sampled["sampler.rate"].drop_nulls().unique().to_list())
    missing = set(rates) - present
    if missing:
        raise SystemExit(f"ERROR: RCA report missing required sampled rates: {sorted(missing)}")
    extra = set(float(x) for x in df["sampler.rate"].drop_nulls().unique().to_list()) - set(rates)
    if extra:
        print(f"[full:figures] ignoring non-paper RCA sampled rates: {sorted(extra)}")
    return filtered


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
    rca_rates = args.rca_rate or [0.01, 0.1]
    args.figure_dir.mkdir(parents=True, exist_ok=True)
    args.table_dir.mkdir(parents=True, exist_ok=True)

    ds_a_sampler = pl.read_parquet(require(args.sampler_root / args.dataset_a / "aggregated_perf.parquet"))
    ds_b_sampler = pl.read_parquet(require(args.sampler_root / args.dataset_b / "aggregated_perf.parquet"))
    rca = pl.read_parquet(require(args.rca_root / args.dataset_a / "sampler.grouped.perf.parquet"))

    # Paper RQ1/Fig.4 style: Dataset A sampling quality summary.
    rq1_a_raw = ds_a_sampler.select([c for c in [
        "sampler", "dataset", "sampling_rate", "mode", "datapack_count",
        "avg_api_coverage", "avg_path_coverage_dedup", "avg_event_coverage",
        "avg_shannon_entropy", "avg_proportion_anomaly", "avg_proportion_rare",
        "avg_benefit_cost_ratio", "avg_actual_sampling_rate", "avg_runtime_per_trace_ms",
    ] if c in ds_a_sampler.columns]).sort(["sampling_rate", "sampler"])
    rq1_a = paper_sampler_table(rq1_a_raw, rq1_a_raw.columns)
    write_csv(rq1_a, args.table_dir / "rq1_dataset_a_sampling_quality.csv")
    plot_metric(rows_at_rate(rq1_a_raw, 0.1), "sampler", "avg_event_coverage", "RQ1 Dataset A Trace Pattern Coverage", args.figure_dir / "fig4_dataset_a_sampling_quality.png")

    # Paper RQ1/Fig.5 style: Dataset B cross-system/cross-baseline sampler summary.
    rq1_b_raw = ds_b_sampler.select([c for c in [
        "sampler", "dataset", "sampling_rate", "mode", "datapack_count",
        "avg_api_coverage", "avg_path_coverage_dedup", "avg_event_coverage",
        "avg_benefit_cost_ratio", "avg_actual_sampling_rate", "avg_runtime_per_trace_ms",
    ] if c in ds_b_sampler.columns]).sort(["sampling_rate", "sampler"])
    rq1_b = paper_sampler_table(rq1_b_raw, rq1_b_raw.columns)
    write_csv(rq1_b, args.table_dir / "rq1_dataset_b_cross_system.csv")
    plot_metric(rows_at_rate(rq1_b_raw, 0.1), "sampler", "avg_event_coverage", "RQ1 Dataset B Trace Pattern Coverage", args.figure_dir / "fig5_dataset_b_cross_system.png")

    # Paper RQ2 ablation/Fig.6-Fig.7/Table5 style.
    rq2_raw = rq1_a_raw.filter(pl.col("sampler").is_in(PAPER_ABLATION_SAMPLERS))
    rq2 = paper_sampler_table(rq2_raw, rq2_raw.columns)
    write_csv(rq2, args.table_dir / "rq2_ablation_sampling.csv")
    plot_metric(rows_at_rate(rq2_raw, 0.1), "sampler", "avg_event_coverage", "RQ2 Gleaner Ablation Trace Pattern Coverage", args.figure_dir / "fig6_7_ablation.png")

    # Paper RQ3/Table6-7 style RCA impact.
    rca_cols = [c for c in [
        "algorithm", "dataset", "sampler.name", "sampler.rate", "sampler.mode", "total",
        "AC@1", "AC@3",
    ] if c in rca.columns]
    rq3 = filter_rca_rates(rca.select(rca_cols), rca_rates).with_columns([
        pl.when(pl.col("sampler.name").is_null()).then(pl.lit("__full__")).otherwise(pl.col("sampler.name")).alias("sampler.name")
    ]).filter(pl.col("sampler.name").is_in(PAPER_RCA_SAMPLERS)).sort([c for c in ["algorithm", "sampler.rate", "sampler.name"] if c in rca_cols])
    rq3 = add_sampler_display(rq3, "sampler.name").rename({
        "algorithm": "RCA Algorithm",
        "sampler.rate": "Sampling Rate",
        "sampler.mode": "Mode",
        "total": "Cases",
        "AC@1": "Accuracy@1",
        "AC@3": "Accuracy@3",
    })
    write_csv(rq3, args.table_dir / "rq3_rca_effectiveness.csv")
    sampled = rq3.filter(pl.col("Sampler") != "Full (unsampled)") if "Sampler" in rq3.columns else rq3
    if "Accuracy@3" in sampled.columns and "Sampler" in sampled.columns:
        ac = sampled.group_by("Sampler").agg(pl.col("Accuracy@3").mean().alias("Accuracy@3 mean")).rename({"Sampler": "sampler"})
        plot_metric(ac, "sampler", "Accuracy@3 mean", "RQ3 Downstream RCA Accuracy@3", args.figure_dir / "table6_7_rca_effectiveness.png")

    # Paper RQ4/Table8 style efficiency.
    rq4_source = rq1_a_raw.filter(pl.col("mode") == args.efficiency_mode)
    if rq4_source.height == 0:
        raise SystemExit(f"ERROR: RQ4 efficiency missing required mode {args.efficiency_mode!r}")
    rq4_raw = require_rows_at_rate(rq4_source, args.efficiency_rate, "RQ4 efficiency").select([c for c in [
        "sampler", "sampling_rate", "avg_runtime_per_trace_ms",
        "avg_actual_sampling_rate", "avg_benefit_cost_ratio"
    ] if c in rq1_a_raw.columns])
    rq4 = paper_sampler_table(rq4_raw, rq4_raw.columns)
    write_csv(rq4, args.table_dir / "rq4_efficiency.csv")
    plot_metric(rq4_raw, "sampler", "avg_runtime_per_trace_ms", "RQ4 Efficiency at 5% Target Rate", args.figure_dir / "table8_efficiency.png")

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
