"""
No DPP Variant - Gleaner with quota allocation but no DPP sampling

Features:
- Uses traces, logs for encoding
- Quota allocation by root span type groups
- No DPP diversity selection - select by anomaly score per group
- Maintains hierarchical sampling structure without diversity optimization
"""

import math
import time
from typing import List

import polars as pl
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import SamplerArgs, SampleResult, SamplingMode

from ..components.dataloader import load_data
from ..core.sampler import GleanerSampler


class NoDPPVariant(GleanerSampler):
    """
    Gleaner variant that uses quota allocation but removes DPP sampling

    Features:
    - Uses traces and logs for encoding
    - Quota allocation by root span type (hierarchical grouping)
    - No DPP diversity selection
    - Selects top traces by anomaly score within each quota group
    """

    def __call__(self, args: SamplerArgs) -> List[SampleResult]:
        """Execute variant with quota allocation but no DPP"""
        logger.info(
            f"=== Gleaner No-DPP Variant: {args.dataset}/{args.datapack} ==="
        )
        logger.info(f"Mode: {args.mode}, Target rate: {args.sampling_rate}")

        start_time = time.time()

        # Load all data types
        logger.info("Loading data (no DPP variant)...")
        data = load_data(args.input_folder, need_traces=True, need_logs=True)

        # Update input folder for alarm system and quota allocator
        from pathlib import Path

        input_folder_path = Path(args.input_folder)
        self.alarm_system.input_folder = input_folder_path
        self.quota_allocator.input_folder = input_folder_path
        self.quota_allocator.alarm_system.input_folder = input_folder_path

        traces_df = data["traces"].collect()
        logs_df = data.get("logs")
        logs_df = logs_df.collect() if logs_df is not None else None

        logger.info(
            f"Loaded {len(traces_df)} trace spans, "
            f"{len(logs_df) if logs_df is not None and not logs_df.is_empty() else 0} logs"
        )

        # Time-based data splitting for lookback
        logger.info("Splitting data into lookback and alarm periods...")
        lookback_traces, alarm_traces, lookback_end_time = (
            self._split_lookback_alarm_data(traces_df)
        )

        logger.info(
            f"Lookback: {len(lookback_traces)} spans, Alarm: {len(alarm_traces)} spans"
        )

        # Encode ALL traces at once (with logs)
        from ..components.trace_encoder import encode_all_traces_batch

        logger.info("Encoding all traces at once...")
        all_encoded_traces, performance_thresholds = encode_all_traces_batch(
            traces_df, logs_df, input_folder_path, args.dataset
        )

        # Split encoded traces based on lookback split time
        logger.info("Splitting encoded traces into lookback and alarm periods...")
        if lookback_end_time:
            import datetime

            split_datetime = datetime.datetime.fromtimestamp(
                lookback_end_time, tz=datetime.timezone.utc
            )
            lookback_encoded = all_encoded_traces.filter(
                pl.col("time") <= split_datetime
            )
            alarm_encoded = all_encoded_traces.filter(pl.col("time") > split_datetime)
        else:
            split_point = int(len(all_encoded_traces) * 0.3)
            lookback_encoded = all_encoded_traces[:split_point]
            alarm_encoded = all_encoded_traces[split_point:]

        logger.info(
            f"Encoded traces split - Lookback: {len(lookback_encoded)}, Alarm: {len(alarm_encoded)}"
        )

        # Calculate budget allocation (same as main sampler)
        total_traces = len(all_encoded_traces)
        target_total_samples = max(1, math.ceil(total_traces * args.sampling_rate))
        self.target_total_samples = target_total_samples

        # Calculate time ranges for budget allocation
        import datetime

        warmup_time_range_minutes = 1.0
        processing_time_range_minutes = 1.0

        if not lookback_encoded.is_empty():
            warmup_min_time = lookback_encoded["time"].min()
            warmup_max_time = lookback_encoded["time"].max()
            if (
                warmup_min_time is not None
                and warmup_max_time is not None
                and isinstance(warmup_min_time, datetime.datetime)
                and isinstance(warmup_max_time, datetime.datetime)
            ):
                warmup_time_range_minutes = max(
                    1.0, (warmup_max_time - warmup_min_time).total_seconds() / 60.0
                )

        if not alarm_encoded.is_empty():
            processing_min_time = alarm_encoded["time"].min()
            processing_max_time = alarm_encoded["time"].max()
            if (
                processing_min_time is not None
                and processing_max_time is not None
                and isinstance(processing_min_time, datetime.datetime)
                and isinstance(processing_max_time, datetime.datetime)
            ):
                processing_time_range_minutes = max(
                    1.0,
                    (processing_max_time - processing_min_time).total_seconds() / 60.0,
                )

        total_weighted_time = warmup_time_range_minutes + processing_time_range_minutes
        if total_weighted_time > 0:
            lookback_budget_factor = warmup_time_range_minutes / total_weighted_time
        else:
            lookback_budget_factor = 0.5

        lookback_budget = int(round(target_total_samples * lookback_budget_factor))
        alarm_budget = target_total_samples - lookback_budget

        logger.info(
            f"No-DPP budget allocation - Warmup: {lookback_budget}, Processing: {alarm_budget}"
        )

        # Build lookback baselines
        logger.info("Building lookback baselines...")
        self.quota_allocator.build_lookback_baselines(
            lookback_encoded, performance_thresholds
        )
        self.alarm_system.set_warmup_end_time(lookback_end_time)

        # Process traces
        all_results = []

        # Process lookback data with quota allocation but no DPP
        if not lookback_encoded.is_empty():
            lookback_results = self._process_no_dpp_batch(
                lookback_encoded, lookback_budget, str(args.input_folder), is_warmup=True
            )
            if args.mode == SamplingMode.OFFLINE:
                self.total_sampled_count += len(lookback_results)
                self.batch_results_history.append(lookback_results.copy())
            all_results.extend(lookback_results)

        # Process alarm data with quota allocation but no DPP
        if not alarm_encoded.is_empty():
            total_alarm_traces = len(alarm_encoded)
            total_batches = (
                total_alarm_traces + self.config.batch_size - 1
            ) // self.config.batch_size

            # Distribute alarm budget across batches
            batch_budget_base = alarm_budget // total_batches if total_batches > 0 else alarm_budget
            remaining_budget = alarm_budget % total_batches if total_batches > 0 else 0

            for batch_idx in range(total_batches):
                if args.mode == SamplingMode.OFFLINE and self._is_budget_exhausted():
                    logger.warning(f"Budget exhausted after batch {batch_idx}")
                    break

                start_idx = batch_idx * self.config.batch_size
                end_idx = min(start_idx + self.config.batch_size, total_alarm_traces)

                batch_encoded = alarm_encoded[start_idx:end_idx]

                # Calculate batch budget
                batch_budget = batch_budget_base + (1 if batch_idx < remaining_budget else 0)

                logger.info(
                    f"No-DPP batch {batch_idx + 1}/{total_batches}: "
                    f"{len(batch_encoded)} traces, budget: {batch_budget}"
                )

                batch_results = self._process_no_dpp_batch(
                    batch_encoded, batch_budget, str(args.input_folder), is_warmup=False
                )

                if args.mode == SamplingMode.OFFLINE:
                    self.total_sampled_count += len(batch_results)
                    self.batch_results_history.append(batch_results.copy())

                all_results.extend(batch_results)

        # Handle offline budget shortfall
        if args.mode == SamplingMode.OFFLINE:
            all_results = self._handle_offline_budget_backfill(
                all_results, all_encoded_traces, performance_thresholds
            )

        # Apply final sampling mode strategy
        final_results = self._apply_sampling_mode(args, all_results)

        total_time = time.time() - start_time
        logger.info(
            f"No-DPP variant complete: {len(final_results)}/{len(traces_df)} traces "
            f"(rate: {len(final_results) / len(traces_df):.3f}, time: {total_time:.2f}s)"
        )

        return final_results

    def _process_no_dpp_batch(
        self,
        batch_encoded: pl.DataFrame,
        batch_budget: int,
        input_folder: str,
        is_warmup: bool = False,
    ) -> List[SampleResult]:
        """
        Process a batch with quota allocation but no DPP

        Instead of DPP diversity selection, select top traces by anomaly score
        within each quota group.
        """
        if batch_encoded.is_empty():
            return []

        logger.info(f"Processing {len(batch_encoded)} traces without DPP, budget: {batch_budget}")

        # Step 1: Allocate quotas by root span type
        try:
            quotas = self.quota_allocator.allocate_quotas(
                trace_batch=batch_encoded,
                batch_budget=batch_budget,
                input_folder=input_folder if not is_warmup else None,
            )

            logger.info(f"Quota allocation completed for {len(quotas)} root span types")

        except Exception as e:
            logger.error(f"Quota allocation failed: {e}, falling back to global top-k")
            # Fallback: global top-k selection
            return self._select_global_top_k(batch_encoded, batch_budget)

        # Step 2: Select top traces by anomaly score within each quota group
        results = []

        # Pre-partition by root
        try:
            parts = batch_encoded.partition_by("root", as_dict=False)
            root_groups = {}
            for part in parts:
                if part.is_empty():
                    continue
                try:
                    key = part.select(pl.col("root")).head(1).item()
                except Exception:
                    key = None
                if key is not None:
                    root_groups[str(key)] = part
        except Exception:
            root_groups = None

        for root_span_name, quota_info in quotas.items():
            if quota_info.allocated_quota <= 0:
                continue

            # Get traces for this root span type
            if root_groups is not None:
                root_traces = root_groups.get(str(root_span_name), pl.DataFrame([]))
            else:
                root_traces = batch_encoded.filter(pl.col("root") == root_span_name)

            if root_traces.is_empty():
                continue

            available_traces = len(root_traces)
            quota = min(quota_info.allocated_quota, available_traces)

            # Sort by dpp_score (anomaly score) descending and select top quota
            sorted_traces = root_traces.sort("dpp_score", descending=True, nulls_last=True)
            selected_traces = sorted_traces.head(quota)

            # Create results
            for row in selected_traces.iter_rows(named=True):
                trace_id = row.get("traceid")
                if trace_id is None:
                    continue
                score = float(row.get("dpp_score", 0.0) or 0.0)
                results.append(
                    SampleResult(trace_id=str(trace_id), sample_score=score)
                )

            logger.debug(
                f"No-DPP: Selected {quota}/{available_traces} traces for {root_span_name}"
            )

        logger.info(f"No-DPP batch processed: {len(results)}/{len(batch_encoded)} traces")
        return results

    def _select_global_top_k(
        self, batch_encoded: pl.DataFrame, budget: int
    ) -> List[SampleResult]:
        """Fallback: select top-k traces globally by anomaly score"""
        if batch_encoded.is_empty():
            return []

        sorted_traces = batch_encoded.sort("dpp_score", descending=True, nulls_last=True)
        selected_traces = sorted_traces.head(budget)

        results = []
        for row in selected_traces.iter_rows(named=True):
            trace_id = row.get("traceid")
            if trace_id is None:
                continue
            score = float(row.get("dpp_score", 0.0) or 0.0)
            results.append(SampleResult(trace_id=str(trace_id), sample_score=score))

        return results
