#!/usr/bin/env python3
"""Generate reduced RQ1 sampling-quality outputs from Gleaner sampler reports."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

import polars as pl

DEFAULT_INPUT_AGGREGATED = Path(
    "output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/aggregated_perf.parquet"
)
DEFAULT_INPUT_DETAILED = Path(
    "output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/detailed_perf.parquet"
)
DEFAULT_OUTPUT_DIR = Path("output/artifact/reduced/rq1")
DEFAULT_MODE = "offline"

DISPLAY_NAMES = {
    "gleaner": "Gleaner",
    "gleaner_no_logs": "Gleaner w/o Logs",
    "gleaner_no_ad": "Gleaner w/o AD",
    "gleaner_no_logs_no_ad": "Gleaner w/o Logs + AD",
    "gleaner_pure_diversity": "Gleaner Pure Diversity",
    "gleaner_small_batch": "Gleaner Small Batch",
    "gleaner_medium_batch": "Gleaner Medium Batch",
    "gleaner_unlimited_batch": "Gleaner Unlimited Batch",
    "gleaner_no_dpp": "Gleaner w/o DPP",
    "gleaner_no_rebalance": "Gleaner w/o Rebalance",
    "gleaner_latency_dominate": "Gleaner Latency-Dominant",
    "gleaner_log_dominate": "Gleaner Log-Dominant",
    "gleaner_top_score": "Gleaner Top Score",
    "gleaner_wl_kernel": "Gleaner WL Kernel",
    "tracepicker": "TracePicker",
    "trastrainer": "TrasTrainer",
    "trastrainer_no_metrics": "TrasTrainer w/o Metrics",
    "sifter": "Sifter",
    "sieve": "Sieve",
    "random": "Random",
}

REQUIRED_AGGREGATED_COLUMNS = {"sampler", "mode", "sampling_rate"}
REQUIRED_DETAILED_COLUMNS = {"sampler", "mode", "sampling_rate", "datapack"}
SUMMARY_METRICS = [
    "avg_api_coverage",
    "avg_path_coverage_dedup",
    "avg_path_coverage",
    "avg_event_coverage",
    "avg_unique_trace_coverage",
    "avg_shannon_entropy",
    "avg_proportion_anomaly",
    "avg_gt_trace_proportion",
]
REQUIRED_METRIC_CANDIDATES = [
    "avg_api_coverage",
    "avg_path_coverage_dedup",
    "avg_path_coverage",
    "avg_event_coverage",
    "avg_unique_trace_coverage",
    "avg_shannon_entropy",
    "avg_proportion_anomaly",
]
HIGHER_IS_BETTER = {
    "avg_api_coverage",
    "avg_path_coverage_dedup",
    "avg_path_coverage",
    "avg_event_coverage",
    "avg_unique_trace_coverage",
    "avg_shannon_entropy",
    "avg_proportion_anomaly",
    "avg_gt_trace_proportion",
}
LIMITATIONS = [
    "Reduced RQ1 currently summarizes existing Gleaner sampler variants.",
    "Full cross-baseline sampler comparison needs additional TracePicker/TraStrainer/Sieve/Sifter reports.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate reduced RQ1 sampling quality summaries."
    )
    parser.add_argument(
        "--input-aggregated",
        type=Path,
        default=DEFAULT_INPUT_AGGREGATED,
        help=f"Input aggregated_perf.parquet (default: {DEFAULT_INPUT_AGGREGATED})",
    )
    parser.add_argument(
        "--input-detailed",
        type=Path,
        default=DEFAULT_INPUT_DETAILED,
        help=f"Input detailed_perf.parquet (default: {DEFAULT_INPUT_DETAILED})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for RQ1 outputs (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--mode",
        default=DEFAULT_MODE,
        help=f"Sampler mode to filter (default: {DEFAULT_MODE})",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def metric_label(metric: str) -> str:
    labels = {
        "avg_api_coverage": "API Coverage",
        "avg_path_coverage_dedup": "Path Coverage Dedup",
        "avg_path_coverage": "Path Coverage",
        "avg_event_coverage": "Event Coverage",
        "avg_unique_trace_coverage": "Unique Trace Coverage",
        "avg_shannon_entropy": "Shannon Entropy",
        "avg_proportion_anomaly": "Proportion Anomaly",
        "avg_gt_trace_proportion": "GT Trace Proportion",
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
    metrics = [metric for metric in SUMMARY_METRICS if metric in column_set]
    # Prefer the de-duplicated path coverage column when both are available.
    if "avg_path_coverage_dedup" in metrics and "avg_path_coverage" in metrics:
        metrics.remove("avg_path_coverage")
    return metrics


def metric_presence_expr(metrics: list[str]) -> pl.Expr:
    expr = pl.lit(False)
    for metric in metrics:
        expr = expr | (pl.col(metric).is_not_null() & pl.col(metric).is_finite())
    return expr


def validate_parquet(path: Path, required_columns: set[str], label: str) -> pl.DataFrame:
    if not path.exists():
        fail(f"{label} parquet not found: {path}")
    df = pl.read_parquet(path)
    missing_required = sorted(required_columns - set(df.columns))
    if missing_required:
        fail(
            f"{label} parquet is missing required columns: "
            + ", ".join(missing_required)
        )
    return df


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
    input_aggregated: Path, input_detailed: Path, mode: str
) -> tuple[pl.DataFrame, pl.DataFrame, list[str], list[float], list[str]]:
    aggregated = validate_parquet(
        input_aggregated, REQUIRED_AGGREGATED_COLUMNS, "aggregated input"
    )
    detailed = validate_parquet(input_detailed, REQUIRED_DETAILED_COLUMNS, "detailed input")

    metrics = available_metrics(aggregated.columns)
    required_present = [
        metric for metric in REQUIRED_METRIC_CANDIDATES if metric in aggregated.columns
    ]
    if not required_present:
        fail(
            "aggregated input has none of the RQ1 metric columns; expected one of: "
            + ", ".join(REQUIRED_METRIC_CANDIDATES)
        )
    if not metrics:
        fail("aggregated input has no summary metrics available")

    filtered = aggregated.filter(pl.col("mode") == mode)
    detailed_filtered = detailed.filter(pl.col("mode") == mode)
    if filtered.height == 0:
        fail(
            f"no rows after filtering mode={mode!r}; available configurations: "
            f"{available_configurations(aggregated) or 'none'}"
        )
    if detailed_filtered.height == 0:
        fail(f"detailed input has no rows after filtering mode={mode!r}")

    if filtered.filter(metric_presence_expr(required_present)).height == 0:
        fail(
            "all available RQ1 metric values are missing or non-finite after filtering; "
            f"checked: {', '.join(required_present)}"
        )

    samplers = sorted(filtered.get_column("sampler").unique().to_list())
    sampling_rates = sorted(filtered.get_column("sampling_rate").unique().to_list())
    if len(samplers) < 2:
        fail(
            "RQ1 reduced sampling quality requires at least 2 samplers after filtering; "
            f"found {len(samplers)}: {', '.join(samplers) or 'none'}"
        )

    return filtered, detailed_filtered, metrics, sampling_rates, samplers


def sanitize_metric_columns(df: pl.DataFrame, metrics: list[str]) -> pl.DataFrame:
    expressions: list[pl.Expr] = []
    for metric in metrics:
        expressions.append(
            pl.when(pl.col(metric).is_finite())
            .then(pl.col(metric))
            .otherwise(None)
            .alias(metric)
        )
    return df.with_columns(expressions) if expressions else df


def datapack_counts(aggregated: pl.DataFrame, detailed: pl.DataFrame) -> pl.DataFrame:
    counts = detailed.group_by("sampler").agg(
        pl.col("datapack").n_unique().alias("datapack_count")
    )
    if "datapack_count" not in aggregated.columns:
        return counts
    fallback = aggregated.group_by("sampler").agg(
        pl.col("datapack_count").max().alias("aggregated_datapack_count")
    )
    return counts.join(fallback, on="sampler", how="full", coalesce=True).with_columns(
        pl.coalesce(["datapack_count", "aggregated_datapack_count"])
        .cast(pl.Int64)
        .alias("datapack_count")
    ).select(["sampler", "datapack_count"])


def summarize_by_sampler(
    aggregated: pl.DataFrame, detailed: pl.DataFrame, metrics: list[str]
) -> pl.DataFrame:
    aggregated = sanitize_metric_columns(aggregated, metrics)
    summary = aggregated.group_by("sampler").agg(
        [
            pl.col("sampling_rate").n_unique().alias("sample_rate_count"),
            *[pl.col(metric).mean().alias(metric) for metric in metrics],
        ]
    )
    summary = summary.join(datapack_counts(aggregated, detailed), on="sampler", how="left")
    summary = sanitize_metric_columns(summary, metrics)
    summary = summary.with_columns(
        pl.col("sampler")
        .map_elements(lambda name: DISPLAY_NAMES.get(name, name), return_dtype=pl.String)
        .alias("display_name")
    ).select(["sampler", "display_name", "sample_rate_count", "datapack_count", *metrics])
    summary = summary.sort("sampler")
    if summary.height == 0:
        fail("filtered data produced an empty sampler summary")
    return summary


def best_leaders(summary: pl.DataFrame, metrics: list[str]) -> dict[str, dict[str, Any] | None]:
    leaders: dict[str, dict[str, Any] | None] = {}
    for metric in metrics:
        non_null = summary.filter(pl.col(metric).is_not_null() & pl.col(metric).is_finite())
        if non_null.height == 0:
            leaders[metric] = None
            continue
        descending = metric in HIGHER_IS_BETTER
        best = non_null.sort([metric, "sampler"], descending=[descending, False]).head(1)
        row = best.row(0, named=True)
        leaders[metric] = {
            "sampler": row["sampler"],
            "display_name": row["display_name"],
            "value": json_safe(row[metric]),
            "higher_is_better": descending,
        }
    return leaders


def make_markdown(
    summary: pl.DataFrame,
    metrics: list[str],
    sampling_rates: list[float],
    samplers: list[str],
    input_aggregated: Path,
    input_detailed: Path,
    mode: str,
    output_dir: Path,
    leaders: dict[str, dict[str, Any] | None],
) -> str:
    lines: list[str] = []
    lines.append("# RQ1: Sampling Quality")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- Input aggregated parquet: `{input_aggregated}`")
    lines.append(f"- Input detailed parquet: `{input_detailed}`")
    lines.append(f"- Output directory: `{output_dir}`")
    lines.append(f"- Mode: `{mode}`")
    lines.append(
        "- Available sampling rates: " + ", ".join(f"`{rate:g}`" for rate in sampling_rates)
    )
    lines.append(
        "- Samplers included: "
        + ", ".join(DISPLAY_NAMES.get(sampler, sampler) for sampler in samplers)
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    headers = ["Sampler", "Display Name", "Sample Rates", "Datapacks"] + [
        metric_label(metric) for metric in metrics
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in summary.iter_rows(named=True):
        values = [
            row["sampler"],
            row["display_name"],
            str(row["sample_rate_count"]),
            str(row["datapack_count"]),
            *[format_value(row[metric]) for metric in metrics],
        ]
        lines.append("| " + " | ".join(values) + " |")

    lines.append("")
    lines.append("## Leaders")
    lines.append("")
    for metric in metrics:
        leader = leaders.get(metric)
        if leader is None:
            lines.append(f"- {metric_label(metric)}: N/A")
            continue
        direction = "higher is better" if leader["higher_is_better"] else "lower is better"
        lines.append(
            f"- {metric_label(metric)} ({direction}): "
            f"{leader['display_name']} ({format_value(leader['value'])})"
        )

    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append(
        "- Reduced RQ1 currently summarizes existing Gleaner sampler variants; full "
        "cross-baseline sampler comparison needs additional "
        "TracePicker/TraStrainer/Sieve/Sifter reports."
    )
    lines.append("- Plot files are intentionally omitted to keep expected-output comparison stable.")
    lines.append("")
    return "\n".join(lines)


def schema_payload(metrics: list[str]) -> dict[str, Any]:
    return {
        "primary_key": ["sampler"],
        "columns": [
            {"name": "sampler", "type": "string"},
            {"name": "display_name", "type": "string"},
            {"name": "sample_rate_count", "type": "integer"},
            {"name": "datapack_count", "type": "integer"},
            *[
                {
                    "name": metric,
                    "type": "number|null",
                    "label": metric_label(metric),
                    "higher_is_better": metric in HIGHER_IS_BETTER,
                }
                for metric in metrics
            ],
        ],
    }


def write_outputs(args: argparse.Namespace) -> None:
    aggregated, detailed, metrics, sampling_rates, samplers = load_filtered(
        args.input_aggregated, args.input_detailed, args.mode
    )
    summary = summarize_by_sampler(aggregated, detailed, metrics)
    leaders = best_leaders(summary, metrics)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    md_path = args.output_dir / "rq1_sampling_quality_results.md"
    csv_path = args.output_dir / "rq1_sampling_quality_summary.csv"
    json_path = args.output_dir / "rq1_sampling_quality_summary.json"

    markdown = make_markdown(
        summary=summary,
        metrics=metrics,
        sampling_rates=sampling_rates,
        samplers=samplers,
        input_aggregated=args.input_aggregated,
        input_detailed=args.input_detailed,
        mode=args.mode,
        output_dir=args.output_dir,
        leaders=leaders,
    )
    md_path.write_text(markdown, encoding="utf-8")
    summary.write_csv(csv_path, null_value="")

    payload = {
        "config": {
            "input_aggregated": str(args.input_aggregated),
            "input_detailed": str(args.input_detailed),
            "output_dir": str(args.output_dir),
            "mode": args.mode,
            "sampling_rates": sampling_rates,
            "samplers": samplers,
        },
        "schema": schema_payload(metrics),
        "summary": [
            {key: json_safe(value) for key, value in row.items()}
            for row in summary.to_dicts()
        ],
        "leaders": leaders,
        "limitations": LIMITATIONS,
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
