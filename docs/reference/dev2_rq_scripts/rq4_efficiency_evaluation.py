#!/usr/bin/env python3
"""
RQ4: Efficiency Evaluation - Generate efficiency assessment for sampling algorithms.

This script evaluates sampling efficiency across four key dimensions:
1. Runtime per trace (ms)
2. Benefit-cost ratio
3. Actual sampling rate
4. Controllability

Target configuration: sampling_rate=0.05, mode=online
Target algorithms: gleaner, tracepicker, trastrainer, trastrainer w/o metrics, sifter, sieve, random
"""

from pathlib import Path

import polars as pl


def load_and_filter_efficiency_data(parquet_path: str):
    """Load aggregated performance data and filter for online mode and 0.05 sampling rate."""

    print("Loading efficiency data...")
    df = pl.read_parquet(parquet_path)

    print(f"Original data shape: {df.shape}")
    print("Available columns:")
    print(df.columns)

    # Filter for online mode and 0.05 sampling rate
    target_algorithms = [
        "gleaner",
        "tracepicker",
        "trastrainer",
        "trastrainer_no_metrics",
        "sifter",
        "sieve",
        "random",
    ]

    filtered_df = df.filter(
        (pl.col("mode") == "online")
        & (pl.col("sampling_rate") == 0.05)
        & (pl.col("sampler").is_in(target_algorithms))
    )

    print(f"\nFiltered data shape: {filtered_df.shape}")
    print(f"Available samplers: {sorted(filtered_df['sampler'].unique().to_list())}")
    print(f"Sampling rates: {sorted(filtered_df['sampling_rate'].unique().to_list())}")
    print(f"Modes: {sorted(filtered_df['mode'].unique().to_list())}")

    return filtered_df


def get_algorithm_display_names():
    """Get display names for algorithms."""
    return {
        "gleaner": "Gleaner",
        "tracepicker": "TracePicker",
        "trastrainer": "TrasTrainer",
        "trastrainer_no_metrics": "TrasTrainer w/o Metrics",
        "sifter": "Sifter",
        "sieve": "Sieve",
        "random": "Random",
    }


def calculate_efficiency_metrics(df: pl.DataFrame):
    """Calculate aggregated efficiency metrics for each algorithm."""

    # Define efficiency metrics to analyze (with avg_ prefix from the data)
    efficiency_metrics = [
        "avg_runtime_per_trace_ms",
        "avg_benefit_cost_ratio",
        "avg_actual_sampling_rate",
        "avg_controllability",
    ]

    # Check which metrics are available
    available_metrics = [
        metric for metric in efficiency_metrics if metric in df.columns
    ]
    missing_metrics = [
        metric for metric in efficiency_metrics if metric not in df.columns
    ]

    print(f"Available efficiency metrics: {available_metrics}")
    if missing_metrics:
        print(f"Missing efficiency metrics: {missing_metrics}")

    if not available_metrics:
        print("No efficiency metrics found! Available columns:")
        print(df.columns)
        return pl.DataFrame(), []

    # Since the data is already aggregated, we just need to select the relevant columns
    # Group by sampler and get the values (should be one row per sampler already)
    result = df.select(["sampler"] + available_metrics)

    return result, available_metrics


def create_efficiency_markdown_table(df: pl.DataFrame, available_metrics: list):
    """Create a comprehensive markdown table for RQ4 efficiency evaluation."""

    print("\nGenerating RQ4 efficiency markdown table...")

    if df.height == 0:
        print("No data available for efficiency table generation!")
        return

    # Convert to pandas for easier manipulation
    df_pd = df.to_pandas()
    display_names = get_algorithm_display_names()

    # Generate markdown content
    markdown_content = []

    # Header
    markdown_content.append("# RQ4: Efficiency Evaluation")
    markdown_content.append("")
    markdown_content.append(
        "This table shows the efficiency performance of different sampling algorithms."
    )
    markdown_content.append("**Configuration**: Sampling Rate = 0.05, Mode = Online")
    markdown_content.append(
        f"**Metrics**: {', '.join([m.replace('avg_', '') for m in available_metrics])}"
    )
    markdown_content.append("")

    # Create main efficiency table
    markdown_content.append("## Efficiency Performance Summary")
    markdown_content.append("")

    # Build table header
    header_parts = ["| Algorithm |"]
    separator_parts = ["|-----------|"]

    for metric in available_metrics:
        # Format metric name for display (remove avg_ prefix)
        display_metric = metric.replace("avg_", "").replace("_", " ").title()
        header_parts.append(f" {display_metric} |")
        separator_parts.append("------------|")

    header = "".join(header_parts)
    separator = "".join(separator_parts)

    markdown_content.append(header)
    markdown_content.append(separator)

    # Sort algorithms by name for consistent ordering
    df_pd = df_pd.sort_values("sampler")

    # Add rows
    for _, row in df_pd.iterrows():
        sampler = row["sampler"]
        display_name = display_names.get(sampler, sampler)

        row_parts = [f"| {display_name} |"]

        for metric in available_metrics:
            val = row[metric]

            if pd.isna(val):
                formatted_val = "N/A"
            else:
                if "runtime_per_trace_ms" in metric:
                    # Show in milliseconds with 3 decimal places
                    formatted_val = f"{val:.3f}"
                elif "actual_sampling_rate" in metric:
                    # Show as percentage
                    formatted_val = f"{val:.1%}"
                elif "benefit_cost_ratio" in metric:
                    # Show ratio with 2 decimal places
                    formatted_val = f"{val:.2f}"
                elif "controllability" in metric:
                    # Show with 4 decimal places
                    formatted_val = f"{val:.4f}"
                else:
                    # Default formatting
                    formatted_val = f"{val:.4f}"

            row_parts.append(f" {formatted_val} |")

        table_row = "".join(row_parts)
        markdown_content.append(table_row)

    markdown_content.append("")

    # Analysis section
    markdown_content.append("## Performance Analysis")
    markdown_content.append("")

    # Find best and worst performers for each metric
    for metric in available_metrics:
        display_metric = metric.replace("avg_", "").replace("_", " ").title()

        # Skip if all values are NaN
        if df_pd[metric].isna().all():
            continue

        markdown_content.append(f"### {display_metric}")
        markdown_content.append("")

        # Best performer (depends on metric)
        if "runtime_per_trace_ms" in metric:
            # Lower is better for runtime
            best_idx = df_pd[metric].idxmin()
            worst_idx = df_pd[metric].idxmax()
            best_label = "Fastest"
            worst_label = "Slowest"
        else:
            # Higher is better for other metrics
            best_idx = df_pd[metric].idxmax()
            worst_idx = df_pd[metric].idxmin()
            best_label = "Best"
            worst_label = "Worst"

        if not pd.isna(best_idx):
            best_row = df_pd.loc[best_idx]
            best_name = display_names.get(best_row["sampler"], best_row["sampler"])
            best_val = best_row[metric]

            if "runtime_per_trace_ms" in metric:
                markdown_content.append(
                    f"**{best_label}**: {best_name} ({best_val:.3f} ms)"
                )
            elif "actual_sampling_rate" in metric:
                markdown_content.append(
                    f"**{best_label}**: {best_name} ({best_val:.1%})"
                )
            else:
                markdown_content.append(
                    f"**{best_label}**: {best_name} ({best_val:.4f})"
                )

        if not pd.isna(worst_idx):
            worst_row = df_pd.loc[worst_idx]
            worst_name = display_names.get(worst_row["sampler"], worst_row["sampler"])
            worst_val = worst_row[metric]

            if "runtime_per_trace_ms" in metric:
                markdown_content.append(
                    f"**{worst_label}**: {worst_name} ({worst_val:.3f} ms)"
                )
            elif "actual_sampling_rate" in metric:
                markdown_content.append(
                    f"**{worst_label}**: {worst_name} ({worst_val:.1%})"
                )
            else:
                markdown_content.append(
                    f"**{worst_label}**: {worst_name} ({worst_val:.4f})"
                )

        markdown_content.append("")

    # Overall efficiency ranking
    markdown_content.append("## Overall Efficiency Ranking")
    markdown_content.append("")
    markdown_content.append(
        "**Ranking methodology**: Combined score considering all metrics"
    )
    markdown_content.append(
        "(Lower runtime is better, higher values are better for other metrics)"
    )
    markdown_content.append("")

    # Simple ranking based on available metrics
    if len(available_metrics) > 1:
        # Normalize metrics (0-1 scale) and combine
        df_rank = df_pd.copy()

        for metric in available_metrics:
            if not df_rank[metric].isna().all():
                if "runtime_per_trace_ms" in metric:
                    # Invert for runtime (lower is better)
                    df_rank[f"{metric}_norm"] = 1 - (
                        df_rank[metric] - df_rank[metric].min()
                    ) / (df_rank[metric].max() - df_rank[metric].min())
                else:
                    # Higher is better for other metrics
                    df_rank[f"{metric}_norm"] = (
                        df_rank[metric] - df_rank[metric].min()
                    ) / (df_rank[metric].max() - df_rank[metric].min())

        # Calculate combined score
        norm_cols = [f"{metric}_norm" for metric in available_metrics]
        df_rank["combined_score"] = df_rank[norm_cols].mean(axis=1)
        df_rank = df_rank.sort_values("combined_score", ascending=False)

        for i, (_, row) in enumerate(df_rank.iterrows(), 1):
            sampler_name = display_names.get(row["sampler"], row["sampler"])
            score = row["combined_score"]
            markdown_content.append(f"{i}. **{sampler_name}** (Score: {score:.3f})")

    markdown_content.append("")

    # Write to file
    output_file = "rq4_efficiency_results.md"
    with open(output_file, "w") as f:
        f.write("\n".join(markdown_content))

    # Also print to console
    print("\n" + "=" * 60)
    print("RQ4: Efficiency Evaluation Results")
    print("=" * 60)
    for line in markdown_content:
        print(line)

    print(f"\nMarkdown table saved to: {output_file}")


def main():
    """Main function to generate RQ4 efficiency analysis."""

    # Path to aggregated performance data
    parquet_path = "/home/nn/workspace/gleaner-rc/output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet"

    print("RQ4: Efficiency Evaluation")
    print("=" * 60)
    print("Target configuration: sampling_rate=0.05, mode=online")
    print(
        "Target metrics: runtime_per_trace_ms, benefit_cost_ratio, actual_sampling_rate, controllability"
    )
    print(
        "Target algorithms: gleaner, tracepicker, trastrainer, trastrainer w/o metrics, sifter, sieve, random"
    )

    # Check if file exists
    if not Path(parquet_path).exists():
        print(f"Error: Data file not found: {parquet_path}")
        return

    # Load and filter data
    df = load_and_filter_efficiency_data(parquet_path)

    if df.height == 0:
        print("No data found for the specified configuration!")
        return

    # Calculate efficiency metrics
    result_df, available_metrics = calculate_efficiency_metrics(df)

    if result_df.height == 0:
        print("No efficiency metrics could be calculated!")
        return

    # Generate markdown table
    create_efficiency_markdown_table(result_df, available_metrics)

    print("\nRQ4 efficiency analysis complete!")


if __name__ == "__main__":
    # Add pandas import for formatting
    import pandas as pd

    main()
