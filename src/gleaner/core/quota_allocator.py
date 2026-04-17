"""
Hierarchical Quota Allocator for Gleaner V2

This module implements quota allocation based on root span health analysis
and error/latency metrics from SLI data.
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import polars as pl
from rcabench_platform.v2.logging import logger

from ..utils.config import GleanerConfig
from .alarm_system import AlarmSystem


@dataclass
class RootSpanHealthMetrics:
    """Health metrics for a root span type"""

    error_count: int = 0
    duration_p90: float = 0.0
    total_count: int = 0
    is_anomalous: bool = False
    weight: float = 1.0
    dpp_anomaly_score: float = 0.0  # Aggregated DPP anomaly score from trace encoder (precomputed per-trace scores)


@dataclass
class QuotaInfo:
    """Quota allocation information for a root span type"""

    root_span_name: str
    trace_count: int
    allocated_quota: int
    weight: float
    is_full_sampling: bool = False  # True if trace_count < quota
    health_metrics: Optional[RootSpanHealthMetrics] = None


class QuotaAllocator:
    """
    Hierarchical Quota Allocator

    Allocates sampling quotas based on:
    1. Root span health analysis (error count, P90 latency)
    2. Anomaly detection compared to warmup baselines
    3. Dynamic weight adjustment for anomalous categories
    """

    def __init__(
        self,
        budget_per_batch: int = 100,
        trace_encoder: Optional[Any] = None,
        input_folder: Optional[Path] = None,
        config: Optional[GleanerConfig] = None,
        alarm_system: Optional[AlarmSystem] = None,
    ):
        """
        Initialize quota allocator

        Args:
            budget_per_batch: Budget quota per batch
            trace_encoder: TraceEncoder instance for trace processing
            input_folder: Input folder containing env.json for injection time
            config: GleanerConfig instance containing algorithm parameters
        """
        from ..utils.config import DEFAULT_CONFIG

        # Use provided config or default
        if config is None:
            config = DEFAULT_CONFIG

        self.budget_per_batch = budget_per_batch
        self.trace_encoder = trace_encoder
        self.input_folder = input_folder
        self.p90_factor = config.p90_factor
        self.anomaly_weight_cap = config.anomaly_weight_cap
        self.p90_improvement_threshold = config.p90_improvement_threshold
        # Feature toggles
        self.enable_global_balancing = getattr(config, "enable_global_balancing", True)

        # Warmup baselines {root_span_name: baseline_metrics}
        self.warmup_baselines = {}

        # Step 4: Global sampled quota tracking
        self.global_sampled_counts = defaultdict(int)  # {root_span_name: sampled_count}
        self.total_batches_processed = 0  # Number of batches processed

        # Step 5: Detector-based alarm system
        self.alarm_system = alarm_system or AlarmSystem(
            input_folder=input_folder,
            detector_weight=config.detector_weight,
            max_detector_budget_ratio=config.max_detector_budget_ratio,
        )

        self.warmup_end_timestamp = None

        # Cache for metrics_sli to avoid re-reading the parquet on every batch
        self._cached_sli_folder = None
        self._cached_sli_df = None
        self._cached_sli_index = None  # {(minute_ts, span_name): {metrics}}

    def build_lookback_baselines(
        self,
        lookback_traces: pl.DataFrame,
        performance_thresholds: Optional[dict] = None,
    ) -> None:
        """
        Build baseline metrics from lookback period data
        Use rcabench platform's performance_thresholds as P90 baseline

        Args:
            lookback_traces: Lookback trace data
            performance_thresholds: Performance thresholds dict or object with performance_thresholds attribute
        """
        logger.info("Building lookback baselines from lookback traces...")

        # Try to load injection time (if not yet loaded and input_folder is available)
        self.alarm_system.load_injection_time_if_needed(self.input_folder)

        # Use injection time or lookback end timestamp
        if self.alarm_system.injection_time is not None:
            # Use injection time as split point
            split_time = self.alarm_system.injection_time
            logger.info(f"Using injection time for split: {split_time}")
        else:
            # Calculate lookback end timestamp as fallback
            if not lookback_traces.is_empty():
                max_time = lookback_traces.select("time").max().item()
                if max_time is not None:
                    if hasattr(max_time, "timestamp"):
                        # If it is a datetime object, convert to timestamp
                        split_time = max_time.timestamp()
                    else:
                        # Assume it is already a timestamp
                        split_time = float(max_time)
                    logger.info(f"Using lookback end timestamp: {split_time}")
                else:
                    split_time = None
            else:
                split_time = None

        self.warmup_end_timestamp = split_time

        # Set the warmup end time for alarm system
        if self.warmup_end_timestamp is not None:
            self.alarm_system.set_warmup_end_time(self.warmup_end_timestamp)

        # Filter to only root spans: Use the new encoding format, group directly by root column
        # Calculate error count, P90 uses trace_encoder's performance_thresholds
        root_span_groups = lookback_traces.group_by("root").agg(
            [
                pl.count().alias("total_count"),
                # Use root_is_error to calculate error count
                pl.col("root_is_error").sum().alias("error_count"),
            ]
        )

        # Get performance thresholds as P90 baseline
        thresholds_dict = {}
        if isinstance(performance_thresholds, dict):
            thresholds_dict = performance_thresholds
            logger.info(
                f"Loaded {len(thresholds_dict)} performance thresholds from dict"
            )
        else:
            logger.warning(
                "No performance thresholds available, P90 baselines will be 0"
            )

        for row in root_span_groups.iter_rows(named=True):
            root_span_name = row["root"]

            # Try to get corresponding P90 threshold from performance_thresholds
            # performance_thresholds key format is "service_name_span_name"
            duration_p90 = 0.0

            # Extract service and span information from root span name to match performance_thresholds
            for threshold_key, threshold_value in thresholds_dict.items():
                # threshold_value is already in milliseconds from updated dependency
                if threshold_key in root_span_name or root_span_name in threshold_key:
                    duration_p90 = float(threshold_value)  # Already in milliseconds
                    logger.debug(
                        f"Found P90 threshold for {root_span_name}: {duration_p90:.2f}ms (from {threshold_key})"
                    )
                    break

            if duration_p90 == 0.0:
                logger.debug(
                    f"No P90 threshold found for {root_span_name}, using 0.0ms"
                )

            baseline = RootSpanHealthMetrics(
                error_count=row["error_count"],
                duration_p90=duration_p90,
                total_count=row["total_count"],
                is_anomalous=False,
                weight=1.0,
            )

            self.warmup_baselines[root_span_name] = baseline

        logger.info(f"Built baselines for {len(self.warmup_baselines)} root span types")

        # Log some baseline examples
        for name, baseline in list(self.warmup_baselines.items())[:3]:
            logger.debug(
                f"Baseline {name}: P90={baseline.duration_p90:.2f}ms, "
                f"errors={baseline.error_count}/{baseline.total_count}"
            )

    def allocate_quotas(
        self,
        trace_batch: pl.DataFrame,
        batch_budget: int,
        input_folder: Optional[str] = None,
    ) -> Dict[str, QuotaInfo]:
        """
        Allocate quotas for root span types in current batch

        Args:
            trace_batch: Current batch of traces
            batch_budget: Total sampling budget for this batch
            input_folder: Optional input folder to load metrics_sli data

        Returns:
            Dictionary mapping root_span_name to QuotaInfo
        """
        # Try to load injection time (if input_folder parameter is provided and not yet loaded)
        if input_folder is not None:
            from pathlib import Path

            self.alarm_system.load_injection_time_if_needed(Path(input_folder))

        # Step 1: Group traces by root span type
        root_span_groups = self._group_by_root_span(trace_batch)

        if not root_span_groups:
            # Count total spans in batch for context
            total_spans = len(trace_batch)
            loadgenerator_spans = len(
                trace_batch.filter(pl.col("service_name") == "loadgenerator")
            )
            logger.warning(
                f"No root span groups found in batch: {total_spans} total spans, "
                f"{loadgenerator_spans} loadgenerator spans (non-root traces)"
            )
            return {}

        # Step 2: Analyze health metrics for each group
        health_analysis = self._analyze_root_span_health(
            root_span_groups, trace_batch, input_folder
        )

        # Step 3: Calculate quotas with weights
        quotas = self._calculate_weighted_quotas(health_analysis, batch_budget)

        # Step 4: Handle full sampling cases
        quotas = self._handle_full_sampling(quotas)

        # Step 4: Global quota balancing adjustment
        quotas = self._apply_global_quota_balancing(quotas, batch_budget)

        # Step 5: DPP anomaly score calculation (only performed after warmup)
        if self.warmup_end_timestamp is not None:
            quotas = self._apply_dpp_anomaly_scoring(quotas, trace_batch, input_folder)

        # Update global sampled statistics
        self._update_global_sampled_counts(quotas)

        # Log quota allocation summary
        self._log_quota_summary(quotas, batch_budget)

        return quotas

    def _group_by_root_span(self, trace_batch: pl.DataFrame) -> Dict[str, List[str]]:
        """Group traces by root span type"""
        root_span_groups = defaultdict(list)

        # Use new encoding format, group directly by root and traceid
        for row in trace_batch.iter_rows(named=True):
            root_span_name = row["root"]
            trace_id = row["traceid"]
            root_span_groups[root_span_name].append(trace_id)

        logger.debug(f"Found {len(root_span_groups)} root span types")
        return dict(root_span_groups)

    def _analyze_root_span_health(
        self,
        root_span_groups: Dict[str, List[str]],
        trace_batch: pl.DataFrame,
        input_folder: Optional[str],
    ) -> Dict[str, QuotaInfo]:
        """Analyze health metrics for each root span type"""
        health_analysis = {}

        # Load metrics_sli data if available
        sli_data = self._load_metrics_sli(input_folder) if input_folder else None

        for root_span_name, trace_ids in root_span_groups.items():
            # Get traces for this root span type (using new encoding format)
            root_traces = trace_batch.filter(
                pl.col("traceid").is_in(trace_ids) & pl.col("root").eq(root_span_name)
            )

            if root_traces.is_empty():
                continue

            # Calculate current health metrics
            current_metrics = self._calculate_current_health_metrics(
                root_traces, sli_data
            )

            # Compare with baseline and determine anomaly status
            baseline = self.warmup_baselines.get(root_span_name)
            if baseline:
                current_metrics.is_anomalous = self._is_anomalous(
                    current_metrics, baseline
                )
                current_metrics.weight = self._calculate_weight(
                    current_metrics, baseline
                )

            quota_info = QuotaInfo(
                root_span_name=root_span_name,
                trace_count=len(trace_ids),
                allocated_quota=0,  # Will be calculated later
                weight=current_metrics.weight,
                health_metrics=current_metrics,
            )

            health_analysis[root_span_name] = quota_info

        return health_analysis

    def _load_metrics_sli(self, input_folder: str) -> Optional[pd.DataFrame]:
        """Load metrics_sli.parquet if available"""
        try:
            import os

            # Return cached if same folder
            if (
                self._cached_sli_folder == input_folder
                and self._cached_sli_df is not None
            ):
                # Ensure index exists for cached DF
                if self._cached_sli_index is None:
                    try:
                        df = self._cached_sli_df
                        # Normalize time to minute
                        if not pd.api.types.is_datetime64_any_dtype(df["time"]):
                            df = df.copy()
                            df["time"] = pd.to_datetime(df["time"]).dt.floor("min")
                        else:
                            df = df.copy()
                            df["time"] = df["time"].dt.floor("min")
                        index = {}
                        for _, row in df.iterrows():
                            key = (row.get("time"), row.get("span_name"))
                            if key not in index:
                                index[key] = {
                                    "error_count": int(row.get("error_count", 0) or 0),
                                    "duration_p90": float(
                                        row.get("duration_p90", 0.0) or 0.0
                                    ),
                                }
                        self._cached_sli_index = index
                    except Exception as ie:
                        logger.debug(f"Failed building cached SLI index: {ie}")
                return self._cached_sli_df

            sli_path = os.path.join(input_folder, "metrics_sli.parquet")
            sli_path = os.path.join(input_folder, "metrics_sli.parquet")
            if os.path.exists(sli_path):
                sli_df = pd.read_parquet(sli_path)
                # Build O(1) index {(minute_ts, span_name) -> metrics}
                try:
                    df = sli_df
                    index = {}
                    for _, row in df.iterrows():
                        key = (row.get("time"), row.get("span_name"))
                        if key not in index:
                            index[key] = {
                                "error_count": int(row.get("error_count", 0) or 0),
                                "duration_p90": float(
                                    row.get("duration_p90", 0.0) or 0.0
                                ),
                            }
                    self._cached_sli_index = index
                except Exception as ie:
                    logger.debug(f"Failed building SLI index: {ie}")

                # Cache for subsequent batches
                self._cached_sli_folder = input_folder
                self._cached_sli_df = sli_df
                logger.debug(f"Loaded metrics_sli with {len(sli_df)} records")
                return sli_df
        except Exception as e:
            logger.warning(f"Could not load metrics_sli: {e}")

        return None

    def _calculate_current_health_metrics(
        self, root_traces: pl.DataFrame, sli_data: Optional[pd.DataFrame]
    ) -> RootSpanHealthMetrics:
        """Calculate health metrics for current root span traces"""

        # Use new encoding format, no duration and status_code information
        # Temporarily use default values, can be supplemented from SLI data later
        total_count = len(root_traces)
        duration_p90 = 0.0  # No duration information after encoding
        error_count = 0  # No status information after encoding

        # Try to get more accurate metrics from SLI data
        if sli_data is not None and not root_traces.is_empty():
            sli_metrics = self._get_sli_metrics(root_traces, sli_data)
            if sli_metrics:
                error_count = max(error_count, sli_metrics.get("error_count", 0))
                sli_p90 = sli_metrics.get("duration_p90")
                if sli_p90 is not None:
                    duration_p90 = sli_p90

        return RootSpanHealthMetrics(
            error_count=int(error_count),
            duration_p90=duration_p90 or 0.0,
            total_count=total_count,
        )

    def _get_sli_metrics(
        self, root_traces: pl.DataFrame, sli_data: pd.DataFrame
    ) -> Optional[Dict[str, float]]:
        """Extract metrics from SLI data based on trace timing"""
        try:
            # Get first trace timestamp to determine minute
            first_trace = root_traces.select("time").limit(1)
            if first_trace.is_empty():
                return None

            first_time = first_trace.item()

            # Convert to minute timestamp for SLI lookup
            if hasattr(first_time, "timestamp"):
                # It's a datetime
                minute_timestamp = pd.Timestamp(first_time).floor("min")
            else:
                # Try to parse as timestamp
                minute_timestamp = pd.to_datetime(first_time).floor("min")

            # Get root span name (using new format)
            root_span_name = root_traces.select("root").limit(1).item()

            # Try O(1) index first
            if self._cached_sli_index is not None:
                key = (minute_timestamp.floor("min"), root_span_name)
                val = self._cached_sli_index.get(key)
                if val is not None:
                    return {
                        "error_count": int(val.get("error_count", 0)),
                        "duration_p90": float(val.get("duration_p90", 0.0)),
                    }

            # Fallback to DataFrame filtering
            df = sli_data
            try:
                if not pd.api.types.is_datetime64_any_dtype(df["time"]):
                    df = df.copy()
                    df["time"] = pd.to_datetime(df["time"]).dt.floor("min")
                else:
                    df = df.copy()
                    df["time"] = df["time"].dt.floor("min")
            except Exception:
                pass
            sli_match = df[
                (df["time"] == minute_timestamp) & (df["span_name"] == root_span_name)
            ]
            if not sli_match.empty:
                row0 = sli_match.iloc[0]
                return {
                    "error_count": int(row0.get("error_count", 0) or 0),
                    "duration_p90": float(row0.get("duration_p90", 0.0)),
                }
        except Exception as e:
            logger.debug(f"Error extracting SLI metrics: {e}")

        return None

    def _is_anomalous(
        self, current: RootSpanHealthMetrics, baseline: RootSpanHealthMetrics
    ) -> bool:
        """Determine if current metrics indicate anomaly"""
        # Check for errors
        if current.error_count > 0:
            return True

        # Check P90 latency increase
        if baseline.duration_p90 > 0:
            p90_ratio = current.duration_p90 / baseline.duration_p90
            if p90_ratio > self.p90_factor:
                return True

        return False

    def _calculate_weight(
        self, current: RootSpanHealthMetrics, baseline: RootSpanHealthMetrics
    ) -> float:
        """Calculate sampling weight based on anomaly severity"""
        if not current.is_anomalous:
            return 1.0

        # If there are errors, use max weight
        if current.error_count > 0:
            return self.anomaly_weight_cap

        # Calculate weight based on P90 improvement ratio
        if baseline.duration_p90 > 0:
            p90_ratio = current.duration_p90 / baseline.duration_p90
            if p90_ratio > self.p90_factor:
                # Linear mapping from p90_factor to p90_improvement_threshold
                # Maps to weight range [1.0, anomaly_weight_cap]
                improvement_ratio = (p90_ratio - self.p90_factor) / (
                    self.p90_improvement_threshold - self.p90_factor
                )
                improvement_ratio = min(improvement_ratio, 1.0)  # Cap at 1.0

                weight = 1.0 + improvement_ratio * (self.anomaly_weight_cap - 1.0)
                return min(weight, self.anomaly_weight_cap)

        return 1.0

    def _calculate_weighted_quotas(
        self,
        health_analysis: Dict[str, QuotaInfo],
        batch_budget: int,
    ) -> Dict[str, QuotaInfo]:
        """Allocate quotas using detector-span based logic.

        Rules:
        - Detector root span types get configurable weight (default 3x) but can take at most
          configurable ratio (default 50%) of total budget.
        - Allocate detector share first; if full-sampled, refund unused to common pool.
        - Remaining budget is split evenly among non-detector types.
        - If some non-detector types are full-sampled, keep refunding evenly until exhausted.
        """
        if not health_analysis:
            return {}

        # Helper: exact even-split under caps; returns total allocated
        def exact_even_split(total: int, names: List[str]) -> int:
            if total <= 0 or not names:
                return 0

            # Sort names by ascending trace_count for rare-first allocation
            sorted_names = sorted(
                names, key=lambda n: (health_analysis[n].trace_count, n)
            )

            n = len(sorted_names)
            base = total // n
            rem = total % n

            # Initial allocation: give each type the base amount plus remainder
            alloc = {}
            for i, name in enumerate(sorted_names):
                want = base + (1 if i < rem else 0)
                alloc[name] = want

            # Apply allocation back to health_analysis
            for name in sorted_names:
                qi = health_analysis[name]
                qi.allocated_quota = int(alloc.get(name, 0))
                qi.is_full_sampling = qi.allocated_quota >= qi.trace_count

            return sum(alloc.values())

        detector_spans = self.alarm_system.get_detector_spans_cached()
        detector_set = set(detector_spans) if detector_spans else set()

        detector_types = sorted(
            [k for k in health_analysis.keys() if k in detector_set]
        )

        # If detector bias is disabled (ratio <= 0 or weight <= 1), exact even split across all types
        detector_bias_enabled = (
            self.alarm_system.max_detector_budget_ratio > 0
            and self.alarm_system.detector_weight > 1
            and len(detector_types) > 0
        )

        if not detector_bias_enabled:
            if batch_budget <= 0:
                return health_analysis
            names = list(health_analysis.keys())
            _ = exact_even_split(batch_budget, names)
            return health_analysis

        # NEW STRATEGY: First ensure minimum 1 quota per type, then apply detector bias
        all_types = list(health_analysis.keys())

        # Step 1: Allocate minimum 1 quota to each type
        min_quota_needed = len(all_types)
        if batch_budget < min_quota_needed:
            # If budget is too small, fall back to even split
            _ = exact_even_split(batch_budget, all_types)
            return health_analysis

        # Allocate 1 quota to each type first
        for name in all_types:
            health_analysis[name].allocated_quota = 1
            health_analysis[name].is_full_sampling = (
                health_analysis[name].allocated_quota
                >= health_analysis[name].trace_count
            )

        allocated_total = min_quota_needed
        remaining_budget = batch_budget - allocated_total

        if remaining_budget <= 0:
            return health_analysis

        # Step 2: Apply detector bias to remaining budget
        # Cap additional detector budget at configured ratio of TOTAL budget minus minimum allocations
        max_additional_detector_budget = int(
            math.floor(batch_budget * self.alarm_system.max_detector_budget_ratio)
        ) - len(
            detector_types
        )  # Subtract already allocated minimum quotas for detector types
        max_additional_detector_budget = max(0, max_additional_detector_budget)

        # But can't exceed remaining budget
        max_additional_detector_budget = min(
            max_additional_detector_budget, remaining_budget
        )

        refunds = 0

        if detector_types and max_additional_detector_budget > 0:
            # Mark weight for detector types (for logging)
            for name in detector_types:
                health_analysis[name].weight = self.alarm_system.detector_weight

            # Allocate additional quotas to detector types
            detector_additional = {}
            if max_additional_detector_budget > 0:
                # Sort detector types by ascending trace_count for rare-first allocation
                sorted_detector_types = sorted(
                    detector_types, key=lambda n: (health_analysis[n].trace_count, n)
                )

                n = len(sorted_detector_types)
                base = max_additional_detector_budget // n
                rem = max_additional_detector_budget % n

                for i, name in enumerate(sorted_detector_types):
                    additional = base + (1 if i < rem else 0)
                    detector_additional[name] = additional
                    health_analysis[name].allocated_quota += additional
                    health_analysis[name].is_full_sampling = (
                        health_analysis[name].allocated_quota
                        >= health_analysis[name].trace_count
                    )

            spent_additional = sum(detector_additional.values())
            allocated_total += spent_additional
            refunds = max(0, max_additional_detector_budget - spent_additional)

        # Step 3: Distribute remaining budget to all types (including detectors)
        final_remaining_budget = max(0, batch_budget - allocated_total) + refunds

        if final_remaining_budget > 0:
            # Sort all types by current allocated quota (ascending) to help balance
            sorted_all_types = sorted(
                all_types,
                key=lambda n: (
                    health_analysis[n].allocated_quota,
                    health_analysis[n].trace_count,
                    n,
                ),
            )

            n = len(sorted_all_types)
            base = final_remaining_budget // n
            rem = final_remaining_budget % n

            for i, name in enumerate(sorted_all_types):
                additional = base + (1 if i < rem else 0)
                health_analysis[name].allocated_quota += additional
                health_analysis[name].is_full_sampling = (
                    health_analysis[name].allocated_quota
                    >= health_analysis[name].trace_count
                )

            allocated_total += final_remaining_budget

        # Defensive check: ensure we don't exceed batch_budget (should rarely happen with new logic)
        total_allocated_now = sum(
            info.allocated_quota for info in health_analysis.values()
        )
        if total_allocated_now > batch_budget:
            overflow = total_allocated_now - batch_budget
            logger.warning(
                f"Quota allocation overflow detected: {total_allocated_now} > {batch_budget}, overflow = {overflow}"
            )

            # Smart overflow handling: reduce from types with most allocation first, protect minimum quota
            sorted_by_allocation = sorted(
                health_analysis.items(),
                key=lambda x: x[1].allocated_quota,
                reverse=True,  # Start with highest allocation
            )

            for name, qi in sorted_by_allocation:
                if overflow <= 0:
                    break

                # Don't reduce below minimum quota (1) to preserve coverage
                can_reduce = max(0, qi.allocated_quota - 1)
                reduction = min(can_reduce, overflow)

                if reduction > 0:
                    qi.allocated_quota -= reduction
                    overflow -= reduction
                    qi.is_full_sampling = qi.allocated_quota >= qi.trace_count
                    logger.debug(
                        f"Reduced {name} quota by {reduction} to {qi.allocated_quota}"
                    )

            if overflow > 0:
                logger.error(
                    f"Failed to eliminate all overflow: {overflow} quota still exceeds budget"
                )

        return health_analysis

    def _handle_full_sampling(
        self, quotas: Dict[str, QuotaInfo]
    ) -> Dict[str, QuotaInfo]:
        """Handle cases where trace count < allocated quota and redistribute remaining budget"""
        # Step 1: Handle full sampling cases, record saved quota
        saved_quota = 0
        non_full_sampling_types = []

        for quota_info in quotas.values():
            if quota_info.trace_count <= quota_info.allocated_quota:
                quota_info.is_full_sampling = True
                saved_quota += quota_info.allocated_quota - quota_info.trace_count
                quota_info.allocated_quota = quota_info.trace_count
                logger.debug(
                    f"Full sampling for {quota_info.root_span_name}: "
                    f"{quota_info.trace_count} traces"
                )
            else:
                non_full_sampling_types.append(quota_info)

        # Step 2: Redistribute saved quota to non-full sampling types
        if saved_quota > 0 and non_full_sampling_types:
            extra_quota_per_type = saved_quota // len(non_full_sampling_types)
            remaining_quota = saved_quota % len(non_full_sampling_types)

            logger.debug(
                f"Redistributing {saved_quota} saved quota to {len(non_full_sampling_types)} types"
            )

            for i, quota_info in enumerate(non_full_sampling_types):
                # First remaining_quota types get 1 extra allocation
                extra = extra_quota_per_type + (1 if i < remaining_quota else 0)
                quota_info.allocated_quota += extra

                logger.debug(
                    f"  {quota_info.root_span_name}: +{extra} quota, total={quota_info.allocated_quota}"
                )

        return quotas

    def _log_quota_summary(self, quotas: Dict[str, QuotaInfo], batch_budget: int):
        """Log quota allocation summary"""
        total_traces = sum(info.trace_count for info in quotas.values())
        total_allocated = sum(info.allocated_quota for info in quotas.values())

        logger.info(
            f"Quota allocation: {total_allocated}/{total_traces} traces "
            f"(budget: {batch_budget}, efficiency: {total_allocated / batch_budget * 100:.1f}%)"
        )

        # Log anomalous categories
        anomalous_types = [
            info
            for info in quotas.values()
            if info.health_metrics and info.health_metrics.is_anomalous
        ]

        if anomalous_types:
            logger.debug(f"Anomalous root span types ({len(anomalous_types)}):")
            for info in anomalous_types:
                logger.debug(
                    f"  {info.root_span_name}: weight={info.weight:.2f}, "
                    f"quota={info.allocated_quota}/{info.trace_count}"
                )

    def _apply_global_quota_balancing(
        self, quotas: Dict[str, QuotaInfo], batch_budget: int
    ) -> Dict[str, QuotaInfo]:
        """
        Step 4: Global quota balancing adjustment

        If a root type's proportion is less than the current average sampled,
        then relax its quota a bit more, the relaxation amount is the deviation
        between its already sampled count and the already sampled average.
        """
        # Feature toggle: allow disabling global balancing
        if not getattr(self, "enable_global_balancing", True):
            logger.debug("Global balancing disabled via config")
            return quotas
        if self.total_batches_processed == 0:
            # First batch, no historical data, return as is
            logger.debug("First batch, no global balancing applied")
            return quotas

        # Calculate global average sampled count
        total_global_sampled = sum(self.global_sampled_counts.values())
        unique_types_seen = len(self.global_sampled_counts)

        if unique_types_seen == 0 or total_global_sampled == 0:
            logger.debug("No global sampling history, no balancing applied")
            return quotas

        global_average = total_global_sampled / unique_types_seen

        logger.debug(
            f"Global balancing: total_sampled={total_global_sampled}, "
            f"unique_types={unique_types_seen}, average={global_average:.1f}"
        )

        # Find types that need adjustment (sampled count below global average)
        undersampled_types = []
        adjustment_needed = 0

        for root_name, quota_info in quotas.items():
            current_global_count = self.global_sampled_counts.get(root_name, 0)

            if current_global_count < global_average:
                # Calculate deviation degree
                deficit = global_average - current_global_count
                deficit_ratio = deficit / global_average if global_average > 0 else 0

                # Calculate extra quota based on deviation degree (fixed int truncation)
                # Larger deviation means more extra quota, max 50% of original quota
                extra_quota = int(quota_info.allocated_quota * deficit_ratio * 0.5)
                extra_quota = max(1, extra_quota)  # At least give 1 extra quota

                undersampled_types.append((quota_info, extra_quota, deficit_ratio))
                adjustment_needed += extra_quota

                logger.debug(
                    f"  {root_name}: global_count={current_global_count}, "
                    f"deficit={deficit:.1f}, ratio={deficit_ratio:.2f}, "
                    f"extra_quota={extra_quota}"
                )

        if not undersampled_types:
            logger.debug("No undersampled types found, no adjustment needed")
            return quotas

        # Check if there is enough budget for adjustment
        current_total_quota = sum(info.allocated_quota for info in quotas.values())
        available_budget = batch_budget - current_total_quota

        if available_budget <= 0:
            logger.debug(
                f"No available budget for global balancing (used: {current_total_quota}/{batch_budget})"
            )
            return quotas

        # If needed adjustment exceeds available budget, scale down proportionally
        if adjustment_needed > available_budget:
            scale_factor = available_budget / adjustment_needed
            logger.debug(f"Scaling down adjustments by {scale_factor:.2f}")
            undersampled_types = [
                (quota_info, max(1, int(extra * scale_factor)), deficit_ratio)
                for quota_info, extra, deficit_ratio in undersampled_types
            ]

        # Apply adjustments
        total_adjustment = 0
        for quota_info, extra_quota, deficit_ratio in undersampled_types:
            quota_info.allocated_quota += extra_quota
            total_adjustment += extra_quota

            logger.debug(
                f"Global balancing: {quota_info.root_span_name} "
                f"quota +{extra_quota} -> {quota_info.allocated_quota}"
            )

        logger.debug(
            f"Applied global quota balancing: +{total_adjustment} quota to "
            f"{len(undersampled_types)} undersampled types"
        )

        return quotas

    def _update_global_sampled_counts(self, quotas: Dict[str, QuotaInfo]) -> None:
        """Update global sampled statistics"""
        for root_name, quota_info in quotas.items():
            # Update sampled count (using allocated quota as the number to be sampled)
            self.global_sampled_counts[root_name] += quota_info.allocated_quota

        self.total_batches_processed += 1

        logger.debug(
            f"Updated global counts: {dict(self.global_sampled_counts)}, "
            f"total_batches={self.total_batches_processed}"
        )

    def get_global_sampling_stats(self) -> Dict[str, Any]:
        """Get global sampling statistics"""
        total_sampled = sum(self.global_sampled_counts.values())

        return {
            "total_batches_processed": self.total_batches_processed,
            "total_sampled": total_sampled,
            "unique_types": len(self.global_sampled_counts),
            "average_per_type": total_sampled / len(self.global_sampled_counts)
            if self.global_sampled_counts
            else 0,
            "counts_by_type": dict(self.global_sampled_counts),
        }

    def get_warmup_baselines(self) -> Dict[str, RootSpanHealthMetrics]:
        """Get current warmup baselines"""
        return self.warmup_baselines.copy()

    def _apply_dpp_anomaly_scoring(
        self,
        quotas: Dict[str, QuotaInfo],
        trace_batch: pl.DataFrame,
        input_folder: Optional[str],
    ) -> Dict[str, QuotaInfo]:
        """
        Step 4: Final quota allocation with minimum guarantees

        No DPP anomaly score calculation needed - trace encoder already provides
        per-trace dpp_score for sampling decisions.
        """
        logger.debug("Finalizing quota allocation...")

        # Get the root time of the first trace in current batch for logging
        if trace_batch.is_empty():
            logger.warning("Empty trace batch, returning quotas as-is")
            return quotas

        logger.info(
            "Quota allocation completed - using trace encoder dpp_scores for sampling"
        )

        return quotas

    def _get_first_root_trace_time(self, trace_batch: pl.DataFrame) -> Optional[float]:
        """Get timestamp of first root trace"""
        try:
            # Use new encoding format, directly get time from first row
            if trace_batch.is_empty():
                return None

            first_time = trace_batch.sort("time").select("time").limit(1).item()

            # Convert to timestamp
            if hasattr(first_time, "timestamp"):
                return first_time.timestamp()
            else:
                return float(first_time)

        except Exception as e:
            logger.error(f"Error getting first root trace time: {e}")
            return None

    # Removed _perform_anomaly_detection as metrics-based AD is no longer used

    # Removed _calculate_dpp_anomaly_scores and _calculate_error_performance_anomaly_score
    # These are no longer needed since trace encoder provides per-trace dpp_score
