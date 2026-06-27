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
        "gleaner_no_ad": "Gleaner w/o AD",
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
        "gleaner_no_logs": "-",  # Solid but different color
        "gleaner_no_ad": "-",  # Solid but different color
        "gleaner_pure_diversity": "-",  # Solid but different color
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


def generate_rq3_markdown_table(df: pl.DataFrame, output_dir: str = "tables"):
    """Generate RQ3 ablation study markdown table with overview metrics."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Overview metrics (same as the combined overview plot)
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

    print("\nRQ3: Generating Markdown Table")
    print(f"Available overview metrics: {len(available_metrics)}")
    for col, name in available_metrics:
        print(f"  - {name} ({col})")

    if len(available_metrics) == 0:
        print("No overview metrics available!")
        return

    # Get display names
    display_names = get_rq3_algorithm_display_names()

    # Algorithm ordering: random, pure diversity, wo log, wo ad, gleaner (bottom to top)
    algorithm_order = [
        "random",
        "gleaner_pure_diversity",
        "gleaner_no_logs",
        "gleaner_no_ad",
        "gleaner",
    ]

    # Calculate average values across all sampling rates for each algorithm
    algorithm_data = {}

    for algorithm in algorithm_order:
        if algorithm in df_pd["sampler"].values:
            alg_data = df_pd[df_pd["sampler"] == algorithm]
            algorithm_data[algorithm] = {}

            for metric_col, metric_name in available_metrics:
                # Calculate mean across all sampling rates
                avg_value = alg_data[metric_col].mean()
                algorithm_data[algorithm][metric_col] = avg_value

    # Generate markdown table
    markdown_lines = []

    # Table header
    header_line = "| Algorithm |"
    separator_line = "|-----------|"

    for _, metric_name in available_metrics:
        header_line += f" {metric_name} |"
        separator_line += "-----------|"

    markdown_lines.append(header_line)
    markdown_lines.append(separator_line)

    # Table rows (in specified order)
    for algorithm in algorithm_order:
        if algorithm in algorithm_data:
            display_name = display_names.get(algorithm, algorithm)
            row_line = f"| {display_name} |"

            for metric_col, _ in available_metrics:
                value = algorithm_data[algorithm][metric_col]
                # Format values with 3 decimal places
                row_line += f" {value:.3f} |"

            markdown_lines.append(row_line)

    # Join all lines
    markdown_table = "\n".join(markdown_lines)

    # Print to console
    print("\nRQ3 Ablation Study - Overview Metrics Table")
    print("=" * 60)
    print(markdown_table)

    # Save to file
    output_file = Path(output_dir) / "rq3_ablation_table.md"
    with open(output_file, "w") as f:
        f.write("# RQ3 Ablation Study - Overview Metrics\n\n")
        f.write("Average performance across all sampling rates:\n\n")
        f.write(markdown_table)
        f.write("\n\n")
        f.write("**Note**: Values are averaged across all sampling rates. ")
        f.write("Gleaner (full version) is shown at the bottom for easy comparison.\n")

    print(f"\nMarkdown table saved to: {output_file}")

    return markdown_table


def main():
    """Main function to generate RQ3 ablation study table."""

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

    print("\nGenerating RQ3 ablation study markdown table...")
    print("Algorithms: random -> pure diversity -> wo logs -> wo ad -> gleaner")
    print(
        "Metrics: API Coverage, Unique Trace Coverage, Shannon Entropy, Proportion Anomaly"
    )

    # Generate markdown table
    print("\n" + "=" * 60)
    generate_rq3_markdown_table(df)

    print("\n" + "=" * 60)
    print("RQ3 Ablation Study Complete!")
    print("\nGenerated markdown table (check 'tables' directory):")
    print("- rq3_ablation_table.md")
    print("\nTable shows average performance across all sampling rates.")
    print("Gleaner variants ordered from baseline to full version (bottom).")


if __name__ == "__main__":
    main()
