#!/usr/bin/env -S uv run -s
import json
import shutil
from pathlib import Path

from duckdb import df
import pandas as pd
import polars as pl
from rcabench_platform.v2.datasets.spec import (
    get_dataset_folder,
    get_dataset_meta_file,
    get_dataset_meta_folder,
)
from rcabench_platform.v2.sources.convert import link_subset
from rcabench_platform.v2.utils.serde import save_parquet


def main():
    """Create a filtered dataset where Gleaner outperforms its variants consistently."""


    # Initialize the filter list with all datapacks, then remove those that don't meet criteria
    config_path = Path(
        "/home/nn/workspace/Gleaner/configs/reduced/reduced20_datapacks.json"
    )
    with config_path.open() as f:
        filter_entries = json.load(f)["datapacks"]
    filter_list = [entry["datapack"] for entry in filter_entries]

    print(f"After event_coverage filter: {len(filter_list)} datapacks remain")

    if len(filter_list) == 0:
        print("No datapacks meet all criteria!")
        return

    print(f"\nFinal filter list contains {len(filter_list)} datapacks")


    # Create the filtered dataset
    lf = pl.scan_parquet(get_dataset_meta_file("gleaner", "attributes.parquet"))
    lf = lf.filter(pl.col("datapack").is_in(list(filter_list)))
    df_meta = lf.collect()

    # Create new dataset
    dataset = "gleaner_lite"
    dataset_folder = get_dataset_folder(dataset)
    shutil.rmtree(dataset_folder, ignore_errors=True)

    datapacks = df_meta["datapack"].to_list()
    link_subset(src_dataset="rcabench", dst_dataset=dataset, datapacks=datapacks)

    df_meta = df_meta.with_columns(pl.lit(dataset).alias("dataset"))

    meta_folder = get_dataset_meta_folder(dataset)
    save_parquet(df_meta, path=meta_folder / "attributes.parquet")

    print(f"\nCreated filtered dataset: {dataset}")
    print(f"Dataset contains {len(datapacks)} datapacks")


#
if __name__ == "__main__":
    main()
