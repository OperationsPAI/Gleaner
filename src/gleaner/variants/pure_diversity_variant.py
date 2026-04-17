"""
Pure Diversity Variant - Gleaner with pure diversity sampling

Features:
- Uses traces and logs (no metrics needed)
- No quota allocation or hierarchical sampling
- No anomaly detection
- Pure DPP diversity selection like original lookback batch processing
"""

import math
from typing import List

import polars as pl
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import SamplerArgs, SampleResult, SamplingMode

from ..components.dataloader import load_data
from ..core.sampler import GleanerSampler


class PureDiversityVariant(GleanerSampler):
    """
    Gleaner variant that uses pure diversity sampling only

    Features:
    - Uses traces and logs
    - No quota allocation or hierarchical sampling
    - No anomaly detection - no alarm system
    - Pure DPP diversity selection throughout
    """

    def __call__(self, args: SamplerArgs) -> List[SampleResult]:
        """Execute variant with pure diversity sampling"""
        logger.info(
            f"=== Gleaner Pure-Diversity Variant: {args.dataset}/{args.datapack} ==="
        )
        logger.info(f"Mode: {args.mode}, Target rate: {args.sampling_rate}")

        import time

        start_time = time.time()

        # Load data with traces and logs, but no metrics
        logger.info("Loading data (pure diversity)...")
        data = load_data(
            args.input_folder,
            need_traces=True,
            need_logs=True,  # Keep logs for pattern diversity
        )

        traces_df = data["traces"].collect()
        logs_df = data.get("logs")
        logs_df = logs_df.collect() if logs_df is not None else None

        logger.info(
            f"Loaded {len(traces_df)} trace spans, "
            f"{len(logs_df) if logs_df is not None and not logs_df.is_empty() else 0} logs"
        )

        # Encode ALL traces at once (with logs for pattern extraction)
        from pathlib import Path

        from ..components.trace_encoder import encode_all_traces_batch

        logger.info("Encoding all traces at once (with logs for diversity)...")
        all_encoded_traces, performance_thresholds = encode_all_traces_batch(
            traces_df, logs_df, Path(args.input_folder)
        )

        logger.info(
            f"Encoded {len(all_encoded_traces)} traces for pure diversity sampling"
        )

        # Calculate target samples
        total_traces = len(all_encoded_traces)
        target_total_samples = max(1, math.ceil(total_traces * args.sampling_rate))

        # Store target for budget tracking
        self.target_total_samples = target_total_samples

        logger.info(
            f"Pure diversity variant: {total_traces} traces, target: {target_total_samples}"
        )

        # Use the lookback pure diversity method for all data (backup method)
        # This is exactly the original lookback batch processing approach
        logger.info("Applying pure diversity sampling to all traces...")

        # Calculate sampling rate for all data
        overall_sampling_rate = (
            target_total_samples / total_traces if total_traces > 0 else 0.0
        )
        overall_sampling_rate = min(1.0, overall_sampling_rate)

        # Use the backup pure diversity method from the main sampler
        all_results = self._process_lookback_pure_diversity(
            all_encoded_traces, overall_sampling_rate, performance_thresholds
        )

        # Handle offline budget shortfall using the encoded pool and precomputed scores
        if args.mode == SamplingMode.OFFLINE:
            all_results = self._handle_offline_budget_backfill(
                all_results, all_encoded_traces, performance_thresholds
            )

        # Apply final sampling mode strategy
        final_results = self._apply_sampling_mode(args, all_results)

        total_time = time.time() - start_time
        logger.info(
            f"Pure-Diversity variant complete: {len(final_results)}/{len(traces_df)} traces "
            f"(rate: {len(final_results) / len(traces_df):.3f}, time: {total_time:.2f}s)"
        )

        return final_results

    def _process_lookback_pure_diversity(
        self,
        lookback_encoded: pl.DataFrame,
        sampling_rate: float,
        performance_thresholds: dict,
    ) -> List[SampleResult]:
        """Pure diversity processing - copied from main sampler backup method"""

        if lookback_encoded.is_empty():
            return []

        logger.info("Processing traces with pure diversity sampling in batches...")

        # Direct processing - each row is one trace
        total_traces = len(lookback_encoded)
        target_count = max(1, math.ceil(total_traces * sampling_rate))

        logger.info(
            f"Pure diversity processing: {total_traces} traces, target: {target_count}"
        )

        # Process in batches to avoid O(M²) complexity
        batch_size = self.config.batch_size  # Use same batch size
        total_batches = (total_traces + batch_size - 1) // batch_size
        all_results = []

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_traces)

            # Direct slice of DataFrame (much more efficient)
            batch_encoded = lookback_encoded[start_idx:end_idx]
            batch_size_actual = len(batch_encoded)

            # Calculate target for this batch (proportional)
            batch_target = max(1, math.ceil(batch_size_actual * sampling_rate))

            logger.info(
                f"Processing pure diversity batch {batch_idx + 1}/{total_batches}: "
                f"{batch_size_actual} traces, target: {batch_target}"
            )

            # Extract event patterns from batch encoded data
            trace_patterns = []  # DPP expects edge sets (patterns)
            trace_ids = []

            for row in batch_encoded.iter_rows(named=True):
                trace_data = row
                trace_id = trace_data.get("traceid")
                pattern = self._make_pattern_from_row(trace_data)
                trace_patterns.append(pattern)
                trace_ids.append(trace_id)

            # Use DPP selector for diverse sampling
            try:
                selected_trace_ids = self.dpp_selector.select_diverse_traces(
                    patterns=trace_patterns,
                    trace_ids=trace_ids,
                    quota=batch_target,
                    alarm_active=False,  # Pure diversity mode - no alarm
                    relevance_scores=None,  # Pure diversity - no relevance scores
                )

                batch_results = []
                # Create a mapping for efficient lookup
                trace_id_to_row = {trace_ids[i]: i for i in range(len(trace_ids))}

                for trace_id in selected_trace_ids:
                    row_idx = trace_id_to_row[trace_id]
                    trace_data = batch_encoded.row(row_idx, named=True)

                    # Use only base anomaly score (no additional scoring)
                    base_score = trace_data.get("anomaly_score", 0.5)
                    batch_results.append(
                        SampleResult(
                            trace_id=str(trace_id), sample_score=float(base_score)
                        )
                    )

            except Exception as e:
                logger.warning(
                    f"DPP selection failed: {e}, falling back to random selection"
                )
                # Fallback: random selection
                import random

                selected_indices = random.sample(
                    range(len(trace_ids)), min(batch_target, len(trace_ids))
                )

                batch_results = []
                for idx in selected_indices:
                    trace_data = batch_encoded.row(idx, named=True)
                    trace_id = trace_data.get("traceid")
                    if trace_id is None:
                        continue
                    base_score = trace_data.get("anomaly_score", 0.5)
                    batch_results.append(
                        SampleResult(
                            trace_id=str(trace_id), sample_score=float(base_score)
                        )
                    )

            all_results.extend(batch_results)
            logger.info(
                f"Pure diversity batch {batch_idx + 1} sampled: {len(batch_results)}/{batch_size_actual} traces"
            )

        logger.info(
            f"Pure diversity sampling complete: {len(all_results)}/{total_traces} traces"
        )
        return all_results
