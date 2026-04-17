"""
Weisfeiler-Lehman Graph Kernel for Graph Similarity

Implements the Weisfeiler-Lehman (WL) subtree kernel for computing similarity
between graph structures. Used as an alternative to Jaccard similarity for
trace pattern comparison in the DPP algorithm.

This module builds graphs directly from raw trace data using string labels:
- Span nodes use span_name (with numerical suffix for duplicates)
- Log nodes use attr.log_template string
"""

from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import polars as pl


def compute_wl_hash(node_label: str, neighbor_labels: List[str]) -> str:
    """
    Compute WL hash for a node based on its label and sorted neighbor labels.

    Args:
        node_label: The label of the current node
        neighbor_labels: Labels of neighboring nodes

    Returns:
        A hash string representing the node's neighborhood structure
    """
    # Sort neighbor labels for deterministic hashing
    sorted_neighbors = sorted(neighbor_labels)
    # Concatenate node label with sorted neighbor labels
    combined = f"{node_label}|{','.join(sorted_neighbors)}"
    return combined


def wl_iteration(
    graph: Dict[str, Set[str]], node_labels: Dict[str, str]
) -> Dict[str, str]:
    """
    Perform one iteration of the Weisfeiler-Lehman algorithm.

    Args:
        graph: Adjacency list representation {node: set of neighbors}
        node_labels: Current labels for each node {node: label}

    Returns:
        Updated node labels after one WL iteration
    """
    new_labels = {}
    for node in graph:
        # Get neighbor labels
        neighbor_labels = [node_labels.get(n, "") for n in graph[node]]
        # Compute new label as hash of current label + neighbor labels
        new_labels[node] = compute_wl_hash(node_labels[node], neighbor_labels)
    return new_labels


def trace_spans_to_graph(
    trace_spans_df: pl.DataFrame,
    trace_logs_df: Optional[pl.DataFrame] = None,
) -> Tuple[Dict[str, Set[str]], Dict[str, str]]:
    """
    Convert raw trace spans and logs to a complete graph representation.

    Builds a graph where:
    - Span nodes use span_name as labels (with numerical suffix for duplicates)
    - Log nodes use attr.log_template string as labels (falls back to attr.template_id
      if log_template is not available, converted to string)
    - Edges follow the trace hierarchy (parent-child relationships)
    - Logs are connected to their associated span

    Note on duplicate handling:
    - For duplicate span names (same span_name, different span_id), numerical
      suffixes are added: service_a, service_a_2, service_a_3, etc.
    - Same logic applies to duplicate log templates within the same trace.

    Args:
        trace_spans_df: DataFrame with trace span data (must have span_id,
            parent_span_id, span_name columns)
        trace_logs_df: Optional DataFrame with log data (should have span_id,
            attr.log_template or attr.template_id columns)

    Returns:
        Tuple of (adjacency_list, node_labels)
        - adjacency_list: {node_id: set of neighbor node_ids}
        - node_labels: {node_id: string label (span_name or log_template)}
    """
    if trace_spans_df.is_empty():
        return {}, {}

    graph: Dict[str, Set[str]] = {}
    node_labels: Dict[str, str] = {}

    # Track span_name occurrences to add numerical suffixes for duplicates
    span_name_counts: Dict[str, int] = defaultdict(int)
    span_id_to_node_id: Dict[str, str] = {}

    # First pass: create nodes for all spans with unique IDs
    for row in trace_spans_df.iter_rows(named=True):
        span_id = row.get("span_id", "")
        span_name = row.get("span_name", "unknown_span")

        if not span_id:
            continue

        # Increment count for this span_name
        span_name_counts[span_name] += 1
        count = span_name_counts[span_name]

        # Create node ID with numerical suffix for duplicates
        if count == 1:
            node_id = f"span_{span_name}"
        else:
            node_id = f"span_{span_name}_{count}"

        span_id_to_node_id[span_id] = node_id
        graph[node_id] = set()
        # Use span_name as the label (with suffix if duplicate)
        node_labels[node_id] = span_name if count == 1 else f"{span_name}_{count}"

    # Second pass: create edges based on parent-child relationships
    for row in trace_spans_df.iter_rows(named=True):
        span_id = row.get("span_id", "")
        parent_span_id = row.get("parent_span_id", "")

        if not span_id:
            continue

        node_id = span_id_to_node_id.get(span_id)
        if not node_id:
            continue

        # Connect to parent if exists
        if parent_span_id and parent_span_id in span_id_to_node_id:
            parent_node_id = span_id_to_node_id[parent_span_id]
            # Add undirected edge
            graph[node_id].add(parent_node_id)
            graph[parent_node_id].add(node_id)

    # Third pass: add log nodes if available
    if trace_logs_df is not None and not trace_logs_df.is_empty():
        log_template_counts: Dict[str, int] = defaultdict(int)

        for row in trace_logs_df.iter_rows(named=True):
            span_id = row.get("span_id", "")
            # Use attr.log_template string instead of template_id
            log_template = row.get("attr.log_template", "")

            if not log_template:
                # Fallback to template_id if log_template not available
                log_template = str(row.get("attr.template_id", "unknown_log"))

            if not log_template:
                continue

            # Create unique node ID for this log
            log_template_counts[log_template] += 1
            count = log_template_counts[log_template]

            if count == 1:
                log_node_id = f"log_{log_template}"
            else:
                log_node_id = f"log_{log_template}_{count}"

            graph[log_node_id] = set()
            # Use log_template string as the label
            node_labels[log_node_id] = (
                log_template if count == 1 else f"{log_template}_{count}"
            )

            # Connect log to its associated span
            if span_id and span_id in span_id_to_node_id:
                span_node_id = span_id_to_node_id[span_id]
                graph[log_node_id].add(span_node_id)
                graph[span_node_id].add(log_node_id)

    return graph, node_labels


def trace_to_graph(
    trace_pattern: Set[Tuple[int, int]]
) -> Tuple[Dict[str, Set[str]], Dict[str, str]]:
    """
    Convert a trace pattern (edge set) to a complete graph representation.

    DEPRECATED: Use trace_spans_to_graph for string-based graph construction.

    The trace pattern contains edges as (source_id, target_id) tuples.
    We build an undirected graph from these edges.

    Args:
        trace_pattern: Set of (source_id, target_id) edge tuples

    Returns:
        Tuple of (adjacency_list, node_labels)
        - adjacency_list: {node_id: set of neighbor node_ids}
        - node_labels: {node_id: initial label}
    """
    if not trace_pattern:
        return {}, {}

    # Build adjacency list (undirected graph from directed edges)
    graph: Dict[str, Set[str]] = {}
    all_nodes: Set[str] = set()

    for src, tgt in trace_pattern:
        src_str = str(src)
        tgt_str = str(tgt)
        all_nodes.add(src_str)
        all_nodes.add(tgt_str)

        # Add edges (undirected)
        if src_str not in graph:
            graph[src_str] = set()
        if tgt_str not in graph:
            graph[tgt_str] = set()

        graph[src_str].add(tgt_str)
        graph[tgt_str].add(src_str)

    # Ensure all nodes are in graph
    for node in all_nodes:
        if node not in graph:
            graph[node] = set()

    # Initial labels are the node IDs themselves
    node_labels = {node: node for node in all_nodes}

    return graph, node_labels


def compute_wl_feature_vector(
    graph: Dict[str, Set[str]],
    node_labels: Dict[str, str],
    num_iterations: int = 3,
) -> Counter:
    """
    Compute WL feature vector for a graph.

    The feature vector is a Counter of all labels seen across all WL iterations.

    Args:
        graph: Adjacency list representation
        node_labels: Initial node labels
        num_iterations: Number of WL iterations (subtree depth)

    Returns:
        Counter of label occurrences across all iterations
    """
    if not graph:
        return Counter()

    feature_vector = Counter()
    current_labels = node_labels.copy()

    # Add initial labels to feature vector
    feature_vector.update(current_labels.values())

    # Perform WL iterations
    for _ in range(num_iterations):
        current_labels = wl_iteration(graph, current_labels)
        feature_vector.update(current_labels.values())

    return feature_vector


def wl_kernel_similarity(
    pattern1: Set[Tuple[int, int]],
    pattern2: Set[Tuple[int, int]],
    num_iterations: int = 3,
) -> float:
    """
    Compute Weisfeiler-Lehman kernel similarity between two trace patterns.

    DEPRECATED: Use wl_kernel_similarity_from_graphs for string-based comparison.

    The WL kernel computes similarity based on shared subtree patterns.

    Args:
        pattern1: First trace pattern (edge set)
        pattern2: Second trace pattern (edge set)
        num_iterations: Number of WL iterations (default: 3)

    Returns:
        Normalized similarity score between 0 and 1
    """
    # Handle empty patterns
    if not pattern1 and not pattern2:
        return 1.0
    if not pattern1 or not pattern2:
        return 0.0

    # Convert patterns to graphs
    graph1, labels1 = trace_to_graph(pattern1)
    graph2, labels2 = trace_to_graph(pattern2)

    # Compute WL feature vectors
    fv1 = compute_wl_feature_vector(graph1, labels1, num_iterations)
    fv2 = compute_wl_feature_vector(graph2, labels2, num_iterations)

    # Compute dot product of feature vectors (kernel value)
    # K(G1, G2) = <φ(G1), φ(G2)>
    common_labels = set(fv1.keys()) & set(fv2.keys())
    kernel_value = sum(fv1[label] * fv2[label] for label in common_labels)

    # Normalize by geometric mean of self-similarities
    # K_norm(G1, G2) = K(G1, G2) / sqrt(K(G1, G1) * K(G2, G2))
    self_sim1 = sum(v * v for v in fv1.values())
    self_sim2 = sum(v * v for v in fv2.values())

    if self_sim1 == 0 or self_sim2 == 0:
        return 0.0

    normalized_similarity = kernel_value / np.sqrt(self_sim1 * self_sim2)

    # Clamp to [0, 1] range
    return float(np.clip(normalized_similarity, 0.0, 1.0))


def wl_kernel_similarity_from_graphs(
    graph1: Dict[str, Set[str]],
    labels1: Dict[str, str],
    graph2: Dict[str, Set[str]],
    labels2: Dict[str, str],
    num_iterations: int = 3,
) -> float:
    """
    Compute WL kernel similarity between two pre-built graphs.

    Args:
        graph1: First graph adjacency list
        labels1: First graph node labels
        graph2: Second graph adjacency list
        labels2: Second graph node labels
        num_iterations: Number of WL iterations

    Returns:
        Normalized similarity score between 0 and 1
    """
    # Handle empty graphs
    if not graph1 and not graph2:
        return 1.0
    if not graph1 or not graph2:
        return 0.0

    # Compute WL feature vectors
    fv1 = compute_wl_feature_vector(graph1, labels1, num_iterations)
    fv2 = compute_wl_feature_vector(graph2, labels2, num_iterations)

    # Compute kernel value
    common_labels = set(fv1.keys()) & set(fv2.keys())
    kernel_value = sum(fv1[label] * fv2[label] for label in common_labels)

    # Normalize
    self_sim1 = sum(v * v for v in fv1.values())
    self_sim2 = sum(v * v for v in fv2.values())

    if self_sim1 == 0 or self_sim2 == 0:
        return 0.0

    normalized_similarity = kernel_value / np.sqrt(self_sim1 * self_sim2)
    return float(np.clip(normalized_similarity, 0.0, 1.0))


def build_wl_similarity_matrix(
    patterns: List[Set[Tuple[int, int]]], num_iterations: int = 3
) -> np.ndarray:
    """
    Build a similarity matrix using WL kernel for a list of patterns.

    DEPRECATED: Use build_wl_similarity_matrix_from_graphs for string-based graphs.

    Args:
        patterns: List of trace patterns (edge sets)
        num_iterations: Number of WL iterations

    Returns:
        Symmetric similarity matrix (n x n)
    """
    n = len(patterns)
    similarity_matrix = np.zeros((n, n))

    # Precompute graphs and WL feature vectors for all patterns
    feature_vectors = []
    self_similarities = []

    for pattern in patterns:
        if not pattern:
            feature_vectors.append(Counter())
            self_similarities.append(0.0)
        else:
            graph, labels = trace_to_graph(pattern)
            fv = compute_wl_feature_vector(graph, labels, num_iterations)
            feature_vectors.append(fv)
            self_similarities.append(sum(v * v for v in fv.values()))

    # Compute pairwise similarities
    for i in range(n):
        for j in range(i, n):
            if i == j:
                similarity_matrix[i, j] = 1.0
            else:
                fv1 = feature_vectors[i]
                fv2 = feature_vectors[j]
                ss1 = self_similarities[i]
                ss2 = self_similarities[j]

                if ss1 == 0 or ss2 == 0:
                    sim = 0.0
                else:
                    common_labels = set(fv1.keys()) & set(fv2.keys())
                    kernel_value = sum(fv1[label] * fv2[label] for label in common_labels)
                    sim = float(np.clip(kernel_value / np.sqrt(ss1 * ss2), 0.0, 1.0))

                similarity_matrix[i, j] = sim
                similarity_matrix[j, i] = sim

    return similarity_matrix


def build_wl_similarity_matrix_from_graphs(
    graphs: List[Tuple[Dict[str, Set[str]], Dict[str, str]]],
    num_iterations: int = 3,
) -> np.ndarray:
    """
    Build a similarity matrix using WL kernel for a list of pre-built graphs.

    This is the preferred method for the WL kernel variant as it works with
    string-based node labels (span_name, log_template).

    Args:
        graphs: List of (graph, node_labels) tuples
        num_iterations: Number of WL iterations

    Returns:
        Symmetric similarity matrix (n x n)
    """
    n = len(graphs)
    similarity_matrix = np.zeros((n, n))

    # Precompute WL feature vectors for all graphs
    feature_vectors: List[Counter[str]] = []
    self_similarities: List[float] = []

    for graph, labels in graphs:
        if not graph:
            feature_vectors.append(Counter())
            self_similarities.append(0.0)
        else:
            fv = compute_wl_feature_vector(graph, labels, num_iterations)
            feature_vectors.append(fv)
            self_similarities.append(sum(v * v for v in fv.values()))

    # Compute pairwise similarities
    for i in range(n):
        for j in range(i, n):
            if i == j:
                similarity_matrix[i, j] = 1.0
            else:
                fv1 = feature_vectors[i]
                fv2 = feature_vectors[j]
                ss1 = self_similarities[i]
                ss2 = self_similarities[j]

                if ss1 == 0 or ss2 == 0:
                    sim = 0.0
                else:
                    common_labels = set(fv1.keys()) & set(fv2.keys())
                    kernel_value = sum(fv1[label] * fv2[label] for label in common_labels)
                    sim = float(np.clip(kernel_value / np.sqrt(ss1 * ss2), 0.0, 1.0))

                similarity_matrix[i, j] = sim
                similarity_matrix[j, i] = sim

    return similarity_matrix


# Export interface
__all__ = [
    "wl_kernel_similarity",
    "wl_kernel_similarity_from_graphs",
    "build_wl_similarity_matrix",
    "build_wl_similarity_matrix_from_graphs",
    "trace_to_graph",
    "trace_spans_to_graph",
    "compute_wl_feature_vector",
]
