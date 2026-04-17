"""
Gleaner Main Sampler

Implements the alarm-driven hierarchical sampling algorithm with Fast DPP diversity selection.
"""

import math
import time
from typing import List, Optional

import polars as pl
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import (
    SamplerArgs,
    SampleResult,
    SamplingMode,
    TraceSampler,
)

from ..algorithms.fast_dpp import DPPSelector
from ..components.dataloader import load_data
from ..core.alarm_system import AlarmSystem
from ..core.quota_allocator import QuotaAllocator
from ..utils.config import DEFAULT_CONFIG, GleanerConfig


class GleanerSampler(TraceSampler):
    """
    Gleaner Sampler - Alarm-Driven Online Hierarchical Sampling Algorithm

    Features:
    - Stateful alarm system with RobustScorer anomaly detection
    - Hierarchical quota allocation based on root span health
    - Fast DPP diverse selection with relevance scoring
    - Support for both alarm and normal modes
    """

    def __init__(self, config: Optional[GleanerConfig] = None):
        """
        Initialize Gleaner sampler

        Args:
            config: Optional configuration, uses DEFAULT_CONFIG if not provided
        """
        self.config = config or DEFAULT_CONFIG

        # Initialize core components
        self.alarm_system = AlarmSystem()

        # Share a single AlarmSystem instance to avoid duplicated state
        self.quota_allocator = QuotaAllocator(
            config=self.config,
            alarm_system=self.alarm_system,
        )

        self.dpp_selector = DPPSelector(epsilon=self.config.dpp_epsilon)

        # Budget tracking for offline mode
        self.total_sampled_count = 0
        self.target_total_samples = 0
        self.batch_results_history = []  # Store results from each batch for potential backfill

        # Optional reproducibility for random fallbacks
        try:
            seed_val = getattr(self.config, "random_seed", None)
            if seed_val is not None:
                import random

                random.seed(int(seed_val))
        except Exception:
            pass

        # Apply global log level from config
        try:
            import sys

            import loguru

            level_name = str(getattr(self.config, "log_level", "INFO")).upper()
            loguru.logger.remove()  # Remove existing handlers
            loguru.logger.add(sys.stderr, level=level_name)
        except Exception:
            pass

        logger.info(
            "Initialized Gleaner sampler with alarm-driven hierarchical sampling"
        )

    def needs_cpu_count(self) -> int | None:
        """Return number of CPU cores needed"""
        return 2

    def __call__(self, args: SamplerArgs) -> List[SampleResult]:
        """
        Execute Gleaner sampling algorithm

        Args:
            args: SamplerArgs with sampling configuration

        Returns:
            List of SampleResult with trace_id and combined score
        """
        logger.info(f"=== Gleaner Sampling: {args.dataset}/{args.datapack} ===")
        logger.info(f"Mode: {args.mode}, Target rate: {args.sampling_rate}")
        start_time = time.time()

        # Step 1: Load data with configurable log weights
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

        traces_lf = data["traces"]

        # warmup_unique_services will be built from warmup traces later; avoid premature/global collection here
        traces_df = traces_lf.collect()
        logs_df = data.get("logs")
        logs_df = logs_df.collect() if logs_df is not None else None

        logger.info(
            f"Loaded {len(traces_df)} trace spans, "
            f"{len(logs_df) if logs_df is not None and not logs_df.is_empty() else 0} logs"
        )

        # Step 2: Time-based data splitting for lookback window
        logger.info("Splitting data into lookback and alarm periods...")
        lookback_traces, alarm_traces, lookback_end_time = (
            self._split_lookback_alarm_data(traces_df)
        )

        logger.info(
            f"Lookback: {len(lookback_traces)} spans, Alarm: {len(alarm_traces)} spans"
        )

        # Step 3: Encode ALL traces once (much more efficient)
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

        # Step 4: Split encoded traces based on lookback split time
        logger.info("Splitting encoded traces into lookback and alarm periods...")
        if lookback_end_time:
            # Convert lookback_end_time to datetime for comparison
            import datetime

            split_datetime = datetime.datetime.fromtimestamp(
                lookback_end_time, tz=datetime.timezone.utc
            )
            lookback_encoded = all_encoded_traces.filter(
                pl.col("time") <= split_datetime
            )
            alarm_encoded = all_encoded_traces.filter(pl.col("time") > split_datetime)
        else:
            # Fallback to row-based split
            split_point = int(len(all_encoded_traces) * 0.3)
            lookback_encoded = all_encoded_traces[:split_point]
            alarm_encoded = all_encoded_traces[split_point:]

        logger.info(
            f"Encoded traces split - Lookback: {len(lookback_encoded)}, Alarm: {len(alarm_encoded)}"
        )

        # Calculate budget rebalancing factors based on time ranges and QPM
        total_traces = len(all_encoded_traces)
        target_total_samples = max(1, math.ceil(total_traces * args.sampling_rate))

        # Store target for budget tracking
        self.target_total_samples = target_total_samples

        # Calculate actual time ranges from encoded data (already in minute granularity)
        warmup_time_range_minutes = 1.0  # Minimum 1 minute
        processing_time_range_minutes = 1.0  # Minimum 1 minute

        import datetime

        # Calculate warmup time range from actual data
        if not lookback_encoded.is_empty():
            warmup_min_time = lookback_encoded["time"].min()
            warmup_max_time = lookback_encoded["time"].max()
            if (
                warmup_min_time is not None
                and warmup_max_time is not None
                and isinstance(warmup_min_time, datetime.datetime)
                and isinstance(warmup_max_time, datetime.datetime)
            ):
                # Time is already truncated to minutes, calculate difference in minutes directly
                warmup_time_range_minutes = max(
                    1.0, (warmup_max_time - warmup_min_time).total_seconds() / 60.0
                )

        # Calculate processing time range from actual data
        if not alarm_encoded.is_empty():
            processing_min_time = alarm_encoded["time"].min()
            processing_max_time = alarm_encoded["time"].max()
            if (
                processing_min_time is not None
                and processing_max_time is not None
                and isinstance(processing_min_time, datetime.datetime)
                and isinstance(processing_max_time, datetime.datetime)
            ):
                # Time is already truncated to minutes, calculate difference in minutes directly
                processing_time_range_minutes = max(
                    1.0,
                    (processing_max_time - processing_min_time).total_seconds() / 60.0,
                )

        # Calculate QPM (queries per minute) for each period
        lookback_qpm = (
            len(lookback_encoded) / warmup_time_range_minutes
            if warmup_time_range_minutes > 0
            else 0
        )
        alarm_qpm = (
            len(alarm_encoded) / processing_time_range_minutes
            if processing_time_range_minutes > 0
            else 0
        )

        # Simple proportional budget allocation based on time ranges
        total_weighted_time = warmup_time_range_minutes + processing_time_range_minutes
        if total_weighted_time > 0:
            lookback_budget_factor = warmup_time_range_minutes / total_weighted_time
            alarm_budget_factor = processing_time_range_minutes / total_weighted_time
        else:
            # Fallback: equal allocation
            lookback_budget_factor = 0.5
            alarm_budget_factor = 0.5

        # Calculate QPM rebalancing factor only when warmup QPM > processing QPM
        qpm_rebalancing_factor = 1.0  # Default: no rebalancing
        if lookback_qpm > alarm_qpm and alarm_qpm > 0:
            # Check if processing would need full sampling before applying QPM rebalancing
            tentative_alarm_sampling_rate = (
                (target_total_samples * alarm_budget_factor) / len(alarm_encoded)
                if len(alarm_encoded) > 0
                else 0
            )

            # Only apply QPM rebalancing if processing doesn't need full sampling
            if tentative_alarm_sampling_rate < 1.0:
                # Calculate mean QPM and scaling factor
                mean_qpm = (lookback_qpm + alarm_qpm) / 2.0
                qpm_rebalancing_factor = (
                    mean_qpm / lookback_qpm
                )  # Reduce warmup sampling rate

                logger.info(
                    f"QPM rebalancing applied - Mean QPM: {mean_qpm:.1f}, Factor: {qpm_rebalancing_factor:.3f}"
                )

                # Apply QPM rebalancing at budget level to preserve total target
                lookback_budget = int(
                    round(
                        target_total_samples
                        * lookback_budget_factor
                        * qpm_rebalancing_factor
                    )
                )
                # Assign the remainder to processing to keep total budget exact
                alarm_budget = max(0, target_total_samples - lookback_budget)
            else:
                logger.info(
                    f"QPM rebalancing skipped - Processing needs full sampling (rate: {tentative_alarm_sampling_rate:.3f})"
                )

                # Rebalance budget allocation when processing needs full sampling
                if len(alarm_encoded) > 0:
                    # Processing gets exactly the number of traces it has (full sampling)
                    alarm_budget = len(alarm_encoded)
                    # Warmup gets the remaining budget
                    lookback_budget = max(0, target_total_samples - alarm_budget)

                    logger.info(
                        f"Budget rebalanced for processing full sampling - "
                        f"Processing: {alarm_budget}, Warmup: {lookback_budget}, "
                        f"Total: {alarm_budget + lookback_budget}/{target_total_samples}"
                    )
                else:
                    # Use time-based proportional allocation as fallback
                    lookback_budget = target_total_samples * lookback_budget_factor
                    alarm_budget = target_total_samples * alarm_budget_factor
        else:
            # No QPM rebalancing conditions met, use time-based proportional allocation
            lookback_budget = target_total_samples * lookback_budget_factor
            alarm_budget = target_total_samples * alarm_budget_factor

        logger.info(
            f"Time ranges - Warmup: {warmup_time_range_minutes:.1f}min, Processing: {processing_time_range_minutes:.1f}min"
        )
        logger.info(f"QPM - Warmup: {lookback_qpm:.1f}, Processing: {alarm_qpm:.1f}")
        logger.info(
            f"Budget allocation - Warmup: {lookback_budget:.0f}, "
            f"Processing: {alarm_budget:.0f}, "
            f"QPM rebalancing factor: {qpm_rebalancing_factor:.3f}, "
            f"Target total: {target_total_samples}"
        )

        # Step 5: Build lookback baselines
        logger.info("Building lookback baselines...")
        self.quota_allocator.build_lookback_baselines(
            lookback_encoded, performance_thresholds
        )
        self.alarm_system.set_warmup_end_time(lookback_end_time)

        # Step 6: Process in batches using pre-encoded data
        logger.info(f"Processing traces in batches of {self.config.batch_size}...")
        all_results = []

        # Process lookback window data (no alarm, pure diversity)
        if not lookback_encoded.is_empty():
            # QPM rebalancing already applied at budget level
            lookback_sampling_rate = lookback_budget / len(lookback_encoded)
            lookback_sampling_rate = min(1.0, lookback_sampling_rate)

            logger.info(
                f"Warmup sampling rate adjusted to: {lookback_sampling_rate:.3f} (with QPM rebalancing)"
            )
            lookback_results = self._process_lookback_encoded_batch(
                lookback_encoded, lookback_sampling_rate, performance_thresholds
            )

            # Update budget tracking for warmup results
            if args.mode == SamplingMode.OFFLINE:
                self.total_sampled_count += len(lookback_results)
                # Store warmup results for potential backfill
                self.batch_results_history.append(lookback_results.copy())

            all_results.extend(lookback_results)

        # Process alarm window data in batches using pre-encoded data with rebalanced budget
        if not alarm_encoded.is_empty():
            alarm_sampling_rate = alarm_budget / len(alarm_encoded)
            alarm_sampling_rate = min(
                1.0, alarm_sampling_rate
            )  # No additional factor for processing

            logger.info(
                f"Processing sampling rate adjusted to: {alarm_sampling_rate:.3f}"
            )

            # Get unique trace IDs from encoded data
            total_alarm_traces = len(alarm_encoded)
            total_batches = (
                total_alarm_traces + self.config.batch_size - 1
            ) // self.config.batch_size

            for batch_idx in range(total_batches):
                # Check budget limit for offline mode before processing each batch
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

                # Direct slice of DataFrame (much more efficient)
                batch_encoded = alarm_encoded[start_idx:end_idx]
                batch_size = len(batch_encoded)

                logger.info(
                    f"Alarm batch {batch_idx + 1}/{total_batches}: {batch_size} traces"
                )

                batch_results = self._process_encoded_batch(
                    batch_encoded,
                    alarm_sampling_rate,  # Use adjusted rate
                    str(args.input_folder),
                    performance_thresholds,  # Pass performance thresholds
                )

                # Update budget tracking for offline mode
                if args.mode == SamplingMode.OFFLINE:
                    self.total_sampled_count += len(batch_results)
                    # Store batch results for potential backfill
                    self.batch_results_history.append(batch_results.copy())

                all_results.extend(batch_results)

        # Step 6: Apply final sampling mode strategy
        # Handle budget shortfall for offline mode
        if args.mode == SamplingMode.OFFLINE:
            # Provide encoded pool and thresholds for effective, prioritized backfill
            all_results = self._handle_offline_budget_backfill(
                all_results, all_encoded_traces, performance_thresholds
            )

        final_results = self._apply_sampling_mode(args, all_results)

        total_time = time.time() - start_time
        logger.info(
            f"Gleaner sampling complete: {len(final_results)}/{len(traces_df)} traces "
            f"(rate: {len(final_results) / len(traces_df):.3f}, time: {total_time:.2f}s)"
        )

        # Log DPP cache metrics and then clear caches after each full run
        try:
            cache_info = DPPSelector.get_cache_info()
            logger.info(
                f"DPP cache: hits={cache_info.get('hits')}, misses={cache_info.get('misses')}, "
                f"currsize={cache_info.get('currsize')}, maxsize={cache_info.get('maxsize')}"
            )
            DPPSelector.clear_caches()
            logger.debug("Cleared DPP LRU caches after run")
        except Exception as e:
            logger.debug(f"Failed to report/clear DPP caches: {e}")

        return final_results

    def _split_lookback_alarm_data(
        self, traces_df: pl.DataFrame
    ) -> tuple[pl.DataFrame, pl.DataFrame, float]:
        """Split traces into lookback window and alarm window periods"""

        # Handle different time column formats
        time_col = None
        for col in ["time", "timestamp", "start_time"]:
            if col in traces_df.columns:
                time_col = col
                break

        if time_col is None:
            # Fallback to row-based split
            logger.warning("No time column found, using row-based split for warmup")
            split_point = int(len(traces_df) * 0.3)  # 30% for warmup
            lookback_traces = traces_df[:split_point]
            alarm_traces = traces_df[split_point:]
            lookback_end_time = time.time()  # Use current time as fallback
        else:
            try:
                # Get time range
                min_time_value = traces_df[time_col].min()

                if min_time_value is None:
                    raise ValueError("No time data available")

                # Try to convert to numeric timestamp
                import datetime

                if isinstance(min_time_value, datetime.datetime):
                    # Datetime format
                    min_time_seconds = float(min_time_value.timestamp())
                    lookback_end_time = min_time_seconds + self.config.warmup_duration

                    split_datetime = datetime.datetime.fromtimestamp(
                        lookback_end_time, tz=datetime.timezone.utc
                    )

                    lookback_traces = traces_df.filter(
                        pl.col(time_col) <= split_datetime
                    )
                    alarm_traces = traces_df.filter(pl.col(time_col) > split_datetime)

                elif isinstance(min_time_value, (int, float)):
                    # Numeric timestamp
                    min_time_float = float(min_time_value)

                    # Detect timestamp format by magnitude
                    if min_time_float > 1e12:  # Microseconds
                        split_time = min_time_float + (
                            self.config.warmup_duration * 1_000_000
                        )
                    elif min_time_float > 1e10:  # Nanoseconds
                        split_time = min_time_float + (
                            self.config.warmup_duration * 1_000_000_000
                        )
                    else:  # Seconds
                        split_time = min_time_float + self.config.warmup_duration

                    lookback_traces = traces_df.filter(pl.col(time_col) <= split_time)
                    alarm_traces = traces_df.filter(pl.col(time_col) > split_time)
                    lookback_end_time = float(split_time)

                else:
                    # Try to convert to float for other numeric types
                    min_time_float = float(str(min_time_value))
                    split_time = min_time_float + self.config.warmup_duration

                    lookback_traces = traces_df.filter(pl.col(time_col) <= split_time)
                    alarm_traces = traces_df.filter(pl.col(time_col) > split_time)
                    lookback_end_time = float(split_time)

            except (ValueError, TypeError, AttributeError) as e:
                # Fallback for any time parsing errors
                logger.warning(
                    f"Failed to parse time column '{time_col}': {e}, using row-based split"
                )
                split_point = int(len(traces_df) * 0.3)
                lookback_traces = traces_df[:split_point]
                alarm_traces = traces_df[split_point:]
                lookback_end_time = time.time()

        return lookback_traces, alarm_traces, lookback_end_time

    def _process_lookback_encoded_batch(
        self,
        lookback_encoded: pl.DataFrame,
        sampling_rate: float,
        performance_thresholds: dict,
    ) -> List[SampleResult]:
        """Process lookback encoded data with root type quota allocation but no alarm system"""

        if lookback_encoded.is_empty():
            return []

        logger.info(
            "Processing lookback encoded batch with root type quota allocation (no alarm)..."
        )

        # Direct processing - each row is one trace
        total_traces = len(lookback_encoded)
        target_count = max(1, math.ceil(total_traces * sampling_rate))

        logger.info(
            f"Lookback processing: {total_traces} traces, target: {target_count}"
        )

        # Backup the current lookback batch processing for pure diversity variant
        self._warmup_pure_diversity_backup = self._process_lookback_pure_diversity

        # Use quota allocator for warmup but WITHOUT alarm system
        try:
            # Allocate quotas by root span type (no alarm context)
            quotas = self.quota_allocator.allocate_quotas(
                trace_batch=lookback_encoded,
                batch_budget=target_count,
                input_folder=None,  # No input folder for warmup
            )

            logger.info(
                f"Warmup quota allocation completed for {len(quotas)} root span types"
            )

            # Select traces based on allocated quotas with pure diversity (no relevance scores)
            results = []

            # Pre-slice by root once to avoid repeated filters
            try:
                parts = lookback_encoded.partition_by("root", as_dict=False)
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
                    root_traces = lookback_encoded.filter(
                        pl.col("root") == root_span_name
                    )
                if root_traces.is_empty():
                    continue

                # Extract patterns and trace IDs for this root span type
                trace_patterns = []
                trace_ids = []

                for row in root_traces.iter_rows(named=True):
                    trace_data = row
                    trace_id = trace_data.get("traceid")
                    pattern = self._make_pattern_from_row(trace_data)
                    trace_patterns.append(pattern)
                    trace_ids.append(trace_id)

                available_traces = len(trace_ids)
                quota = min(quota_info.allocated_quota, available_traces)

                # Use DPP for pure diversity (no relevance scores)
                try:
                    selected_trace_ids = self.dpp_selector.select_diverse_traces(
                        patterns=trace_patterns,
                        trace_ids=trace_ids,
                        quota=quota,
                        alarm_active=False,  # Warmup mode - no alarm
                        relevance_scores=None,  # Pure diversity - no relevance scores
                    )

                    # DPP now performs internal gap filling; no extra fill needed here

                    # Create results with base scores only (no root duration/status code scoring)
                    for trace_id in selected_trace_ids:
                        trace_data = root_traces.filter(
                            pl.col("traceid") == trace_id
                        ).row(0, named=True)

                        # Use only base anomaly score (no additional scoring for warmup)
                        base_score = trace_data.get("anomaly_score", 0.5)

                        results.append(
                            SampleResult(
                                trace_id=trace_id, sample_score=float(base_score)
                            )
                        )

                except Exception as e:
                    logger.warning(
                        f"DPP selection failed for {root_span_name}: {e}, using random selection"
                    )
                    # Fallback: random selection for this root span type
                    import random

                    selected_trace_ids = random.sample(
                        trace_ids, min(quota, len(trace_ids))
                    )

                    for trace_id in selected_trace_ids:
                        trace_data = root_traces.filter(
                            pl.col("traceid") == trace_id
                        ).row(0, named=True)
                        base_score = trace_data.get("anomaly_score", 0.5)
                        results.append(
                            SampleResult(
                                trace_id=trace_id, sample_score=float(base_score)
                            )
                        )

                logger.debug(
                    f"Warmup: Selected {len([r for r in results if r.trace_id in trace_ids])}"
                    f"/{available_traces} traces for {root_span_name}"
                )

        except Exception as e:
            logger.error(
                f"Warmup quota allocation failed: {e}, falling back to pure diversity"
            )
            # Fallback to original pure diversity approach
            results = self._process_lookback_pure_diversity(
                lookback_encoded, sampling_rate, performance_thresholds
            )

        logger.info(
            f"lookback batch sampled: {len(results)}/{total_traces} traces (root type quotas, pure diversity)"
        )
        return results

    def _process_lookback_pure_diversity(
        self,
        lookback_encoded: pl.DataFrame,
        sampling_rate: float,
        performance_thresholds: dict,
    ) -> List[SampleResult]:
        """Backup method: Pure diversity warmup processing (original implementation)"""

        if lookback_encoded.is_empty():
            return []

        logger.info(
            "Processing warmup encoded batch (pure diversity mode) in batches..."
        )

        # Direct processing - each row is one trace
        total_traces = len(lookback_encoded)
        target_count = max(1, math.ceil(total_traces * sampling_rate))

        logger.info(
            f"Lookback processing: {total_traces} traces, target: {target_count}"
        )

        # Process warmup in batches to avoid O(M²) complexity
        warmup_batch_size = self.config.batch_size  # Use same batch size
        total_batches = (total_traces + warmup_batch_size - 1) // warmup_batch_size
        all_results = []

        for batch_idx in range(total_batches):
            start_idx = batch_idx * warmup_batch_size
            end_idx = min(start_idx + warmup_batch_size, total_traces)

            # Direct slice of DataFrame (much more efficient)
            batch_encoded = lookback_encoded[start_idx:end_idx]
            batch_size = len(batch_encoded)

            # Calculate target for this batch (proportional)
            batch_target = max(1, math.ceil(batch_size * sampling_rate))

            logger.info(
                f"Processing lookback batch {batch_idx + 1}/{total_batches}: "
                f"{batch_size} traces, target: {batch_target}"
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
                    alarm_active=False,  # Warmup mode - no alarm
                    relevance_scores=None,  # Pure diversity - no relevance scores
                )

                # DPP now performs internal gap filling; no extra fill needed here

                batch_results = []
                # Create a mapping for efficient lookup
                trace_id_to_row = {trace_ids[i]: i for i in range(len(trace_ids))}

                for trace_id in selected_trace_ids:
                    row_idx = trace_id_to_row[trace_id]
                    trace_data = batch_encoded.row(row_idx, named=True)

                    # Use only base anomaly score
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
                f"lookback batch {batch_idx + 1} sampled: {len(batch_results)}/{batch_size} traces"
            )

        logger.info(
            f"lookback batch sampled: {len(all_results)}/{total_traces} traces (pure diversity, batched)"
        )
        return all_results

    def _process_encoded_batch(
        self,
        batch_encoded: pl.DataFrame,
        sampling_rate: float,
        input_folder: str,
        performance_thresholds: dict,
    ) -> List[SampleResult]:
        """Process a single encoded batch with full alarm+quota+DPP pipeline"""

        if batch_encoded.is_empty():
            return []

        # Get total traces and calculate budget
        total_traces = len(batch_encoded)
        batch_budget = max(1, math.ceil(total_traces * sampling_rate))

        logger.info(f"Processing {total_traces} traces, budget: {batch_budget}")

        # Step 1: Use QuotaAllocator with full alarm+quota+DPP pipeline
        try:
            quotas = self.quota_allocator.allocate_quotas(
                trace_batch=batch_encoded,
                batch_budget=batch_budget,
                input_folder=input_folder,
            )

            logger.info(f"Quota allocation completed for {len(quotas)} root span types")

            # Step 2: Select traces based on allocated quotas
            results = []

            # Pre-slice by root once to avoid repeated filters
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

                # Extract patterns and trace IDs for DPP selection
                trace_patterns = []
                trace_ids = []
                relevance_scores = []

                for i in range(len(root_traces)):
                    trace_data = root_traces.row(i, named=True)
                    trace_id = trace_data.get("traceid")
                    if trace_id is None:
                        continue

                    # Extract pattern for DPP
                    pattern = self._make_pattern_from_row(trace_data)
                    trace_patterns.append(pattern)
                    trace_ids.append(trace_id)

                    # Calculate relevance score (same logic as before)
                    base_score = trace_data.get("anomaly_score", 0.0)
                    dpp_score_val = trace_data.get("dpp_score", None)

                    if dpp_score_val is not None:
                        # Use per-trace dpp_score
                        final_score = base_score + float(dpp_score_val or 0.0)
                    else:
                        # Fallback to manual calculation
                        error_boost = (
                            5.0 if trace_data.get("root_is_error", False) else 0.0
                        )
                        duration_boost = 0.0
                        root_duration = trace_data.get("root_duration_ms", 0.0)
                        root_span_name = trace_data.get("root", "")
                        p90_threshold = performance_thresholds.get(root_span_name, 0.0)
                        if p90_threshold > 0 and root_duration > p90_threshold:
                            degradation_ratio = root_duration / p90_threshold
                            if degradation_ratio >= 5.0:
                                duration_boost = 3.0
                            elif degradation_ratio >= 3.0:
                                duration_boost = 2.0
                            elif degradation_ratio >= 1.5:
                                duration_boost = 1.0
                        final_score = base_score + error_boost + duration_boost

                    relevance_scores.append(final_score)

                # Use DPP selector for diverse + relevant sampling
                try:
                    selected_trace_ids = self.dpp_selector.select_diverse_traces(
                        patterns=trace_patterns,
                        trace_ids=trace_ids,
                        quota=quota,
                        alarm_active=True,  # Processing mode - use alarm
                        relevance_scores=relevance_scores,  # Use relevance scores
                    )

                    # Create results from DPP selection
                    trace_id_to_score = {
                        trace_ids[i]: relevance_scores[i] for i in range(len(trace_ids))
                    }

                    for trace_id in selected_trace_ids:
                        score = trace_id_to_score.get(trace_id, 0.0)
                        results.append(
                            SampleResult(
                                trace_id=str(trace_id), sample_score=float(score)
                            )
                        )

                except Exception as e:
                    logger.warning(
                        f"DPP selection failed for {root_span_name}: {e}, falling back to top-k selection"
                    )
                    # Fallback: top-k selection (original logic)
                    trace_scores = [
                        (trace_ids[i], relevance_scores[i])
                        for i in range(len(trace_ids))
                    ]
                    trace_scores.sort(key=lambda x: x[1], reverse=True)
                    selected_traces = trace_scores[:quota]

                    for trace_id, score in selected_traces:
                        results.append(
                            SampleResult(
                                trace_id=str(trace_id), sample_score=float(score)
                            )
                        )

                logger.debug(
                    f"Selected {len([r for r in results if r.trace_id in [str(tid) for tid in trace_ids]])}"
                    f"/{available_traces} traces for {root_span_name}"
                )

        except Exception as e:
            logger.error(
                f"Quota allocation failed: {e}, falling back to simple scoring"
            )
            # Fallback: use precomputed per-trace dpp_score if available
            trace_scores = []
            for i in range(len(batch_encoded)):
                trace_data = batch_encoded.row(i, named=True)
                trace_id = trace_data.get("traceid")
                if trace_id is None:
                    continue

                dpp_score = float(trace_data.get("dpp_score", 0.0) or 0.0)
                base_score = trace_data.get("anomaly_score", 0.0)
                final_score = base_score + dpp_score

                trace_scores.append((trace_id, final_score))

            # Select top traces by score
            trace_scores.sort(key=lambda x: x[1], reverse=True)
            selected_traces = trace_scores[:batch_budget]

            results = []
            for trace_id, score in selected_traces:
                results.append(
                    SampleResult(trace_id=str(trace_id), sample_score=float(score))
                )

        logger.info(f"Processed batch: {len(results)}/{total_traces} traces sampled")
        return results

    def _is_budget_exhausted(self) -> bool:
        """Check if budget is exhausted for offline mode"""
        return self.total_sampled_count >= self.target_total_samples

    def _handle_offline_budget_backfill(
        self,
        all_results: List[SampleResult],
        encoded_pool: pl.DataFrame,
        performance_thresholds: dict,
    ) -> List[SampleResult]:
        """Handle budget shortfall by backfilling from previous batches"""
        current_count = len(all_results)
        shortfall = self.target_total_samples - current_count

        if shortfall <= 0:
            logger.info(
                f"Offline budget satisfied: {current_count}/{self.target_total_samples}"
            )
            return all_results

        logger.info(
            f"Budget shortfall detected: {current_count}/{self.target_total_samples}, need {shortfall} more samples"
        )

        # Build selection set and choose additional traces from the encoded pool, prioritizing higher per-trace dpp_score
        selected_trace_ids = {str(result.trace_id) for result in all_results}

        # Filter remaining pool efficiently
        try:
            remaining_df = encoded_pool.filter(
                ~pl.col("traceid").cast(pl.Utf8).is_in(list(selected_trace_ids))
            )
        except Exception:
            # Fallback without cast
            remaining_df = encoded_pool.filter(
                ~pl.col("traceid").is_in(list(selected_trace_ids))
            )

        if remaining_df.is_empty():
            logger.warning("No remaining traces available for backfill from pool")
            return all_results

        # Prefer using precomputed dpp_score; if missing, treat as 0
        ranked = (
            remaining_df.with_columns(
                [pl.col("dpp_score").fill_null(0.0).cast(pl.Float64).alias("dpp_score")]
            )
            .select([pl.col("traceid").cast(pl.Utf8).alias("traceid"), "dpp_score"])
            .sort("dpp_score", descending=True)
        )

        backfill_count = min(shortfall, len(ranked))
        if backfill_count <= 0:
            logger.warning("No candidates available for backfill after ranking")
            return all_results

        topk = ranked.head(backfill_count)
        backfill_results = [
            SampleResult(
                trace_id=str(topk.row(i)[0]), sample_score=float(topk.row(i)[1])
            )
            for i in range(len(topk))
        ]

        logger.info(
            f"Backfilled {backfill_count} traces from encoded pool (prioritized by DPP-like anomaly)"
        )

        final_results = all_results + backfill_results
        logger.info(
            f"Final offline budget: {len(final_results)}/{self.target_total_samples}"
        )

        return final_results

    def _make_pattern_from_row(self, trace_data: dict) -> set:
        """Convert encoded row into an edge-set pattern for DPP.

        Supports both tuple and list edge formats
        """
        event_edges = trace_data.get("event", [])
        if not event_edges:
            return set()
        first = event_edges[0]
        if isinstance(first, tuple):
            return set(event_edges)
        # Legacy nested-list format
        pattern = set()
        for edge in event_edges:
            if isinstance(edge, list) and len(edge) == 2:
                pattern.add((edge[0], edge[1]))
        return pattern

    def _apply_sampling_mode(
        self, args: SamplerArgs, results: List[SampleResult]
    ) -> List[SampleResult]:
        """Apply final sampling mode strategy"""

        if args.mode == SamplingMode.ONLINE:
            # Online mode: budget control already applied during batch processing
            # Just sort by score and return all results (no additional rate limiting)
            if not results:
                return []

            results.sort(key=lambda x: x.sample_score, reverse=True)

            logger.info(
                f"Online sampling: returning {len(results)} traces (budget already applied)"
            )

            return results

        elif args.mode == SamplingMode.OFFLINE:
            # Offline mode: budget control already applied during batch processing
            # Sort by score and apply strict budget limit
            results.sort(key=lambda x: x.sample_score, reverse=True)

            # Apply strict budget limit - never exceed target
            if len(results) > self.target_total_samples:
                results = results[: self.target_total_samples]
                logger.info(
                    f"Offline sampling: truncated to strict budget {len(results)}/{self.target_total_samples}"
                )
            else:
                logger.info(
                    f"Offline sampling: returning {len(results)}/{self.target_total_samples} traces (within budget)"
                )

            return results

        return results
