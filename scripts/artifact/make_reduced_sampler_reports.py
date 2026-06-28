#!/usr/bin/env python3
"""Build a deterministic fault-balanced reduced sampler report from detailed reports."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import polars as pl

DEFAULT_INPUT_DETAILED = Path(
    "data/artifact/reduced/rq1/gleaner_source.detailed_perf.parquet"
)
DEFAULT_OUTPUT_DIR = Path("output/rcabench-platform-v2/sampler_reports/gleaner_reduced20")
DEFAULT_SUBSET_SIZE = 20
META_COLUMNS = {"dataset", "datapack", "sampler", "sampling_rate", "mode"}
COLUMN_ALIASES = {
    "comprehensiveness": "api_coverage",
}
CATEGORY_PATTERNS = [
    "request-delay",
    "response-delay",
    "latency",
    "delay",
    "loss",
    "exception",
    "stress",
    "container-kill",
    "corrupt",
    "partition",
    "replace-method",
    "replace-body",
    "replace-code",
    "return",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create fault-balanced reduced20 sampler detailed/aggregated parquets."
    )
    parser.add_argument("--input-detailed", type=Path, default=DEFAULT_INPUT_DETAILED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--subset-size", type=int, default=DEFAULT_SUBSET_SIZE)
    parser.add_argument("--manifest", type=Path, default=None)
    return parser.parse_args()


def fault_category(datapack: str) -> str:
    name = datapack.lower()
    for pattern in CATEGORY_PATTERNS:
        if pattern in name:
            return pattern
    return "other"


def choose_balanced_datapacks(df: pl.DataFrame, subset_size: int) -> list[str]:
    datapack_stats = (
        df.group_by("datapack")
        .agg(
            pl.col("total_traces").median().alias("median_total_traces"),
            pl.col("total_span_count").median().alias("median_total_spans"),
        )
        .with_columns(
            pl.col("datapack")
            .map_elements(fault_category, return_dtype=pl.String)
            .alias("fault_category")
        )
        .sort(["fault_category", "median_total_traces", "datapack"])
    )

    by_category: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in datapack_stats.iter_rows(named=True):
        by_category[str(row["fault_category"])].append(row)

    selected: list[str] = []
    categories = sorted(by_category)

    # First cover every observable fault category, then allocate the remaining
    # budget to larger categories so the subset is both diverse and representative.
    for category in categories:
        selected.append(str(by_category[category][0]["datapack"]))
        if len(selected) == subset_size:
            return sorted(selected)

    remaining_categories = sorted(
        categories,
        key=lambda category: (-len(by_category[category]), category),
    )
    round_index = 1
    while len(selected) < subset_size:
        progressed = False
        for category in remaining_categories:
            rows = by_category[category]
            if round_index < len(rows):
                selected.append(str(rows[round_index]["datapack"]))
                progressed = True
                if len(selected) == subset_size:
                    break
        if not progressed:
            break
        round_index += 1

    if len(selected) < subset_size:
        raise SystemExit(
            f"could only select {len(selected)} datapacks from {len(categories)} categories"
        )
    return sorted(selected)


def aggregate_detailed(df: pl.DataFrame) -> pl.DataFrame:
    metric_columns = [
        col
        for col, dtype in zip(df.columns, df.dtypes, strict=True)
        if col not in META_COLUMNS and dtype.is_numeric()
    ]
    aggregations: list[pl.Expr] = [pl.len().alias("datapack_count")]
    aggregations.extend(
        pl.col(col).mean().alias(f"avg_{COLUMN_ALIASES.get(col, col)}")
        for col in metric_columns
    )
    aggregations.extend(
        pl.col(col).std().alias(f"std_{COLUMN_ALIASES.get(col, col)}")
        for col in metric_columns
    )
    aggregations.extend(
        pl.col(col).min().alias(f"min_{COLUMN_ALIASES.get(col, col)}")
        for col in metric_columns
    )
    aggregations.extend(
        pl.col(col).max().alias(f"max_{COLUMN_ALIASES.get(col, col)}")
        for col in metric_columns
    )
    return (
        df.group_by(["sampler", "dataset", "sampling_rate", "mode"])
        .agg(aggregations)
        .sort(["sampler", "dataset", "sampling_rate", "mode"])
    )


def write_text_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    widths = {
        col: max(len(col), *(len(str(row.get(col, ""))) for row in rows))
        for col in columns
    }
    sep = "  ".join("-" * widths[col] for col in columns)
    lines = ["  ".join(col.ljust(widths[col]) for col in columns), sep]
    for row in rows:
        lines.append("  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if args.subset_size <= 0:
        raise SystemExit("--subset-size must be positive")
    if not args.input_detailed.exists():
        raise SystemExit(f"missing input detailed parquet: {args.input_detailed}")

    detailed = pl.read_parquet(args.input_detailed)
    missing = META_COLUMNS - set(detailed.columns)
    if missing:
        raise SystemExit(f"input detailed parquet missing columns: {sorted(missing)}")

    selected = choose_balanced_datapacks(detailed, args.subset_size)
    reduced = detailed.filter(pl.col("datapack").is_in(selected)).sort(
        ["datapack", "sampler", "sampling_rate", "mode"]
    )
    aggregated = aggregate_detailed(reduced)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    detailed_path = args.output_dir / "detailed_perf.parquet"
    aggregated_path = args.output_dir / "aggregated_perf.parquet"
    subset_path = args.output_dir / "reduced20_datapacks.json"
    summary_path = args.output_dir / "reduced20_fault_summary.csv"

    reduced.write_parquet(detailed_path)
    aggregated.write_parquet(aggregated_path)

    subset_rows = [
        {"datapack": dp, "fault_category": fault_category(dp)} for dp in selected
    ]
    subset_path.write_text(json.dumps(subset_rows, indent=2, sort_keys=True) + "\n")

    summary = (
        pl.DataFrame(subset_rows)
        .group_by("fault_category")
        .agg(pl.len().alias("datapack_count"))
        .sort(["datapack_count", "fault_category"], descending=[True, False])
    )
    summary.write_csv(summary_path)

    if args.manifest is not None:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": "1.0",
            "source_detailed": str(args.input_detailed),
            "output_dir": str(args.output_dir),
            "subset_size": args.subset_size,
            "datapacks": subset_rows,
            "fault_category_counts": summary.to_dicts(),
        }
        args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(f"[reduced-data] wrote {detailed_path}")
    print(f"[reduced-data] wrote {aggregated_path}")
    print(f"[reduced-data] selected {len(selected)} fault-balanced datapacks")
    print(write_text_table(summary.to_dicts(), ["fault_category", "datapack_count"]))


if __name__ == "__main__":
    main()
