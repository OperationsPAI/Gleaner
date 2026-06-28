#!/usr/bin/env python3
"""Filter previous per-datapack RCA results to the reduced20 datapack subset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

DEFAULT_SUBSET = Path("configs/reduced/reduced20_datapacks.json")
DEFAULT_NEZHA = Path("../Nezha/output/rcabench-platform-v2/meta/gleaner/sampler.detailed.perf.parquet")
DEFAULT_SHAPLEY = Path("../ShapleyIQ/output/rcabench-platform-v2/meta/gleaner/sampler.detailed.perf.parquet")
DEFAULT_OUT = Path("data/artifact/reduced/rq2")
KEYS = ["algorithm", "dataset", "sampler.name", "sampler.rate", "sampler.mode"]
COUNT_COLS = [f"AC@{k}.count" for k in range(1, 6)]
RATIO_COLS = [f"AC@{k}" for k in range(1, 6)] + [f"Avg@{k}" for k in range(1, 6)] + [f"MAP@{k}" for k in range(1, 6)] + ["MRR"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", type=Path, default=DEFAULT_SUBSET)
    parser.add_argument("--nezha-detailed", type=Path, default=DEFAULT_NEZHA)
    parser.add_argument("--shapleyiq-microrca-detailed", type=Path, default=DEFAULT_SHAPLEY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def load_subset(path: Path) -> set[str]:
    payload = json.loads(path.read_text())
    return {row["datapack"] for row in payload["datapacks"]}


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    weights = weights.fillna(0)
    denom = weights.sum()
    if denom == 0:
        return float("nan")
    return float((values.fillna(0) * weights).sum() / denom)


def aggregate(filtered: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key, group in filtered.groupby(KEYS, dropna=False, sort=True):
        row = dict(zip(KEYS, key, strict=True))
        total = group["total"].sum()
        row["total"] = int(total)
        row["error"] = int(group["error"].sum()) if "error" in group else 0
        row["runtime.seconds:avg"] = weighted_mean(group["runtime.seconds:avg"], group["total"])
        for col in COUNT_COLS:
            row[col] = int(group[col].sum())
        for k in range(1, 6):
            count_col = f"AC@{k}.count"
            row[f"AC@{k}"] = float(row[count_col] / total) if total else float("nan")
        for col in ["MRR"] + [f"Avg@{k}" for k in range(1, 6)] + [f"MAP@{k}" for k in range(1, 6)]:
            if col in group:
                row[col] = weighted_mean(group[col], group["total"])
        rows.append(row)
    columns = KEYS + ["total", "error", "runtime.seconds:avg", "MRR"] + COUNT_COLS + [f"AC@{k}" for k in range(1, 6)] + [f"Avg@{k}" for k in range(1, 6)] + [f"MAP@{k}" for k in range(1, 6)]
    out = pd.DataFrame(rows)
    return out[[col for col in columns if col in out.columns]]


def filter_one(input_path: Path, output_dir: Path, subset: set[str]) -> tuple[Path, Path, pd.DataFrame]:
    if not input_path.exists():
        raise SystemExit(f"missing detailed RCA parquet: {input_path}")
    df = pd.read_parquet(input_path)
    if "datapack" not in df.columns:
        raise SystemExit(f"detailed RCA parquet has no datapack column: {input_path}")
    missing = sorted(subset - set(df["datapack"].unique()))
    if missing:
        raise SystemExit(f"{input_path} is missing reduced20 datapacks: {missing}")
    filtered = df[df["datapack"].isin(subset)].copy()
    grouped = aggregate(filtered)
    output_dir.mkdir(parents=True, exist_ok=True)
    detailed_path = output_dir / "sampler.detailed.perf.parquet"
    grouped_path = output_dir / "sampler.grouped.perf.parquet"
    filtered.to_parquet(detailed_path, index=False)
    grouped.to_parquet(grouped_path, index=False)
    return detailed_path, grouped_path, grouped


def print_summary(label: str, grouped: pd.DataFrame) -> None:
    print(f"[rq2-reduced20] {label}: {len(grouped)} grouped rows")
    view = grouped.sort_values(["AC@3", "AC@1"], ascending=False).head(5)
    for data in view.to_dict("records"):
        print(
            f"  {data['algorithm']} {data['sampler.name']} rate={data['sampler.rate']:.3g} "
            f"total={data['total']} AC@1={data['AC@1']:.4f} AC@3={data['AC@3']:.4f}"
        )


def main() -> None:
    args = parse_args()
    subset = load_subset(args.subset)
    nezha_detail, nezha_grouped, nezha_df = filter_one(
        args.nezha_detailed, args.output_dir / "nezha", subset
    )
    shapley_detail, shapley_grouped, shapley_df = filter_one(
        args.shapleyiq_microrca_detailed,
        args.output_dir / "shapleyiq_microrca",
        subset,
    )
    print(f"[rq2-reduced20] subset datapacks: {len(subset)}")
    print(f"[rq2-reduced20] wrote {nezha_detail}")
    print(f"[rq2-reduced20] wrote {nezha_grouped}")
    print_summary("nezha", nezha_df)
    print(f"[rq2-reduced20] wrote {shapley_detail}")
    print(f"[rq2-reduced20] wrote {shapley_grouped}")
    print_summary("shapleyiq_microrca", shapley_df)


if __name__ == "__main__":
    main()
