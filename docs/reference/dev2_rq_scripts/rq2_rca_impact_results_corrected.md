# RQ2: Impact on Root Cause Analysis

This table shows the performance of different sampling algorithms on RCA effectiveness.
**Sampling Rates**:  0.010, 0.100
**Metrics**: AC@1 (Accuracy@1), AC@3 (Accuracy@3)
**RCA Algorithms**: microrca, nezha, shapleyiq

## Microrca Results

| Sampler            | Rate  | AC@1     | AC@3     |
| ------------------ | ----- | -------- | -------- |
| gleaner            | 0.010 | 0.4534   | 0.4969   |
| gleaner            | 0.100 | 0.4534   | 0.4969   |
| random             | 0.010 | 0.3913   | 0.4410   |
| random             | 0.100 | 0.4534   | 0.4907   |
| sieve              | 0.010 | 0.4161   | 0.4658   |
| sieve              | 0.100 | 0.4534   | 0.4845   |
| sifter             | 0.010 | 0.4099   | 0.4783   |
| sifter             | 0.100 | 0.4534   | 0.4845   |
| tracepicker        | 0.010 | 0.4534   | 0.4845   |
| tracepicker        | 0.100 | 0.4534   | 0.4845   |
| trastrainer        | 0.010 | 0.4037   | 0.4845   |
| trastrainer        | 0.100 | 0.4534   | 0.4907   |
| trastrainer_no_met | 0.010 | 0.3789   | 0.4534   |
| trastrainer_no_met | 0.100 | 0.4534   | 0.4969   |
| null               | null  | 0.453416 | 0.496894 |

## Nezha Results

| Sampler            | Rate  | AC@1    | AC@3     |
| ------------------ | ----- | ------- | -------- |
| gleaner            | 0.010 | 0.1863  | 0.4472   |
| gleaner            | 0.100 | 0.1366  | 0.3478   |
| random             | 0.010 | 0.0621  | 0.1491   |
| random             | 0.100 | 0.0870  | 0.1925   |
| sieve              | 0.010 | 0.1118  | 0.2298   |
| sieve              | 0.100 | 0.0932  | 0.1677   |
| sifter             | 0.010 | 0.0186  | 0.1491   |
| sifter             | 0.100 | 0.0807  | 0.2484   |
| tracepicker        | 0.010 | 0.0807  | 0.1863   |
| tracepicker        | 0.100 | 0.0559  | 0.1988   |
| trastrainer        | 0.010 | 0.0994  | 0.2360   |
| trastrainer        | 0.100 | 0.0683  | 0.1863   |
| trastrainer_no_met | 0.010 | 0.0932  | 0.2547   |
| trastrainer_no_met | 0.100 | 0.0932  | 0.2360   |
| null               | null  | 0.10559 | 0.267081 |

## Shapleyiq Results

| Sampler            | Rate  | AC@1     | AC@3     |
| ------------------ | ----- | -------- | -------- |
| gleaner            | 0.010 | 0.5590   | 0.6398   |
| gleaner            | 0.100 | 0.5155   | 0.6087   |
| random             | 0.010 | 0.1677   | 0.3043   |
| random             | 0.100 | 0.4037   | 0.5590   |
| sieve              | 0.010 | 0.2733   | 0.4037   |
| sieve              | 0.100 | 0.4721   | 0.6025   |
| sifter             | 0.010 | 0.1801   | 0.3665   |
| sifter             | 0.100 | 0.3975   | 0.5839   |
| tracepicker        | 0.010 | 0.2547   | 0.4472   |
| tracepicker        | 0.100 | 0.3913   | 0.4783   |
| trastrainer        | 0.010 | 0.0559   | 0.1925   |
| trastrainer        | 0.100 | 0.0311   | 0.2236   |
| trastrainer_no_met | 0.010 | 0.0932   | 0.2298   |
| trastrainer_no_met | 0.100 | 0.3230   | 0.5714   |
| null               | null  | 0.409938 | 0.565217 |


python3 << 'EOF'
import pandas as pd

# File paths
files = [
    '/home/nn/workspace/gleaner-rc/output/rcabench-platform-v2/sampler_reports/rcabench_sampler_microrca_filtered/aggregated_perf.parquet'
]

# Update each file
for file_path in files:
    print(f"Processing {file_path.split('/')[-1]}...")

    # Read the parquet file
    df = pd.read_parquet(file_path)

    # Show before
    print(f"  Before: dataset column unique values = {df['dataset'].unique()}")

    # Update the dataset column
    df['dataset'] = 'gleaner'

    # Show after
    print(f"  After: dataset column unique values = {df['dataset'].unique()}")

    # Save back to the same file
    df.to_parquet(file_path, index=False)

    print(f"  ✓ Updated and saved\n")

print("All files updated successfully!")
EOF

avg_proportion_rare

avg_proportion_anomaly

avg_api_coverage

avg_path_coverage_dedup