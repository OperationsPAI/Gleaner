#!/usr/bin/env python3
"""
RQ3: Ablation Study - Compare Gleaner variants with baseline algorithms.

This script evaluates the impact of different Gleaner components by comparing:
- Gleaner (full version)
- Gleaner variants (4 variants including pure diversity)
- Random (baseline)

Uses the same quality metrics as RQ1:
1. Coverage: API coverage, path dedup coverage, event pair coverage, unique trace coverage
2. Diversity: Shannon entropy
3. Anomaly Detection: proportion rare, proportion anomaly, avg sampled anomaly score

All evaluations use offline mode data across all sampling rates.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl


def load_and_filter_data_rq3(parquet_path: str):
    """Load aggregated performance data and filter for RQ3 algorithms only."""
    df = pl.read_parquet(parquet_path)

    # Filter for offline mode and RQ3 specific algorithms - 5 algorithms including pure diversity
    rq3_algorithms = [
        "gleaner",
        "gleaner_no_logs",
        "gleaner_no_ad",
        "gleaner_pure_diversity",
        "random",
    ]

    offline_df = (
        df.filter(pl.col("mode") == "offline")
        .filter(pl.col("sampler").is_in(rq3_algorithms))
        .filter(pl.col("sampling_rate") != 0.005)
    )

    print("Available columns:")
    print(offline_df.columns)

    print(f"\nData shape: {offline_df.shape}")
    print(f"\nSamplers: {offline_df['sampler'].unique().to_list()}")
    print(f"Sampling rates: {sorted(offline_df['sampling_rate'].unique().to_list())}")

    return offline_df


def get_rq3_algorithm_display_names():
    """Get display names for RQ3 algorithms."""
    display_names = {
        "gleaner": "Gleaner",
        "gleaner_no_logs": "Gleaner w/o Logs",
        "gleaner_no_ad": "Gleaner w/o Alarms",
        "gleaner_pure_diversity": "Gleaner Pure Diversity",
        "random": "Random",
    }
    return display_names


def get_rq3_algorithm_color_scheme():
    """Get color scheme for RQ3 algorithms with improved distinction between variants."""
    algorithm_colors = {
        # Main Gleaner - strong blue
        "gleaner": "#1f77b4",
        # Gleaner variants - distinct colors
        "gleaner_no_logs": "#ff7f0e",  # Orange - high contrast
        "gleaner_no_ad": "#2ca02c",  # Green - high contrast
        "gleaner_pure_diversity": "#d62728",  # Red - high contrast
        # Baseline - black for maximum contrast
        "random": "#000000",
    }
    return algorithm_colors


def get_rq3_line_styles():
    """Get line styles for RQ3 algorithms with better distinction."""
    line_styles = {
        # Main Gleaner - solid
        "gleaner": "-",
        # Gleaner variants - solid lines for better visibility
        "gleaner_no_logs": "--",  # Solid but different color
        "gleaner_no_ad": "--",  # Solid but different color
        "gleaner_pure_diversity": "-.",  # Solid but different color
        # Baseline - dashed for distinction
        "random": "--",
    }
    return line_styles


def setup_axis_formatting_rq3(ax, sampling_rates, y_label="Value", y_max=None):
    """Set up proper axis formatting with evenly spaced sampling rates for RQ3."""
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
        y_max = 1.05
    ax.set_ylim(0, y_max)

    # Labels
    ax.set_xlabel("Sampling Rate (%)", fontsize=10)
    ax.set_ylabel(y_label, fontsize=10)

    # Improve grid
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)


def plot_rq3_combined_overview(df: pl.DataFrame, output_dir: str = "plots"):
    """Plot RQ3: Combined Overview for Ablation Study with 2x2 layout."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    color_scheme = get_rq3_algorithm_color_scheme()
    line_styles = get_rq3_line_styles()
    display_names = get_rq3_algorithm_display_names()

    # Select key metrics for overview
    overview_metrics = [
        ("avg_api_coverage", "API Coverage"),
        ("avg_unique_trace_coverage", "Trace Pattern Coverage"),
        ("avg_shannon_entropy", "Shannon Entropy"),
        ("avg_proportion_anomaly", "Proportion Anomaly"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in overview_metrics if col in df_pd.columns
    ]

    print("\nRQ3: Combined Overview Ablation Study")
    print(f"Available overview metrics: {len(available_metrics)}")
    for col, name in available_metrics:
        print(f"  - {name} ({col})")

    if len(available_metrics) == 0:
        print("No overview metrics available!")
        return

    # Set up figure - 2x2 layout matching RQ1 style, adjust size to be similar to RQ1 combined
    fig, axes = plt.subplots(
        2, 2, figsize=(8, 8)
    )  # Changed from (8, 7.5) to (8, 8) for more square shape
    axes = axes.flatten()

    # Use a clean style to match RQ1
    plt.style.use("default")
    fig.patch.set_facecolor("white")

    # Create mapping from sampling rate to evenly spaced positions
    rate_positions = {rate: i for i, rate in enumerate(sampling_rates)}

    # Sequence labels for subplots - add parentheses
    sequence_labels = ["(a)", "(b)", "(c)", "(d)"]

    # Define plot order matching RQ1 style - reverse order so gleaner is drawn last
    plot_order = [
        "random",
        "gleaner_pure_diversity",
        "gleaner_no_logs",
        "gleaner_no_ad",
        "gleaner",
    ]

    for idx, (metric_col, metric_name) in enumerate(available_metrics):
        if idx >= len(axes):
            break

        ax = axes[idx]

        # Get available samplers
        all_samplers = df_pd["sampler"].unique()

        # Use consistent ordering, filter to available samplers
        sorted_samplers = [s for s in plot_order if s in all_samplers]

        for sampler in sorted_samplers:
            sampler_data = df_pd[df_pd["sampler"] == sampler].sort_values(
                "sampling_rate"
            )

            if len(sampler_data) > 0:
                color = color_scheme.get(sampler, "#333333")
                linestyle = line_styles.get(sampler, "-")
                display_name = display_names.get(sampler, sampler)

                # Match RQ1 styling - consistent line width and marker size
                line_width = 1.8
                marker_size = 4

                if sampler == "gleaner":
                    alpha = 0.8
                    marker = "o"
                elif sampler == "random":
                    alpha = 0.8
                    marker = "X"
                else:
                    alpha = 0.8
                    variant_markers = {
                        "gleaner_no_logs": "s",
                        "gleaner_no_ad": "^",
                        "gleaner_pure_diversity": "D",
                    }
                    marker = variant_markers.get(sampler, "s")

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
                )

        # Convert sampling rates to percentages and sort
        rate_percentages = sorted([rate * 100 for rate in sampling_rates])
        x_positions_axis = range(len(rate_percentages))

        # Set x-axis ticks to evenly spaced positions - larger font
        ax.set_xticks(x_positions_axis)
        ax.set_xticklabels([f"{rate:.1f}%" for rate in rate_percentages], fontsize=14)

        # Set reasonable axis limits
        ax.set_xlim(-0.2, len(rate_percentages) - 0.8)

        # Auto-scale y-axis with adaptive scaling
        data_max = df_pd[metric_col].max()

        # Special handling for proportion_anomaly
        if "proportion_anomaly" in metric_col:
            y_max = 0.3  # Cap at 0.3 for proportion_anomaly
        elif "coverage" in metric_col.lower() or "proportion" in metric_col.lower():
            if data_max <= 0.5:
                y_max = min(1.05, data_max * 1.2)
            else:
                y_max = 1.05
        else:
            if data_max > 0:
                if data_max <= 0.5:
                    y_max = data_max * 1.2
                else:
                    y_max = data_max * 1.1
            else:
                y_max = 1.0

        ax.set_ylim(0, y_max)

        # Labels - larger font, remove "Value" from y-axis
        ax.set_xlabel("Sampling Rate (%)", fontsize=16)
        ax.set_ylabel("", fontsize=16)  # Empty y-axis label

        # Grid matching RQ1 style
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

    # Get handles and labels from the first subplot
    handles, labels = axes[0].get_legend_handles_labels()

    # Calculate ncol for 2 rows
    ncol = (len(labels) + 1) // 2

    # Add legend at the bottom with adjusted position - smaller font than title
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.03),  # More space from titles (was -0.06)
        ncol=ncol,
        fontsize=14,  # Smaller than title font (was 16)
        frameon=True,
        fancybox=True,
        edgecolor="gray",
    )

    # Tight layout with adjusted spacing
    plt.tight_layout()
    plt.subplots_adjust(
        bottom=0.18, top=0.98, hspace=0.35, wspace=0.25
    )  # Increased bottom margin

    # Save figures
    plt.savefig(
        f"{output_dir}/rq3_overview_ablation.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        f"{output_dir}/rq3_overview_ablation.pdf",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(
        f"RQ3 overview ablation saved to {output_dir}/rq3_overview_ablation.png and .pdf"
    )
    plt.close()


def save_rq3_data_to_markdown(df: pl.DataFrame, output_dir: str = "plots"):
    """Save RQ3 plot data to Markdown format for quantitative analysis."""
    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    display_names = get_rq3_algorithm_display_names()

    # Select key metrics for overview
    overview_metrics = [
        ("avg_api_coverage", "API Coverage"),
        ("avg_unique_trace_coverage", "Trace Pattern Coverage"),
        ("avg_shannon_entropy", "Shannon Entropy"),
        ("avg_proportion_anomaly", "Proportion Anomaly"),
    ]

    # Filter available metrics
    available_metrics = [
        (col, name) for col, name in overview_metrics if col in df_pd.columns
    ]

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())

    # Define sampler order
    sampler_order = [
        "gleaner",
        "gleaner_no_logs",
        "gleaner_no_ad",
        "gleaner_pure_diversity",
        "random",
    ]

    # Create markdown content
    md_content = ["# RQ3: Ablation Study Data\n"]
    md_content.append(
        "This file contains the exact values used in RQ3 plots for quantitative analysis.\n"
    )
    md_content.append(
        "\nCompares Gleaner variants to evaluate the impact of different components.\n"
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

    # Add improvement analysis section
    md_content.append("\n## Improvement Analysis\n")
    md_content.append(
        "Comparing Gleaner variants against baseline (Random) at 10% sampling rate:\n"
    )

    # Get 10% sampling rate data
    rate_10_data = df_pd[df_pd["sampling_rate"] == 0.1]

    if len(rate_10_data) > 0:
        random_data = rate_10_data[rate_10_data["sampler"] == "random"]

        if len(random_data) > 0:
            md_content.append("\n| Metric | Random | Gleaner | Improvement |")
            md_content.append("|--------|--------|---------|-------------|")

            for metric_col, metric_name in available_metrics:
                if metric_col not in rate_10_data.columns:
                    continue

                random_val = random_data[metric_col].iloc[0]
                gleaner_data = rate_10_data[rate_10_data["sampler"] == "gleaner"]

                if len(gleaner_data) > 0:
                    gleaner_val = gleaner_data[metric_col].iloc[0]
                    improvement = ((gleaner_val - random_val) / random_val) * 100
                    md_content.append(
                        f"| {metric_name} | {random_val:.4f} | {gleaner_val:.4f} | {improvement:+.2f}% |"
                    )

    # Write to file
    output_file = f"{output_dir}/rq3_data.md"
    with open(output_file, "w") as f:
        f.write("\n".join(md_content))

    print(f"RQ3 plot data saved to {output_file}")


def main():
    """Main function to generate RQ3 ablation study figures."""

    parquet_path = "/home/nn/workspace/gleaner-rc/output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet"

    if not Path(parquet_path).exists():
        print(f"Error: File not found: {parquet_path}")
        return

    print("RQ3: Ablation Study - Gleaner Component Analysis")
    print("=" * 60)
    print("Loading and filtering data...")
    df = load_and_filter_data_rq3(parquet_path)

    if df.height == 0:
        print("No data found for RQ3 algorithms!")
        return

    print("\nGenerating RQ3 ablation study figures...")
    print(
        "Algorithms: gleaner + gleaner_no_logs + gleaner_no_ad + gleaner_pure_diversity + random"
    )
    print("Quality dimensions: Coverage, Diversity, Anomaly Detection")
    print("Improved visual distinction: different colors and markers for each variant")

    print("\n" + "=" * 60)
    plot_rq3_combined_overview(df)

    # Save plot data to markdown
    print("\n" + "=" * 60)
    save_rq3_data_to_markdown(df)

    print("\n" + "=" * 60)
    print("RQ3 Ablation Study Complete!")
    print("\nGenerated ablation study figures (check 'plots' directory):")

    print("- rq3_overview_ablation.png/pdf")
    print("- rq3_data.md (quantitative data)")
    print(
        "\nFigures show impact of removing logs, AD, or using pure diversity vs. Random baseline."
    )


if __name__ == "__main__":
    main()
