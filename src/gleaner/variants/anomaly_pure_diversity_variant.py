"""
Anomaly Pure Diversity Variant - Gleaner with pure diversity in anomaly phase

Features:
- Uses traces, logs, and metrics like base Gleaner
- Uses alarm system and quota allocation
- During anomaly phase: uses ONLY diversity (no anomaly score) for DPP selection
- During lookback phase: uses diversity (same as always)
"""

import math
import random
from typing import List

import polars as pl
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.spec import SampleResult

from ..core.sampler import GleanerSampler


class AnomalyPureDiversityVariant(GleanerSampler):
    """
    Gleaner variant that uses pure diversity during anomaly phase

    Features:
    - Uses full alarm system and quota allocation
    - During anomaly phase: DPP selection uses ONLY diversity (no anomaly score)
    - During lookback phase: DPP selection uses diversity (as usual)
    - This makes both phases use the same diversity-only selection strategy
    """

    def _process_encoded_batch(
        self,
        batch_encoded: pl.DataFrame,
        sampling_rate: float,
        input_folder: str,
        performance_thresholds: dict,
    ) -> List[SampleResult]:
        """
        Process a single encoded batch with alarm+quota+DPP pipeline
        but using PURE DIVERSITY (no anomaly score) in DPP selection
        """

        if batch_encoded.is_empty():
            return []

        # Get total traces and calculate budget
        total_traces = len(batch_encoded)
        batch_budget = max(1, math.ceil(total_traces * sampling_rate))

        logger.info(
            f"Processing {total_traces} traces, budget: {batch_budget} (anomaly pure diversity)"
        )

        # Step 1: Use QuotaAllocator with full alarm+quota pipeline
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

                for i in range(len(root_traces)):
                    trace_data = root_traces.row(i, named=True)
                    trace_id = trace_data.get("traceid")
                    if trace_id is None:
                        continue

                    # Extract pattern for DPP
                    pattern = self._make_pattern_from_row(trace_data)
                    trace_patterns.append(pattern)
                    trace_ids.append(trace_id)

                # KEY DIFFERENCE: Use DPP with PURE DIVERSITY (no relevance scores)
                # This is the same as normal phase - diversity only
                try:
                    selected_trace_ids = self.dpp_selector.select_diverse_traces(
                        patterns=trace_patterns,
                        trace_ids=trace_ids,
                        quota=quota,
                        alarm_active=False,  # Pure diversity mode - no alarm weighting
                        relevance_scores=None,  # Pure diversity - no relevance scores
                    )

                    # Create results from DPP selection
                    # Use base anomaly score for reporting (but not for selection)
                    trace_id_to_row = {trace_ids[i]: i for i in range(len(trace_ids))}
                    selected_count = 0

                    for trace_id in selected_trace_ids:
                        row_idx = trace_id_to_row.get(trace_id)
                        if row_idx is not None:
                            trace_data = root_traces.row(row_idx, named=True)
                            base_score = trace_data.get("anomaly_score", 0.0)
                            results.append(
                                SampleResult(
                                    trace_id=str(trace_id), sample_score=float(base_score)
                                )
                            )
                            selected_count += 1

                except Exception as e:
                    logger.warning(
                        f"DPP selection failed for {root_span_name}: {e}, falling back to random selection"
                    )
                    # Fallback: random selection (diversity-preserving)
                    selected_indices = random.sample(
                        range(len(trace_ids)), min(quota, len(trace_ids))
                    )
                    selected_count = 0

                    for idx in selected_indices:
                        trace_data = root_traces.row(idx, named=True)
                        trace_id = trace_data.get("traceid")
                        if trace_id is None:
                            continue
                        base_score = trace_data.get("anomaly_score", 0.0)
                        results.append(
                            SampleResult(
                                trace_id=str(trace_id), sample_score=float(base_score)
                            )
                        )
                        selected_count += 1

                logger.debug(
                    f"Selected {selected_count}/{available_traces} traces for {root_span_name} (pure diversity)"
                )

        except Exception as e:
            logger.error(
                f"Quota allocation failed: {e}, falling back to simple diversity sampling"
            )
            # Fallback: random sampling (diversity-preserving)
            trace_ids = []
            for i in range(len(batch_encoded)):
                trace_data = batch_encoded.row(i, named=True)
                trace_id = trace_data.get("traceid")
                if trace_id is not None:
                    trace_ids.append((i, trace_id))

            # Random sample
            num_to_select = min(batch_budget, len(trace_ids))
            selected = random.sample(trace_ids, num_to_select)

            results = []
            for idx, trace_id in selected:
                trace_data = batch_encoded.row(idx, named=True)
                base_score = trace_data.get("anomaly_score", 0.0)
                results.append(
                    SampleResult(trace_id=str(trace_id), sample_score=float(base_score))
                )

        logger.info(f"Batch processed: {len(results)}/{total_traces} traces (pure diversity)")
        return results
