"""
No Logs Variant - Gleaner without logs data

Features:
- Uses traces and metrics only
- No logs in encoding process
- Full alarm system and quota allocation
"""

import math
from typing import List

import polars as pl
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import SamplerArgs, SampleResult, SamplingMode

from ..components.dataloader import load_data
from ..core.sampler import GleanerSampler


class NoLogsVariant(GleanerSampler):
    """
    Gleaner variant that excludes logs data

    Features:
    - Full alarm system and quota allocation
    - No logs in trace encoding
    """

    def __call__(self, args: SamplerArgs) -> List[SampleResult]:
        """Execute variant with no logs data"""
        logger.info(f"=== Gleaner No-Logs Variant: {args.dataset}/{args.datapack} ===")
        logger.info(f"Mode: {args.mode}, Target rate: {args.sampling_rate}")

        import time

        start_time = time.time()

        # Load data without logs
        logger.info("Loading data (no logs)...")
        data = load_data(
            args.input_folder,
            need_traces=True,
            need_logs=False,  # No logs
        )

        # Update input folder for alarm system and quota allocator
        from pathlib import Path

        input_folder_path = Path(args.input_folder)
        self.alarm_system.input_folder = input_folder_path
        self.quota_allocator.input_folder = input_folder_path
        self.quota_allocator.alarm_system.input_folder = input_folder_path

        traces_df = data["traces"].collect()
        logger.info(f"Loaded {len(traces_df)} trace spans")

        # Time-based data splitting for warmup
        logger.info("Splitting data into lookback and alarm periods...")
        lookback_traces, alarm_traces, lookback_end_time = (
            self._split_lookback_alarm_data(traces_df)
        )

        logger.info(
            f"Lookback: {len(lookback_traces)} spans, Alarm: {len(alarm_traces)} spans"
        )

        # Encode ALL traces at once (without logs)
        from pathlib import Path

        from ..components.trace_encoder import encode_all_traces_batch

        logger.info("Encoding all traces at once (no logs)...")
        all_encoded_traces, performance_thresholds = encode_all_traces_batch(
            traces_df,
            None,
            Path(args.input_folder),  # logs_df = None
        )

        # Split encoded traces based on warmup split time
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

        # Calculate budget allocation
        total_traces = len(all_encoded_traces)
        target_total_samples = max(1, math.ceil(total_traces * args.sampling_rate))

        # Store target for budget tracking
        self.target_total_samples = target_total_samples

        # Calculate time ranges and QPM rebalancing (same as main implementation)
        lookback_time_range_minutes = 1.0
        alarm_time_range_minutes = 1.0

        import datetime

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

        total_weighted_time = lookback_time_range_minutes + alarm_time_range_minutes
        if total_weighted_time > 0:
            lookback_budget_factor = lookback_time_range_minutes / total_weighted_time
            alarm_budget_factor = alarm_time_range_minutes / total_weighted_time
        else:
            lookback_budget_factor = 0.5
            alarm_budget_factor = 0.5

        # QPM rebalancing (gated by config)
        qpm_rebalancing_factor = 1.0
        qpm_enabled = getattr(self.config, "enable_qpm_rebalancing", True)
        if qpm_enabled and lookback_qpm > alarm_qpm and alarm_qpm > 0:
            # Check if processing would need full sampling before applying QPM rebalancing
            tentative_alarm_sampling_rate = (
                (target_total_samples * alarm_budget_factor) / len(alarm_encoded)
                if len(alarm_encoded) > 0
                else 0
            )

            if tentative_alarm_sampling_rate < 1.0:
                mean_qpm = (lookback_qpm + alarm_qpm) / 2.0
                qpm_rebalancing_factor = mean_qpm / lookback_qpm
                logger.info(
                    f"QPM rebalancing applied - Mean QPM: {mean_qpm:.1f}, Factor: {qpm_rebalancing_factor:.3f}"
                )
                # Use time-based proportional allocation
                lookback_budget = target_total_samples * lookback_budget_factor
                alarm_budget = target_total_samples * alarm_budget_factor
            else:
                logger.info(
                    f"QPM rebalancing skipped - Processing needs full sampling (rate: {tentative_alarm_sampling_rate:.3f})"
                )
                if len(alarm_encoded) > 0:
                    alarm_budget = len(alarm_encoded)
                    lookback_budget = max(0, target_total_samples - alarm_budget)
                    logger.info(
                        f"Budget rebalanced for processing full sampling - "
                        f"Alarm: {alarm_budget}, Lookback: {lookback_budget}, "
                        f"Total: {alarm_budget + lookback_budget}/{target_total_samples}"
                    )
                else:
                    lookback_budget = target_total_samples * lookback_budget_factor
                    alarm_budget = target_total_samples * alarm_budget_factor
        else:
            lookback_budget = target_total_samples * lookback_budget_factor
            alarm_budget = target_total_samples * alarm_budget_factor

        logger.info(
            f"No-Logs variant budget allocation - Lookback: {lookback_budget:.0f}, "
            f"Alarm: {alarm_budget:.0f}, "
            f"QPM rebalancing factor: {qpm_rebalancing_factor:.3f}, "
            f"Target total: {target_total_samples}"
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
            lookback_sampling_rate = min(
                1.0, lookback_sampling_rate * qpm_rebalancing_factor
            )

            logger.info(f"No-Logs warmup sampling rate: {lookback_sampling_rate:.3f}")
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

            logger.info(f"No-Logs processing sampling rate: {alarm_sampling_rate:.3f}")

            total_alarm_traces = len(alarm_encoded)
            total_batches = (
                total_alarm_traces + self.config.batch_size - 1
            ) // self.config.batch_size

            for batch_idx in range(total_batches):
                if args.mode == SamplingMode.OFFLINE:
                    if self._is_budget_exhausted():
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
                    f"Processing batch {batch_idx + 1}/{total_batches}: {batch_size} traces (no logs)"
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
            f"No-Logs variant complete: {len(final_results)}/{len(traces_df)} traces "
            f"(rate: {len(final_results) / len(traces_df):.3f}, time: {total_time:.2f}s)"
        )

        return final_results
