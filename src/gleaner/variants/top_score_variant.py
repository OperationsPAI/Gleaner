"""
Top Score Variant - Gleaner with direct anomaly score ranking

Features:
- Uses traces and logs for encoding
- No quota allocation or hierarchical sampling
- No DPP diversity selection
- Direct selection by anomaly score ranking according to budget
"""

import math
import time
from typing import List

import polars as pl
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import SamplerArgs, SampleResult, SamplingMode

from ..components.dataloader import load_data
from ..core.sampler import GleanerSampler


class TopScoreVariant(GleanerSampler):
    """
    Gleaner variant that uses direct anomaly score ranking

    Features:
    - Uses traces and logs for encoding
    - No quota allocation (no grouping by root span type)
    - No DPP diversity selection
    - Direct top-k selection by anomaly score based on budget
    """

    def __call__(self, args: SamplerArgs) -> List[SampleResult]:
        """Execute variant with direct anomaly score ranking"""
        logger.info(
            f"=== Gleaner Top-Score Variant: {args.dataset}/{args.datapack} ==="
        )
        logger.info(f"Mode: {args.mode}, Target rate: {args.sampling_rate}")

        start_time = time.time()

        # Load data with traces and logs
        logger.info("Loading data (top score variant)...")
        data = load_data(
            args.input_folder,
            need_traces=True,
            need_logs=True,
        )

        traces_df = data["traces"].collect()
        logs_df = data.get("logs")
        logs_df = logs_df.collect() if logs_df is not None else None

        logger.info(
            f"Loaded {len(traces_df)} trace spans, "
            f"{len(logs_df) if logs_df is not None and not logs_df.is_empty() else 0} logs"
        )

        # Encode ALL traces at once (with logs for anomaly score calculation)
        from pathlib import Path

        from ..components.trace_encoder import encode_all_traces_batch

        logger.info("Encoding all traces at once (for anomaly scoring)...")
        all_encoded_traces, _ = encode_all_traces_batch(
            traces_df, logs_df, Path(args.input_folder), args.dataset
        )

        logger.info(
            f"Encoded {len(all_encoded_traces)} traces for top-score selection"
        )

        # Calculate target samples based on budget
        total_traces = len(all_encoded_traces)
        target_total_samples = max(1, math.ceil(total_traces * args.sampling_rate))

        # Store target for budget tracking
        self.target_total_samples = target_total_samples

        logger.info(
            f"Top-score variant: {total_traces} traces, target: {target_total_samples}"
        )

        # Direct selection by anomaly score (dpp_score column)
        # Sort by dpp_score descending and take top-k
        logger.info("Selecting top traces by anomaly score...")

        # Ensure dpp_score column exists and handle nulls
        if "dpp_score" not in all_encoded_traces.columns:
            logger.warning("dpp_score column not found, using 0.0 as default")
            all_encoded_traces = all_encoded_traces.with_columns(
                [pl.lit(0.0).alias("dpp_score")]
            )

        # Sort by dpp_score descending and select top traces
        sorted_traces = all_encoded_traces.sort("dpp_score", descending=True)

        # Select top-k traces
        selected_traces = sorted_traces.head(target_total_samples)

        # Create results
        all_results = []
        for row in selected_traces.iter_rows(named=True):
            trace_id = row.get("traceid")
            if trace_id is None:
                continue
            score = float(row.get("dpp_score", 0.0) or 0.0)
            all_results.append(
                SampleResult(trace_id=str(trace_id), sample_score=score)
            )

        logger.info(
            f"Selected {len(all_results)}/{total_traces} traces by anomaly score"
        )

        # Handle offline budget shortfall (should rarely happen since we select exact count)
        if args.mode == SamplingMode.OFFLINE:
            shortfall = target_total_samples - len(all_results)
            if shortfall > 0:
                logger.info(f"Budget shortfall: {shortfall}, backfilling...")
                all_results = self._handle_offline_budget_backfill(
                    all_results, all_encoded_traces, {}
                )

        # Apply final sampling mode strategy
        final_results = self._apply_sampling_mode(args, all_results)

        total_time = time.time() - start_time
        logger.info(
            f"Top-Score variant complete: {len(final_results)}/{len(traces_df)} traces "
            f"(rate: {len(final_results) / len(traces_df):.3f}, time: {total_time:.2f}s)"
        )

        return final_results
