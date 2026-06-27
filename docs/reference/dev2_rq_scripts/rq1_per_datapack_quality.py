#!/usr/bin/env python3
"""
RQ1: Per-Datapack Quality Evaluation - Generate quality assessment figures for each datapack individually.

This script evaluates sampling quality for each datapack across multiple dimensions:
1. Coverage: API coverage, path dedup coverage, event pair coverage, unique trace coverage
2. Diversity: Shannon entropy
3. Anomaly Detection: proportion rare, proportion anomaly

Uses tracepicker dataset with detailed per-datapack analysis.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl


def load_datapack_data(parquet_path: str):
    """Load detailed performance data and filter for offline mode."""
    df = pl.read_parquet(parquet_path)

    # Filter for offline mode only
    offline_df = (
        df.filter(pl.col("mode") == "offline")
        .filter(
            pl.col("sampler").is_in(
                [
                    "gleaner_no_logs_no_ad",
                    "tracepicker",
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
    print(f"Datapacks: {len(offline_df['datapack'].unique())} unique datapacks")

    return offline_df


def get_algorithm_display_names():
    """Get display names for algorithms with proper formatting."""
    display_names = {
        "gleaner_no_logs_no_ad": "Gleaner w/o Logs w/o Alarms",
        "tracepicker": "TracePicker",
        "trastrainer_no_metrics": "TrasTrainer w/o Metrics",
        "sifter": "Sifter",
        "sieve": "Sieve",
        "random": "Random",
    }
    return display_names


def get_algorithm_color_scheme():
    """Get a comprehensive color scheme for all algorithms."""
    algorithm_colors = {
        "gleaner_no_logs_no_ad": "#1f77b4",  # Blue
        "tracepicker": "#2ca02c",  # Green
        "trastrainer_no_metrics": "#ff7f0e",  # Orange
        "sifter": "#9467bd",  # Purple
        "sieve": "#8c564b",  # Brown
        "random": "#000000",  # Black
    }
    return algorithm_colors


def get_marker_styles():
    """Get distinct marker styles for additional differentiation."""
    marker_styles = {
        "gleaner_no_logs_no_ad": "o",  # circle
        "tracepicker": "s",  # square
        "trastrainer_no_metrics": "^",  # triangle up
        "sifter": "D",  # diamond
        "sieve": "p",  # pentagon
        "random": "x",  # x
    }
    return marker_styles


def get_datapack_display_names():
    """Get display names for datapacks with proper capitalization."""
    display_names = {
        "trainticket": "Train Ticket",
        "socialNetwork": "Social Network",
        "onlineBoutique": "Online Boutique",
        "sockshop": "Sock Shop",
        "media": "Media",
    }
    return display_names


def calculate_traces_per_min_from_data(datapack: str):
    """Calculate average unique traces per minute by aggregating per minute and excluding zero-trace minutes."""
    try:
        import pandas as pd

        # Path to the normal traces parquet file
        traces_file = f"/home/nn/workspace/gleaner-rc/data/rcabench-platform-v2/data/tracepicker/{datapack}/normal_traces.parquet"

        if not Path(traces_file).exists():
            print(f"    Traces file not found: {traces_file}")
            return "N/A"

        # Read the traces data
        traces_df = pd.read_parquet(traces_file)

        if "time" not in traces_df.columns:
            print("    No time column found in traces data")
            return "N/A"

        # Convert time to datetime
        traces_df["time"] = pd.to_datetime(traces_df["time"])

        # Create a minute-level timestamp (truncate to minute)
        traces_df["minute"] = traces_df["time"].dt.floor(
            "min"
        )  # 'min' is minute frequency

        # Group by minute and count unique trace_ids
        minute_stats = traces_df.groupby("minute")["trace_id"].nunique().reset_index()
        minute_stats.columns = ["minute", "unique_traces"]

        # Remove minutes with 0 unique traces (shouldn't happen with actual data, but just to be safe)
        minute_stats = minute_stats[minute_stats["unique_traces"] > 0]

        # Calculate average unique traces per minute
        if len(minute_stats) == 0:
            print("    No valid minutes found with trace data")
            return "N/A"

        avg_traces_per_min = minute_stats["unique_traces"].mean()
        total_minutes = len(minute_stats)
        total_unique_traces = minute_stats["unique_traces"].sum()

        print(
            f"    Minute aggregation: {total_minutes} active minutes, {total_unique_traces} total unique traces"
        )
        print(f"    Average unique traces per minute: {avg_traces_per_min:.1f}")

        return round(avg_traces_per_min, 1)

    except Exception as e:
        print(f"    Error calculating traces per min from data: {e}")
        return "N/A"


def setup_axis_formatting(
    ax, sampling_rates, y_label="Value", y_max=None, show_ylabel=True
):
    """Set up axis formatting with evenly spaced sampling rates."""
    # Convert sampling rates to percentages and sort
    rate_percentages = sorted([rate * 100 for rate in sampling_rates])

    # Use evenly spaced positions instead of actual values
    x_positions = range(len(rate_percentages))

    # Set x-axis ticks to evenly spaced positions
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        [f"{rate:.1f}%" for rate in rate_percentages], fontsize=14
    )  # Match combined

    # Set reasonable axis limits
    ax.set_xlim(-0.2, len(rate_percentages) - 0.8)

    if y_max is None:
        y_max = 1.05
    ax.set_ylim(0, y_max)

    # Labels - match combined style
    ax.set_xlabel("Sampling Rate (%)", fontsize=16)
    # Only show y-axis label for leftmost plots
    if show_ylabel:
        ax.set_ylabel(y_label, fontsize=16)
    else:
        ax.set_ylabel("", fontsize=16)

    # Grid
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)

    # Tick parameters - match combined
    ax.tick_params(axis="both", which="major", labelsize=12)


def plot_multiple_datapacks_unique_trace_coverage(
    df: pl.DataFrame, selected_datapacks: list, output_dir: str = "plots"
):
    """Plot unique trace coverage for multiple datapacks in one figure."""

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    color_scheme = get_algorithm_color_scheme()
    marker_styles = get_marker_styles()
    display_names = get_algorithm_display_names()
    datapack_display_names = get_datapack_display_names()

    # Set up figure - 2x3 layout matching RQ1 combined style
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))  # Match combined figure size
    axes = axes.flatten()

    # Use a clean style
    plt.style.use("default")
    fig.patch.set_facecolor("white")

    # Define consistent ordering matching RQ1 - reverse order so gleaner is drawn last
    plot_order = [
        "random",
        "sifter",
        "sieve",
        "trastrainer_no_metrics",
        "tracepicker",
        "gleaner_no_logs_no_ad",
    ]

    # Sequence labels for subplots - add parentheses
    sequence_labels = ["(a)", "(b)", "(c)", "(d)", "(e)"]

    for idx, datapack in enumerate(selected_datapacks):
        print(f"Processing datapack {idx + 1}/{len(selected_datapacks)}: {datapack}")
        if idx >= len(axes) - 1:  # Reserve last position for legend
            break

        ax = axes[idx]

        # Filter data for this datapack
        datapack_df = df.filter(pl.col("datapack") == datapack)
        df_pd = datapack_df.to_pandas()

        if len(df_pd) == 0:
            print(f"No data found for datapack: {datapack}")
            datapack_display = datapack_display_names.get(datapack, datapack)
            # Add title below even for no data case
            ax.text(
                0.5,
                0.5,
                "No Data",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=14,
            )
            sequence_label = (
                sequence_labels[idx]
                if idx < len(sequence_labels)
                else f"({chr(97 + idx)})"
            )
            ax.text(
                0.5,
                -0.21,  # Match combined
                f"{sequence_label} {datapack_display}",
                transform=ax.transAxes,
                ha="center",
                va="top",
                fontsize=16,  # Match combined
                fontweight="bold",
            )
            continue
        else:
            print(f"Found {len(df_pd)} rows for datapack: {datapack}")

        # Get unique sampling rates for this datapack
        sampling_rates = sorted(df_pd["sampling_rate"].unique())

        # Create mapping from sampling rate to evenly spaced positions
        rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

        # Get available samplers for this datapack
        available_samplers = df_pd["sampler"].unique()

        # Use consistent ordering, filter to available samplers
        sorted_samplers = [s for s in plot_order if s in available_samplers]

        for sampler in sorted_samplers:
            sampler_data = df_pd[df_pd["sampler"] == sampler]

            if len(sampler_data) == 0:
                continue

            # Get unique_trace_coverage values for each sampling rate
            x_vals = []
            y_vals = []

            for rate in sampling_rates:
                rate_data = sampler_data[sampler_data["sampling_rate"] == rate]
                if len(rate_data) > 0 and "unique_trace_coverage" in rate_data.columns:
                    x_vals.append(rate_positions[rate])
                    y_vals.append(rate_data["unique_trace_coverage"].iloc[0])

            if len(x_vals) == 0:
                continue

            # Plot line with markers - use compact script styling
            display_name = display_names.get(sampler, sampler)
            color = color_scheme.get(sampler, "#666666")
            marker = marker_styles.get(sampler, "o")

            ax.plot(
                x_vals,
                y_vals,
                label=display_name,
                color=color,
                marker=marker,
                markersize=4,
                linewidth=1.8,
                alpha=0.8,
            )

        # Auto-scale y-axis based on actual data range
        if len(df_pd) > 0 and "unique_trace_coverage" in df_pd.columns:
            data_max = df_pd["unique_trace_coverage"].max()

            if data_max <= 0.5:
                y_max = 0.6
            elif data_max <= 1.0:
                y_max = 1.05
            else:
                y_max = data_max * 1.1
        else:
            y_max = 1.05

        setup_axis_formatting(
            ax,
            sampling_rates,
            "Trace Pattern Coverage",
            y_max,
            show_ylabel=(
                idx % 3 == 0
            ),  # Only show for leftmost plots (indices 0 and 3)
        )

        # Add sequence label and title below the plot - match combined
        datapack_display = datapack_display_names.get(datapack, datapack)
        sequence_label = (
            sequence_labels[idx] if idx < len(sequence_labels) else f"({chr(97 + idx)})"
        )
        ax.text(
            0.5,
            -0.21,  # Match combined
            f"{sequence_label} {datapack_display}",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=16,  # Match combined
            fontweight="bold",
        )

    # Use the last subplot position for legend
    legend_ax = axes[-1]
    legend_ax.axis("off")  # Hide the axes

    # Get handles and labels from the first subplot
    if len(selected_datapacks) > 0:
        handles, labels = axes[0].get_legend_handles_labels()
        if handles:
            # Place legend in the center of the last subplot - match combined
            legend_ax.legend(
                handles,
                labels,
                loc="center",
                fontsize=14,  # Match combined
                frameon=True,
                fancybox=True,
                edgecolor="gray",
            )

    # Tight layout with proper spacing - match combined with slightly relaxed spacing
    plt.tight_layout()
    plt.subplots_adjust(
        bottom=0.15, top=0.98, hspace=0.31, wspace=0.2
    )  # hspace: 0.26 + 0.05

    # Save figure
    plt.savefig(
        f"{output_dir}/rq1_cross_system_coverage.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/rq1_cross_system_coverage.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"Multiple datapacks unique trace coverage saved to {output_dir}/rq1_cross_system_coverage.png"
    )
    plt.close()


def plot_datapack_quality(
    df: pl.DataFrame, datapack: str, output_dir: str = "plots/per_datapack"
):
    """Plot quality assessment for a single datapack."""

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Filter data for this datapack
    datapack_df = df.filter(pl.col("datapack") == datapack)
    df_pd = datapack_df.to_pandas()

    if len(df_pd) == 0:
        print(f"No data found for datapack: {datapack}")
        return

    # Get unique sampling rates for this datapack
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    color_scheme = get_algorithm_color_scheme()
    marker_styles = get_marker_styles()
    display_names = get_algorithm_display_names()
    datapack_display_names = get_datapack_display_names()

    # Quality metrics (only trace pattern coverage now)
    quality_metrics = [
        ("unique_trace_coverage", "Trace Pattern Coverage"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in quality_metrics if col in df_pd.columns
    ]

    print(f"\nProcessing datapack: {datapack}")
    print(f"Available quality metrics: {len(available_metrics)}")

    if len(available_metrics) == 0:
        print(f"No quality metrics available for datapack: {datapack}")
        return

    # Set up figure - 5-column layout
    fig, axes = plt.subplots(1, 5, figsize=(20, 4))

    # Use a clean style
    plt.style.use("default")
    fig.patch.set_facecolor("white")

    # Create mapping from sampling rate to evenly spaced positions
    rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

    for idx, (metric_col, metric_name) in enumerate(available_metrics):
        if idx >= len(axes):
            break

        ax = axes[idx]

        # Get available samplers for this datapack
        available_samplers = df_pd["sampler"].unique()

        # Sort samplers for consistent ordering
        sorted_samplers = [
            "gleaner_no_logs_no_ad",
            "tracepicker",
            "trastrainer_no_metrics",
            "sifter",
            "sieve",
            "random",
        ]
        sorted_samplers = [s for s in sorted_samplers if s in available_samplers]

        for sampler in sorted_samplers:
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

            # Plot line with markers - use compact script styling
            display_name = display_names.get(sampler, sampler)
            color = color_scheme.get(sampler, "#666666")
            marker = marker_styles.get(sampler, "o")

            ax.plot(
                x_vals,
                y_vals,
                label=display_name,
                color=color,
                marker=marker,
                markersize=4,  # Match compact script
                linewidth=1.8,  # Match compact script
                alpha=0.8,
            )

        # Formatting
        ax.set_title(metric_name, fontsize=13, fontweight="bold", pad=6)

        # Auto-scale y-axis based on actual data range
        if len(df_pd) > 0 and metric_col in df_pd.columns:
            data_max = df_pd[metric_col].max()
            data_min = df_pd[metric_col].min()

            if data_max <= 0.5:
                y_max = 0.6
            elif data_max <= 1.0:
                y_max = 1.05
            else:
                y_max = data_max * 1.1
        else:
            y_max = 1.05

        setup_axis_formatting(ax, sampling_rates, "Value", y_max)

    # Add legend at the bottom
    if len(available_metrics) > 0:
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.05),
            ncol=len(labels),
            fontsize=13,
            frameon=False,
        )

    # Hide unused subplots
    for idx in range(len(available_metrics), len(axes)):
        axes[idx].remove()

    # Set title for the entire figure - use display name
    datapack_display = datapack_display_names.get(datapack, datapack)
    fig.suptitle(
        f"Quality Assessment - Datapack: {datapack_display}",
        fontsize=16,
        fontweight="bold",
        y=0.95,
    )

    # Tight layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15, top=0.85)

    # Save figure
    safe_datapack_name = datapack.replace("/", "_").replace("\\", "_")
    plt.savefig(
        f"{output_dir}/datapack_{safe_datapack_name}_quality.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/datapack_{safe_datapack_name}_quality.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"Quality assessment for {datapack} saved to {output_dir}/datapack_{safe_datapack_name}_quality.png"
    )
    plt.close()


def generate_datapack_statistics(df: pl.DataFrame, selected_datapacks: list):
    """Generate detailed statistics for each datapack including time range analysis."""

    import json

    print("\n" + "=" * 80)
    print("DATAPACK STATISTICS")
    print("=" * 80)

    datapack_display_names = get_datapack_display_names()

    # Generate markdown table
    md_content = ["# Datapack Statistics\n"]
    md_content.append(
        "| Datapack | Total Traces | Total Unique Traces | Total Entries | Total Events | Total Paths (Dedup) | Duration | Traces/min | Start Time | End Time |"
    )
    md_content.append(
        "|----------|--------------|---------------------|---------------|--------------|---------------------|----------|------------|------------|----------|"
    )

    for datapack in selected_datapacks:
        print(f"\nProcessing statistics for: {datapack}")

        # Filter data for this datapack (get first row with highest sampling rate for totals)
        datapack_df = df.filter(pl.col("datapack") == datapack)
        # Use the random sampler at 10% sampling rate to get total statistics
        datapack_df = datapack_df.filter(pl.col("sampler") == "random").filter(
            pl.col("sampling_rate") == 0.1
        )

        if datapack_df.height == 0:
            print(f"No data found for {datapack}")
            continue

        # Get statistics from the data
        row = datapack_df.row(0, named=True)
        total_traces = row.get("total_traces", "N/A")
        total_unique_traces = row.get("total_unique_traces", "N/A")
        total_entries = row.get("total_entry_types", "N/A")
        total_events = row.get("total_event_pairs", "N/A")
        total_paths_dedup = row.get("total_path_types_dedup", "N/A")

        # Print basic statistics
        print(f"  Total traces: {total_traces}")
        print(f"  Total unique traces: {total_unique_traces}")
        print(f"  Total entries: {total_entries}")
        print(f"  Total events: {total_events}")
        print(f"  Total paths (dedup): {total_paths_dedup}")

        # Load env.json for time information
        env_path = f"/home/nn/workspace/gleaner-rc/data/rcabench-platform-v2/data/tracepicker/{datapack}/env.json"
        duration_str = "N/A"
        traces_per_min = "N/A"
        start_time = "N/A"
        end_time = "N/A"

        try:
            if Path(env_path).exists():
                import datetime

                with open(env_path, "r") as f:
                    env_data = json.load(f)

                normal_start = env_data.get("NORMAL_START", 0)
                normal_end = env_data.get("NORMAL_END", 0)

                # Calculate total duration in minutes (timestamps are in seconds)
                total_duration_sec = normal_end - normal_start
                duration_min = total_duration_sec / 60
                duration_hours = duration_min / 60

                # Format duration based on length
                if duration_hours >= 24:
                    duration_days = duration_hours / 24
                    duration_str = f"{duration_days:.1f} days"
                elif duration_hours >= 1:
                    duration_str = f"{duration_hours:.1f} hours"
                else:
                    duration_str = f"{duration_min:.1f} min"

                # Calculate traces per minute from the last minute of actual data
                traces_per_min = calculate_traces_per_min_from_data(datapack)

                # Format timestamps
                start_dt = datetime.datetime.fromtimestamp(normal_start)
                end_dt = datetime.datetime.fromtimestamp(normal_end)
                start_time = start_dt.strftime("%Y-%m-%d %H:%M")
                end_time = end_dt.strftime("%Y-%m-%d %H:%M")

                print(f"  Duration: {duration_str}")
                print(f"  Traces per minute: {traces_per_min}")
                print(f"  Start: {start_time}")
                print(f"  End: {end_time}")
            else:
                print(f"  env.json not found at {env_path}")
        except Exception as e:
            print(f"  Error reading env.json: {e}")

        # Add to markdown table - use display name
        datapack_display = datapack_display_names.get(datapack, datapack)
        md_content.append(
            f"| {datapack_display} | {total_traces} | {total_unique_traces} | {total_entries} | {total_events} | {total_paths_dedup} | {duration_str} | {traces_per_min} | {start_time} | {end_time} |"
        )

    # Write markdown file
    md_content.append("\n## Notes")
    md_content.append(
        "- Duration calculated from NORMAL_START to NORMAL_END timestamps"
    )
    md_content.append("- Traces/min = Total Traces / Duration")
    md_content.append("- Statistics extracted from 10% sampling rate data")
    md_content.append("- Timestamps are in local time format (YYYY-MM-DD HH:MM)")

    output_file = "plots/datapack_statistics.md"
    with open(output_file, "w") as f:
        f.write("\n".join(md_content))

    print(f"\n📝 Markdown statistics saved to: {output_file}")
    return md_content


def save_datapack_plot_data_to_markdown(
    df: pl.DataFrame, selected_datapacks: list, output_dir: str = "plots"
):
    """Save per-datapack plot data to Markdown format for quantitative analysis."""
    Path(output_dir).mkdir(exist_ok=True)

    display_names = get_algorithm_display_names()
    datapack_display_names = get_datapack_display_names()

    # Define sampler order
    sampler_order = [
        "gleaner_no_logs_no_ad",
        "tracepicker",
        "trastrainer_no_metrics",
        "sifter",
        "sieve",
        "random",
    ]

    # Create markdown content
    md_content = ["# RQ1: Per-Datapack Coverage Data\n"]
    md_content.append(
        "This file contains the exact Trace Pattern Coverage values used in cross-system plots for quantitative analysis.\n"
    )

    for datapack in selected_datapacks:
        # Filter data for this datapack
        datapack_df = df.filter(pl.col("datapack") == datapack)
        df_pd = datapack_df.to_pandas()

        if len(df_pd) == 0:
            continue

        # Get unique sampling rates for this datapack
        sampling_rates = sorted(df_pd["sampling_rate"].unique())

        datapack_display = datapack_display_names.get(datapack, datapack)
        md_content.append(f"\n## {datapack_display}\n")

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
                if len(rate_data) > 0 and "unique_trace_coverage" in rate_data.columns:
                    value = rate_data["unique_trace_coverage"].iloc[0]
                    row += f" {value:.4f} |"
                else:
                    row += " N/A |"

            md_content.append(row)

    # Add comparative analysis section
    md_content.append("\n## Cross-System Comparison at 10% Sampling Rate\n")
    md_content.append("\nComparing algorithm performance across different systems:\n")

    # Create comparison table at 10% sampling rate
    md_content.append(
        "\n| Algorithm | "
        + " | ".join([datapack_display_names.get(dp, dp) for dp in selected_datapacks])
        + " | Average |"
    )
    md_content.append("|-----------|" + "----:|" * (len(selected_datapacks) + 1))

    for sampler in sampler_order:
        row = f"| {display_names.get(sampler, sampler)} |"
        values = []

        for datapack in selected_datapacks:
            datapack_df = df.filter(pl.col("datapack") == datapack)
            df_pd = datapack_df.to_pandas()

            rate_10_data = df_pd[
                (df_pd["sampler"] == sampler) & (df_pd["sampling_rate"] == 0.1)
            ]

            if (
                len(rate_10_data) > 0
                and "unique_trace_coverage" in rate_10_data.columns
            ):
                value = rate_10_data["unique_trace_coverage"].iloc[0]
                row += f" {value:.4f} |"
                values.append(value)
            else:
                row += " N/A |"

        # Add average
        if values:
            avg = sum(values) / len(values)
            row += f" {avg:.4f} |"
        else:
            row += " N/A |"

        md_content.append(row)

    # Add system characteristics summary
    md_content.append("\n## System Characteristics\n")
    md_content.append(
        "\nBrief summary of each system (see datapack_statistics.md for full details):\n"
    )

    for datapack in selected_datapacks:
        datapack_df = df.filter(pl.col("datapack") == datapack)
        datapack_df = datapack_df.filter(pl.col("sampler") == "random").filter(
            pl.col("sampling_rate") == 0.1
        )

        if datapack_df.height > 0:
            row = datapack_df.row(0, named=True)
            datapack_display = datapack_display_names.get(datapack, datapack)
            total_traces = row.get("total_traces", "N/A")
            total_unique = row.get("total_unique_traces", "N/A")

            md_content.append(
                f"\n**{datapack_display}**: {total_traces} total traces, {total_unique} unique patterns"
            )

    # Write to file
    output_file = f"{output_dir}/rq1_cross_system_data.md"
    with open(output_file, "w") as f:
        f.write("\n".join(md_content))

    print(f"Per-datapack plot data saved to {output_file}")


def main():
    """Main function to generate per-datapack quality evaluation figures."""

    parquet_path = "/home/nn/workspace/gleaner-rc/output/rcabench-platform-v2/sampler_reports/tracepicker/detailed_perf.parquet"

    if not Path(parquet_path).exists():
        print(f"Error: Parquet file not found at {parquet_path}")
        return

    print("RQ1: Per-Datapack Unique Trace Coverage Evaluation")
    print("=" * 60)
    print("Loading and filtering data...")
    df = load_datapack_data(parquet_path)

    if df.height == 0:
        print("No data available after filtering!")
        return

    # Get all unique datapacks
    all_datapacks = df["datapack"].unique().to_list()

    print(f"\nFound {len(all_datapacks)} datapacks total")
    print(f"All datapacks: {all_datapacks}")

    # Directly select the 5 datapacks we want
    selected_datapacks = [
        "trainticket",
        "media",
        "onlineBoutique",
        "sockshop",
        "socialNetwork",
    ]

    # Verify all selected datapacks exist in the data
    available_datapacks = []
    for datapack in selected_datapacks:
        if datapack in all_datapacks:
            available_datapacks.append(datapack)
        else:
            print(f"Warning: Datapack '{datapack}' not found in data")

    selected_datapacks = available_datapacks

    print(f"\nSelected 5 datapacks: {selected_datapacks}")
    print(f"Number of selected datapacks: {len(selected_datapacks)}")

    if len(selected_datapacks) == 0:
        print("No datapacks available after filtering!")
        return

    # Create output directory
    output_dir = "plots"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("\nGenerating multi-datapack unique trace coverage figure...")

    # Generate the combined figure
    plot_multiple_datapacks_unique_trace_coverage(df, selected_datapacks, output_dir)

    # Generate detailed statistics
    generate_datapack_statistics(df, selected_datapacks)

    # Save plot data to markdown
    print("\n" + "=" * 60)
    save_datapack_plot_data_to_markdown(df, selected_datapacks, output_dir)

    print("\n" + "=" * 60)
    print("Per-Datapack Unique Trace Coverage Evaluation Complete!")
    print(
        f"\nGenerated combined figure with {len(selected_datapacks)} datapacks (check '{output_dir}' directory)"
    )
    print(
        "Figure shows unique trace coverage across sampling rates for selected datapacks"
    )
    print(f"Selected datapacks: {', '.join(selected_datapacks)}")
    print("📊 Detailed datapack statistics generated in markdown format")
    print("📊 Per-datapack coverage data saved to rq1_cross_system_data.md")

if __name__ == "__main__":
    main()