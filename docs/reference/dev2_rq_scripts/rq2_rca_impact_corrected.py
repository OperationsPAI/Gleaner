#!/usr/bin/env python3
"""
RQ2: Impact on Root Cause Analysis - Generate markdown tables for RCA performance.

This script analyzes the impact of different sampling algorithms on RCA effectiveness
using MRR, AC@1, and AC@3 metrics from three RCA algorithms:
- ShapleyIQ and MicroRCA (from shapleyiq file)
- Nezha (from nezha file)

Target sampling rates: 0.005, 0.01, 0.1
Target metrics: MRR, AC@1, AC@3
"""

import polars as pl
from pathlib import Path
import numpy as np

def load_rca_data(shapleyiq_nezha_path: str, nezha_path: str):
    """Load RCA performance data from both files, correctly parsing algorithms."""

    print("Loading RCA performance data...")

    # Load file containing ShapleyIQ and MicroRCA
    if Path(shapleyiq_nezha_path).exists():
        combined_df = pl.read_parquet(shapleyiq_nezha_path)
        print(f"ShapleyIQ+MicroRCA file shape: {combined_df.shape}")
        print(f"Algorithms in first file: {sorted(combined_df['algorithm'].unique().to_list())}")
    else:
        print(f"Warning: ShapleyIQ+MicroRCA file not found: {shapleyiq_nezha_path}")
        combined_df = pl.DataFrame()

    # Load Nezha file
    if Path(nezha_path).exists():
        nezha_df = pl.read_parquet(nezha_path)
        print(f"Nezha file shape: {nezha_df.shape}")
        print(f"Algorithms in second file: {sorted(nezha_df['algorithm'].unique().to_list())}")
    else:
        print(f"Warning: Nezha file not found: {nezha_path}")
        nezha_df = pl.DataFrame()

    return combined_df, nezha_df

def filter_target_rates_and_algorithms(df: pl.DataFrame, target_rates: list):
    """Filter for target sampling rates and clean algorithm names."""

    if df.height == 0:
        return df

    # Filter for target sampling rates
    filtered_df = df.filter(pl.col("sampler.rate").is_in(target_rates))

    # Clean sampler names (handle potential long names)
    filtered_df = filtered_df.with_columns([
        pl.col("sampler.name").str.replace("trastrainer_no_metrics", "trastrainer_no_met").alias("sampler.name")
    ])

    print(f"Available samplers: {sorted(filtered_df['sampler.name'].unique().to_list())}")
    print(f"Available rates: {sorted(filtered_df['sampler.rate'].unique().to_list())}")

    return filtered_df

def calculate_algorithm_averages(df: pl.DataFrame, filter_algorithm: str = None):
    """Calculate average performance across sampling rates for each sampler and algorithm."""

    if df.height == 0:
        return pl.DataFrame()

    # Filter by algorithm if specified
    if filter_algorithm:
        df = df.filter(pl.col("algorithm") == filter_algorithm)

    # Group by algorithm, sampler and rate, then calculate means
    result = df.group_by(["algorithm", "sampler.name", "sampler.rate"]).agg([
        pl.col("AC@1").mean().alias("AC@1"),
        pl.col("AC@3").mean().alias("AC@3")
    ])

    return result

def create_markdown_table(combined_df: pl.DataFrame, nezha_df: pl.DataFrame):
    """Create a comprehensive markdown table for RQ2."""

    print("\nGenerating RQ2 markdown table...")

    # Target sampling rates
    target_rates = [0.005, 0.01, 0.1]

    # Process datasets
    combined_filtered = filter_target_rates_and_algorithms(combined_df, target_rates)
    nezha_filtered = filter_target_rates_and_algorithms(nezha_df, target_rates)

    # Calculate averages for each algorithm
    combined_avg = calculate_algorithm_averages(combined_filtered)  # Contains both shapleyiq and microrca
    nezha_avg = calculate_algorithm_averages(nezha_filtered)  # Contains nezha

    # Combine all data
    all_data = []
    if combined_avg.height > 0:
        all_data.append(combined_avg)
    if nezha_avg.height > 0:
        all_data.append(nezha_avg)

    if not all_data:
        print("No data available for markdown table generation!")
        return

    final_df = pl.concat(all_data)

    # Convert to pandas for easier manipulation
    final_pd = final_df.to_pandas()

    # Get all unique values
    algorithms = sorted(final_pd['algorithm'].unique())
    samplers = sorted(final_pd['sampler.name'].unique())
    rates = sorted(final_pd['sampler.rate'].unique())

    print(f"RCA Algorithms: {algorithms}")
    print(f"Samplers: {samplers}")
    print(f"Rates: {rates}")

    # Generate markdown content
    markdown_content = []

    # Header
    markdown_content.append("# RQ2: Impact on Root Cause Analysis")
    markdown_content.append("")
    markdown_content.append("This table shows the performance of different sampling algorithms on RCA effectiveness.")
    markdown_content.append(f"**Sampling Rates**: {', '.join([f'{r:.3f}' for r in rates])}")
    markdown_content.append(f"**Metrics**: MRR (Mean Reciprocal Rank), AC@1 (Accuracy@1), AC@3 (Accuracy@3)")
    markdown_content.append(f"**RCA Algorithms**: {', '.join(algorithms)}")
    markdown_content.append("")

    # Create table for each RCA algorithm
    for algorithm in algorithms:
        # Format algorithm name for display
        display_name = algorithm.replace('_', ' ').title()
        markdown_content.append(f"## {display_name} Results")
        markdown_content.append("")

        # Table header
        header = "| Sampler | Rate |  AC@1 | AC@3 |"
        separator = "|---------|-----|------|------|"
        markdown_content.append(header)
        markdown_content.append(separator)

        # Filter data for this RCA algorithm
        alg_data = final_pd[final_pd['algorithm'] == algorithm]

        # Sort by sampler name and rate
        alg_data = alg_data.sort_values(['sampler.name', 'sampler.rate'])

        # Add rows
        for _, row in alg_data.iterrows():
            sampler = row['sampler.name']
            rate = f"{row['sampler.rate']:.3f}"
            ac1 = f"{row['AC@1']:.4f}" if not np.isnan(row['AC@1']) else "N/A"
            ac3 = f"{row['AC@3']:.4f}" if not np.isnan(row['AC@3']) else "N/A"

            table_row = f"| {sampler} | {rate} | {ac1} | {ac3} |"
            markdown_content.append(table_row)

        markdown_content.append("")

    # Summary section
    markdown_content.append("## Summary")
    markdown_content.append("")

    # Calculate best performers for each metric and algorithm
    for algorithm in algorithms:
        alg_data = final_pd[final_pd['algorithm'] == algorithm]
        display_name = algorithm.replace('_', ' ').title()

        if len(alg_data) > 0:
            markdown_content.append(f"### {display_name} Best Performers")

            # For each rate, find best performers
            for rate in rates:
                rate_data = alg_data[alg_data['sampler.rate'] == rate]

                if len(rate_data) > 0:
                    markdown_content.append(f"**Rate {rate:.3f}:**")


                    # Best AC@1
                    best_ac1 = rate_data.loc[rate_data['AC@1'].idxmax()]
                    markdown_content.append(f"- Best AC@1: {best_ac1['sampler.name']} ({best_ac1['AC@1']:.4f})")

                    # Best AC@3
                    best_ac3 = rate_data.loc[rate_data['AC@3'].idxmax()]
                    markdown_content.append(f"- Best AC@3: {best_ac3['sampler.name']} ({best_ac3['AC@3']:.4f})")

                    markdown_content.append("")

    # Cross-algorithm comparison
    markdown_content.append("## Cross-Algorithm Performance Comparison")
    markdown_content.append("")

    # Find best performing sampler-rate combination for each metric across all algorithms
    markdown_content.append("### Overall Best Performers Across All RCA Algorithms")
    markdown_content.append("")

    for metric in [ 'AC@1', 'AC@3']:
        best_overall = final_pd.loc[final_pd[metric].idxmax()]
        alg_name = best_overall['algorithm'].replace('_', ' ').title()
        markdown_content.append(f"**Best {metric}**: {best_overall['sampler.name']} @ rate {best_overall['sampler.rate']:.3f} "
                               f"with {alg_name} ({best_overall[metric]:.4f})")

    markdown_content.append("")

    # Write to file
    output_file = "rq2_rca_impact_results_corrected.md"
    with open(output_file, 'w') as f:
        f.write('\n'.join(markdown_content))

    # Also print to console
    print("\n" + "="*60)
    print("RQ2: Root Cause Analysis Impact Results (CORRECTED)")
    print("="*60)
    for line in markdown_content:
        print(line)

    print(f"\nMarkdown table saved to: {output_file}")

def main():
    """Main function to generate RQ2 RCA impact analysis."""

    shapleyiq_microrca_path = "/home/nn/workspace/gleaner-rc/rca/shapleyiq/sampler.grouped.perf.parquet"
    nezha_path = "/home/nn/workspace/gleaner-rc/rca/nezha/sampler.grouped.perf.parquet"

    print("RQ2: Impact on Root Cause Analysis (CORRECTED)")
    print("=" * 60)
    print("Target sampling rates: 0.005, 0.01, 0.1")
    print("Target metrics: MRR, AC@1, AC@3")
    print("RCA algorithms: ShapleyIQ, MicroRCA, Nezha")

    # Load data
    combined_df, nezha_df = load_rca_data(shapleyiq_microrca_path, nezha_path)

    # Generate markdown table
    create_markdown_table(combined_df, nezha_df)

    print("\nRQ2 analysis complete!")

if __name__ == "__main__":
    main()
