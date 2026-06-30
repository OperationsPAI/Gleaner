#!/usr/bin/env python3
"""Apply the deterministic Gleaner reduced Dataset A manifest."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "rcabench-platform-v2"
MANIFEST = ROOT / "configs" / "reduced" / "reduced20_datapacks.json"
SRC_DATASET = "gleaner"
DST_DATASET = "gleaner_lite"


def load_manifest() -> list[str]:
    with MANIFEST.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    datapacks = [entry["datapack"] for entry in payload["datapacks"]]
    if len(datapacks) != len(set(datapacks)):
        raise SystemExit("reduced manifest contains duplicate datapacks")
    return datapacks


def copy_datapacks(datapacks: list[str]) -> None:
    src_root = DATA_ROOT / "data" / SRC_DATASET
    dst_root = DATA_ROOT / "data" / DST_DATASET
    shutil.rmtree(dst_root, ignore_errors=True)
    dst_root.mkdir(parents=True, exist_ok=True)
    for datapack in datapacks:
        src = src_root / datapack
        if not src.exists():
            raise SystemExit(f"missing source datapack: {src}")
        dst = dst_root / datapack
        shutil.copytree(src, dst, symlinks=False)
        shutil.rmtree(dst / "sampled", ignore_errors=True)


def copy_meta(datapacks: list[str]) -> None:
    src_meta = DATA_ROOT / "meta" / SRC_DATASET
    dst_meta = DATA_ROOT / "meta" / DST_DATASET
    dst_meta.mkdir(parents=True, exist_ok=True)
    order = pl.DataFrame({"datapack": datapacks, "_order": list(range(len(datapacks)))})
    for name in ["index.parquet", "labels.parquet", "attributes.parquet"]:
        df = pl.read_parquet(src_meta / name)
        df = df.filter(pl.col("datapack").is_in(datapacks)).with_columns(
            pl.lit(DST_DATASET).alias("dataset")
        )
        if name == "index.parquet":
            df = df.join(order, on="datapack", how="left").sort("_order").drop("_order")
        df.write_parquet(dst_meta / name)


def main() -> None:
    datapacks = load_manifest()
    copy_datapacks(datapacks)
    copy_meta(datapacks)
    print(f"Created {DST_DATASET} with {len(datapacks)} datapacks from {SRC_DATASET}")


if __name__ == "__main__":
    main()
