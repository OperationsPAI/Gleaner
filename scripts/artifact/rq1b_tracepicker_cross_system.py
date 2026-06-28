#!/usr/bin/env python3
"""Generate reduced RQ1-B cross-system evidence for TracePicker Dataset B."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_INPUT = Path("../TracePicker/TracePicker/data")
DEFAULT_SUMMARY = Path("data/artifact/reduced/rq1b_tracepicker_cross_system_summary.csv")
DEFAULT_OUTPUT = Path("output/artifact/reduced/rq1_cross_system")
SYSTEMS = ["trainticket", "media", "onlineBoutique", "sockshop", "socialNetwork"]
DISPLAY = {
    "trainticket": "Train Ticket",
    "media": "Media",
    "onlineBoutique": "Online Boutique",
    "sockshop": "Sock Shop",
    "socialNetwork": "Social Network",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--summary-input", type=Path, default=DEFAULT_SUMMARY, help="Portable precomputed reduced Dataset B summary CSV")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def read_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        fail(f"missing TracePicker Dataset B file: {path}")
    return pd.read_csv(path, usecols=columns)


def summarize_system(root: Path, system: str) -> dict[str, Any]:
    folder = root / system
    traces = read_csv(folder / "traces_traces.csv")
    spans = read_csv(folder / "traces_spans.csv", columns=["traceID", "service", "operation", "statusCode"])
    types = read_csv(folder / "type.csv", columns=["traceId", "pathId"])
    nodes = read_csv(folder / "nodes.csv")

    trace_count = int(traces["traceID"].nunique())
    span_count = int(len(spans))
    service_count = int(spans["service"].nunique(dropna=True))
    node_count = int(nodes.iloc[:, 0].nunique(dropna=True))
    operation_count = int((spans["service"].astype(str) + ":" + spans["operation"].astype(str)).nunique())
    path_count = int(types["pathId"].nunique(dropna=True))
    avg_spans = float(traces["span_count"].mean())
    p95_spans = float(traces["span_count"].quantile(0.95))
    error_rate = float(traces["isError"].mean()) if "isError" in traces else 0.0
    abnormal_rate = float(traces["abnormal"].mean()) if "abnormal" in traces else 0.0
    status_error_rate = float((pd.to_numeric(spans["statusCode"], errors="coerce") >= 400).mean())

    return {
        "system": system,
        "display_name": DISPLAY.get(system, system),
        "trace_count": trace_count,
        "span_count": span_count,
        "service_count": service_count,
        "node_count": node_count,
        "operation_count": operation_count,
        "path_type_count": path_count,
        "avg_spans_per_trace": avg_spans,
        "p95_spans_per_trace": p95_spans,
        "trace_error_rate": error_rate,
        "trace_abnormal_rate": abnormal_rate,
        "span_status_error_rate": status_error_rate,
    }


def fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def make_markdown(rows: list[dict[str, Any]], input_root: Path, output_dir: Path) -> str:
    lines = [
        "# RQ1-B: Dataset B Cross-System Evidence",
        "",
        "## Configuration",
        "",
        f"- Input root: `{input_root}`",
        f"- Output directory: `{output_dir}`",
        "- Systems: " + ", ".join(row["display_name"] for row in rows),
        "- Scope: reduced cross-system evidence from TracePicker Dataset B raw traces; full sampler-baseline cross-system reproduction is reserved for the full pipeline.",
        "",
        "## Cross-System Summary",
        "",
    ]
    cols = [
        ("display_name", "System"),
        ("trace_count", "Traces"),
        ("span_count", "Spans"),
        ("service_count", "Services"),
        ("operation_count", "Operations"),
        ("path_type_count", "Path Types"),
        ("avg_spans_per_trace", "Avg Spans/Trace"),
        ("trace_error_rate", "Trace Error Rate"),
    ]
    lines.append("| " + " | ".join(label for _, label in cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(fmt(row[key]) for key, _ in cols) + " |")
    lines += [
        "",
        "## Interpretation",
        "",
        "- Dataset B spans five heterogeneous microservice systems with different trace volumes, service counts, path types, and span depths.",
        "- This reduced evidence supports the cross-system part of RQ1 at the dataset-diversity/input-coverage level without rerunning expensive baseline samplers.",
        "- Full paper-equivalent cross-system sampler comparison should use the full pipeline to regenerate TracePicker sampler reports and paper figures.",
        "",
    ]
    return "\n".join(lines)


def plot(rows: list[dict[str, Any]], output_dir: Path) -> None:
    df = pd.DataFrame(rows)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    x = range(len(df))
    labels = df["display_name"].tolist()
    specs = [
        ("trace_count", "Traces"),
        ("service_count", "Services"),
        ("path_type_count", "Path Types"),
    ]
    colors = ["#2b6f6c", "#d58a2a", "#6f7d2b"]
    for ax, (metric, title), color in zip(axes, specs, colors, strict=True):
        ax.bar(x, df[metric], color=color, alpha=0.88)
        ax.set_title(title, fontsize=12, weight="bold")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=9)
        ax.grid(axis="y", alpha=0.25, linestyle="--")
    fig.suptitle("RQ1-B Dataset B Cross-System Scale", fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(output_dir / "rq1b_tracepicker_cross_system.png", dpi=200)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    if args.summary_input.exists():
        rows = pd.read_csv(args.summary_input).to_dict(orient="records")
    else:
        rows = [summarize_system(args.input_root, system) for system in SYSTEMS]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output_dir / "rq1b_tracepicker_cross_system_summary.csv", index=False, lineterminator="\n")
    (args.output_dir / "rq1b_tracepicker_cross_system_summary.json").write_text(json.dumps({"config": {"input_root": str(args.input_root), "output_dir": str(args.output_dir)}, "summary": rows}, indent=2) + "\n")
    (args.output_dir / "rq1b_tracepicker_cross_system_results.md").write_text(make_markdown(rows, args.input_root, args.output_dir), encoding="utf-8")
    plot(rows, args.output_dir)
    print(f"[rq1b] wrote cross-system evidence to {args.output_dir}")


if __name__ == "__main__":
    main()
