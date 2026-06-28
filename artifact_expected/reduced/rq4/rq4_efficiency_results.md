# RQ4: Efficiency Evaluation

## Configuration

- Input parquet: `output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/aggregated_perf.parquet`
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
| gleaner_latency_dominate | 0.914 | 0.144 | 0.709 | 1.208 | 0.7769 | 0.0966 | 0.5857 | 0.8832 | 10.01% | 0.01% | 10.00% | 10.02% | 0.0020 | 0.0011 | 0.0000 | 0.0038 |
| gleaner_log_dominate | 0.946 | 0.156 | 0.710 | 1.275 | 0.7796 | 0.0920 | 0.5869 | 0.8832 | 10.01% | 0.01% | 10.00% | 10.02% | 0.0020 | 0.0011 | 0.0000 | 0.0038 |
| gleaner_no_ad | 44.719 | 35.887 | 0.730 | 95.611 | 0.7824 | 0.0835 | 0.5899 | 0.9101 | 10.00% | 0.03% | 9.90% | 10.02% | 0.0024 | 0.0023 | 0.0000 | 0.0091 |
| gleaner_no_dpp | 0.607 | 0.073 | 0.516 | 0.813 | 0.7103 | 0.1043 | 0.4599 | 0.8447 | 10.01% | 0.01% | 10.00% | 10.02% | 0.0020 | 0.0011 | 0.0000 | 0.0038 |
| gleaner_no_logs | 0.821 | 0.301 | 0.537 | 1.828 | 0.7652 | 0.0907 | 0.5802 | 0.8713 | 10.00% | 0.03% | 9.90% | 10.02% | 0.0024 | 0.0023 | 0.0000 | 0.0091 |
| gleaner_no_logs_no_ad | 0.679 | 0.092 | 0.566 | 0.887 | 0.7287 | 0.0837 | 0.5466 | 0.8549 | 10.01% | 0.01% | 10.00% | 10.02% | 0.0020 | 0.0011 | 0.0000 | 0.0038 |
| gleaner_no_rebalance | 0.995 | 0.189 | 0.713 | 1.334 | 0.8011 | 0.0875 | 0.5880 | 0.9101 | 10.01% | 0.01% | 10.00% | 10.02% | 0.0020 | 0.0011 | 0.0000 | 0.0038 |
| gleaner_pure_diversity | 1.695 | 0.284 | 1.230 | 2.162 | 0.7164 | 0.0752 | 0.5379 | 0.8211 | 10.00% | 0.03% | 9.90% | 10.02% | 0.0024 | 0.0023 | 0.0000 | 0.0091 |
| gleaner_top_score | 0.511 | 0.053 | 0.405 | 0.603 | 0.8183 | 0.0923 | 0.5967 | 0.9267 | 10.01% | 0.01% | 10.00% | 10.02% | 0.0020 | 0.0011 | 0.0000 | 0.0038 |
| gleaner_wl_kernel | 6.660 | 6.373 | 2.101 | 23.688 | 0.6887 | 0.0971 | 0.4744 | 0.8234 | 10.01% | 0.01% | 10.00% | 10.02% | 0.0020 | 0.0011 | 0.0000 | 0.0038 |

## Metric Leaders

- Runtime Per Trace Ms (lowest is best): gleaner_top_score (0.511)
- Std Runtime Per Trace Ms (lowest is best): gleaner_top_score (0.053)
- Min Runtime Per Trace Ms (lowest is best): gleaner_top_score (0.405)
- Max Runtime Per Trace Ms (lowest is best): gleaner_top_score (0.603)
- Benefit Cost Ratio (highest is best): gleaner_top_score (0.8183)
- Std Benefit Cost Ratio (lowest is best): gleaner_pure_diversity (0.0752)
- Min Benefit Cost Ratio (highest is best): gleaner_top_score (0.5967)
- Max Benefit Cost Ratio (highest is best): gleaner_top_score (0.9267)
- Actual Sampling Rate (highest is best): gleaner_latency_dominate (10.01%)
- Std Actual Sampling Rate (lowest is best): gleaner_latency_dominate (0.01%)
- Min Actual Sampling Rate (highest is best): gleaner_latency_dominate (10.00%)
- Max Actual Sampling Rate (highest is best): gleaner_latency_dominate (10.02%)
- Controllability (highest is best): gleaner_no_ad (0.0024)
- Std Controllability (lowest is best): gleaner_latency_dominate (0.0011)
- Min Controllability (highest is best): gleaner_latency_dominate (0.0000)
- Max Controllability (highest is best): gleaner_no_ad (0.0091)
