#!/usr/bin/env python3
"""
RQ1: Diversity Quality Assessment - Generate markdown table for Shannon Entropy.

This script generates a markdown table showing Shannon Entropy scores
for different sampling algorithms across sampling rates.
"""

from pathlib import Path

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


def generate_diversity_markdown_table(df: pl.DataFrame, output_dir: str = "plots"):
    """Generate RQ1 Section 2: Diversity Quality Assessment as Markdown Table."""

    Path(output_dir).mkdir(exist_ok=True)
    df_pd = df.to_pandas()

    # Get unique sampling rates
    sampling_rates = sorted(df_pd["sampling_rate"].unique())
    display_names = get_algorithm_display_names()

    # Diversity metrics for RQ1
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

    # Generate markdown content
    markdown_content = []

    # Header
    markdown_content.append("# RQ1: Diversity Quality Assessment")
    markdown_content.append("")
    markdown_content.append(
        "This table shows the Shannon Entropy scores for different sampling algorithms across sampling rates."
    )
    markdown_content.append(
        f"**Sampling Rates**: {', '.join([f'{r:.1f}%' for r in sorted([rate * 100 for rate in sampling_rates])])}"
    )
    markdown_content.append("**Metric**: Shannon Entropy (measure of trace diversity)")
    markdown_content.append("")

    for metric_col, metric_name in available_metrics:
        markdown_content.append(f"## {metric_name} Results")
        markdown_content.append("")

        # Table header
        header = (
            "| Sampler | "
            + " | ".join(
                [f"{rate:.1f}%" for rate in sorted([r * 100 for r in sampling_rates])]
            )
            + " |"
        )
        separator = "|---------|" + "|".join(["------|" for _ in sampling_rates])
        markdown_content.append(header)
        markdown_content.append(separator)

        # Get all samplers and sort them
        all_samplers = df_pd["sampler"].unique()
        non_gleaner_algorithms = [
            s for s in all_samplers if not s.startswith("gleaner")
        ]
        gleaner_algorithms = [s for s in all_samplers if s.startswith("gleaner")]
        gleaner_sorted = ["gleaner"] + [
            s for s in sorted(gleaner_algorithms) if s != "gleaner"
        ]
        sorted_samplers = sorted(non_gleaner_algorithms) + gleaner_sorted

        # Add rows for each sampler
        for sampler in sorted_samplers:
            sampler_data = df_pd[df_pd["sampler"] == sampler]
            display_name = display_names.get(sampler, sampler)

            row_values = [display_name]
            for rate in sorted(sampling_rates):
                rate_data = sampler_data[sampler_data["sampling_rate"] == rate]
                if len(rate_data) > 0:
                    value = rate_data[metric_col].iloc[0]
                    row_values.append(f"{value:.4f}")
                else:
                    row_values.append("N/A")

            table_row = "| " + " | ".join(row_values) + " |"
            markdown_content.append(table_row)

        markdown_content.append("")

        # Add best performers for each rate
        markdown_content.append("### Best Performers by Sampling Rate")
        markdown_content.append("")

        for rate in sorted(sampling_rates):
            rate_data = df_pd[df_pd["sampling_rate"] == rate]
            if len(rate_data) > 0:
                best_performer = rate_data.loc[rate_data[metric_col].idxmax()]
                best_name = display_names.get(
                    best_performer["sampler"], best_performer["sampler"]
                )
                best_score = best_performer[metric_col]

                markdown_content.append(
                    f"**{rate:.1f}% Rate**: {best_name} ({best_score:.4f})"
                )

        markdown_content.append("")

    # Write to file
    output_file = f"{output_dir}/rq1_diversity_quality_table.md"
    with open(output_file, "w") as f:
        f.write("\n".join(markdown_content))

    # Also print to console
    print("\n" + "=" * 60)
    print("RQ1: Diversity Quality Assessment - Markdown Table")
    print("=" * 60)
    for line in markdown_content:
        print(line)

    print(f"\nDiversity quality table saved to: {output_file}")


def main():
    """Main function to generate RQ1 diversity quality markdown table."""

    parquet_path = "/home/nn/workspace/gleaner-rc/output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet"

    if not Path(parquet_path).exists():
        print(f"Error: File not found: {parquet_path}")
        return

    print("RQ1: Diversity Quality Assessment - Markdown Table Generation")
    print("=" * 60)
    print("Loading and filtering data...")
    df = load_and_filter_data(parquet_path)

    if df.height == 0:
        print("No offline mode data found!")
        return

    print("\nGenerating RQ1 diversity quality markdown table...")
    print(
        "Target algorithms: gleaner, tracepicker, trastrainer, trastrainer w/o metrics, sifter, sieve, random"
    )
    print("Metric: Shannon Entropy (trace diversity measure)")

    # Generate markdown table
    print("\n" + "=" * 60)
    generate_diversity_markdown_table(df)

    print("\n" + "=" * 60)
    print("RQ1 Diversity Quality Markdown Table Complete!")
    print("\nGenerated table (check 'plots' directory):")
    print("- rq1_diversity_quality_table.md")


if __name__ == "__main__":
    main()
