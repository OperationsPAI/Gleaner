"""
Trace Encoder for Gleaner V2 - Batch Processing Mode

Uses rcabench_platform's event_encoding components to encode all traces at once,
then creates a simplified DataFrame for batch processing.
"""

from pathlib import Path
from typing import Optional

import polars as pl
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.event_encoding import EventEncoder, EventIDManager

from ..utils.config import AnomalyScoreConfig


def encode_all_traces_batch(
    traces_df: pl.DataFrame,
    logs_df: Optional[pl.DataFrame],
    input_folder: Path,
    dataset_name: Optional[str] = None,
    anomaly_score_config: Optional[AnomalyScoreConfig] = None,
) -> tuple[pl.DataFrame, dict]:
    """
    Use rcabench_platform's event encoding components to encode all traces,
    generating batch processing format DataFrame

    Args:
        traces_df: All trace data
        logs_df: All log data (optional)
        input_folder: Input folder path for loading metrics_sli
        dataset_name: Dataset name for root span detection
        anomaly_score_config: Configuration for anomaly score weights (optional).
            If not provided, uses default weights.

    Returns:
        tuple: (encoded DataFrame, performance_thresholds dict)
        - DataFrame contains columns: time, root, traceid, event, root_is_error,
          root_duration_ms
        - performance_thresholds: P90 threshold dict loaded from EventEncoder
    """
    logger.info("Starting batch trace encoding using rcabench_platform components...")

    # Use default config if not provided
    if anomaly_score_config is None:
        anomaly_score_config = AnomalyScoreConfig()

    # Step 1: Initialize event manager and encoder
    event_manager = EventIDManager()
    encoder = EventEncoder(event_manager)

    # Step 2: Extract span names and load performance thresholds
    event_manager.extract_span_names_from_traces(traces_df)
    encoder.load_performance_thresholds(input_folder)

    # Step 3: Pre-compute root rows for each trace - adapt for different datasets
    if dataset_name and not dataset_name.startswith("rcabench"):
        # For non-rcabench datasets (like TracePicker), use any root span
        traces_with_root_flag = traces_df.with_columns(
            (
                pl.col("parent_span_id").is_null() | (pl.col("parent_span_id") == "")
            ).alias("__is_root")
        )
    else:
        # For rcabench datasets, use loadgenerator as before
        traces_with_root_flag = traces_df.with_columns(
            (
                (pl.col("service_name") == "loadgenerator")
                & (
                    pl.col("parent_span_id").is_null()
                    | (pl.col("parent_span_id") == "")
                )
            ).alias("__is_root")
        )
    # Split root rows and non-root rows for subsequent fast lookup
    root_rows = traces_with_root_flag.filter(pl.col("__is_root")).select(
        [
            "trace_id",
            pl.col("span_name").alias("root"),
            pl.col("time").alias("time"),
            (pl.col("duration") / 1_000_000).alias("root_duration_ms"),
            (pl.col("attr.status_code") == "Error")
            .cast(pl.Int8)
            .alias("root_is_error"),
        ]
    )
    root_meta = root_rows
    # Step 4: Use Series operations for better performance
    logger.info(f"Processing {len(root_meta)} traces for encoding")

    # Precompute P90 values for all root names using Series operations
    root_names = root_meta.get_column("root")
    p90_values = []
    for root_name in root_names:
        p90_ms = 0.0
        for key, th_ms in encoder.performance_thresholds.items():
            if key in root_name or root_name in key:
                p90_ms = float(th_ms)
                break
        p90_values.append(p90_ms)

    # Precompute error counts per trace using Series operations
    error_counts_per_trace = (
        traces_df.filter(pl.col("attr.status_code") == "Error")
        .group_by("trace_id")
        .agg(pl.len().alias("error_count"))
    )

    # Precompute log scores per trace if logs are available
    log_scores_per_trace = None
    if (
        logs_df is not None
        and not logs_df.is_empty()
        and "gleaner_log_score" in logs_df.columns
    ):
        log_scores_per_trace = logs_df.group_by("trace_id").agg(
            pl.col("gleaner_log_score").sum().alias("log_score")
        )

    # Join precomputed values with root_meta
    root_meta_enhanced = (
        root_meta.with_columns([pl.Series("p90_ms", p90_values)])
        .join(error_counts_per_trace, on="trace_id", how="left")
        .with_columns([pl.col("error_count").fill_null(0)])
    )

    if log_scores_per_trace is not None:
        root_meta_enhanced = root_meta_enhanced.join(
            log_scores_per_trace, on="trace_id", how="left"
        ).with_columns([pl.col("log_score").fill_null(0.0)])
    else:
        root_meta_enhanced = root_meta_enhanced.with_columns(
            [pl.lit(0.0).alias("log_score")]
        )

    # Create a Series-based lookup structure instead of dict
    # Sort by trace_id for efficient binary search if needed
    root_meta_sorted = root_meta_enhanced.sort("trace_id")

    # Create index mapping for O(1) lookups
    trace_id_to_index = {
        trace_id: idx
        for idx, trace_id in enumerate(root_meta_sorted.get_column("trace_id"))
        if trace_id is not None
    }

    # Extract all columns as Series for efficient access
    sorted_roots = root_meta_sorted.get_column("root")
    sorted_times = root_meta_sorted.get_column("time")
    sorted_durations = root_meta_sorted.get_column("root_duration_ms")
    sorted_p90s = root_meta_sorted.get_column("p90_ms")
    sorted_error_counts = root_meta_sorted.get_column("error_count")
    sorted_log_scores = root_meta_sorted.get_column("log_score")

    # Use partition_by but avoid as_dict=True - iterate through partitions directly
    trace_partitions = traces_df.partition_by("trace_id", maintain_order=True)

    # Group logs by trace_id if available - also avoid as_dict
    log_partitions = {}
    if logs_df is not None and not logs_df.is_empty():
        log_parts = logs_df.partition_by("trace_id", maintain_order=True)
        # Only create dict for logs since we need random access
        for partition in log_parts:
            if not partition.is_empty():
                trace_id = partition.get_column("trace_id")[0]
                log_partitions[trace_id] = partition

    encoded_rows = []

    # Process each trace partition directly (avoiding dict lookup)
    for trace_partition in trace_partitions:
        if trace_partition.is_empty():
            continue

        # Get trace_id from the partition
        trace_id = trace_partition.get_column("trace_id")[0]
        if not trace_id:
            continue

        # Use Series index lookup instead of dict
        index = trace_id_to_index.get(trace_id)
        if index is None:
            continue

        # Get logs for this trace (if any)
        trace_logs = log_partitions.get(trace_id)

        # Use rcabench_platform encoder to get events (returns set[tuple[int, int]])
        event_pairs = encoder.encode_trace_events(trace_partition, trace_logs)

        # Calculate DPP-like anomaly score for each trace using Series indexing:
        #   error (status_error_weight per error span within the trace)  [PRECOMPUTED]
        #   + performance (configurable based on root P90 ratio)
        #   + log level score aggregated per-trace  [PRECOMPUTED with config weights]
        root_name = sorted_roots[index]
        dur_ms = float(sorted_durations[index])
        p90_ms = sorted_p90s[index]

        # Calculate latency P90 score using configurable thresholds
        perf = 0.0
        if p90_ms > 0 and dur_ms > p90_ms:
            ratio = dur_ms / p90_ms
            # Apply thresholds in order (first match wins)
            for threshold, score in anomaly_score_config.latency_p90_thresholds:
                if ratio >= threshold:
                    perf = score
                    break

        # Use precomputed error count and log score from Series
        err_count = int(sorted_error_counts[index])
        log_score = float(sorted_log_scores[index])

        # Calculate dpp_score using configurable weights
        dpp_score = (
            err_count * anomaly_score_config.status_error_weight + perf + log_score
        )

        encoded_rows.append(
            {
                "time": sorted_times[index],
                "root": sorted_roots[index],
                "traceid": trace_id,
                "event": list(event_pairs) if event_pairs else [],
                "root_is_error": 1 if err_count > 0 else 0,
                "root_duration_ms": float(sorted_durations[index]),
                "dpp_score": float(dpp_score),
            }
        )

    # Step 5: Create DataFrame, uniformly truncate time to minute level, then sort
    result_df = pl.DataFrame(encoded_rows)

    # Uniformly truncate time to minute level and sort
    result_df = result_df.with_columns(
        [pl.col("time").dt.truncate("1m").alias("time")]
    ).sort("time")

    logger.info(f"Encoded {len(result_df)} traces with batch processing format")

    # Return DataFrame and performance_thresholds
    return result_df, encoder.performance_thresholds


# Re-export interface
__all__ = ["encode_all_traces_batch"]
