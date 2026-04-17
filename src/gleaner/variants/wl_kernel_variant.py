"""
WL Kernel Variant - Gleaner with Weisfeiler-Lehman Graph Kernel similarity

Features:
- Builds complete graph representation directly from raw trace data
- Uses string labels: span_name for spans, attr.log_template for logs
- Handles duplicate span names with numerical suffixes
- Replaces Jaccard similarity with Weisfeiler-Lehman Kernel for DPP phase
- Maintains full alarm + quota + DPP pipeline with WL kernel similarity
"""

import math
import time
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import polars as pl
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import SamplerArgs, SampleResult, SamplingMode

from ..algorithms.fast_dpp import fast_dpp_greedy
from ..algorithms.wl_kernel import (
    build_wl_similarity_matrix_from_graphs,
    trace_spans_to_graph,
)
from ..components.dataloader import load_data
from ..core.sampler import GleanerSampler


class WLKernelDPPSelector:
    """
    DPP selector using Weisfeiler-Lehman Kernel for similarity computation

    This replaces the Jaccard similarity in the standard DPP selector with
    WL kernel similarity for graph-based trace comparison.
    Uses string-based node labels (span_name, log_template).
    """

    def __init__(self, epsilon: float = 1e-8, wl_iterations: int = 3):
        """
        Initialize WL Kernel DPP selector

        Args:
            epsilon: Convergence threshold for DPP algorithm
            wl_iterations: Number of WL iterations for kernel computation
        """
        self.epsilon = epsilon
        self.wl_iterations = wl_iterations

    def select_diverse_traces(
        self,
        graphs: List[Tuple[Dict[str, Set[str]], Dict[str, str]]],
        trace_ids: List[str],
        quota: int,
        alarm_active: bool = False,
        relevance_scores: Optional[List[float]] = None,
    ) -> List[str]:
        """
        Select diverse traces using DPP with WL Kernel similarity

        Args:
            graphs: List of (graph, node_labels) tuples for each trace
            trace_ids: List of trace IDs corresponding to graphs
            quota: Number of traces to select
            alarm_active: Whether alarm mode is active
            relevance_scores: Optional relevance scores for alarm mode

        Returns:
            List of selected trace IDs
        """
        if not graphs or quota <= 0:
            return []

        if len(graphs) <= quota:
            return trace_ids[: len(graphs)]

        # Build similarity matrix using WL Kernel with string-based graphs
        similarity_matrix = build_wl_similarity_matrix_from_graphs(
            graphs, num_iterations=self.wl_iterations
        )

        # Build kernel matrix based on mode
        if alarm_active and relevance_scores is not None:
            # Alarm mode: L_ij = r_i * r_j * S_ij
            relevance_array = np.array(relevance_scores)
            kernel_matrix = (
                np.outer(relevance_array, relevance_array) * similarity_matrix
            )
        else:
            # Normal mode: L_ij = S_ij (diversity only)
            kernel_matrix = similarity_matrix

        # Ensure positive semi-definiteness
        kernel_matrix = np.maximum(kernel_matrix, 0)

        # Run Fast DPP
        selected_indices = fast_dpp_greedy(kernel_matrix, quota, self.epsilon)

        # If early-stopped and underfilled, perform gap filling
        if len(selected_indices) < quota:
            extra_needed = quota - len(selected_indices)
            remaining = [i for i in range(len(trace_ids)) if i not in selected_indices]
            if remaining:
                logger.debug(f"WL-DPP: performing gap fill for {extra_needed} traces")
                fill = self._minsim_gap_fill(
                    similarity_matrix, selected_indices, remaining, extra_needed
                )
                selected_indices.extend(fill)

        # Return selected trace IDs
        selected_trace_ids = [
            trace_ids[i] for i in selected_indices if i < len(trace_ids)
        ]

        logger.debug(
            f"WL-DPP selected {len(selected_trace_ids)}/{len(graphs)} traces "
            f"(quota: {quota}, alarm_active: {alarm_active})"
        )

        return selected_trace_ids

    def _minsim_gap_fill(
        self,
        similarity_matrix: np.ndarray,
        selected: List[int],
        candidates: List[int],
        k: int,
    ) -> List[int]:
        """Greedy fill: iteratively pick candidate minimizing max similarity to current selection."""
        chosen: List[int] = []
        sel = list(selected)
        cand = list(candidates)
        while k > 0 and cand:
            best_i = None
            best_score = float("inf")
            for idx in cand:
                if sel:
                    max_sim = float(np.max(similarity_matrix[idx, sel]))
                else:
                    max_sim = 0.0
                if max_sim < best_score:
                    best_score = max_sim
                    best_i = idx
            if best_i is None:
                break
            chosen.append(best_i)
            sel.append(best_i)
            cand.remove(best_i)
            k -= 1
        return chosen


class WLKernelVariant(GleanerSampler):
    """
    Gleaner variant using Weisfeiler-Lehman Kernel for graph similarity in DPP

    Features:
    - Builds complete graph representation directly from raw trace data
    - Uses string labels for nodes (span_name, attr.log_template)
    - Handles duplicate span names with numerical suffixes
    - Replaces Jaccard similarity with WL Kernel similarity
    - Maintains full alarm + quota + DPP pipeline structure
    """

    def __init__(self, *args, **kwargs):
        """Initialize WL Kernel variant with WL-based DPP selector"""
        super().__init__(*args, **kwargs)
        # Replace the standard DPP selector with WL kernel version
        self.wl_dpp_selector = WLKernelDPPSelector(
            epsilon=self.config.dpp_epsilon, wl_iterations=3
        )

    def __call__(self, args: SamplerArgs) -> List[SampleResult]:
        """Execute variant with WL Kernel similarity"""
        logger.info(
            f"=== Gleaner WL-Kernel Variant: {args.dataset}/{args.datapack} ==="
        )
        logger.info(f"Mode: {args.mode}, Target rate: {args.sampling_rate}")

        start_time = time.time()

        # Load all data types
        logger.info("Loading data (WL kernel variant)...")
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

        # Store raw traces and logs for graph building
        self._raw_traces_df = traces_df
        self._raw_logs_df = logs_df

        # Build trace_id to spans/logs index for efficient lookup
        self._traces_by_trace_id = {}
        for partition in traces_df.partition_by("trace_id", maintain_order=True):
            if not partition.is_empty():
                tid = partition.get_column("trace_id")[0]
                self._traces_by_trace_id[tid] = partition

        self._logs_by_trace_id = {}
        if logs_df is not None and not logs_df.is_empty():
            for partition in logs_df.partition_by("trace_id", maintain_order=True):
                if not partition.is_empty():
                    tid = partition.get_column("trace_id")[0]
                    self._logs_by_trace_id[tid] = partition

        # Time-based data splitting for lookback
        logger.info("Splitting data into lookback and alarm periods...")
        lookback_traces, alarm_traces, lookback_end_time = (
            self._split_lookback_alarm_data(traces_df)
        )

        logger.info(
            f"Lookback: {len(lookback_traces)} spans, Alarm: {len(alarm_traces)} spans"
        )

        # Encode ALL traces at once (with logs) - still needed for quota allocation and scoring
        from ..components.trace_encoder import encode_all_traces_batch

        logger.info("Encoding all traces for quota allocation and scoring...")
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
            f"WL-Kernel budget allocation - Warmup: {lookback_budget}, Processing: {alarm_budget}"
        )

        # Build lookback baselines
        logger.info("Building lookback baselines...")
        self.quota_allocator.build_lookback_baselines(
            lookback_encoded, performance_thresholds
        )
        self.alarm_system.set_warmup_end_time(lookback_end_time)

        # Process traces with WL Kernel DPP
        all_results = []

        # Process lookback data with WL kernel DPP
        if not lookback_encoded.is_empty():
            lookback_sampling_rate = lookback_budget / len(lookback_encoded)
            lookback_sampling_rate = min(1.0, lookback_sampling_rate)

            lookback_results = self._process_wl_batch(
                lookback_encoded,
                lookback_sampling_rate,
                str(args.input_folder),
                performance_thresholds,
                is_warmup=True,
            )
            if args.mode == SamplingMode.OFFLINE:
                self.total_sampled_count += len(lookback_results)
                self.batch_results_history.append(lookback_results.copy())
            all_results.extend(lookback_results)

        # Process alarm data with WL kernel DPP
        if not alarm_encoded.is_empty():
            alarm_sampling_rate = alarm_budget / len(alarm_encoded)
            alarm_sampling_rate = min(1.0, alarm_sampling_rate)

            total_alarm_traces = len(alarm_encoded)
            total_batches = (
                total_alarm_traces + self.config.batch_size - 1
            ) // self.config.batch_size

            for batch_idx in range(total_batches):
                if args.mode == SamplingMode.OFFLINE and self._is_budget_exhausted():
                    logger.warning(f"Budget exhausted after batch {batch_idx}")
                    break

                start_idx = batch_idx * self.config.batch_size
                end_idx = min(start_idx + self.config.batch_size, total_alarm_traces)

                batch_encoded = alarm_encoded[start_idx:end_idx]

                logger.info(
                    f"WL-Kernel batch {batch_idx + 1}/{total_batches}: {len(batch_encoded)} traces"
                )

                batch_results = self._process_wl_batch(
                    batch_encoded,
                    alarm_sampling_rate,
                    str(args.input_folder),
                    performance_thresholds,
                    is_warmup=False,
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

        # Clean up cached data
        self._raw_traces_df = None
        self._raw_logs_df = None
        self._traces_by_trace_id = {}
        self._logs_by_trace_id = {}

        total_time = time.time() - start_time
        logger.info(
            f"WL-Kernel variant complete: {len(final_results)}/{len(traces_df)} traces "
            f"(rate: {len(final_results) / len(traces_df):.3f}, time: {total_time:.2f}s)"
        )

        return final_results

    def _build_graph_for_trace(
        self, trace_id: str
    ) -> Tuple[Dict[str, Set[str]], Dict[str, str]]:
        """
        Build a graph from raw trace spans and logs for a single trace.

        Uses string labels: span_name for spans, attr.log_template for logs.
        Handles duplicate span names with numerical suffixes.
        """
        trace_spans = self._traces_by_trace_id.get(trace_id)
        trace_logs = self._logs_by_trace_id.get(trace_id)

        if trace_spans is None or trace_spans.is_empty():
            return {}, {}

        return trace_spans_to_graph(trace_spans, trace_logs)

    def _process_wl_batch(
        self,
        batch_encoded: pl.DataFrame,
        sampling_rate: float,
        input_folder: str,
        performance_thresholds: dict,
        is_warmup: bool = False,
    ) -> List[SampleResult]:
        """
        Process a batch using WL Kernel DPP for diversity selection.

        Builds graphs from raw trace data using string labels (span_name, log_template).
        """
        if batch_encoded.is_empty():
            return []

        total_traces = len(batch_encoded)
        batch_budget = max(1, math.ceil(total_traces * sampling_rate))

        logger.info(
            f"WL-Kernel processing {total_traces} traces, budget: {batch_budget}"
        )

        # Step 1: Allocate quotas by root span type
        try:
            quotas = self.quota_allocator.allocate_quotas(
                trace_batch=batch_encoded,
                batch_budget=batch_budget,
                input_folder=input_folder if not is_warmup else None,
            )

            logger.info(f"Quota allocation completed for {len(quotas)} root span types")

        except Exception as e:
            logger.error(f"Quota allocation failed: {e}, falling back to global WL-DPP")
            return self._process_wl_global(batch_encoded, batch_budget, is_warmup)

        # Step 2: Select traces using WL Kernel DPP within each quota group
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

            # Build graphs and collect trace IDs for WL-DPP selection
            trace_graphs: List[Tuple[Dict[str, Set[str]], Dict[str, str]]] = []
            trace_ids: List[str] = []
            relevance_scores: List[float] = []

            for row in root_traces.iter_rows(named=True):
                trace_id = row.get("traceid")
                if trace_id is None:
                    continue

                # Build graph from raw trace data
                graph, labels = self._build_graph_for_trace(trace_id)
                trace_graphs.append((graph, labels))
                trace_ids.append(trace_id)

                # Calculate relevance score
                base_score = row.get("anomaly_score", 0.0)
                dpp_score_val = row.get("dpp_score", None)

                if dpp_score_val is not None:
                    final_score = base_score + float(dpp_score_val or 0.0)
                else:
                    error_boost = 5.0 if row.get("root_is_error", False) else 0.0
                    duration_boost = 0.0
                    root_duration = row.get("root_duration_ms", 0.0)
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

            # Use WL Kernel DPP selector with graphs
            try:
                selected_trace_ids = self.wl_dpp_selector.select_diverse_traces(
                    graphs=trace_graphs,
                    trace_ids=trace_ids,
                    quota=quota,
                    alarm_active=not is_warmup,  # Use alarm in processing mode
                    relevance_scores=relevance_scores if not is_warmup else None,
                )

                # Create results from selection
                trace_id_to_score = {
                    trace_ids[i]: relevance_scores[i] for i in range(len(trace_ids))
                }

                for trace_id in selected_trace_ids:
                    score = trace_id_to_score.get(trace_id, 0.0)
                    results.append(
                        SampleResult(trace_id=str(trace_id), sample_score=float(score))
                    )

            except Exception as e:
                logger.warning(
                    f"WL-DPP selection failed for {root_span_name}: {e}, falling back to top-k"
                )
                # Fallback: top-k selection by relevance score
                trace_scores = [
                    (trace_ids[i], relevance_scores[i]) for i in range(len(trace_ids))
                ]
                trace_scores.sort(key=lambda x: x[1], reverse=True)
                selected_traces = trace_scores[:quota]

                for trace_id, score in selected_traces:
                    results.append(
                        SampleResult(trace_id=str(trace_id), sample_score=float(score))
                    )

            logger.debug(
                f"WL-Kernel: Selected {len([r for r in results if r.trace_id in [str(tid) for tid in trace_ids]])}"
                f"/{available_traces} traces for {root_span_name}"
            )

        logger.info(f"WL-Kernel batch processed: {len(results)}/{total_traces} traces")
        return results

    def _process_wl_global(
        self, batch_encoded: pl.DataFrame, budget: int, is_warmup: bool
    ) -> List[SampleResult]:
        """Fallback: apply WL-DPP globally without quota grouping"""
        if batch_encoded.is_empty():
            return []

        trace_graphs: List[Tuple[Dict[str, Set[str]], Dict[str, str]]] = []
        trace_ids: List[str] = []
        relevance_scores: List[float] = []

        for row in batch_encoded.iter_rows(named=True):
            trace_id = row.get("traceid")
            if trace_id is None:
                continue

            # Build graph from raw trace data
            graph, labels = self._build_graph_for_trace(trace_id)
            trace_graphs.append((graph, labels))
            trace_ids.append(trace_id)
            relevance_scores.append(float(row.get("dpp_score", 0.0) or 0.0))

        try:
            selected_trace_ids = self.wl_dpp_selector.select_diverse_traces(
                graphs=trace_graphs,
                trace_ids=trace_ids,
                quota=budget,
                alarm_active=not is_warmup,
                relevance_scores=relevance_scores if not is_warmup else None,
            )

            trace_id_to_score = {
                trace_ids[i]: relevance_scores[i] for i in range(len(trace_ids))
            }

            results = []
            for trace_id in selected_trace_ids:
                score = trace_id_to_score.get(trace_id, 0.0)
                results.append(
                    SampleResult(trace_id=str(trace_id), sample_score=float(score))
                )

            return results

        except Exception as e:
            logger.warning(f"Global WL-DPP failed: {e}, falling back to top-k")
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
