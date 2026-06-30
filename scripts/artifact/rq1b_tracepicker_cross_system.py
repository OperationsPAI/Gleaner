#!/usr/bin/env python3
"""Summarize paper-style RQ1-B Dataset B trace pattern coverage."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import polars as pl

DEFAULT_INPUT = Path("output/rcabench-platform-v2/sampler_reports/tracepicker/detailed_perf.parquet")
DEFAULT_OUTPUT = Path("output/artifact/reduced/rq1_cross_system")
DEFAULT_SAMPLERS = ("gleaner_no_logs_no_ad",)
DEFAULT_RATES = (0.1,)
DISPLAY = {
    "trainticket": "Train Ticket",
    "media": "Media",
    "onlineBoutique": "Online Boutique",
    "sockshop": "Sock Shop",
    "socialNetwork": "Social Network",
    "random": "Random",
    "sifter": "Sifter",
    "sieve": "Sieve",
    "trastrainer_no_metrics": "TraStrainer w/o Metrics",
    "tracepicker": "TracePicker",
    "gleaner_no_logs_no_ad": "Gleaner w/o Logs & Alarms",
}
REQUIRED_COLUMNS = {"sampler", "sampling_rate", "mode", "datapack"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-parquet", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sampler", action="append", default=None)
    parser.add_argument("--sampling-rate", action="append", type=float, default=None)
    parser.add_argument("--mode", default="offline")
    parser.add_argument("--system", action="append", default=None, help="Dataset B system/datapack to include; repeatable. Defaults to all systems present in the input report; the reduced runner passes the two tracepicker_lite systems.")
    return parser.parse_args()


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def finite(value: Any) -> float | None:
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def pick_trace_pattern_column(df: pl.DataFrame) -> str:
    # Platform-internal event coverage corresponds to the paper's EPS/trace-pattern coverage.
    for col in ("event_coverage", "avg_event_coverage", "unique_trace_coverage", "avg_unique_trace_coverage"):
        if col in df.columns:
            return col
    fail("input parquet has no trace-pattern coverage column; expected avg_event_coverage or equivalent")


def load_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    if not args.input_parquet.exists():
        fail(f"missing Dataset B sampler report: {args.input_parquet}")
    df = pl.read_parquet(args.input_parquet)
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        fail(f"input parquet is missing required columns: {', '.join(missing)}")
    metric = pick_trace_pattern_column(df)
    samplers = args.sampler or list(DEFAULT_SAMPLERS)
    rates = args.sampling_rate or list(DEFAULT_RATES)
    systems = args.system or ["trainticket", "media", "onlineBoutique", "sockshop", "socialNetwork"]
    filtered = df.filter(
        (pl.col("mode") == args.mode)
        & pl.col("sampler").is_in(samplers)
        & pl.col("sampling_rate").is_in(rates)
        & pl.col("datapack").is_in(systems)
    )
    if filtered.is_empty():
        available = df.select(["sampler", "sampling_rate", "mode"]).unique().sort(["sampler", "sampling_rate", "mode"])
        fail(
            "no Dataset B rows matched requested samplers/rates; available configurations: "
            + json.dumps(available.to_dicts(), default=str)[:2000]
        )
    records: list[dict[str, Any]] = []
    for row in filtered.sort(["sampler", "dataset", "sampling_rate"]).iter_rows(named=True):
        system = row["datapack"]
        records.append(
            {
                "system": system,
                "system_name": DISPLAY.get(system, system),
                "sampler": row["sampler"],
                "sampler_name": DISPLAY.get(row["sampler"], row["sampler"]),
                "sampling_rate": float(row["sampling_rate"]),
                "trace_pattern_coverage": finite(row.get(metric)),
                "source_metric": metric,
            }
        )
    return records


def make_markdown(rows: list[dict[str, Any]], input_parquet: Path, output_dir: Path) -> str:
    lines = [
        "# RQ1-B: Cross-System Trace Pattern Coverage",
        "",
        "## Configuration",
        "",
        f"- Input parquet: `{input_parquet}`",
        f"- Output directory: `{output_dir}`",
        "- Paper metric: Trace Pattern Coverage",
        "- Platform source metric: `avg_event_coverage` when available",
        "- Dataset: TracePicker Dataset B (five microservice systems)",
        "",
        "## Trace Pattern Coverage",
        "",
        "| System | Sampler | Rate | Trace Pattern Coverage |",
        "|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['system_name']} | {row['sampler_name']} | {row['sampling_rate']:.3f} | {fmt(row['trace_pattern_coverage'])} |"
        )
    lines += [
        "",
        "## Scope Note",
        "",
        "- The reduced live path reruns Gleaner w/o Logs & Alarms on Dataset B by default, matching the paper's log-free/alarm-free Dataset B setting.",
        "- Baseline Dataset B rows are included only if their sampled reports are present or explicitly generated in the full path.",
        "",
    ]
    return "\n".join(lines)


def plot(rows: list[dict[str, Any]], output_dir: Path) -> None:
    df = pl.DataFrame(rows).filter(pl.col("trace_pattern_coverage").is_not_null())
    if df.is_empty():
        return
    samplers = df.get_column("sampler_name").unique(maintain_order=True).to_list()
    systems = df.get_column("system_name").unique(maintain_order=True).to_list()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    width = 0.8 / max(1, len(samplers))
    x = list(range(len(systems)))
    for idx, sampler in enumerate(samplers):
        vals = []
        for system in systems:
            sub = df.filter((pl.col("system_name") == system) & (pl.col("sampler_name") == sampler))
            vals.append(None if sub.is_empty() else sub.get_column("trace_pattern_coverage").mean())
        offsets = [pos + (idx - (len(samplers)-1)/2) * width for pos in x]
        ax.bar(offsets, vals, width=width, label=sampler)
    ax.set_title("RQ1-B Dataset B Trace Pattern Coverage", fontsize=13, weight="bold")
    ax.set_ylabel("Trace Pattern Coverage")
    ax.set_xticks(x)
    ax.set_xticklabels(systems, rotation=25, ha="right")
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.25, linestyle="--")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "rq1b_tracepicker_cross_system.png", dpi=200)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    rows = load_rows(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_csv(args.output_dir / "rq1b_tracepicker_cross_system_summary.csv")
    (args.output_dir / "rq1b_tracepicker_cross_system_summary.json").write_text(
        json.dumps({"config": vars(args) | {"input_parquet": str(args.input_parquet), "output_dir": str(args.output_dir)}, "summary": rows}, indent=2, default=str) + "\n"
    )
    (args.output_dir / "rq1b_tracepicker_cross_system_results.md").write_text(make_markdown(rows, args.input_parquet, args.output_dir), encoding="utf-8")
    plot(rows, args.output_dir)
    print(f"[rq1b] wrote Dataset B trace-pattern coverage to {args.output_dir}")


if __name__ == "__main__":
    main()
