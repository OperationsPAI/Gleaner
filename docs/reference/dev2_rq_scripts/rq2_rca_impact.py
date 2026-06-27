#!/usr/bin/env python3
"""
RQ2: Impact on Root Cause Analysis - Generate markdown tables for RCA performance.

This script analyzes the impact of different sampling algorithms on RCA effectiveness
using MRR, AC@1, and AC@3 metrics from both ShapleyIQ and Nezha algorithms.

Target sampling rates: 0.005, 0.01, 0.1
Target metrics: MRR, AC@1, AC@3
"""

import polars as pl
from pathlib import Path
import numpy as np

def load_rca_data(shapleyiq_path: str, nezha_path: str):
    """Load RCA performance data from both algorithms."""

    print("Loading RCA performance data...")

    # Load ShapleyIQ data
    if Path(shapleyiq_path).exists():
        shapleyiq_df = pl.read_parquet(shapleyiq_path)
        print(f"ShapleyIQ data shape: {shapleyiq_df.shape}")
    else:
        print(f"Warning: ShapleyIQ file not found: {shapleyiq_path}")
        shapleyiq_df = pl.DataFrame()

    # Load Nezha data
    if Path(nezha_path).exists():
        nezha_df = pl.read_parquet(nezha_path)
        print(f"Nezha data shape: {nezha_df.shape}")
    else:
        print(f"Warning: Nezha file not found: {nezha_path}")
        nezha_df = pl.DataFrame()

    return shapleyiq_df, nezha_df

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

def calculate_algorithm_averages(df: pl.DataFrame, algorithm_name: str):
    """Calculate average performance across sampling rates for each sampler."""

    if df.height == 0:
        return pl.DataFrame()

    # Group by sampler and rate, then calculate means
    result = df.group_by(["sampler.name", "sampler.rate"]).agg([
        pl.col("MRR").mean().alias("MRR"),
        pl.col("AC@1").mean().alias("AC@1"),
        pl.col("AC@3").mean().alias("AC@3")
    ]).with_columns([
        pl.lit(algorithm_name).alias("rca_algorithm")
    ])

    return result

def create_markdown_table(shapleyiq_df: pl.DataFrame, nezha_df: pl.DataFrame):
    """Create a comprehensive markdown table for RQ2."""

    print("\nGenerating RQ2 markdown table...")

    # Target sampling rates
    target_rates = [0.005, 0.01, 0.1]

    # Process both datasets
    shapleyiq_filtered = filter_target_rates_and_algorithms(shapleyiq_df, target_rates)
    nezha_filtered = filter_target_rates_and_algorithms(nezha_df, target_rates)

    shapleyiq_avg = calculate_algorithm_averages(shapleyiq_filtered, "ShapleyIQ")
    nezha_avg = calculate_algorithm_averages(nezha_filtered, "Nezha")

    # Combine data
    combined_df = pl.concat([shapleyiq_avg, nezha_avg]) if shapleyiq_avg.height > 0 and nezha_avg.height > 0 else (
        shapleyiq_avg if shapleyiq_avg.height > 0 else nezha_avg
    )

    if combined_df.height == 0:
        print("No data available for markdown table generation!")
        return

    # Convert to pandas for easier manipulation
    combined_pd = combined_df.to_pandas()

    # Get all unique samplers and rates
    samplers = sorted(combined_pd['sampler.name'].unique())
    rates = sorted(combined_pd['sampler.rate'].unique())
    rca_algorithms = sorted(combined_pd['rca_algorithm'].unique())

    print(f"Samplers: {samplers}")
    print(f"Rates: {rates}")
    print(f"RCA Algorithms: {rca_algorithms}")

    # Generate markdown table
    markdown_content = []

    # Header
    markdown_content.append("# RQ2: Impact on Root Cause Analysis")
    markdown_content.append("")
    markdown_content.append("This table shows the performance of different sampling algorithms on RCA effectiveness.")
    markdown_content.append(f"**Sampling Rates**: {', '.join([f'{r:.3f}' for r in rates])}")
    markdown_content.append(f"**Metrics**: MRR (Mean Reciprocal Rank), AC@1 (Accuracy@1), AC@3 (Accuracy@3)")
    markdown_content.append("")

    # Create table for each RCA algorithm
    for rca_alg in rca_algorithms:
        markdown_content.append(f"## {rca_alg} Results")
        markdown_content.append("")

        # Table header
        header = "| Sampler | Rate | MRR | AC@1 | AC@3 |"
        separator = "|---------|------|-----|------|------|"
        markdown_content.append(header)
        markdown_content.append(separator)

        # Filter data for this RCA algorithm
        rca_data = combined_pd[combined_pd['rca_algorithm'] == rca_alg]

        # Sort by sampler name and rate
        rca_data = rca_data.sort_values(['sampler.name', 'sampler.rate'])

        # Add rows
        for _, row in rca_data.iterrows():
            sampler = row['sampler.name']
            rate = f"{row['sampler.rate']:.3f}"
            mrr = f"{row['MRR']:.4f}" if not np.isnan(row['MRR']) else "N/A"
            ac1 = f"{row['AC@1']:.4f}" if not np.isnan(row['AC@1']) else "N/A"
            ac3 = f"{row['AC@3']:.4f}" if not np.isnan(row['AC@3']) else "N/A"

            table_row = f"| {sampler} | {rate} | {mrr} | {ac1} | {ac3} |"
            markdown_content.append(table_row)

        markdown_content.append("")

    # Summary section
    markdown_content.append("## Summary")
    markdown_content.append("")

    # Calculate best performers for each metric and RCA algorithm
    for rca_alg in rca_algorithms:
        rca_data = combined_pd[combined_pd['rca_algorithm'] == rca_alg]

        if len(rca_data) > 0:
            markdown_content.append(f"### {rca_alg} Best Performers")

            # For each rate, find best performers
            for rate in rates:
                rate_data = rca_data[rca_data['sampler.rate'] == rate]

                if len(rate_data) > 0:
                    markdown_content.append(f"**Rate {rate:.3f}:**")

                    # Best MRR
                    best_mrr = rate_data.loc[rate_data['MRR'].idxmax()]
                    markdown_content.append(f"- Best MRR: {best_mrr['sampler.name']} ({best_mrr['MRR']:.4f})")

                    # Best AC@1
                    best_ac1 = rate_data.loc[rate_data['AC@1'].idxmax()]
                    markdown_content.append(f"- Best AC@1: {best_ac1['sampler.name']} ({best_ac1['AC@1']:.4f})")

                    # Best AC@3
                    best_ac3 = rate_data.loc[rate_data['AC@3'].idxmax()]
                    markdown_content.append(f"- Best AC@3: {best_ac3['sampler.name']} ({best_ac3['AC@3']:.4f})")

                    markdown_content.append("")

    # Write to file
    output_file = "rq2_rca_impact_results.md"
    with open(output_file, 'w') as f:
        f.write('\n'.join(markdown_content))

    # Also print to console
    print("\n" + "="*60)
    print("RQ2: Root Cause Analysis Impact Results")
    print("="*60)
    for line in markdown_content:
        print(line)

    print(f"\nMarkdown table saved to: {output_file}")

def main():
    """Main function to generate RQ2 RCA impact analysis."""

    shapleyiq_path = "/home/nn/workspace/gleaner-rc/rca/shapleyiq/sampler.grouped.perf.parquet"
    nezha_path = "/home/nn/workspace/gleaner-rc/rca/nezha/sampler.grouped.perf.parquet"

    print("RQ2: Impact on Root Cause Analysis")
    print("=" * 60)
    print("Target sampling rates: 0.005, 0.01, 0.1")
    print("Target metrics: MRR, AC@1, AC@3")
    print("RCA algorithms: ShapleyIQ, Nezha")

    # Load data
    shapleyiq_df, nezha_df = load_rca_data(shapleyiq_path, nezha_path)

    # Generate markdown table
    create_markdown_table(shapleyiq_df, nezha_df)

    print("\nRQ2 analysis complete!")

if __name__ == "__main__":
    main()
