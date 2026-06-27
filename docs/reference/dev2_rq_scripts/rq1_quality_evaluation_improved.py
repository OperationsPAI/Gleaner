#!/usr/bin/env python3
"""
RQ1: Quality Evaluation - Generate comprehensive quality assessment figures for all sampling algorithms.
Improved version with better color distinction between algorithms.

This script evaluates sampling quality across three dimensions:
1. Coverage: API coverage, path dedup coverage, event pair coverage, unique trace coverage
2. Diversity: Shannon entropy and intra-sample dissimilarity
3. Anomaly Detection: proportion rare, proportion anomaly, avg sampled anomaly score

All evaluations use offline mode data across all sampling rates.
Figures are optimized for single-column paper format.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl


def load_and_filter_data(parquet_path: str):
    """Load aggregated performance data and filter for offline mode only."""
    df = pl.read_parquet(parquet_path)

    # Filter for offline mode only
    offline_df = (
        df.filter(pl.col("mode") == "offline")
        .filter(
            pl.col("sampler").is_in(
                [
                    "gleaner",
                    "tracepicker",
                    "trastrainer",
                    "trastrainer_no_metrics",
                    "sifter",
                    "sieve",
                    "random",
                ]
            )
        )
        .filter(pl.col("sampling_rate") != 0.005)
    )

    print("Available columns:")
    print(offline_df.columns)

    print(f"\nData shape: {offline_df.shape}")
    print(f"\nSamplers: {offline_df['sampler'].unique().to_list()}")
    print(f"Sampling rates: {sorted(offline_df['sampling_rate'].unique().to_list())}")

    return offline_df


def get_algorithm_display_names():
    """Get display names for algorithms with proper formatting."""
    display_names = {
        # Main algorithms
        "gleaner": "Gleaner",
        "tracepicker": "TracePicker",
        "trastrainer": "TrasTrainer",
        "trastrainer_no_metrics": "TrasTrainer w/o Metrics",
        "sifter": "Sifter",
        "sieve": "Sieve",
        "random": "Random",
        # Gleaner variants
        "gleaner_no_logs": "Gleaner w/o Logs",
        "gleaner_no_ad": "Gleaner w/o AD",
        "gleaner_no_logs_no_ad": "Gleaner w/o Logs w/o AD",
        "gleaner_pure_diversity": "Gleaner Pure Diversity",
        "gleaner_small_batch": "Gleaner Small Batch",
        "gleaner_medium_batch": "Gleaner Medium Batch",
        "gleaner_unlimited_batch": "Gleaner Unlimited Batch",
    }
    return display_names


def get_algorithm_color_scheme():
    """Get a comprehensive color scheme for all algorithms with improved distinction."""
    # Optimized color scheme: main algorithms first with high contrast, then gleaner variants
    algorithm_colors = {
        # Main algorithms - highly distinct colors for maximum separation
        "gleaner": "#1f77b4",  # Strong blue (base gleaner)
        "tracepicker": "#2ca02c",  # Orange
        "trastrainer": "#d62728",  # Green
        "trastrainer_no_metrics": "#ff7f0e",  # Red
        "sifter": "#9467bd",  # Purple - distinct from all above
        "sieve": "#8c564b",  # Brown - earth tone contrast
        "random": "#000000",  # Black - maximum contrast baseline
        # Gleaner variants - variations of blue family for consistency
        "gleaner_no_logs": "#4292c6",  # Medium blue (lighter than base)
        "gleaner_no_ad": "#6baed6",  # Light blue
        "gleaner_no_logs_no_ad": "#9ecae1",  # Very light blue
        "gleaner_pure_diversity": "#08519c",  # Dark blue (darker than base)
        "gleaner_small_batch": "#2171b5",  # Blue-navy (between base and dark)
        "gleaner_medium_batch": "#08306b",  # Navy blue (darkest)
        "gleaner_unlimited_batch": "#c6dbef",  # Pale blue (lightest)
    }
    return algorithm_colors


def get_line_styles():
    """Get distinct line styles for better differentiation."""
    line_styles = {
        # Main algorithms - solid lines
        "gleaner": "-",
        "tracepicker": "-",
        "trastrainer": "-",
        "trastrainer_no_metrics": "-",
        "sifter": "-",
        "sieve": "-",
        "random": "-",
        # Gleaner variants - different line styles for additional distinction
        "gleaner_no_logs": "--",
        "gleaner_no_ad": ":",
        "gleaner_no_logs_no_ad": "-.",
        "gleaner_pure_diversity": "--",
        "gleaner_small_batch": ":",
        "gleaner_medium_batch": "-.",
        "gleaner_unlimited_batch": "--",
    }
    return line_styles


def setup_axis_formatting(ax, sampling_rates, y_label="Value", y_max=None):
    """Set up proper axis formatting with evenly spaced sampling rates."""
    # Convert sampling rates to percentages and sort
    rate_percentages = sorted([rate * 100 for rate in sampling_rates])

    # Use evenly spaced positions instead of actual values
    x_positions = range(len(rate_percentages))

    # Set x-axis ticks to evenly spaced positions
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f"{rate:.1f}%" for rate in rate_percentages], fontsize=9)

    # Set reasonable axis limits
    ax.set_xlim(-0.2, len(rate_percentages) - 0.8)

    if y_max is None:
        # Auto-determine y_max based on data, with some padding
        y_max = 1.05
    ax.set_ylim(0, y_max)

    # Labels
    ax.set_xlabel("Sampling Rate (%)", fontsize=10)
    ax.set_ylabel(y_label, fontsize=10)

    # Improve grid
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)


def plot_coverage_quality(df: pl.DataFrame, output_dir: str = "plots"):
    """Plot RQ1 Section 1: Coverage Quality Assessment."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    color_scheme = get_algorithm_color_scheme()
    line_styles = get_line_styles()
    display_names = get_algorithm_display_names()

    # Coverage metrics for RQ1
    coverage_metrics = [
        ("avg_api_coverage", "API Coverage"),
        ("avg_path_coverage_dedup", "Path Coverage"),
        ("avg_event_coverage", "Event Coverage"),
        ("avg_unique_trace_coverage", "Unique Trace Coverage"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in coverage_metrics if col in df_pd.columns
    ]

    print("\nRQ1 Section 1: Coverage Quality")
    print(f"Available coverage metrics: {len(available_metrics)}")
    for col, name in available_metrics:
        print(f"  - {name} ({col})")

    # Set up figure - 1x4 layout for single column paper
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))

    plt.style.use("seaborn-v0_8-whitegrid")

    # Create mapping from sampling rate to evenly spaced positions
    rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

    for idx, (metric_col, metric_name) in enumerate(available_metrics):
        if idx >= len(axes):
            break

        ax = axes[idx]

        # Sort samplers for consistent ordering: non-gleaner algorithms first, then gleaner series last (on top)
        all_samplers = df_pd["sampler"].unique()
        non_gleaner_algorithms = [
            s for s in all_samplers if not s.startswith("gleaner")
        ]
        gleaner_algorithms = [s for s in all_samplers if s.startswith("gleaner")]
        # Sort gleaner algorithms with base 'gleaner' first, then variants
        gleaner_sorted = ["gleaner"] + [
            s for s in sorted(gleaner_algorithms) if s != "gleaner"
        ]
        sorted_samplers = non_gleaner_algorithms + gleaner_sorted

        for sampler in sorted_samplers:
            sampler_data = df_pd[df_pd["sampler"] == sampler].sort_values(
                "sampling_rate"
            )

            if len(sampler_data) > 0:
                color = color_scheme.get(sampler, "#333333")
                linestyle = line_styles.get(sampler, "-")
                display_name = display_names.get(sampler, sampler)

                # Updated line width and marker size
                line_width = 2.0
                marker_size = 6  # Increased from 4 to 6

                if sampler in ["gleaner", "tracepicker", "random"]:
                    alpha = 1.0
                    marker = "o"
                elif sampler.startswith("gleaner"):
                    alpha = 0.9
                    marker = "s"
                else:
                    alpha = 1.0
                    marker = "^"

                # Plot with evenly spaced x positions
                x_positions = [
                    rate_positions[rate] for rate in sampler_data["sampling_rate"]
                ]
                ax.plot(
                    x_positions,
                    sampler_data[metric_col],
                    marker=marker,
                    linewidth=line_width,
                    markersize=marker_size,
                    label=display_name,
                    color=color,
                    alpha=alpha,
                    linestyle=linestyle,
                    markerfacecolor=color,
                    markeredgecolor="white",
                    markeredgewidth=1.0,
                )

        # Formatting
        ax.set_title(metric_name, fontsize=11, fontweight="bold", pad=8)

        # Auto-scale y-axis based on actual data range
        data_max = df_pd[metric_col].max()
        if data_max <= 0.5:  # For low-value metrics, use tighter scaling
            y_max = min(1.05, data_max * 1.2)  # 20% padding, but max 1.05
        else:
            y_max = 1.05  # Standard scaling for coverage metrics

        setup_axis_formatting(ax, sampling_rates, "Coverage", y_max)

    # Add horizontal legend above the plots, centered
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.95),
        ncol=len(labels),
        fontsize=8,
        frameon=True,
        fancybox=True,
        shadow=True,
    )

    # Hide unused subplots
    for idx in range(len(available_metrics), len(axes)):
        axes[idx].remove()

    # plt.suptitle(
    #    "RQ1: Coverage Quality Assessment", fontsize=14, fontweight="bold", y=0.85
    # )
    plt.tight_layout()
    plt.subplots_adjust(top=0.75)  # Make room for legend above

    # Save high-quality figures
    plt.savefig(
        f"{output_dir}/rq1_coverage_quality_improved.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/rq1_coverage_quality_improved.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"Coverage quality assessment saved to {output_dir}/rq1_coverage_quality_improved.png and .pdf"
    )
    plt.close()


def plot_diversity_quality(df: pl.DataFrame, output_dir: str = "plots"):
    """Plot RQ1 Section 2: Diversity Quality Assessment."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    color_scheme = get_algorithm_color_scheme()
    line_styles = get_line_styles()
    display_names = get_algorithm_display_names()
    # Diversity metrics for RQ1 - removed intra_sample_dissimilarity
    diversity_metrics = [
        ("avg_shannon_entropy", "Shannon Entropy"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in diversity_metrics if col in df_pd.columns
    ]

    print("\nRQ1 Section 2: Diversity Quality")
    print(f"Available diversity metrics: {len(available_metrics)}")
    for col, name in available_metrics:
        print(f"  - {name} ({col})")

    if len(available_metrics) == 0:
        print("No diversity metrics available!")
        return

    # Set up figure - horizontal layout for diversity metrics
    fig, axes = plt.subplots(
        1, len(available_metrics), figsize=(8 * len(available_metrics), 4)
    )
    if len(available_metrics) == 1:
        axes = [axes]

    plt.style.use("seaborn-v0_8-whitegrid")

    # Create mapping from sampling rate to evenly spaced positions
    rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

    for idx, (metric_col, metric_name) in enumerate(available_metrics):
        ax = axes[idx]

        # Sort samplers for consistent ordering: non-gleaner algorithms first, then gleaner series last (on top)
        all_samplers = df_pd["sampler"].unique()
        non_gleaner_algorithms = [
            s for s in all_samplers if not s.startswith("gleaner")
        ]
        gleaner_algorithms = [s for s in all_samplers if s.startswith("gleaner")]
        # Sort gleaner algorithms with base 'gleaner' first, then variants
        gleaner_sorted = ["gleaner"] + [
            s for s in sorted(gleaner_algorithms) if s != "gleaner"
        ]
        sorted_samplers = non_gleaner_algorithms + gleaner_sorted

        for sampler in sorted_samplers:
            sampler_data = df_pd[df_pd["sampler"] == sampler].sort_values(
                "sampling_rate"
            )

            if len(sampler_data) > 0:
                color = color_scheme.get(sampler, "#333333")
                linestyle = line_styles.get(sampler, "-")
                display_name = display_names.get(sampler, sampler)

                # Updated line width and marker size
                line_width = 2.0
                marker_size = 6  # Increased from 4 to 6

                if sampler in ["gleaner", "tracepicker", "random"]:
                    alpha = 1.0
                    marker = "o"
                elif sampler.startswith("gleaner"):
                    alpha = 0.9
                    marker = "s"
                else:
                    alpha = 1.0
                    marker = "^"

                # Plot with evenly spaced x positions
                x_positions = [
                    rate_positions[rate] for rate in sampler_data["sampling_rate"]
                ]
                ax.plot(
                    x_positions,
                    sampler_data[metric_col],
                    marker=marker,
                    linewidth=line_width,
                    markersize=marker_size,
                    label=display_name,
                    color=color,
                    alpha=alpha,
                    linestyle=linestyle,
                    markerfacecolor=color,
                    markeredgecolor="white",
                    markeredgewidth=1.0,
                )

        # Formatting
        ax.set_title(metric_name, fontsize=11, fontweight="bold", pad=8)

        # Auto-scale y-axis for diversity metrics with better scaling
        data_max = df_pd[metric_col].max()
        if data_max > 0:
            if data_max <= 0.5:  # For low-value metrics
                y_max = data_max * 1.2  # 20% padding
            else:
                y_max = data_max * 1.1  # 10% padding for higher values
        else:
            y_max = 1.0

        setup_axis_formatting(ax, sampling_rates, "Score", y_max)

    # Add horizontal legend above the plots, centered
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.95),
        ncol=len(labels),
        fontsize=8,
        frameon=True,
        fancybox=True,
        shadow=True,
    )

    # plt.suptitle(
    #    "RQ1: Diversity Quality Assessment", fontsize=14, fontweight="bold", y=0.85
    # )
    plt.tight_layout()
    plt.subplots_adjust(top=0.75)  # Make room for legend above

    # Save high-quality figures
    plt.savefig(
        f"{output_dir}/rq1_diversity_quality_improved.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/rq1_diversity_quality_improved.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"Diversity quality assessment saved to {output_dir}/rq1_diversity_quality_improved.png and .pdf"
    )
    plt.close()


def plot_anomaly_detection_quality(df: pl.DataFrame, output_dir: str = "plots"):
    """Plot RQ1 Section 3: Anomaly Detection Quality Assessment."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    color_scheme = get_algorithm_color_scheme()
    line_styles = get_line_styles()
    display_names = get_algorithm_display_names()

    # Anomaly detection metrics for RQ1
    anomaly_metrics = [
        ("avg_proportion_rare", "Proportion Rare"),
        ("avg_proportion_anomaly", "Proportion Anomaly"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in anomaly_metrics if col in df_pd.columns
    ]

    print("\nRQ1 Section 3: Anomaly Detection Quality")
    print(f"Available anomaly detection metrics: {len(available_metrics)}")
    for col, name in available_metrics:
        print(f"  - {name} ({col})")

    if len(available_metrics) == 0:
        print("No anomaly detection metrics available!")
        return

    # Set up figure - single row layout for 3 metrics
    fig, axes = plt.subplots(
        1, len(available_metrics), figsize=(5 * len(available_metrics), 4)
    )
    if len(available_metrics) == 1:
        axes = [axes]

    plt.style.use("seaborn-v0_8-whitegrid")

    # Create mapping from sampling rate to evenly spaced positions
    rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

    for idx, (metric_col, metric_name) in enumerate(available_metrics):
        ax = axes[idx]

        # Sort samplers for consistent ordering: non-gleaner algorithms first, then gleaner series last (on top)
        all_samplers = df_pd["sampler"].unique()
        non_gleaner_algorithms = [
            s for s in all_samplers if not s.startswith("gleaner")
        ]
        gleaner_algorithms = [s for s in all_samplers if s.startswith("gleaner")]
        # Sort gleaner algorithms with base 'gleaner' first, then variants
        gleaner_sorted = ["gleaner"] + [
            s for s in sorted(gleaner_algorithms) if s != "gleaner"
        ]
        sorted_samplers = non_gleaner_algorithms + gleaner_sorted

        for sampler in sorted_samplers:
            sampler_data = df_pd[df_pd["sampler"] == sampler].sort_values(
                "sampling_rate"
            )

            if len(sampler_data) > 0:
                color = color_scheme.get(sampler, "#333333")
                linestyle = line_styles.get(sampler, "-")
                display_name = display_names.get(sampler, sampler)

                # Updated line width and marker size
                line_width = 2.0
                marker_size = 6  # Increased from 4 to 6

                if sampler in ["gleaner", "tracepicker", "random"]:
                    alpha = 1.0
                    marker = "o"
                elif sampler.startswith("gleaner"):
                    alpha = 0.9
                    marker = "s"
                else:
                    alpha = 1.0
                    marker = "^"

                # Plot with evenly spaced x positions
                x_positions = [
                    rate_positions[rate] for rate in sampler_data["sampling_rate"]
                ]
                ax.plot(
                    x_positions,
                    sampler_data[metric_col],
                    marker=marker,
                    linewidth=line_width,
                    markersize=marker_size,
                    label=display_name,
                    color=color,
                    alpha=alpha,
                    linestyle=linestyle,
                    markerfacecolor=color,
                    markeredgecolor="white",
                    markeredgewidth=1.0,
                )

        # Formatting
        ax.set_title(metric_name, fontsize=11, fontweight="bold", pad=8)

        # Auto-scale y-axis based on metric type and actual data range
        data_max = df_pd[metric_col].max()
        if "proportion" in metric_col.lower():
            # Apply adaptive scaling for proportion metrics too
            if data_max <= 0.5:  # For low-value proportion metrics
                y_max = data_max * 1.2  # 20% padding
            else:
                y_max = 1.05  # Standard scaling for high proportion values
        else:
            # For other anomaly metrics, use adaptive scaling
            if data_max > 0:
                if data_max <= 0.5:  # For low-value metrics
                    y_max = data_max * 1.2  # 20% padding
                else:
                    y_max = data_max * 1.1  # 10% padding for higher values
            else:
                y_max = 1.0

        setup_axis_formatting(ax, sampling_rates, "Score", y_max)

    # Add horizontal legend above the plots, centered
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.95),
        ncol=len(labels),
        fontsize=8,
        frameon=True,
        fancybox=True,
        shadow=True,
    )

    # plt.suptitle(
    #    "RQ1: Anomaly Detection Quality Assessment",
    #    fontsize=14,
    #    fontweight="bold",
    #    y=0.85,
    # )
    plt.tight_layout()
    plt.subplots_adjust(top=0.75)  # Make room for legend above

    # Save high-quality figures
    plt.savefig(
        f"{output_dir}/rq1_anomaly_detection_quality_improved.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/rq1_anomaly_detection_quality_improved.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"Anomaly detection quality assessment saved to {output_dir}/rq1_anomaly_detection_quality_improved.png and .pdf"
    )
    plt.close()


def plot_combined_quality_overview(df: pl.DataFrame, output_dir: str = "plots"):
    """Plot RQ1 Combined: Overall Quality Assessment Overview."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    color_scheme = get_algorithm_color_scheme()
    line_styles = get_line_styles()
    display_names = get_algorithm_display_names()

    # Select key metrics for overview (one from each category)
    overview_metrics = [
        ("avg_api_coverage", "API Coverage"),
        ("avg_unique_trace_coverage", "Unique Trace Coverage"),
        ("avg_shannon_entropy", "Shannon Entropy"),
        ("avg_proportion_anomaly", "Proportion Anomaly"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in overview_metrics if col in df_pd.columns
    ]

    print("\nRQ1 Combined: Quality Overview")
    print(f"Available overview metrics: {len(available_metrics)}")
    for col, name in available_metrics:
        print(f"  - {name} ({col})")

    if len(available_metrics) == 0:
        print("No overview metrics available!")
        return

    # Set up figure - 1x4 layout for overview
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))

    plt.style.use("seaborn-v0_8-whitegrid")

    # Create mapping from sampling rate to evenly spaced positions
    rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

    for idx, (metric_col, metric_name) in enumerate(available_metrics):
        if idx >= len(axes):
            break

        ax = axes[idx]

        # Sort samplers for consistent ordering: non-gleaner algorithms first, then gleaner series last (on top)
        all_samplers = df_pd["sampler"].unique()
        non_gleaner_algorithms = [
            s for s in all_samplers if not s.startswith("gleaner")
        ]
        gleaner_algorithms = [s for s in all_samplers if s.startswith("gleaner")]
        # Sort gleaner algorithms with base 'gleaner' first, then variants
        gleaner_sorted = ["gleaner"] + [
            s for s in sorted(gleaner_algorithms) if s != "gleaner"
        ]
        sorted_samplers = non_gleaner_algorithms + gleaner_sorted

        for sampler in sorted_samplers:
            sampler_data = df_pd[df_pd["sampler"] == sampler].sort_values(
                "sampling_rate"
            )

            if len(sampler_data) > 0:
                color = color_scheme.get(sampler, "#333333")
                linestyle = line_styles.get(sampler, "-")
                display_name = display_names.get(sampler, sampler)

                # Updated line width and marker size
                line_width = 2.0
                marker_size = 6  # Increased from 4 to 6

                if sampler in ["gleaner", "tracepicker", "random"]:
                    alpha = 1.0
                    marker = "o"
                elif sampler.startswith("gleaner"):
                    alpha = 0.8
                    marker = "s"
                else:
                    alpha = 1.0
                    marker = "^"

                # Plot with evenly spaced x positions
                x_positions = [
                    rate_positions[rate] for rate in sampler_data["sampling_rate"]
                ]
                ax.plot(
                    x_positions,
                    sampler_data[metric_col],
                    marker=marker,
                    linewidth=line_width,
                    markersize=marker_size,
                    label=display_name,
                    color=color,
                    alpha=alpha,
                    linestyle=linestyle,
                    markerfacecolor=color,
                    markeredgecolor="white",
                    markeredgewidth=1.0,
                )

        # Formatting
        ax.set_title(metric_name, fontsize=11, fontweight="bold", pad=8)

        # Auto-scale y-axis with adaptive scaling
        data_max = df_pd[metric_col].max()
        if "coverage" in metric_col.lower() or "proportion" in metric_col.lower():
            if data_max <= 0.5:  # For low-value coverage/proportion metrics
                y_max = min(1.05, data_max * 1.2)  # 20% padding, but max 1.05
            else:
                y_max = 1.05  # Standard scaling
        else:
            # For diversity and other metrics
            if data_max > 0:
                if data_max <= 0.5:  # For low-value metrics
                    y_max = data_max * 1.2  # 20% padding
                else:
                    y_max = data_max * 1.1  # 10% padding for higher values
            else:
                y_max = 1.0

        setup_axis_formatting(ax, sampling_rates, "Score", y_max)

    # Add horizontal legend above the plots, centered
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.95),
        ncol=len(labels),
        fontsize=8,
        frameon=True,
        fancybox=True,
        shadow=True,
    )

    # Hide unused subplots
    for idx in range(len(available_metrics), len(axes)):
        axes[idx].remove()

    # plt.suptitle(
    #    "RQ1: Sampling Quality Overview - All Algorithms",
    #    fontsize=14,
    #    fontweight="bold",
    #    y=0.85,
    # )
    plt.tight_layout()
    plt.subplots_adjust(top=0.75)  # Make room for legend above

    # Save high-quality figures
    plt.savefig(
        f"{output_dir}/rq1_quality_overview_improved.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/rq1_quality_overview_improved.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"Quality overview saved to {output_dir}/rq1_quality_overview_improved.png and .pdf"
    )
    plt.close()


def main():
    """Main function to generate RQ1 quality evaluation figures."""

    parquet_path = "/home/nn/workspace/gleaner-rc/output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet"

    if not Path(parquet_path).exists():
        print(f"Error: File not found: {parquet_path}")
        return

    print("RQ1: Quality Evaluation - Sampling Algorithm Assessment (IMPROVED)")
    print("=" * 60)
    print("Loading and filtering data...")
    df = load_and_filter_data(parquet_path)

    if df.height == 0:
        print("No offline mode data found!")
        return

    print("\nGenerating RQ1 quality assessment figures...")
    print(
        "Target algorithms: gleaner, tracepicker, trastrainer, trastrainer w/o metrics, sifter, sieve, random"
    )
    print("Quality dimensions: Coverage, Diversity, Anomaly Detection")
    print(
        "Improvements: Enhanced color scheme, line styles, and marker shapes for better distinction"
    )

    # Generate individual section figures
    print("\n" + "=" * 60)
    plot_coverage_quality(df)

    print("\n" + "=" * 60)
    plot_diversity_quality(df)

    print("\n" + "=" * 60)
    plot_anomaly_detection_quality(df)

    print("\n" + "=" * 60)
    plot_combined_quality_overview(df)

    print("\n" + "=" * 60)
    print("RQ1 Quality Evaluation Complete!")
    print("\nGenerated improved figures (check 'plots' directory):")
    print("- rq1_coverage_quality_improved.png/pdf")
    print("- rq1_diversity_quality_improved.png/pdf")
    print("- rq1_anomaly_detection_quality_improved.png/pdf")
    print("- rq1_quality_overview_improved.png/pdf")
    print(
        "\nAll figures are optimized for single-column paper format with enhanced visual distinction."
    )


if __name__ == "__main__":
    main()
    print("\nGenerated improved figures (check 'plots' directory):")
    print("- rq1_coverage_quality_improved.png/pdf")
    print("- rq1_diversity_quality_improved.png/pdf")
    print("- rq1_anomaly_detection_quality_improved.png/pdf")
    print("- rq1_quality_overview_improved.png/pdf")
    print(
        "\nAll figures are optimized for single-column paper format with enhanced visual distinction."
    )
