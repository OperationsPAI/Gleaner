#!/usr/bin/env python3
"""Generate reduced RQ2 RCA effectiveness outputs from RCA parquet files."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import polars as pl

DEFAULT_OUTPUT_DIR = Path("output/artifact/reduced/rq2")
DEFAULT_SAMPLING_RATES = (0.01, 0.1)
REQUIRED_COLUMNS = {"algorithm", "sampler.name", "sampler.rate", "AC@1", "AC@3"}
OUTPUT_MD = "rq2_rca_effectiveness_results.md"
OUTPUT_CSV = "rq2_rca_effectiveness_summary.csv"
OUTPUT_JSON = "rq2_rca_effectiveness_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate reduced RQ2 RCA effectiveness summaries."
    )
    parser.add_argument(
        "--shapleyiq-microrca-parquet",
        required=True,
        type=Path,
        help="Parquet with ShapleyIQ and MicroRCA RCA metrics.",
    )
    parser.add_argument(
        "--nezha-parquet",
        required=True,
        type=Path,
        help="Parquet with Nezha RCA metrics.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for RQ2 outputs (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--sampling-rate",
        action="append",
        type=float,
        default=None,
        help=(
            "Sampling rate to include; repeatable. "
            "Defaults to 0.01 and 0.1 when omitted."
        ),
    )
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_input(path: Path, label: str) -> pl.DataFrame:
    if not path.exists():
        fail(f"{label} parquet does not exist: {path}")
    try:
        df = pl.read_parquet(path)
    except Exception as exc:  # pragma: no cover - exact backend exception varies.
        fail(f"failed to read {label} parquet {path}: {exc}")

    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        fail(
            f"{label} parquet {path} is missing required columns: "
            f"{', '.join(missing)}"
        )
    return df


def finite_or_none(value: Any) -> float | None:
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def validate_sampling_rates(sampling_rates: list[float]) -> list[float]:
    bad_values = [repr(rate) for rate in sampling_rates if not math.isfinite(rate)]
    if bad_values:
        fail(
            "--sampling-rate values must be finite numbers; "
            f"non-finite value(s): {', '.join(bad_values)}"
        )
    return sorted(set(sampling_rates))


def validate_finite_summary_columns(df: pl.DataFrame) -> None:
    bad_counts: list[str] = []
    for column in ("sampler.rate", "AC@1", "AC@3"):
        values = pl.col(column).cast(pl.Float64, strict=False)
        bad_count = df.select(
            (values.is_null() | values.is_nan() | values.is_infinite())
            .sum()
            .alias("bad_count")
        ).item()
        if bad_count:
            bad_counts.append(f"{column}: {bad_count} bad row(s)")

    if bad_counts:
        fail(
            "non-finite numeric values found in rows selected for RQ2 summary: "
            + "; ".join(bad_counts)
        )


def format_number(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.4f}"


def rate_label(rate: float) -> str:
    return f"{rate:.3f}"


def combine_and_summarize(
    shapleyiq_microrca: pl.DataFrame,
    nezha: pl.DataFrame,
    sampling_rates: list[float],
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    combined = pl.concat([shapleyiq_microrca, nezha], how="vertical")
    filtered = combined.filter(pl.col("sampler.rate").is_in(sampling_rates))
    if filtered.is_empty():
        available = sorted(combined.get_column("sampler.rate").unique().to_list())
        fail(
            "no rows matched requested --sampling-rate values "
            f"{sampling_rates}; available sampler.rate values: {available}"
        )

    validate_finite_summary_columns(filtered)

    summary = (
        filtered.group_by(["algorithm", "sampler.name", "sampler.rate"])
        .agg(
            pl.len().alias("row_count"),
            pl.col("AC@1").mean().alias("AC@1_mean"),
            pl.col("AC@3").mean().alias("AC@3_mean"),
        )
        .sort(["algorithm", "sampler.name", "sampler.rate"])
    )

    records: list[dict[str, Any]] = []
    for row in summary.iter_rows(named=True):
        records.append(
            {
                "algorithm": row["algorithm"],
                "sampler_name": row["sampler.name"],
                "sampler_rate": float(row["sampler.rate"]),
                "row_count": int(row["row_count"]),
                "ac_at_1_mean": finite_or_none(row["AC@1_mean"]),
                "ac_at_3_mean": finite_or_none(row["AC@3_mean"]),
            }
        )
    return filtered, records


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fieldnames = [
        "row_key",
        "algorithm",
        "sampler_name",
        "sampler_rate",
        "row_count",
        "ac_at_1_mean",
        "ac_at_3_mean",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "row_key": (
                        f"{record['algorithm']}|{record['sampler_name']}|"
                        f"{rate_label(record['sampler_rate'])}"
                    ),
                    "algorithm": record["algorithm"],
                    "sampler_name": record["sampler_name"],
                    "sampler_rate": rate_label(record["sampler_rate"]),
                    "row_count": record["row_count"],
                    "ac_at_1_mean": format_number(record["ac_at_1_mean"]),
                    "ac_at_3_mean": format_number(record["ac_at_3_mean"]),
                }
            )


def best_record(
    records: list[dict[str, Any]], algorithm: str, rate: float, metric: str
) -> dict[str, Any] | None:
    candidates = [
        record
        for record in records
        if record["algorithm"] == algorithm
        and record["sampler_rate"] == rate
        and record[metric] is not None
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda record: record[metric])


def write_markdown(
    path: Path,
    records: list[dict[str, Any]],
    sampling_rates: list[float],
    input_rows: int,
) -> None:
    algorithms = sorted({record["algorithm"] for record in records})
    lines = [
        "# RQ2: RCA Effectiveness",
        "",
        "This reduced artifact summarizes RCA accuracy after sampling.",
        f"- Sampling rates: {', '.join(rate_label(rate) for rate in sampling_rates)}",
        "- Metrics: AC@1 and AC@3 means grouped by RCA algorithm, sampler, and rate.",
        f"- Matched input rows: {input_rows}",
        "",
    ]

    for algorithm in algorithms:
        lines.extend(
            [
                f"## {algorithm}",
                "",
                "| Sampler | Rate | Rows | AC@1 Mean | AC@3 Mean |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for record in records:
            if record["algorithm"] != algorithm:
                continue
            lines.append(
                "| {sampler} | {rate} | {rows} | {ac1} | {ac3} |".format(
                    sampler=record["sampler_name"],
                    rate=rate_label(record["sampler_rate"]),
                    rows=record["row_count"],
                    ac1=format_number(record["ac_at_1_mean"]),
                    ac3=format_number(record["ac_at_3_mean"]),
                )
            )
        lines.append("")

    lines.extend(["## Best Samplers By Rate", ""])
    for algorithm in algorithms:
        lines.append(f"### {algorithm}")
        for rate in sampling_rates:
            best_ac1 = best_record(records, algorithm, rate, "ac_at_1_mean")
            best_ac3 = best_record(records, algorithm, rate, "ac_at_3_mean")
            ac1_text = (
                "N/A"
                if best_ac1 is None
                else f"{best_ac1['sampler_name']} ({format_number(best_ac1['ac_at_1_mean'])})"
            )
            ac3_text = (
                "N/A"
                if best_ac3 is None
                else f"{best_ac3['sampler_name']} ({format_number(best_ac3['ac_at_3_mean'])})"
            )
            lines.append(f"- Rate {rate_label(rate)}: AC@1 {ac1_text}; AC@3 {ac3_text}")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_json(
    path: Path,
    records: list[dict[str, Any]],
    sampling_rates: list[float],
    input_rows: int,
    args: argparse.Namespace,
) -> None:
    payload = {
        "config": {
            "shapleyiq_microrca_parquet": str(args.shapleyiq_microrca_parquet),
            "nezha_parquet": str(args.nezha_parquet),
            "output_dir": str(args.output_dir),
            "sampling_rates": sampling_rates,
        },
        "input_rows_matched": input_rows,
        "summary": records,
    }
    serialized = json.dumps(payload, allow_nan=False, indent=2, sort_keys=True)
    path.write_text(serialized + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    sampling_rates = validate_sampling_rates(list(args.sampling_rate or DEFAULT_SAMPLING_RATES))

    shapleyiq_microrca = validate_input(
        args.shapleyiq_microrca_parquet, "ShapleyIQ/MicroRCA"
    )
    nezha = validate_input(args.nezha_parquet, "Nezha")
    filtered, records = combine_and_summarize(shapleyiq_microrca, nezha, sampling_rates)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_markdown(args.output_dir / OUTPUT_MD, records, sampling_rates, filtered.height)
    write_csv(args.output_dir / OUTPUT_CSV, records)
    write_json(args.output_dir / OUTPUT_JSON, records, sampling_rates, filtered.height, args)

    print(f"[rq2] wrote {args.output_dir / OUTPUT_MD}")
    print(f"[rq2] wrote {args.output_dir / OUTPUT_CSV}")
    print(f"[rq2] wrote {args.output_dir / OUTPUT_JSON}")


if __name__ == "__main__":
    main()
