#!/usr/bin/env python3
"""Generate reduced illustrative RQ plots and a final artifact report.

The plots are intentionally derived from the reduced artifact summary CSVs. They
are not exact reproductions of the full-paper figures.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import polars as pl

try:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover - exercised only when env is broken.
    print(
        "ERROR: matplotlib is required to generate reduced RQ plots. "
        "Install the project environment with uv and rerun this script.",
        file=sys.stderr,
    )
    print(f"Import failure: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc

DEFAULT_RQ1 = Path("output/artifact/reduced/rq1/rq1_sampling_quality_summary.csv")
DEFAULT_RQ2 = Path("output/artifact/reduced/rq2/rq2_ablation_summary.csv")
DEFAULT_RQ3 = Path("output/artifact/reduced/rq3/rq3_rca_effectiveness_summary.csv")
DEFAULT_RQ4 = Path("output/artifact/reduced/rq4/rq4_efficiency_summary.csv")
DEFAULT_FIGURE_DIR = Path("output/artifact/reduced/figures")
DEFAULT_REPORT = Path("output/artifact/reduced/REPORT.md")

STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.labelcolor": "#222222",
    "xtick.color": "#222222",
    "ytick.color": "#222222",
    "font.size": 9,
    "savefig.dpi": 150,
}
COLORS = ["#356f8c", "#f28e2b", "#4e9f3d", "#b35c1e", "#6b7280", "#8c6bb1"]

RQ1_METRICS = [
    "avg_api_coverage",
    "avg_path_coverage_dedup",
    "avg_event_coverage",
    "avg_shannon_entropy",
    "avg_proportion_anomaly",
    "avg_proportion_rare",
]
RQ2_METRICS = [
    "avg_api_coverage",
    "avg_event_coverage",
    "avg_shannon_entropy",
    "avg_proportion_anomaly",
]
RQ3_METRICS = ["accuracy_at_1_mean", "accuracy_at_3_mean"]
RQ4_METRICS = [
    "avg_runtime_per_trace_ms",
    "avg_actual_sampling_rate",
    "avg_benefit_cost_ratio",
]

PAPER_MAPPING = {
    "rq1": "Paper RQ1: Sampling Quality and Diversity (Fig. 4, Fig. 5, Finding 1)",
    "rq2": "Paper RQ2: Ablation Study (Table 5, Fig. 6, Fig. 7, Table 7, Finding 2)",
    "rq3": "Paper RQ3: Impact on Downstream Root Cause Analysis (Table 6, Table 7, Finding 3)",
    "rq4": "Paper RQ4: Efficiency Analysis (Table 8, Finding 4)",
}


@dataclass(frozen=True)
class PlotSpec:
    rq: str
    title: str
    input_csv: Path
    output_png: str
    output_data_csv: str
    metrics: list[str]
    item_columns: list[str]
    max_items: int | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate reduced illustrative RQ plots and final report from summary CSVs."
    )
    parser.add_argument("--rq1-summary", type=Path, default=DEFAULT_RQ1)
    parser.add_argument("--rq2-summary", type=Path, default=DEFAULT_RQ2)
    parser.add_argument("--rq3-summary", type=Path, default=DEFAULT_RQ3)
    parser.add_argument("--rq4-summary", type=Path, default=DEFAULT_RQ4)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def finite_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def label_for_metric(metric: str) -> str:
    labels = {
        "avg_api_coverage": "API coverage",
        "avg_path_coverage_dedup": "Path coverage",
        "avg_event_coverage": "Trace pattern coverage",
        "avg_unique_trace_coverage": "Trace pattern coverage",
        "avg_shannon_entropy": "Shannon entropy",
        "avg_proportion_anomaly": "Anomaly proportion",
        "avg_proportion_rare": "Rare proportion",
        "avg_gt_trace_proportion": "GT trace proportion",
        "avg_runtime_per_trace_ms": "Runtime / trace (ms)",
        "avg_actual_sampling_rate": "Actual sampling rate",
        "avg_benefit_cost_ratio": "Benefit-cost ratio",
        "accuracy_at_1_mean": "Accuracy@1 mean",
        "accuracy_at_3_mean": "Accuracy@3 mean",
    }
    return labels.get(metric, metric.replace("_", " ").title())


def read_summary(path: Path) -> pl.DataFrame:
    if not path.exists():
        fail(f"required summary CSV not found: {path}; run bash scripts/run_reduced_all.sh first")
    try:
        df = pl.read_csv(path)
    except Exception as exc:
        fail(f"failed to read {path}: {exc}")
    if df.height == 0:
        fail(f"summary CSV has no rows: {path}")
    return df


def available_metrics(df: pl.DataFrame, metrics: Iterable[str], rq: str) -> list[str]:
    selected = [metric for metric in metrics if metric in df.columns]
    if not selected:
        fail(f"{rq} summary has none of the known plot metric columns: {', '.join(metrics)}")
    return selected


def item_label(row: dict[str, object], columns: list[str]) -> str:
    parts: list[str] = []
    for col in columns:
        if col in row and row[col] is not None:
            value = row[col]
            if isinstance(value, float):
                parts.append(f"{value:g}")
            else:
                parts.append(str(value))
    return " | ".join(parts) if parts else "row"


def build_plot_rows(df: pl.DataFrame, spec: PlotSpec, metrics: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    item_columns = [column for column in spec.item_columns if column in df.columns]
    source_rows = df.sort(item_columns).iter_rows(named=True) if item_columns else df.iter_rows(named=True)
    for row in source_rows:
        item = item_label(row, item_columns)
        for metric in metrics:
            value = finite_float(row.get(metric))
            if value is None:
                continue
            rows.append(
                {
                    "row_id": f"{spec.rq}|{item}|{metric}",
                    "rq": spec.rq,
                    "paper_mapping": PAPER_MAPPING[spec.rq],
                    "item": item,
                    "metric": metric,
                    "metric_label": label_for_metric(metric),
                    "value": f"{value:.12g}",
                }
            )
    if not rows:
        fail(f"{spec.rq} summary produced no finite values for selected metrics: {', '.join(metrics)}")
    return rows


def write_plot_data(path: Path, rows: list[dict[str, str]]) -> None:
    headers = ["row_id", "rq", "paper_mapping", "item", "metric", "metric_label", "value"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def plot_grouped_bars(rows: list[dict[str, str]], title: str, output_png: Path, max_items: int | None) -> None:
    metrics = sorted({row["metric"] for row in rows})
    metric_labels = {row["metric"]: row["metric_label"] for row in rows}
    items = sorted({row["item"] for row in rows})
    if max_items is not None and len(items) > max_items:
        # Keep plots readable while preserving all values in the plot-data CSV.
        score_by_item: dict[str, float] = {item: 0.0 for item in items}
        for row in rows:
            score_by_item[row["item"]] += abs(float(row["value"]))
        items = sorted(items, key=lambda item: (-score_by_item[item], item))[:max_items]
        items = sorted(items)

    values = {(row["item"], row["metric"]): float(row["value"]) for row in rows}
    width = min(0.8 / max(len(metrics), 1), 0.22)
    x_positions = list(range(len(items)))

    with plt.rc_context(STYLE):
        fig_width = max(8.0, min(18.0, 0.45 * len(items) + 2.0))
        fig, ax = plt.subplots(figsize=(fig_width, 4.8))
        offsets = [((idx - (len(metrics) - 1) / 2) * width) for idx in range(len(metrics))]
        for idx, metric in enumerate(metrics):
            heights = [values.get((item, metric), 0.0) for item in items]
            positions = [x + offsets[idx] for x in x_positions]
            ax.bar(
                positions,
                heights,
                width=width,
                label=metric_labels.get(metric, metric),
                color=COLORS[idx % len(COLORS)],
            )
        ax.set_title(title)
        ax.set_ylabel("Metric value")
        ax.set_xticks(x_positions)
        ax.set_xticklabels(items, rotation=45, ha="right")
        ax.grid(axis="y", color="#dddddd", linewidth=0.7)
        ax.legend(loc="best", fontsize=8)
        fig.tight_layout()
        output_png.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_png, bbox_inches="tight")
        plt.close(fig)


def write_manifest(path: Path, entries: list[dict[str, object]]) -> None:
    payload = {
        "description": "Reduced illustrative plots generated from reduced artifact summary CSVs; not exact full-paper figure reproductions.",
        "plot_count": len(entries),
        "plots": entries,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_plot_data_summary(path: Path, entries: list[dict[str, object]]) -> None:
    headers = ["rq", "paper_mapping", "input_csv", "plot_png", "plot_data_csv", "metrics", "row_count"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "rq": entry["rq"],
                    "paper_mapping": entry["paper_mapping"],
                    "input_csv": entry["input_csv"],
                    "plot_png": entry["plot_png"],
                    "plot_data_csv": entry["plot_data_csv"],
                    "metrics": ";".join(entry["metrics"]),
                    "row_count": entry["row_count"],
                }
            )


def write_report(path: Path, entries: list[dict[str, object]], summary_paths: list[Path]) -> None:
    lines = [
        "# Reduced Artifact Report",
        "",
        "This report is generated from the reduced artifact summary CSVs.",
        "",
        "Important caveat: the PNGs are reduced illustrative plots generated from the reduced artifact summaries. They are not claimed to be exact reproductions of the full-paper Fig. 4-Fig. 7 or paper-ready tables.",
        "",
        "## Inputs",
        "",
    ]
    for path_item in summary_paths:
        lines.append(f"- `{path_item}`")
    lines.extend(
        [
            "",
            "## RQ Mapping",
            "",
            "| Artifact output | Paper target | Generated plot | Plot data |",
            "|---|---|---|---|",
        ]
    )
    for entry in entries:
        lines.append(
            f"| {entry['rq'].upper()} | {entry['paper_mapping']} | `{entry['plot_png']}` | `{entry['plot_data_csv']}` |"
        )
    lines.extend(
        [
            "",
            "## Generated Outputs",
            "",
        ]
    )
    for entry in entries:
        metrics = ", ".join(str(metric) for metric in entry["metrics"])
        lines.extend(
            [
                f"### {entry['rq'].upper()}",
                "",
                f"- Plot: `{entry['plot_png']}`",
                f"- Plot data: `{entry['plot_data_csv']}`",
                f"- Selected metrics: {metrics}",
                f"- Plot-data rows: {entry['row_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Validation Summary",
            "",
            "- RQ summary generation: performed by `bash scripts/run_reduced_all.sh` before this plotting step.",
            "- Plot-data comparison: `scripts/run_reduced_plots.sh` compares CSV/JSON/Markdown outputs against `artifact_expected/reduced/figures/` when expected files are present.",
            "- Image validation: `scripts/run_reduced_plots.sh` checks each generated PNG exists and is non-empty; image bytes are not compared.",
            "- Scope: reduced artifact evidence only; full-dataset plotting and exact full-paper figure reproduction remain outside this snapshot.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    specs = [
        PlotSpec(
            "rq1",
            "RQ1 Reduced Sampling Quality Metrics",
            args.rq1_summary,
            "rq1_sampling_quality_metrics.png",
            "rq1_sampling_quality_plot_data.csv",
            RQ1_METRICS,
            ["display_name"],
            max_items=16,
        ),
        PlotSpec(
            "rq2",
            "RQ2 Reduced Ablation Metrics",
            args.rq2_summary,
            "rq2_ablation_metrics.png",
            "rq2_ablation_plot_data.csv",
            RQ2_METRICS,
            ["display_name"],
            max_items=16,
        ),
        PlotSpec(
            "rq3",
            "RQ3 Reduced RCA Effectiveness",
            args.rq3_summary,
            "rq3_rca_effectiveness_ac.png",
            "rq3_rca_effectiveness_plot_data.csv",
            RQ3_METRICS,
            ["algorithm", "sampler_name", "sampler_rate", "sampler_mode"],
            max_items=24,
        ),
        PlotSpec(
            "rq4",
            "RQ4 Reduced Efficiency Metrics",
            args.rq4_summary,
            "rq4_efficiency_metrics.png",
            "rq4_efficiency_plot_data.csv",
            RQ4_METRICS,
            ["sampler"],
            max_items=16,
        ),
    ]

    args.figure_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    for spec in specs:
        df = read_summary(spec.input_csv)
        metrics = available_metrics(df, spec.metrics, spec.rq)
        rows = build_plot_rows(df, spec, metrics)
        data_path = args.figure_dir / spec.output_data_csv
        png_path = args.figure_dir / spec.output_png
        write_plot_data(data_path, rows)
        plot_grouped_bars(rows, spec.title, png_path, spec.max_items)
        if not png_path.exists() or png_path.stat().st_size <= 0:
            fail(f"plot was not written or is empty: {png_path}")
        entries.append(
            {
                "rq": spec.rq,
                "paper_mapping": PAPER_MAPPING[spec.rq],
                "input_csv": str(spec.input_csv),
                "plot_png": str(png_path),
                "plot_data_csv": str(data_path),
                "metrics": metrics,
                "row_count": len(rows),
            }
        )

    write_manifest(args.figure_dir / "plot_manifest.json", entries)
    write_plot_data_summary(args.figure_dir / "plot_data_summary.csv", entries)
    write_report(args.report, entries, [spec.input_csv for spec in specs])
    print(f"[plots] wrote reduced plots to {args.figure_dir}")
    print(f"[plots] wrote final report to {args.report}")


if __name__ == "__main__":
    main()
