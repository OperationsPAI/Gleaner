#!/usr/bin/env python3
"""Generate artifact-ready RQ3 ablation outputs from sampler performance data."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Iterable

import polars as pl

DEFAULT_INPUT = Path(
    "output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/aggregated_perf.parquet"
)
DEFAULT_OUTPUT_DIR = Path("output/artifact/reduced/rq3")
DEFAULT_MODE = "offline"
DEFAULT_EXCLUDE_SAMPLING_RATE = 0.005

DISPLAY_NAMES = {
    "gleaner": "Gleaner",
    "gleaner_no_logs": "Gleaner w/o Logs",
    "gleaner_no_ad": "Gleaner w/o AD",
    "gleaner_pure_diversity": "Gleaner Pure Diversity",
    "gleaner_no_logs_no_ad": "Gleaner w/o Logs + AD",
    "gleaner_no_dpp": "Gleaner w/o DPP",
    "gleaner_no_rebalance": "Gleaner w/o Rebalance",
    "gleaner_latency_dominate": "Gleaner Latency-Dominant",
    "gleaner_log_dominate": "Gleaner Log-Dominant",
    "gleaner_top_score": "Gleaner Top Score",
    "gleaner_wl_kernel": "Gleaner WL Kernel",
    "random": "Random",
}

CORE_METRICS = [
    "avg_api_coverage",
    "avg_unique_trace_coverage",
    "avg_shannon_entropy",
    "avg_proportion_anomaly",
]
OPTIONAL_METRICS = [
    "avg_path_coverage_dedup",
    "avg_benefit_cost_ratio",
]
PREFERRED_METRICS = CORE_METRICS + OPTIONAL_METRICS
REQUIRED_COLUMNS = {"sampler", "mode", "sampling_rate"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate RQ3 ablation markdown and machine-readable summaries."
    )
    parser.add_argument(
        "--input-parquet",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input aggregated_perf.parquet (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for RQ3 outputs (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--mode",
        default=DEFAULT_MODE,
        help=f"Sampler mode to filter (default: {DEFAULT_MODE})",
    )
    parser.add_argument(
        "--exclude-sampling-rate",
        type=float,
        action="append",
        default=[DEFAULT_EXCLUDE_SAMPLING_RATE],
        help=(
            "Sampling rate to exclude; repeatable "
            f"(default: {DEFAULT_EXCLUDE_SAMPLING_RATE:g})"
        ),
    )
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def metric_label(metric: str) -> str:
    labels = {
        "avg_api_coverage": "API Coverage",
        "avg_unique_trace_coverage": "Unique Trace Coverage",
        "avg_shannon_entropy": "Shannon Entropy",
        "avg_proportion_anomaly": "Proportion Anomaly",
        "avg_path_coverage_dedup": "Path Coverage Dedup",
        "avg_benefit_cost_ratio": "Benefit-Cost Ratio",
    }
    return labels.get(metric, metric.replace("avg_", "").replace("_", " ").title())


def is_finite_number(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def json_safe(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not is_finite_number(value):
        return None
    return value


def format_value(value: object) -> str:
    if value is None:
        return "N/A"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return "N/A"
    return f"{number:.4f}"


def available_metrics(columns: Iterable[str]) -> list[str]:
    column_set = set(columns)
    return [metric for metric in PREFERRED_METRICS if metric in column_set]


def sampling_rate_exclusion_expr(excluded: list[float]) -> pl.Expr:
    keep_expr = pl.lit(True)
    for rate in excluded:
        keep_expr = keep_expr & ((pl.col("sampling_rate") - rate).abs() >= 1e-12)
    return keep_expr


def available_configurations(df: pl.DataFrame) -> str:
    rows = (
        df.select(["mode", "sampling_rate"])
        .unique()
        .sort(["mode", "sampling_rate"])
        .iter_rows(named=True)
    )
    return ", ".join(
        f"mode={row['mode']} sampling_rate={row['sampling_rate']}" for row in rows
    )


def load_filtered(
    input_parquet: Path, mode: str, excluded_sampling_rates: list[float]
) -> tuple[pl.DataFrame, list[str], list[float], list[str]]:
    if not input_parquet.exists():
        fail(f"input parquet not found: {input_parquet}")

    df = pl.read_parquet(input_parquet)
    missing_required = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing_required:
        fail(
            f"input parquet is missing required columns: {', '.join(missing_required)}"
        )

    metrics = available_metrics(df.columns)
    if not metrics:
        expected = ", ".join(PREFERRED_METRICS)
        fail(
            "input parquet has none of the RQ3 overview metric columns; "
            f"expected one of: {expected}"
        )

    filtered = df.filter(
        (pl.col("mode") == mode) & sampling_rate_exclusion_expr(excluded_sampling_rates)
    )
    if filtered.height == 0:
        choices = available_configurations(df)
        excluded = ", ".join(f"{rate:g}" for rate in excluded_sampling_rates)
        fail(
            f"no rows after filtering mode={mode!r}, excluded_sampling_rates=[{excluded}]; "
            f"available configurations: {choices or 'none'}"
        )

    samplers = sorted(filtered.get_column("sampler").unique().to_list())
    sampling_rates = sorted(filtered.get_column("sampling_rate").unique().to_list())
    if len(samplers) < 2:
        fail(
            "RQ3 reduced ablation requires at least 2 samplers after filtering; "
            f"found {len(samplers)}: {', '.join(samplers) or 'none'}"
        )

    return filtered, metrics, sampling_rates, samplers


def sanitize_metric_columns(df: pl.DataFrame, metrics: list[str]) -> pl.DataFrame:
    return df.with_columns(
        [
            pl.when(pl.col(metric).is_finite())
            .then(pl.col(metric))
            .otherwise(None)
            .alias(metric)
            for metric in metrics
        ]
    )


def summarize_by_sampler(df: pl.DataFrame, metrics: list[str]) -> pl.DataFrame:
    df = sanitize_metric_columns(df, metrics)
    aggregations = [
        pl.col("sampling_rate").n_unique().alias("sample_rate_count"),
        *[pl.col(metric).mean().alias(metric) for metric in metrics],
    ]
    summary = df.group_by("sampler").agg(aggregations).sort("sampler")
    summary = sanitize_metric_columns(summary, metrics)
    summary = summary.with_columns(
        pl.col("sampler")
        .map_elements(lambda name: DISPLAY_NAMES.get(name, name), return_dtype=pl.String)
        .alias("display_name")
    ).select(["sampler", "display_name", "sample_rate_count", *metrics])
    if summary.height == 0:
        fail("filtered data produced an empty sampler summary")
    return summary


def make_markdown(
    summary: pl.DataFrame,
    metrics: list[str],
    sampling_rates: list[float],
    samplers: list[str],
    input_parquet: Path,
    mode: str,
    excluded_sampling_rates: list[float],
    output_dir: Path,
) -> str:
    lines: list[str] = []
    lines.append("# RQ3: Ablation Study")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- Input parquet: `{input_parquet}`")
    lines.append(f"- Output directory: `{output_dir}`")
    lines.append(f"- Mode: `{mode}`")
    lines.append(
        "- Excluded sampling rates: "
        + ", ".join(f"`{rate:g}`" for rate in excluded_sampling_rates)
    )
    lines.append(
        "- Sampling rates: " + ", ".join(f"`{rate:g}`" for rate in sampling_rates)
    )
    lines.append(
        "- Samplers: "
        + ", ".join(DISPLAY_NAMES.get(sampler, sampler) for sampler in samplers)
    )
    lines.append("")
    lines.append("## Overview Metrics")
    lines.append("")
    lines.append("| Sampler | Display Name | Sample Rate Count | " + " | ".join(metric_label(m) for m in metrics) + " |")
    lines.append("| " + " | ".join(["---"] * (3 + len(metrics))) + " |")
    for row in summary.iter_rows(named=True):
        values = [
            row["sampler"],
            row["display_name"],
            str(row["sample_rate_count"]),
            *[format_value(row[metric]) for metric in metrics],
        ]
        lines.append("| " + " | ".join(values) + " |")

    lines.append("")
    lines.append("## Best Per Metric")
    lines.append("")
    for metric in metrics:
        non_null = summary.filter(pl.col(metric).is_not_null() & pl.col(metric).is_finite())
        if non_null.height == 0:
            continue
        best = non_null.sort([metric, "sampler"], descending=[True, False]).head(1).row(0, named=True)
        lines.append(
            f"- {metric_label(metric)} (higher is better): "
            f"{best['display_name']} ({format_value(best[metric])})"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- This reduced RQ3 artifact uses the available Gleaner variant sampler report "
        "rather than requiring canonical `gleaner` and `random` rows."
    )
    lines.append(
        "- Values are deterministic means across the filtered sampling rates in "
        "`aggregated_perf.parquet`."
    )
    lines.append("- Plot files are intentionally omitted to keep the artifact harness stable.")
    lines.append("")
    return "\n".join(lines)


def write_outputs(args: argparse.Namespace) -> None:
    excluded = sorted(set(args.exclude_sampling_rate or []))
    filtered, metrics, sampling_rates, samplers = load_filtered(
        args.input_parquet, args.mode, excluded
    )
    summary = summarize_by_sampler(filtered, metrics)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    md_path = args.output_dir / "rq3_ablation_results.md"
    csv_path = args.output_dir / "rq3_ablation_summary.csv"
    json_path = args.output_dir / "rq3_ablation_summary.json"

    markdown = make_markdown(
        summary=summary,
        metrics=metrics,
        sampling_rates=sampling_rates,
        samplers=samplers,
        input_parquet=args.input_parquet,
        mode=args.mode,
        excluded_sampling_rates=excluded,
        output_dir=args.output_dir,
    )
    md_path.write_text(markdown, encoding="utf-8")
    summary.write_csv(csv_path, null_value="")

    payload = {
        "config": {
            "input_parquet": str(args.input_parquet),
            "output_dir": str(args.output_dir),
            "mode": args.mode,
            "exclude_sampling_rate": excluded,
        },
        "metrics": metrics,
        "sampling_rates": sampling_rates,
        "samplers": samplers,
        "rows": [
            {key: json_safe(value) for key, value in row.items()}
            for row in summary.to_dicts()
        ],
    }
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")

    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")


def main() -> None:
    write_outputs(parse_args())


if __name__ == "__main__":
    main()
