"""
No Rebalance Variant - Gleaner without budget rebalancing between normal and abnormal periods

Features:
- Uses traces, logs
- Full alarm system and quota allocation
- No budget rebalancing when abnormal traffic drops (QPM-based rebalance disabled)
- Normal and abnormal periods keep their time-proportional budget allocation regardless of traffic
"""

import datetime
import math
import time
from typing import List

import polars as pl
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import SamplerArgs, SampleResult, SamplingMode

from ..components.dataloader import load_data
from ..core.sampler import GleanerSampler


class NoRebalanceVariant(GleanerSampler):
    """
    Gleaner variant that disables budget rebalancing between normal and abnormal periods

    Features:
    - Full alarm system and quota allocation
    - Budget allocation is purely time-proportional
    - No QPM-based rebalancing when abnormal traffic drops
    - Abnormal period traffic drop does NOT trigger budget reallocation to normal period
    """

    def __call__(self, args: SamplerArgs) -> List[SampleResult]:
        """Execute variant without budget rebalancing"""
        logger.info(
            f"=== Gleaner No-Rebalance Variant: {args.dataset}/{args.datapack} ==="
        )
        logger.info(f"Mode: {args.mode}, Target rate: {args.sampling_rate}")
        start_time = time.time()

        # Load all data types
        logger.info("Loading data...")
        anomaly_cfg = self.config.anomaly_score
        data = load_data(
            args.input_folder,
            need_traces=True,
            need_logs=True,
            log_warning_weight=anomaly_cfg.log_warning_weight,
            log_error_weight=anomaly_cfg.log_error_weight,
        )

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
        from pathlib import Path

        from ..components.trace_encoder import encode_all_traces_batch

        logger.info("Encoding all traces at once...")
        all_encoded_traces, performance_thresholds = encode_all_traces_batch(
            traces_df,
            logs_df,
            Path(args.input_folder),
            args.dataset,
            anomaly_score_config=anomaly_cfg,
        )

        # Split encoded traces based on lookback split time
        logger.info("Splitting encoded traces into lookback and alarm periods...")
        if lookback_end_time:
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

        # Calculate budget allocation
        total_traces = len(all_encoded_traces)
        target_total_samples = max(1, math.ceil(total_traces * args.sampling_rate))

        # Store target for budget tracking
        self.target_total_samples = target_total_samples

        # Calculate time ranges for proportional budget allocation
        lookback_time_range_minutes = 1.0
        alarm_time_range_minutes = 1.0

        if not lookback_encoded.is_empty():
            lookback_min_time = lookback_encoded["time"].min()
            lookback_max_time = lookback_encoded["time"].max()
            if (
                lookback_min_time is not None
                and lookback_max_time is not None
                and isinstance(lookback_min_time, datetime.datetime)
                and isinstance(lookback_max_time, datetime.datetime)
            ):
                lookback_time_range_minutes = max(
                    1.0, (lookback_max_time - lookback_min_time).total_seconds() / 60.0
                )

        if not alarm_encoded.is_empty():
            alarm_min_time = alarm_encoded["time"].min()
            alarm_max_time = alarm_encoded["time"].max()
            if (
                alarm_min_time is not None
                and alarm_max_time is not None
                and isinstance(alarm_min_time, datetime.datetime)
                and isinstance(alarm_max_time, datetime.datetime)
            ):
                alarm_time_range_minutes = max(
                    1.0,
                    (alarm_max_time - alarm_min_time).total_seconds() / 60.0,
                )

        # Calculate QPM for logging purposes only (not used for rebalancing)
        lookback_qpm = (
            len(lookback_encoded) / lookback_time_range_minutes
            if lookback_time_range_minutes > 0
            else 0
        )
        alarm_qpm = (
            len(alarm_encoded) / alarm_time_range_minutes
            if alarm_time_range_minutes > 0
            else 0
        )

        # Simple time-proportional budget allocation - NO REBALANCING
        total_weighted_time = lookback_time_range_minutes + alarm_time_range_minutes
        if total_weighted_time > 0:
            lookback_budget_factor = lookback_time_range_minutes / total_weighted_time
            alarm_budget_factor = alarm_time_range_minutes / total_weighted_time
        else:
            lookback_budget_factor = 0.5
            alarm_budget_factor = 0.5

        # Fixed budget allocation - no rebalancing based on QPM or traffic drop
        lookback_budget = target_total_samples * lookback_budget_factor
        alarm_budget = target_total_samples * alarm_budget_factor

        logger.info(
            f"Time ranges - Lookback: {lookback_time_range_minutes:.1f}min, Alarm: {alarm_time_range_minutes:.1f}min"
        )
        logger.info(f"QPM (info only) - Lookback: {lookback_qpm:.1f}, Alarm: {alarm_qpm:.1f}")
        logger.info(
            f"No-Rebalance budget allocation - Lookback: {lookback_budget:.0f}, "
            f"Alarm: {alarm_budget:.0f}, "
            f"Target total: {target_total_samples} (NO rebalancing applied)"
        )

        # Build lookback baselines
        logger.info("Building lookback baselines...")
        self.quota_allocator.build_lookback_baselines(
            lookback_encoded, performance_thresholds
        )
        self.alarm_system.set_warmup_end_time(lookback_end_time)

        # Process in batches using pre-encoded data
        logger.info(f"Processing traces in batches of {self.config.batch_size}...")
        all_results = []

        # Process lookback data
        if not lookback_encoded.is_empty():
            lookback_sampling_rate = lookback_budget / len(lookback_encoded)
            lookback_sampling_rate = min(1.0, lookback_sampling_rate)

            logger.info(
                f"No-Rebalance lookback sampling rate: {lookback_sampling_rate:.3f}"
            )
            warmup_results = self._process_lookback_encoded_batch(
                lookback_encoded, lookback_sampling_rate, performance_thresholds
            )

            # Update budget tracking for warmup results
            if args.mode == SamplingMode.OFFLINE:
                self.total_sampled_count += len(warmup_results)
                # Store warmup results for potential backfill
                self.batch_results_history.append(warmup_results.copy())

            all_results.extend(warmup_results)

        # Process alarm data in batches
        if not alarm_encoded.is_empty():
            alarm_sampling_rate = alarm_budget / len(alarm_encoded)
            alarm_sampling_rate = min(1.0, alarm_sampling_rate)

            logger.info(
                f"No-Rebalance alarm sampling rate: {alarm_sampling_rate:.3f}"
            )

            total_alarm_traces = len(alarm_encoded)
            total_batches = (
                total_alarm_traces + self.config.batch_size - 1
            ) // self.config.batch_size

            for batch_idx in range(total_batches):
                if args.mode == SamplingMode.OFFLINE and self._is_budget_exhausted():
                    logger.warning(
                        f"Budget target reached after batch {batch_idx}, stopping further processing"
                    )
                    logger.info(
                        f"Budget status: {self.total_sampled_count}/{self.target_total_samples} samples"
                    )
                    break

                start_idx = batch_idx * self.config.batch_size
                end_idx = min(start_idx + self.config.batch_size, total_alarm_traces)

                batch_encoded = alarm_encoded[start_idx:end_idx]
                batch_size = len(batch_encoded)

                logger.info(
                    f"Processing batch {batch_idx + 1}/{total_batches}: {batch_size} traces"
                )

                batch_results = self._process_encoded_batch(
                    batch_encoded,
                    alarm_sampling_rate,
                    str(args.input_folder),
                    performance_thresholds,
                )

                # Update budget tracking for offline mode
                if args.mode == SamplingMode.OFFLINE:
                    self.total_sampled_count += len(batch_results)
                    # Store batch results for potential backfill
                    self.batch_results_history.append(batch_results.copy())

                all_results.extend(batch_results)

        # Apply final sampling mode strategy
        # Handle budget shortfall for offline mode
        if args.mode == SamplingMode.OFFLINE:
            all_results = self._handle_offline_budget_backfill(
                all_results, all_encoded_traces, performance_thresholds
            )

        final_results = self._apply_sampling_mode(args, all_results)

        total_time = time.time() - start_time
        logger.info(
            f"No-Rebalance variant complete: {len(final_results)}/{len(traces_df)} traces "
            f"(rate: {len(final_results) / len(traces_df):.3f}, time: {total_time:.2f}s)"
        )

        return final_results
