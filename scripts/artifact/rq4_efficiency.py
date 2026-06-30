#!/usr/bin/env python3
"""Generate artifact-ready RQ4 efficiency outputs from sampler performance data."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Iterable

import polars as pl

DEFAULT_INPUT = Path(
    os.getenv(
        "GLEANER_REDUCED_AGGREGATED",
        "output/rcabench-platform-v2/sampler_reports/gleaner_lite/aggregated_perf.parquet",
    )
)
DEFAULT_OUTPUT_DIR = Path("output/artifact/reduced/rq4")
DEFAULT_MODE = "online"
DEFAULT_SAMPLING_RATE = 0.05

DISPLAY_NAMES = {
    "gleaner": "Gleaner",
    "tracepicker": "TracePicker",
    "trastrainer": "TrasTrainer",
    "trastrainer_no_metrics": "TrasTrainer w/o Metrics",
    "sifter": "Sifter",
    "sieve": "Sieve",
    "random": "Random",
    "gleaner_wl_kernel": "Gleaner WL Kernel",
}

METRIC_CATEGORIES = {
    "runtime": "runtime_per_trace_ms",
    "actual_rate": "actual_sampling_rate",
    "benefit_cost": "benefit_cost_ratio",
}

PREFERRED_METRICS = [
    "avg_runtime_per_trace_ms",
    "std_runtime_per_trace_ms",
    "min_runtime_per_trace_ms",
    "max_runtime_per_trace_ms",
    "avg_actual_sampling_rate",
    "std_actual_sampling_rate",
    "min_actual_sampling_rate",
    "max_actual_sampling_rate",
    "avg_benefit_cost_ratio",
    "std_benefit_cost_ratio",
    "min_benefit_cost_ratio",
    "max_benefit_cost_ratio",
]

REQUIRED_COLUMNS = {"sampler", "mode", "sampling_rate"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate RQ4 efficiency markdown and machine-readable summaries."
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
        help=f"Directory for RQ4 outputs (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--mode",
        default=DEFAULT_MODE,
        help=f"Sampler mode to filter (default: {DEFAULT_MODE})",
    )
    parser.add_argument(
        "--sampling-rate",
        type=float,
        default=DEFAULT_SAMPLING_RATE,
        help=f"Sampling rate to filter (default: {DEFAULT_SAMPLING_RATE})",
    )
    parser.add_argument(
        "--sampler",
        action="append",
        default=None,
        help="Sampler to include; repeatable. Defaults to paper RQ4 focus: Gleaner and Gleaner WL Kernel.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def metric_label(metric: str) -> str:
    return (
        metric.replace("avg_", "")
        .replace("std_", "std ")
        .replace("min_", "min ")
        .replace("max_", "max ")
        .replace("_", " ")
        .title()
    )


def is_finite_number(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def format_value(metric: str, value: object) -> str:
    if value is None:
        return "N/A"
    try:
        numeric = float(value)  # Polars may return ints for some numeric columns.
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(numeric):
        return "N/A"

    if "actual_sampling_rate" in metric:
        return f"{numeric:.2%}"
    if "runtime_per_trace_ms" in metric:
        return f"{numeric:.3f}"
    if "benefit_cost_ratio" in metric:
        return f"{numeric:.4f}"
    return f"{numeric:.4f}"


def available_efficiency_metrics(columns: Iterable[str]) -> list[str]:
    column_set = set(columns)
    preferred = [metric for metric in PREFERRED_METRICS if metric in column_set]
    extras = sorted(
        col
        for col in column_set
        if col not in preferred
        and any(token in col for token in METRIC_CATEGORIES.values())
        and col not in REQUIRED_COLUMNS
    )
    return preferred + extras


def load_filtered(
    input_parquet: Path, mode: str, sampling_rate: float, samplers: list[str]
) -> tuple[pl.DataFrame, list[str]]:
    if not input_parquet.exists():
        fail(f"input parquet not found: {input_parquet}")

    df = pl.read_parquet(input_parquet)
    missing_required = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing_required:
        fail(
            f"input parquet is missing required columns: {', '.join(missing_required)}"
        )

    metrics = available_efficiency_metrics(df.columns)
    if not metrics:
        expected = ", ".join(PREFERRED_METRICS)
        fail(
            f"input parquet has none of the RQ4 efficiency metric columns; expected one of: {expected}"
        )

    filtered = df.filter(
        (pl.col("mode") == mode)
        & ((pl.col("sampling_rate") - sampling_rate).abs() < 1e-12)
        & pl.col("sampler").is_in(samplers)
    )
    if filtered.height == 0:
        available = (
            df.select(["mode", "sampling_rate"])
            .unique()
            .sort(["mode", "sampling_rate"])
            .iter_rows(named=True)
        )
        choices = ", ".join(
            f"mode={row['mode']} sampling_rate={row['sampling_rate']}"
            for row in available
        )
        fail(
            f"no rows after filtering mode={mode!r}, sampling_rate={sampling_rate}, samplers={samplers}; "
            f"available configurations: {choices or 'none'}"
        )

    return filtered, metrics


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
    aggregations = [pl.col(metric).mean().alias(metric) for metric in metrics]
    summary = sanitize_metric_columns(
        df.group_by("sampler").agg(aggregations).sort("sampler"), metrics
    )
    if summary.height == 0:
        fail("filtered data produced an empty sampler summary")
    return summary


def make_markdown(
    summary: pl.DataFrame,
    metrics: list[str],
    input_parquet: Path,
    mode: str,
    sampling_rate: float,
    output_dir: Path,
) -> str:
    samplers = summary.get_column("sampler").to_list()
    display_algorithms = [DISPLAY_NAMES.get(name, name) for name in samplers]

    lines: list[str] = []
    lines.append("# RQ4: Efficiency Analysis")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- Input parquet: `{input_parquet}`")
    lines.append(f"- Output directory: `{output_dir}`")
    lines.append(f"- Mode: `{mode}`")
    lines.append(f"- Sampling rate: `{sampling_rate:g}` (paper Table 8 uses 5% target rate)")
    lines.append(f"- Samplers: {', '.join(display_algorithms)}")
    lines.append("")
    lines.append("## Available Metrics")
    lines.append("")

    for category, token in METRIC_CATEGORIES.items():
        category_metrics = [metric for metric in metrics if token in metric]
        label = category.replace("_", " ").title()
        if category_metrics:
            lines.append(f"- {label}: {', '.join(f'`{m}`' for m in category_metrics)}")
        else:
            lines.append(f"- {label}: not available")

    lines.append("")
    lines.append("## Efficiency Summary")
    lines.append("")
    header = ["Sampler"] + [metric_label(metric) for metric in metrics]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    for row in summary.iter_rows(named=True):
        values = [DISPLAY_NAMES.get(row["sampler"], row["sampler"])]
        values.extend(format_value(metric, row[metric]) for metric in metrics)
        lines.append("| " + " | ".join(values) + " |")

    lines.append("")
    lines.append("## Metric Leaders")
    lines.append("")

    for metric in metrics:
        non_null = summary.filter(pl.col(metric).is_not_null() & pl.col(metric).is_finite())
        if non_null.height == 0:
            continue
        lower_is_better = "runtime_per_trace_ms" in metric or metric.startswith("std_")
        best_row = (
            non_null.sort(metric, descending=not lower_is_better)
            .head(1)
            .row(0, named=True)
        )
        direction = "lowest" if lower_is_better else "highest"
        name = DISPLAY_NAMES.get(best_row["sampler"], best_row["sampler"])
        lines.append(
            f"- {metric_label(metric)} ({direction} is best): {name} ({format_value(metric, best_row[metric])})"
        )

    lines.append("")
    return "\n".join(lines)


def json_safe(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not is_finite_number(value):
        return None
    return value


def write_outputs(args: argparse.Namespace) -> None:
    samplers = args.sampler or ["gleaner", "gleaner_wl_kernel"]
    filtered, metrics = load_filtered(args.input_parquet, args.mode, args.sampling_rate, samplers)
    summary = summarize_by_sampler(filtered, metrics)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    md_path = args.output_dir / "rq4_efficiency_results.md"
    csv_path = args.output_dir / "rq4_efficiency_summary.csv"
    json_path = args.output_dir / "rq4_efficiency_summary.json"

    markdown = make_markdown(
        summary=summary,
        metrics=metrics,
        input_parquet=args.input_parquet,
        mode=args.mode,
        sampling_rate=args.sampling_rate,
        output_dir=args.output_dir,
    )
    md_path.write_text(markdown, encoding="utf-8")
    summary.write_csv(csv_path, null_value="")

    payload = {
        "config": {
            "input_parquet": str(args.input_parquet),
            "output_dir": str(args.output_dir),
            "mode": args.mode,
            "sampling_rate": args.sampling_rate,
            "samplers": samplers,
        },
        "samplers": summary.get_column("sampler").to_list(),
        "available_metrics": metrics,
        "rows": [
            {key: json_safe(value) for key, value in row.items()}
            for row in summary.to_dicts()
        ],
    }
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")

    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")


def main() -> None:
    write_outputs(parse_args())


if __name__ == "__main__":
    main()
