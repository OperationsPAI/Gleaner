#!/usr/bin/env -S uv run -s

import datetime
from pathlib import Path
from typing import Any

import polars as pl

from rcabench_platform.v2.cli.main import app, logger, timeit
from rcabench_platform.v2.sources.convert import DatapackLoader, DatasetLoader, Label
from rcabench_platform.v2.utils.serde import save_parquet


def convert_tracepicker_traces(src: Path) -> pl.LazyFrame:
    """Convert TracePicker traces_spans.csv to standard format.

    Expected columns: traceID,spanId,parentSpanId,startTime,duration,statusCode,service,operation,instance
    """
    assert src.exists(), f"Source file does not exist: {src}"

    lf = pl.scan_csv(src, infer_schema_length=50000)

    # Convert to standard format
    lf = lf.select(
        # Convert startTime from microseconds to datetime UTC
        pl.from_epoch("startTime", time_unit="us").dt.replace_time_zone("UTC").alias("time"),
        pl.col("traceID").cast(pl.String).alias("trace_id"),
        pl.col("spanId").cast(pl.String).alias("span_id"),
        pl.col("parentSpanId").cast(pl.String).alias("parent_span_id"),
        pl.col("service").cast(pl.String).alias("service_name"),
        pl.col("operation").cast(pl.String).alias("span_name"),
        # Convert duration from microseconds to nanoseconds
        pl.col("duration").cast(pl.UInt64).mul(1_000).alias("duration"),
        # Handle status code - convert HTTP codes to RCABench standard format
        # Fill null with 200 (success) for internal service calls
        pl.when(pl.col("statusCode").is_null() | (pl.col("statusCode").cast(pl.String) == ""))
        .then(pl.lit("Unset"))  # Default to Ok for internal calls
        .when(pl.col("statusCode").cast(pl.Float64) >= 400)
        .then(pl.lit("Error"))
        .otherwise(pl.lit("Ok"))  # 200-399 range
        .alias("attr.status_code"),
    )

    # Handle parent span ID: -1 means root span, convert to empty string
    lf = lf.with_columns(
        pl.when(pl.col("parent_span_id") == "-1")
        .then(pl.lit(""))
        .otherwise(pl.col("parent_span_id"))
        .alias("parent_span_id")
    )

    lf = lf.sort("time")

    return lf


class TracePickerDatapackLoader(DatapackLoader):
    def __init__(self, src_folder: Path, datapack: str) -> None:
        self._src_folder = src_folder
        self._datapack = datapack
        self._traces_file = src_folder / "traces_spans.csv"

    def name(self) -> str:
        return self._datapack

    def labels(self) -> list[Label]:
        # For normal-only data, create a default "normal" label
        return [Label(name="normal", level="trace")]

    def data(self) -> dict[str, Any]:
        # Load and convert traces
        traces_lf = convert_tracepicker_traces(self._traces_file)
        traces_df = traces_lf.collect()

        if traces_df.is_empty():
            raise ValueError(f"Traces dataframe is empty for datapack {self.name()}")

        # Get time range for metadata
        min_time = traces_df["time"].min()
        max_time = traces_df["time"].max()

        logger.info(f"Datapack {self.name()}: {len(traces_df)} spans, {traces_df['trace_id'].n_unique()} traces")
        logger.info(f"Time range: {min_time} to {max_time}")

        # Since all data is normal, we'll put everything in normal_traces
        # and create empty abnormal files
        data_dict: dict[str, Any] = {
            "normal_traces.parquet": traces_lf,
            "abnormal_traces.parquet": pl.LazyFrame(schema=traces_df.schema),  # Empty abnormal traces
            # Create empty logs with proper schema
            "normal_logs.parquet": pl.LazyFrame(
                schema={
                    "time": pl.Datetime("us", "UTC"),
                    "trace_id": pl.String,
                    "span_id": pl.String,
                    "service_name": pl.String,
                    "level": pl.String,
                    "message": pl.String,
                    "attr.template_id": pl.String,
                }
            ),
            "abnormal_logs.parquet": pl.LazyFrame(
                schema={
                    "time": pl.Datetime("us", "UTC"),
                    "trace_id": pl.String,
                    "span_id": pl.String,
                    "service_name": pl.String,
                    "level": pl.String,
                    "message": pl.String,
                    "attr.template_id": pl.String,
                }
            ),
            # Create empty metrics with proper schema
            "normal_metrics.parquet": pl.LazyFrame(
                schema={
                    "time": pl.Datetime("us", "UTC"),
                    "metric": pl.String,
                    "value": pl.Float64,
                    "service_name": pl.String,
                }
            ),
            "abnormal_metrics.parquet": pl.LazyFrame(
                schema={
                    "time": pl.Datetime("us", "UTC"),
                    "metric": pl.String,
                    "value": pl.Float64,
                    "service_name": pl.String,
                }
            ),
            # Create empty histogram metrics
            "normal_metrics_histogram.parquet": pl.LazyFrame(
                schema={
                    "time": pl.Datetime("us", "UTC"),
                    "metric": pl.String,
                    "value": pl.Float64,
                    "service_name": pl.String,
                }
            ),
            "abnormal_metrics_histogram.parquet": pl.LazyFrame(
                schema={
                    "time": pl.Datetime("us", "UTC"),
                    "metric": pl.String,
                    "value": pl.Float64,
                    "service_name": pl.String,
                }
            ),
            # Create empty sum metrics
            "normal_metrics_sum.parquet": pl.LazyFrame(
                schema={
                    "time": pl.Datetime("us", "UTC"),
                    "metric": pl.String,
                    "value": pl.Float64,
                    "service_name": pl.String,
                }
            ),
            "abnormal_metrics_sum.parquet": pl.LazyFrame(
                schema={
                    "time": pl.Datetime("us", "UTC"),
                    "metric": pl.String,
                    "value": pl.Float64,
                    "service_name": pl.String,
                }
            ),
        }

        # Create metadata for normal-only dataset
        metadata = {
            "normal_start_time": str(min_time) if min_time else None,
            "normal_end_time": str(max_time) if max_time else None,
            "abnormal_start_time": str(max_time) if max_time else None,  # Same as normal end
            "abnormal_end_time": str(max_time) if max_time else None,  # Same as normal end
            "injection_name": "none",  # No injection for normal-only data
            "fault_type": "none",
            "data_type": "normal_only",
            "source": "tracepicker",
        }
        data_dict["metadata.json"] = metadata

        # Create empty injection.json for compatibility
        injection_data = {"ground_truth": {"service": [], "fault_type": "none"}}
        data_dict["injection.json"] = injection_data

        # Create minimal env.json with time windows
        # Convert polars datetime to Unix timestamp (seconds)
        if min_time is not None and max_time is not None:
            # Extract timestamp values from polars datetime (convert microseconds to seconds)
            min_timestamp = int(traces_df.select(pl.col("time").min().dt.timestamp("us")).item() // 1_000_000)
            max_timestamp = int(traces_df.select(pl.col("time").max().dt.timestamp("us")).item() // 1_000_000)
        else:
            min_timestamp = 0
            max_timestamp = 0

        env_data = {
            "NORMAL_START": min_timestamp,
            "NORMAL_END": max_timestamp,
            "ABNORMAL_START": max_timestamp,  # Same as normal end for normal-only data
            "ABNORMAL_END": max_timestamp,  # Same as normal end for normal-only data
        }
        data_dict["env.json"] = env_data

        # Create empty k8s.json for compatibility
        k8s_data = {"pods": [], "services": [], "deployments": []}
        data_dict["k8s.json"] = k8s_data

        # Create empty conclusion.parquet for compatibility
        data_dict["conclusion.parquet"] = pl.LazyFrame(
            schema={
                "SpanName": pl.String,
                "Issues": pl.String,
            }
        )

        return data_dict


class TracePickerDatasetLoader(DatasetLoader):
    def __init__(self, src_folder: Path, dataset: str):
        self._src_folder = src_folder
        self._dataset = dataset

        datapack_loaders = []

        # Find all subdirectories containing traces_spans.csv
        for sub_folder in src_folder.iterdir():
            if sub_folder.is_dir():
                traces_file = sub_folder / "traces_spans.csv"
                if traces_file.exists():
                    datapack_name = sub_folder.name

                    loader = TracePickerDatapackLoader(
                        src_folder=sub_folder,
                        datapack=datapack_name,
                    )

                    datapack_loaders.append(loader)
                    logger.info(f"Found datapack: {datapack_name}")

        self._datapack_loaders = datapack_loaders

    def name(self) -> str:
        return self._dataset

    def __len__(self) -> int:
        return len(self._datapack_loaders)

    def __getitem__(self, index: int) -> DatapackLoader:
        return self._datapack_loaders[index]


@app.command()
def local_test():
    """Test the conversion functions with sockshop sample data."""
    sockshop_traces = Path("data/tracepicker/sockshop/traces_spans.csv")

    if not sockshop_traces.exists():
        logger.error(f"Test file not found: {sockshop_traces}")
        return

    traces_lf = convert_tracepicker_traces(sockshop_traces)
    traces_df = traces_lf.collect()
    logger.info(f"Test traces converted: {traces_df.shape}")
    logger.info(f"Sample columns: {traces_df.columns}")
    logger.info(f"Sample data:\n{traces_df.head()}")

    # Check trace count
    trace_count = traces_df["trace_id"].n_unique()
    logger.info(f"Number of unique traces: {trace_count}")

    # Check service distribution
    service_counts = traces_df.group_by("service_name").agg(pl.len().alias("span_count"))
    logger.info(f"Service distribution:\n{service_counts}")


@app.command()
@timeit()
def run(src_folder: str = "data/tracepicker", dataset_name: str = "tracepicker"):
    """Convert TracePicker dataset to RCABench format.

    Args:
        src_folder: Path to folder containing datapack subdirectories
        dataset_name: Name for the converted dataset
    """
    from rcabench_platform.v2.sources.convert import convert_dataset

    src_path = Path(src_folder)

    if not src_path.exists():
        logger.error(f"Source folder not found: {src_path}")
        return

    # Check for subdirectories with traces_spans.csv
    found_datapacks = []
    for sub_folder in src_path.iterdir():
        if sub_folder.is_dir():
            traces_file = sub_folder / "traces_spans.csv"
            if traces_file.exists():
                found_datapacks.append(sub_folder.name)

    if not found_datapacks:
        logger.error(f"No traces_spans.csv files found in subdirectories of {src_path}")
        return

    logger.info(f"Found {len(found_datapacks)} datapacks: {found_datapacks}")

    loader = TracePickerDatasetLoader(src_path, dataset_name)
    logger.info(f"Starting conversion of dataset: {dataset_name}")

    convert_dataset(loader, parallel=4, skip_finished=False)
    logger.info(f"Conversion completed for dataset: {dataset_name}")


if __name__ == "__main__":
    app()
