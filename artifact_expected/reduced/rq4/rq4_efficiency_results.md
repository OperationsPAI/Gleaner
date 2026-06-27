# RQ4: Efficiency Evaluation

## Configuration

- Input parquet: `output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet`
- Output directory: `output/artifact/reduced/rq4`
- Mode: `offline`
- Sampling rate: `0.1`
- Algorithms: gleaner_latency_dominate, gleaner_log_dominate, gleaner_no_ad, gleaner_no_dpp, gleaner_no_logs, gleaner_no_logs_no_ad, gleaner_no_rebalance, gleaner_pure_diversity, gleaner_top_score, gleaner_wl_kernel

## Available Metrics

- Runtime: `avg_runtime_per_trace_ms`, `std_runtime_per_trace_ms`, `min_runtime_per_trace_ms`, `max_runtime_per_trace_ms`
- Benefit Cost: `avg_benefit_cost_ratio`, `std_benefit_cost_ratio`, `min_benefit_cost_ratio`, `max_benefit_cost_ratio`
- Actual Rate: `avg_actual_sampling_rate`, `std_actual_sampling_rate`, `min_actual_sampling_rate`, `max_actual_sampling_rate`
- Controllability: `avg_controllability`, `std_controllability`, `min_controllability`, `max_controllability`

## Efficiency Summary

| Algorithm | Runtime Per Trace Ms | Std Runtime Per Trace Ms | Min Runtime Per Trace Ms | Max Runtime Per Trace Ms | Benefit Cost Ratio | Std Benefit Cost Ratio | Min Benefit Cost Ratio | Max Benefit Cost Ratio | Actual Sampling Rate | Std Actual Sampling Rate | Min Actual Sampling Rate | Max Actual Sampling Rate | Controllability | Std Controllability | Min Controllability | Max Controllability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gleaner_latency_dominate | 1.141 | 0.248 | 0.709 | 1.851 | 0.7323 | 0.0968 | 0.3798 | 0.8832 | 10.00% | 0.00% | 9.99% | 10.02% | 0.0010 | 0.0008 | 0.0000 | 0.0038 |
| gleaner_log_dominate | 1.159 | 0.243 | 0.710 | 1.923 | 0.7365 | 0.0980 | 0.3779 | 0.8845 | 10.00% | 0.00% | 9.99% | 10.02% | 0.0010 | 0.0008 | 0.0000 | 0.0038 |
| gleaner_no_ad | 12.498 | 23.568 | 0.730 | 97.961 | 0.7522 | 0.0797 | 0.4479 | 0.9101 | 9.99% | 0.07% | 9.15% | 10.02% | 0.0021 | 0.0067 | 0.0000 | 0.0848 |
| gleaner_no_dpp | 0.589 | 0.061 | 0.452 | 0.813 | 0.6514 | 0.1062 | 0.1709 | 0.8447 | 10.00% | 0.00% | 9.99% | 10.02% | 0.0010 | 0.0008 | 0.0000 | 0.0038 |
| gleaner_no_logs | 0.932 | 0.233 | 0.537 | 1.828 | 0.7171 | 0.1002 | 0.3573 | 0.8723 | 9.99% | 0.07% | 9.15% | 10.02% | 0.0021 | 0.0067 | 0.0000 | 0.0848 |
| gleaner_no_logs_no_ad | 0.825 | 0.154 | 0.560 | 1.219 | 0.6916 | 0.0671 | 0.4385 | 0.8549 | 10.00% | 0.00% | 9.99% | 10.02% | 0.0010 | 0.0008 | 0.0000 | 0.0038 |
| gleaner_no_rebalance | 1.202 | 0.247 | 0.713 | 1.899 | 0.7586 | 0.1051 | 0.3779 | 0.9101 | 10.00% | 0.00% | 9.99% | 10.02% | 0.0010 | 0.0008 | 0.0000 | 0.0038 |
| gleaner_pure_diversity | 1.685 | 0.284 | 0.915 | 2.433 | 0.6525 | 0.0663 | 0.3205 | 0.8211 | 9.99% | 0.07% | 9.15% | 10.02% | 0.0021 | 0.0067 | 0.0000 | 0.0848 |
| gleaner_top_score | 0.517 | 0.050 | 0.339 | 0.787 | 0.7813 | 0.0970 | 0.0120 | 0.9267 | 10.00% | 0.00% | 9.99% | 10.02% | 0.0010 | 0.0008 | 0.0000 | 0.0038 |
| gleaner_wl_kernel | 8.398 | 5.201 | 2.101 | 24.547 | 0.6352 | 0.1071 | 0.1573 | 0.8234 | 10.00% | 0.00% | 9.99% | 10.02% | 0.0010 | 0.0008 | 0.0000 | 0.0038 |

## Metric Leaders

- Runtime Per Trace Ms (lowest is best): gleaner_top_score (0.517)
- Std Runtime Per Trace Ms (lowest is best): gleaner_top_score (0.050)
- Min Runtime Per Trace Ms (lowest is best): gleaner_top_score (0.339)
- Max Runtime Per Trace Ms (lowest is best): gleaner_top_score (0.787)
- Benefit Cost Ratio (highest is best): gleaner_top_score (0.7813)
- Std Benefit Cost Ratio (lowest is best): gleaner_pure_diversity (0.0663)
- Min Benefit Cost Ratio (highest is best): gleaner_no_ad (0.4479)
- Max Benefit Cost Ratio (highest is best): gleaner_top_score (0.9267)
- Actual Sampling Rate (highest is best): gleaner_latency_dominate (10.00%)
- Std Actual Sampling Rate (lowest is best): gleaner_latency_dominate (0.00%)
- Min Actual Sampling Rate (highest is best): gleaner_latency_dominate (9.99%)
- Max Actual Sampling Rate (highest is best): gleaner_latency_dominate (10.02%)
- Controllability (highest is best): gleaner_no_ad (0.0021)
- Std Controllability (lowest is best): gleaner_latency_dominate (0.0008)
- Min Controllability (highest is best): gleaner_latency_dominate (0.0000)
- Max Controllability (highest is best): gleaner_no_ad (0.0848)
