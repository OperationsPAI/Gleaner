"""
Data Loader for Gleaner V2

Minimal loaders for traces and logs. Metrics SLI are derived from traces by the
AlarmSystem; no standalone metrics loader is provided.
"""

# Import the optimized dataloader from V1
import json
import time
from functools import wraps
from pathlib import Path

import polars as pl
from rcabench_platform.v2.logging import logger


def timeit():
    """Simple timing decorator"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            logger.info(f"{func.__name__} took {end - start:.2f} seconds")
            return result

        return wrapper

    return decorator


def load_json(path: Path) -> dict:
    """Load JSON file"""
    with open(path, "r") as f:
        return json.load(f)


def merge_two_time_ranges(normal: pl.LazyFrame, anomal: pl.LazyFrame) -> pl.LazyFrame:
    """Simply concatenate normal and abnormal data"""
    return pl.concat([normal, anomal])


@timeit()
def load_traces(input_folder: Path) -> pl.LazyFrame:
    """Load traces with only essential fields"""
    normal_traces = pl.scan_parquet(input_folder / "normal_traces.parquet")
    abnormal_traces = pl.scan_parquet(input_folder / "abnormal_traces.parquet")
    lf = merge_two_time_ranges(normal_traces, abnormal_traces)

    # Select only essential fields for trace analysis
    essential_fields = [
        "trace_id",
        "span_id",
        "parent_span_id",
        "span_name",
        "service_name",
        "duration",
        "attr.status_code",
        "time",  # Keep time for timestamp operations
    ]

    # Select essential fields and cast duration to float
    lf = lf.select(essential_fields).with_columns(
        pl.col("duration").cast(pl.Float64),
    )

    # NOTE: avoid sorting here to save work; downstream encoding already normalizes time

    return lf


@timeit()
def load_logs(
    input_folder: Path,
    log_warning_weight: float = 1.0,
    log_error_weight: float = 2.0,
) -> pl.LazyFrame:
    """Load logs with only essential fields and precompute log-level score.

    Scoring rules (configurable):
    - WARN => log_warning_weight (default: 1.0)
    - ERROR/SEVERE => log_error_weight (default: 2.0)
    - Others => 0

    Args:
        input_folder: Path to input data folder
        log_warning_weight: Weight for WARN log entries
        log_error_weight: Weight for ERROR/SEVERE log entries
    """
    normal_logs = pl.scan_parquet(input_folder / "normal_logs.parquet")
    abnormal_logs = pl.scan_parquet(input_folder / "abnormal_logs.parquet")
    lf = merge_two_time_ranges(normal_logs, abnormal_logs)

    # Select only essential fields for log analysis
    essential_fields = [
        "trace_id",
        "span_id",
        "service_name",
        "message",
        "level",
        "attr.template_id",  # Pre-computed template ID - this is what we need!
        "time",  # Keep time for timestamp operations
    ]

    # Select essential fields only
    lf = lf.select(essential_fields)

    # Normalize WARNING -> WARN and compute gleaner_log_score with config weights
    lf = lf.with_columns(
        [
            pl.col("level").str.replace("WARNING", "WARN", literal=True).alias("level"),
        ]
    )
    lf = lf.with_columns(
        [
            pl.when(pl.col("level") == "WARN")
            .then(pl.lit(log_warning_weight))
            .when(pl.col("level").is_in(["ERROR", "SEVERE"]))
            .then(pl.lit(log_error_weight))
            .otherwise(pl.lit(0))
            .cast(pl.Float64)
            .alias("gleaner_log_score")
        ]
    )

    return lf


def load_data(
    input_folder: Path,
    *,
    need_traces: bool = True,
    need_logs: bool = True,
    log_warning_weight: float = 1.0,
    log_error_weight: float = 2.0,
) -> dict:
    """
    Load only the required data types for efficient memory usage

    Args:
        input_folder: Path to input data folder
        need_traces: Whether to load trace data
        need_logs: Whether to load log data
        log_warning_weight: Weight for WARN log entries (default: 1.0)
        log_error_weight: Weight for ERROR/SEVERE log entries (default: 2.0)
    Note: Metrics SLI are derived from traces by AlarmSystem; nothing to load here.

    Returns:
        Dictionary with requested data, keys will only exist for requested data types
    """
    data = {}

    if need_traces:
        logger.info("Loading traces...")
        data["traces"] = load_traces(input_folder)

    if need_logs:
        logger.info("Loading logs...")
        data["logs"] = load_logs(
            input_folder,
            log_warning_weight=log_warning_weight,
            log_error_weight=log_error_weight,
        )

    return data


__all__ = ["load_data", "timeit", "load_json", "load_logs", "load_traces"]
