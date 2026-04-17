"""
Fast DPP (Determinantal Point Process) Implementation for Gleaner V2

Based on the fast greedy MAP inference algorithm with incremental Cholesky updates.
Supports both relevance+diversity mode and diversity-only mode.
"""

import math
from functools import lru_cache
from typing import List, Optional, Set, Tuple

import numpy as np
from rcabench_platform.v2.logging import logger


def jaccard_similarity(set1: Set[Tuple[int, int]], set2: Set[Tuple[int, int]]) -> float:
    """
    Calculate Jaccard similarity between two edge sets (trace patterns)

    Args:
        set1: First edge set (trace pattern)
        set2: Second edge set (trace pattern)

    Returns:
        Jaccard similarity score between 0 and 1
    """
    if not set1 and not set2:
        return 1.0

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0


# --- LRU-cached pairwise similarity to speed up repeated computations ---
def _pattern_key(pattern: Set[Tuple[int, int]]) -> Tuple[Tuple[int, int], ...]:
    """Canonical, hashable key for a pattern (sorted tuple of edges)."""
    if not pattern:
        return tuple()
    # Edges are (int, int); sort for determinism
    try:
        return tuple(sorted(pattern))
    except TypeError:
        # In case elements are lists, convert to 2-tuples defensively
        converted: Tuple[Tuple[int, int], ...] = tuple(
            (int(e[0]), int(e[1]))
            for e in pattern
            if isinstance(e, (list, tuple)) and len(e) == 2
        )
        return tuple(sorted(converted))


@lru_cache(maxsize=200_000)
def _jaccard_similarity_keyed(
    k1: Tuple[Tuple[int, int], ...], k2: Tuple[Tuple[int, int], ...]
) -> float:
    """LRU-cached Jaccard similarity for two canonical pattern keys.

    Keys are tuples of edges; convert to frozensets once per unique key.
    """
    if not k1 and not k2:
        return 1.0
    s1 = frozenset(k1)
    s2 = frozenset(k2)
    if not s1 and not s2:
        return 1.0
    inter = len(s1.intersection(s2))
    uni = len(s1.union(s2))
    return inter / uni if uni > 0 else 0.0


def build_similarity_matrix(patterns: List[Set[Tuple[int, int]]]) -> np.ndarray:
    """
    Build similarity matrix from trace patterns using Jaccard similarity

    Args:
        patterns: List of trace patterns (edge sets)

    Returns:
        Symmetric similarity matrix
    """
    n = len(patterns)
    similarity_matrix = np.zeros((n, n))

    # Precompute canonical keys once per pattern
    keys = [_pattern_key(p) for p in patterns]

    for i in range(n):
        ki = keys[i]
        for j in range(i, n):
            kj = keys[j]
            sim = _jaccard_similarity_keyed(ki, kj)
            similarity_matrix[i, j] = sim
            similarity_matrix[j, i] = sim

    return similarity_matrix


def fast_dpp_greedy(
    kernel_matrix: np.ndarray, max_length: int, epsilon: float = 1e-8
) -> List[int]:
    """
    Fast DPP greedy MAP inference algorithm

    Based on the original dpp() function but with enhanced error handling and logging.

    Args:
        kernel_matrix: Positive semi-definite kernel matrix
        max_length: Maximum number of items to select
        epsilon: Convergence threshold

    Returns:
        List of selected item indices
    """
    if kernel_matrix.shape[0] == 0:
        return []

    if max_length <= 0:
        return []

    if max_length >= kernel_matrix.shape[0]:
        return list(range(kernel_matrix.shape[0]))

    item_size = kernel_matrix.shape[0]
    cis = np.zeros((max_length, item_size))
    di2s = np.copy(np.diag(kernel_matrix))

    # Ensure numerical stability - clip very small diagonal values
    di2s = np.maximum(di2s, epsilon)

    selected_items = list()

    # Select first item with highest diagonal value
    selected_item = np.argmax(di2s)
    selected_items.append(selected_item)

    while len(selected_items) < max_length:
        k = len(selected_items) - 1
        ci_optimal = cis[:k, selected_item]

        # Check for numerical stability to avoid division by zero
        di2_val = di2s[selected_item]
        if di2_val <= epsilon:
            logger.debug(
                f"DPP converged early after {len(selected_items)} selections (di2={di2_val})"
            )
            break

        di_optimal = math.sqrt(di2_val)

        # Additional safety check for very small denominators
        if di_optimal < epsilon:
            logger.debug(
                f"DPP converged early after {len(selected_items)} selections (di_optimal={di_optimal})"
            )
            break

        elements = kernel_matrix[selected_item, :]
        eis = (elements - np.dot(ci_optimal, cis[:k, :])) / di_optimal
        cis[k, :] = eis
        di2s -= np.square(eis)
        di2s[selected_item] = -np.inf
        selected_item = np.argmax(di2s)

        if di2s[selected_item] < epsilon:
            logger.debug(f"DPP converged early after {len(selected_items)} selections")
            break

        selected_items.append(selected_item)

    return selected_items


class DPPSelector:
    """
    DPP-based diverse trace selection with support for both alarm and normal modes
    """

    def __init__(self, epsilon: float = 1e-8):
        """
        Initialize DPP selector

        Args:
            epsilon: Convergence threshold for DPP algorithm
        """
        self.epsilon = epsilon

    @staticmethod
    def clear_caches() -> None:
        """Clear LRU caches used in DPP computations (for tests or memory control)."""
        _jaccard_similarity_keyed.cache_clear()

    @staticmethod
    def get_cache_info() -> dict:
        """Return LRU cache metrics for pairwise similarity computations."""
        info = _jaccard_similarity_keyed.cache_info()
        # CacheInfo(hits, misses, maxsize, currsize)
        return {
            "hits": info.hits,
            "misses": info.misses,
            "maxsize": info.maxsize,
            "currsize": info.currsize,
        }

    def select_diverse_traces(
        self,
        patterns: List[Set[Tuple[int, int]]],
        trace_ids: List[str],
        quota: int,
        alarm_active: bool = False,
        relevance_scores: Optional[List[float]] = None,
    ) -> List[str]:
        """
        Select diverse traces using DPP algorithm

        Args:
            patterns: List of trace patterns (edge sets)
            trace_ids: List of trace IDs corresponding to patterns
            quota: Number of traces to select
            alarm_active: Whether alarm mode is active
            relevance_scores: Optional relevance scores for alarm mode

        Returns:
            List of selected trace IDs
        """
        if not patterns or quota <= 0:
            return []

        if len(patterns) <= quota:
            return trace_ids[: len(patterns)]

        # Build similarity matrix
        similarity_matrix = build_similarity_matrix(patterns)

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

        # If early-stopped and underfilled, perform class-in gap filling using similarity matrix
        if len(selected_indices) < quota:
            extra_needed = quota - len(selected_indices)
            remaining = [i for i in range(len(trace_ids)) if i not in selected_indices]
            if remaining:
                logger.debug(f"remaining{remaining} perform gap fill")
                fill = self._minsim_gap_fill(
                    similarity_matrix, selected_indices, remaining, extra_needed
                )
                selected_indices.extend(fill)

        # Return selected trace IDs
        selected_trace_ids = [
            trace_ids[i] for i in selected_indices if i < len(trace_ids)
        ]

        logger.debug(
            f"DPP selected {len(selected_trace_ids)}/{len(patterns)} traces "
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
                    # max similarity to any selected item
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
