#!/usr/bin/env python3
"""
RQ1: Quality Evaluation - Generate comprehensive quality assessment figures for all sampling algorithms.
Improved version with better color distinction between algorithms and compact layout.

This script evaluates sampling quality across multiple dimensions:
1. Coverage: API coverage, path dedup coverage, event pair coverage, unique trace coverage
2. Diversity: Shannon entropy (now included in main coverage plot)
3. Anomaly Detection: proportion rare, proportion anomaly

All evaluations use offline mode data across all sampling rates.
Figures are optimized for compact single-column paper format.
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
        "gleaner_no_ad": "Gleaner w/o Alarms",
        "gleaner_no_logs_no_ad": "Gleaner w/o Logs w/o Alarms",
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
        "tracepicker": "#2ca02c",  # Green
        "trastrainer": "#d62728",  # Red
        "trastrainer_no_metrics": "#ff7f0e",  # Orange
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


def get_marker_styles():
    """Get distinct marker styles for additional differentiation."""
    marker_styles = {
        # Main algorithms - different markers
        "gleaner": "o",  # circle
        "tracepicker": "s",  # square
        "trastrainer": "^",  # triangle up
        "trastrainer_no_metrics": "v",  # triangle down
        "sifter": "D",  # diamond
        "sieve": "p",  # pentagon
        "random": "x",  # x
        # Gleaner variants - circle variations
        "gleaner_no_logs": "o",
        "gleaner_no_ad": "o",
        "gleaner_no_logs_no_ad": "o",
        "gleaner_pure_diversity": "o",
        "gleaner_small_batch": "o",
        "gleaner_medium_batch": "o",
        "gleaner_unlimited_batch": "o",
    }
    return marker_styles


def setup_axis_formatting_compact(ax, sampling_rates, y_label="Value", y_max=None):
    """Set up compact axis formatting with evenly spaced sampling rates."""
    # Convert sampling rates to percentages and sort
    rate_percentages = sorted([rate * 100 for rate in sampling_rates])

    # Use evenly spaced positions instead of actual values
    x_positions = range(len(rate_percentages))

    # Set x-axis ticks to evenly spaced positions
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f"{rate:.1f}%" for rate in rate_percentages], fontsize=12)

    # Set reasonable axis limits
    ax.set_xlim(-0.2, len(rate_percentages) - 0.8)

    if y_max is None:
        # Auto-determine y_max based on data, with some padding
        y_max = 1.05
    ax.set_ylim(0, y_max)

    # Labels with larger font to match reference
    ax.set_xlabel("Sampling Rate (%)", fontsize=13)
    ax.set_ylabel(y_label, fontsize=13)

    # Improve grid
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)

    # Tighter tick parameters
    ax.tick_params(axis="both", which="major", labelsize=8)


def plot_comprehensive_quality(df: pl.DataFrame, output_dir: str = "plots"):
    """Plot RQ1: Comprehensive Quality Assessment with compact layout."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    color_scheme = get_algorithm_color_scheme()
    line_styles = get_line_styles()
    marker_styles = get_marker_styles()
    display_names = get_algorithm_display_names()

    # Coverage and diversity metrics for RQ1 - removed Event Coverage, now 4 metrics in 2x2 layout
    quality_metrics = [
        ("avg_api_coverage", "API Coverage"),
        ("avg_path_coverage_dedup", "Path Coverage"),
        ("avg_unique_trace_coverage", "Trace Pattern Coverage"),
        ("avg_shannon_entropy", "Shannon Entropy"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in quality_metrics if col in df_pd.columns
    ]

    print("\nRQ1: Comprehensive Quality Assessment")
    print(f"Available quality metrics: {len(available_metrics)}")
    for col, name in available_metrics:
        print(f"  - {name} ({col})")

    # Set up figure - 2x2 layout with square-ish subplots, smaller size
    fig, axes = plt.subplots(2, 2, figsize=(8, 7.5))
    axes = axes.flatten()

    # Use a clean style
    plt.style.use("default")

    # Set white background
    fig.patch.set_facecolor("white")

    # Create mapping from sampling rate to evenly spaced positions
    rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

    # Define consistent ordering for all plots - reverse order so gleaner is drawn last
    plot_order = [
        "random",
        "sifter",
        "sieve",
        "trastrainer_no_metrics",
        "trastrainer",
        "tracepicker",
        "gleaner",
    ]

    # Sequence labels for subplots
    sequence_labels = ["(a)", "(b)", "(c)", "(d)"]

    for idx, (metric_col, metric_name) in enumerate(available_metrics):
        if idx >= len(axes):
            break

        ax = axes[idx]

        # Get available samplers
        all_samplers = df_pd["sampler"].unique()

        # Use consistent ordering, filter to available samplers
        sorted_samplers = [s for s in plot_order if s in all_samplers]

        for sampler in sorted_samplers:
            if sampler not in df_pd["sampler"].values:
                continue

            sampler_data = df_pd[df_pd["sampler"] == sampler]

            if len(sampler_data) == 0:
                continue

            # Get metric values for each sampling rate
            x_vals = []
            y_vals = []

            for rate in sampling_rates:
                rate_data = sampler_data[sampler_data["sampling_rate"] == rate]
                if len(rate_data) > 0:
                    x_vals.append(rate_positions[rate])
                    y_vals.append(rate_data[metric_col].iloc[0])

            if len(x_vals) == 0:
                continue

            # Plot line with markers
            display_name = display_names.get(sampler, sampler)
            color = color_scheme.get(sampler, "#666666")
            linestyle = line_styles.get(sampler, "-")
            marker = marker_styles.get(sampler, "o")

            ax.plot(
                x_vals,
                y_vals,
                label=display_name,
                color=color,
                linestyle=linestyle,
                marker=marker,
                markersize=4,
                linewidth=1.8,
                alpha=0.8,
            )

        # Convert sampling rates to percentages and sort
        rate_percentages = sorted([rate * 100 for rate in sampling_rates])
        x_positions_axis = range(len(rate_percentages))

        # Set x-axis ticks to evenly spaced positions - larger font
        ax.set_xticks(x_positions_axis)
        ax.set_xticklabels([f"{rate:.1f}%" for rate in rate_percentages], fontsize=14)

        # Set reasonable axis limits
        ax.set_xlim(-0.2, len(rate_percentages) - 0.8)

        # Auto-scale y-axis based on actual data range
        data_max = df_pd[metric_col].max()
        if data_max <= 0.5:
            y_max = 0.6
        elif data_max <= 1.0:
            y_max = 1.05
        else:
            y_max = data_max * 1.1

        ax.set_ylim(0, y_max)

        # Labels - larger font
        ax.set_xlabel("Sampling Rate (%)", fontsize=16)
        ax.set_ylabel("Value", fontsize=16)

        # Improve grid
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        ax.set_axisbelow(True)

        # Tick parameters - larger font
        ax.tick_params(axis="both", which="major", labelsize=12)

        # Add sequence label and title below the plot - adjust position for more space
        sequence_label = (
            sequence_labels[idx] if idx < len(sequence_labels) else f"({chr(97 + idx)})"
        )
        ax.text(
            0.5,
            -0.22,  # More space from plot (was -0.18)
            f"{sequence_label} {metric_name}",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=16,
            fontweight="bold",
        )

    # Hide unused subplots
    for idx in range(len(available_metrics), len(axes)):
        axes[idx].remove()

    # Add horizontal legend below the plots - smaller font than title
    handles, labels = axes[0].get_legend_handles_labels()
    # Calculate ncol for 2 rows
    ncol = (len(labels) + 1) // 2
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.06),  # More space from titles (was -0.06)
        ncol=ncol,
        fontsize=14,  # Smaller than title font (was 16)
        frameon=True,
        fancybox=True,
        edgecolor="gray",
    )

    # Tight layout with proper spacing
    plt.tight_layout()
    plt.subplots_adjust(
        bottom=0.18, top=0.98, hspace=0.35, wspace=0.25
    )  # Increased bottom margin

    # Save high-quality figures
    plt.savefig(
        f"{output_dir}/rq1_comprehensive_quality_compact.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/rq1_comprehensive_quality_compact.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"Comprehensive quality assessment saved to {output_dir}/rq1_comprehensive_quality_compact.png and .pdf"
    )
    plt.close()


def plot_anomaly_detection_quality(df: pl.DataFrame, output_dir: str = "plots"):
    """Plot RQ1 Section 2: Anomaly Detection Quality Assessment with compact layout."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    color_scheme = get_algorithm_color_scheme()
    line_styles = get_line_styles()
    marker_styles = get_marker_styles()
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

    print("\nRQ1 Section 2: Anomaly Detection Quality")
    print(f"Available anomaly detection metrics: {len(available_metrics)}")
    for col, name in available_metrics:
        print(f"  - {name} ({col})")

    if len(available_metrics) == 0:
        print("No anomaly detection metrics available!")
        return

    # Set up figure - 1x2 layout with square-ish subplots, smaller size
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.8))

    # Use a clean style
    plt.style.use("default")

    # Set white background
    fig.patch.set_facecolor("white")

    # Create mapping from sampling rate to evenly spaced positions
    rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

    # Define consistent ordering for all plots - reverse order so gleaner is drawn last
    plot_order = [
        "random",
        "sifter",
        "sieve",
        "trastrainer_no_metrics",
        "trastrainer",
        "tracepicker",
        "gleaner",
    ]

    # Sequence labels for subplots
    sequence_labels = ["(a)", "(b)"]

    for idx, (metric_col, metric_name) in enumerate(available_metrics):
        ax = axes[idx]

        # Get available samplers
        all_samplers = df_pd["sampler"].unique()

        # Use consistent ordering, filter to available samplers
        sorted_samplers = [s for s in plot_order if s in all_samplers]

        for sampler in sorted_samplers:
            if sampler not in df_pd["sampler"].values:
                continue

            sampler_data = df_pd[df_pd["sampler"] == sampler]

            if len(sampler_data) == 0:
                continue

            # Get metric values for each sampling rate
            x_vals = []
            y_vals = []

            for rate in sampling_rates:
                rate_data = sampler_data[sampler_data["sampling_rate"] == rate]
                if len(rate_data) > 0:
                    x_vals.append(rate_positions[rate])
                    y_vals.append(rate_data[metric_col].iloc[0])

            if len(x_vals) == 0:
                continue

            # Plot line with markers
            display_name = display_names.get(sampler, sampler)
            color = color_scheme.get(sampler, "#666666")
            linestyle = line_styles.get(sampler, "-")
            marker = marker_styles.get(sampler, "o")

            ax.plot(
                x_vals,
                y_vals,
                label=display_name,
                color=color,
                linestyle=linestyle,
                marker=marker,
                markersize=4,
                linewidth=1.8,
                alpha=0.8,
            )

        # Convert sampling rates to percentages and sort
        rate_percentages = sorted([rate * 100 for rate in sampling_rates])
        x_positions_axis = range(len(rate_percentages))

        # Set x-axis ticks to evenly spaced positions - larger font
        ax.set_xticks(x_positions_axis)
        ax.set_xticklabels([f"{rate:.1f}%" for rate in rate_percentages], fontsize=14)

        # Set reasonable axis limits
        ax.set_xlim(-0.2, len(rate_percentages) - 0.8)

        # Auto-scale y-axis based on actual data range
        data_max = df_pd[metric_col].max()
        if data_max <= 0.5:
            y_max = 0.6
        elif data_max <= 1.0:
            y_max = 1.05
        else:
            y_max = data_max * 1.1

        ax.set_ylim(0, y_max)

        # Labels - larger font
        ax.set_xlabel("Sampling Rate (%)", fontsize=16)
        ax.set_ylabel("Proportion", fontsize=16)

        # Improve grid
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        ax.set_axisbelow(True)

        # Tick parameters - larger font
        ax.tick_params(axis="both", which="major", labelsize=12)

        # Add sequence label and title below the plot - adjust position for more space
        sequence_label = (
            sequence_labels[idx] if idx < len(sequence_labels) else f"({chr(97 + idx)})"
        )
        ax.text(
            0.5,
            -0.18,  # More space from plot (was -0.22)
            f"{sequence_label} {metric_name}",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=16,
            fontweight="bold",
        )

    # Add horizontal legend below the plots with two rows for better spacing - smaller font than title
    handles, labels = axes[0].get_legend_handles_labels()
    # Calculate ncol for 2 rows - divide total labels by 2, round up
    ncol = (len(labels) + 1) // 2
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.26),  # More space from titles (was -0.22)
        ncol=ncol,
        fontsize=14,  # Smaller than title font (was 16)
        frameon=True,
        fancybox=True,
        edgecolor="gray",
    )

    # Tight layout with more bottom space for the two-row legend
    plt.tight_layout()
    plt.subplots_adjust(
        bottom=0.32, top=0.98, hspace=0.2, wspace=0.25
    )  # Increased bottom margin

    # Save high-quality figures
    plt.savefig(
        f"{output_dir}/rq1_anomaly_detection_compact.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/rq1_anomaly_detection_compact.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"Anomaly detection quality assessment saved to {output_dir}/rq1_anomaly_detection_compact.png and .pdf"
    )
    plt.close()


def plot_combined_quality(df: pl.DataFrame, output_dir: str = "plots"):
    """Plot RQ1: Combined Quality Assessment (Coverage + Anomaly Detection) in 2x3 layout."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    color_scheme = get_algorithm_color_scheme()
    line_styles = get_line_styles()
    marker_styles = get_marker_styles()
    display_names = get_algorithm_display_names()

    # Combined metrics for RQ1 - 4 coverage metrics + 2 anomaly metrics
    quality_metrics = [
        ("avg_api_coverage", "API Coverage"),
        ("avg_path_coverage_dedup", "Path Coverage"),
        ("avg_unique_trace_coverage", "Trace Pattern Coverage"),
        ("avg_shannon_entropy", "Shannon Entropy"),
        ("avg_proportion_rare", "Proportion Rare"),
        ("avg_proportion_anomaly", "Proportion Anomaly"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in quality_metrics if col in df_pd.columns
    ]

    print("\nRQ1: Combined Quality Assessment")
    print(f"Available quality metrics: {len(available_metrics)}")
    for col, name in available_metrics:
        print(f"  - {name} ({col})")

    # Set up figure - 2x3 layout: left 2x2 for 4.1 (coverage), right 1x2 for 4.2 (anomaly)
    fig = plt.figure(figsize=(12, 8))

    # Create grid spec for custom layout
    import matplotlib.gridspec as gridspec

    gs = gridspec.GridSpec(2, 3, figure=fig)

    # Left 2x2 grid for coverage metrics (4.1a-4.1d)
    axes_41 = [
        fig.add_subplot(gs[0, 0]),  # 4.1a - top left
        fig.add_subplot(gs[0, 1]),  # 4.1b - top middle
        fig.add_subplot(gs[1, 0]),  # 4.1c - bottom left
        fig.add_subplot(gs[1, 1]),  # 4.1d - bottom middle
    ]

    # Right 1x2 column for anomaly metrics (4.2a-4.2b)
    axes_42 = [
        fig.add_subplot(gs[0, 2]),  # 4.2a - top right
        fig.add_subplot(gs[1, 2]),  # 4.2b - bottom right
    ]

    # Combine all axes
    all_axes = axes_41 + axes_42

    # Use a clean style
    plt.style.use("default")

    # Set white background
    fig.patch.set_facecolor("white")

    # Create mapping from sampling rate to evenly spaced positions
    rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

    # Define consistent ordering for all plots - reverse order so gleaner is drawn last
    plot_order = [
        "random",
        "sifter",
        "sieve",
        "trastrainer_no_metrics",
        "trastrainer",
        "tracepicker",
        "gleaner",
    ]

    # Sequence labels for subplots with sequence numbering in parentheses
    sequence_labels = ["(4.1a)", "(4.1b)", "(4.1c)", "(4.1d)", "(4.2a)", "(4.2b)"]

    for idx, (metric_col, metric_name) in enumerate(available_metrics):
        if idx >= len(all_axes):
            break

        ax = all_axes[idx]

        # Get available samplers
        all_samplers = df_pd["sampler"].unique()

        # Use consistent ordering, filter to available samplers
        sorted_samplers = [s for s in plot_order if s in all_samplers]

        for sampler in sorted_samplers:
            if sampler not in df_pd["sampler"].values:
                continue

            sampler_data = df_pd[df_pd["sampler"] == sampler]

            if len(sampler_data) == 0:
                continue

            # Get metric values for each sampling rate
            x_vals = []
            y_vals = []

            for rate in sampling_rates:
                rate_data = sampler_data[sampler_data["sampling_rate"] == rate]
                if len(rate_data) > 0:
                    x_vals.append(rate_positions[rate])
                    y_vals.append(rate_data[metric_col].iloc[0])

            if len(x_vals) == 0:
                continue

            # Plot line with markers
            display_name = display_names.get(sampler, sampler)
            color = color_scheme.get(sampler, "#666666")
            linestyle = line_styles.get(sampler, "-")
            marker = marker_styles.get(sampler, "o")

            ax.plot(
                x_vals,
                y_vals,
                label=display_name,
                color=color,
                linestyle=linestyle,
                marker=marker,
                markersize=4,
                linewidth=1.8,
                alpha=0.8,
            )

        # Convert sampling rates to percentages and sort
        rate_percentages = sorted([rate * 100 for rate in sampling_rates])
        x_positions_axis = range(len(rate_percentages))

        # Set x-axis ticks to evenly spaced positions
        ax.set_xticks(x_positions_axis)
        ax.set_xticklabels([f"{rate:.1f}%" for rate in rate_percentages], fontsize=14)

        # Set reasonable axis limits
        ax.set_xlim(-0.2, len(rate_percentages) - 0.8)

        # Auto-scale y-axis based on actual data range - cap proportion_anomaly at 0.3
        data_max = df_pd[metric_col].max()

        # Special handling for proportion_anomaly
        if "proportion_anomaly" in metric_col:
            y_max = 0.3  # Cap at 0.3 for proportion_anomaly
        elif data_max <= 0.5:
            y_max = 0.6
        elif data_max <= 1.0:
            y_max = 1.05
        else:
            y_max = data_max * 1.1

        ax.set_ylim(0, y_max)

        # Labels - remove "Value" from y-axis
        ax.set_xlabel("Sampling Rate (%)", fontsize=16)
        ax.set_ylabel("", fontsize=16)  # Empty y-axis label

        # Improve grid
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        ax.set_axisbelow(True)

        # Tick parameters
        ax.tick_params(axis="both", which="major", labelsize=12)

        # Add sequence label and title below the plot
        sequence_label = (
            sequence_labels[idx] if idx < len(sequence_labels) else f"({chr(97 + idx)})"
        )
        ax.text(
            0.5,
            -0.21,
            f"{sequence_label} {metric_name}",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=16,
            fontweight="bold",
        )

    # Hide unused subplots (none expected since we have exactly 6 metrics)
    for idx in range(len(available_metrics), len(all_axes)):
        all_axes[idx].axis("off")

    # Add horizontal legend below the plots
    handles, labels = all_axes[0].get_legend_handles_labels()
    # Calculate ncol for 2 rows
    ncol = (len(labels) + 1) // 2
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.05),
        ncol=ncol,
        fontsize=14,
        frameon=True,
        fancybox=True,
        edgecolor="gray",
    )

    # Tight layout with proper spacing - slightly relaxed
    plt.tight_layout()
    plt.subplots_adjust(
        bottom=0.15, top=0.98, hspace=0.31, wspace=0.2
    )  # hspace: 0.26 + 0.05

    # Save high-quality figures
    plt.savefig(
        f"{output_dir}/rq1_quality_combined.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/rq1_quality_combined.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"Combined quality assessment saved to {output_dir}/rq1_quality_combined.png and .pdf"
    )
    plt.close()


def save_plot_data_to_markdown(df: pl.DataFrame, output_dir: str = "plots"):
    """Save RQ1 plot data to Markdown format for quantitative analysis."""
    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    display_names = get_algorithm_display_names()

    # Combined metrics for RQ1
    quality_metrics = [
        ("avg_api_coverage", "API Coverage"),
        ("avg_path_coverage_dedup", "Path Coverage"),
        ("avg_unique_trace_coverage", "Trace Pattern Coverage"),
        ("avg_shannon_entropy", "Shannon Entropy"),
        ("avg_proportion_rare", "Proportion Rare"),
        ("avg_proportion_anomaly", "Proportion Anomaly"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in quality_metrics if col in df_pd.columns
    ]

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())

    # Define sampler order
    sampler_order = [
        "gleaner",
        "tracepicker",
        "trastrainer",
        "trastrainer_no_metrics",
        "sifter",
        "sieve",
        "random",
    ]

    # Create markdown content
    md_content = ["# RQ1: Quality Evaluation Data\n"]
    md_content.append(
        "This file contains the exact values used in RQ1 plots for quantitative analysis.\n"
    )

    for metric_col, metric_name in available_metrics:
        md_content.append(f"\n## {metric_name}\n")

        # Create table header
        header = "| Algorithm |"
        for rate in sampling_rates:
            header += f" {rate * 100:.1f}% |"
        md_content.append(header)

        # Create separator
        separator = "|-----------|"
        separator += "----:|" * len(sampling_rates)
        md_content.append(separator)

        # Add data rows
        for sampler in sampler_order:
            sampler_data = df_pd[df_pd["sampler"] == sampler]
            if len(sampler_data) == 0:
                continue

            display_name = display_names.get(sampler, sampler)
            row = f"| {display_name} |"

            for rate in sampling_rates:
                rate_data = sampler_data[sampler_data["sampling_rate"] == rate]
                if len(rate_data) > 0:
                    value = rate_data[metric_col].iloc[0]
                    row += f" {value:.4f} |"
                else:
                    row += " N/A |"

            md_content.append(row)

    # Write to file
    output_file = f"{output_dir}/rq1_data.md"
    with open(output_file, "w") as f:
        f.write("\n".join(md_content))

    print(f"RQ1 plot data saved to {output_file}")


def main():
    """Main function to generate RQ1 quality evaluation figures."""

    parquet_path = "/home/nn/workspace/gleaner-rc/output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet"

    if not Path(parquet_path).exists():
        print(f"Error: Parquet file not found at {parquet_path}")
        return

    print("RQ1: Quality Evaluation - Sampling Algorithm Assessment (COMPACT)")
    print("=" * 60)
    print("Loading and filtering data...")
    df = load_and_filter_data(parquet_path)

    if df.height == 0:
        print("No data available after filtering!")
        return

    print("\nGenerating RQ1 quality assessment figures...")
    print(
        "Target algorithms: gleaner, tracepicker, trastrainer, trastrainer w/o metrics, sifter, sieve, random"
    )
    print("Quality dimensions: Coverage + Entropy + Anomaly Detection")
    print("Layout: Combined 2x3 layout for complete RQ1 assessment")

    # Generate combined quality figure (coverage + anomaly)
    print("\n" + "=" * 60)
    plot_combined_quality(df)

    # Save plot data to markdown
    print("\n" + "=" * 60)
    save_plot_data_to_markdown(df)

    print("\n" + "=" * 60)
    print("RQ1 Quality Evaluation Complete!")
    print("\nGenerated combined figure (check 'plots' directory):")
    print("- rq1_quality_combined.png/pdf")
    print("- rq1_data.md (quantitative data)")
    print(
        "\nFigure shows complete RQ1 assessment with section-numbered subplots (4.1a-4.1d, 4.2a-4.2b)."
    )


if __name__ == "__main__":
    main()
