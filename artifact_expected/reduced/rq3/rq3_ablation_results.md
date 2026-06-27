# RQ3: Ablation Study

## Configuration

- Input parquet: `output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet`
- Output directory: `output/artifact/reduced/rq3`
- Mode: `offline`
- Excluded sampling rates: `0.005`
- Sampling rates: `0.01`, `0.1`
- Samplers: Gleaner Latency-Dominant, Gleaner Log-Dominant, Gleaner w/o AD, Gleaner w/o DPP, Gleaner w/o Logs, Gleaner w/o Logs + AD, Gleaner w/o Rebalance, Gleaner Pure Diversity, Gleaner Top Score, Gleaner WL Kernel

## Overview Metrics

| Sampler | Display Name | Sample Rate Count | API Coverage | Unique Trace Coverage | Shannon Entropy | Proportion Anomaly | Path Coverage Dedup | Benefit-Cost Ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gleaner_latency_dominate | Gleaner Latency-Dominant | 2 | 0.9936 | 0.2144 | 7.4328 | 0.1121 | 0.8922 | 0.8165 |
| gleaner_log_dominate | Gleaner Log-Dominant | 2 | 0.9936 | 0.2153 | 7.4374 | 0.1121 | 0.8880 | 0.8181 |
| gleaner_no_ad | Gleaner w/o AD | 2 | 0.9933 | 0.2193 | 7.5133 | 0.0714 | 0.8944 | 0.8312 |
| gleaner_no_dpp | Gleaner w/o DPP | 2 | 0.9966 | 0.1917 | 7.2504 | 0.1065 | 0.8513 | 0.7747 |
| gleaner_no_logs | Gleaner w/o Logs | 2 | 0.9947 | 0.2100 | 7.4044 | 0.1077 | 0.8875 | 0.8070 |
| gleaner_no_logs_no_ad | Gleaner w/o Logs + AD | 2 | 0.9947 | 0.2044 | 7.3932 | 0.0740 | 0.9082 | 0.7961 |
| gleaner_no_rebalance | Gleaner w/o Rebalance | 2 | 0.9967 | 0.2210 | 7.4991 | 0.1009 | 0.8956 | 0.8362 |
| gleaner_pure_diversity | Gleaner Pure Diversity | 2 | 0.8077 | 0.1823 | 6.7227 | 0.0176 | 0.6601 | 0.5751 |
| gleaner_top_score | Gleaner Top Score | 2 | 0.4795 | 0.2275 | 7.5940 | 0.1446 | 0.5199 | 0.8690 |
| gleaner_wl_kernel | Gleaner WL Kernel | 2 | 0.9967 | 0.1874 | 7.1623 | 0.0981 | 0.8958 | 0.7641 |

## Best Per Metric

- API Coverage (higher is better): Gleaner WL Kernel (0.9967)
- Unique Trace Coverage (higher is better): Gleaner Top Score (0.2275)
- Shannon Entropy (higher is better): Gleaner Top Score (7.5940)
- Proportion Anomaly (higher is better): Gleaner Top Score (0.1446)
- Path Coverage Dedup (higher is better): Gleaner w/o Logs + AD (0.9082)
- Benefit-Cost Ratio (higher is better): Gleaner Top Score (0.8690)

## Notes

- This reduced RQ3 artifact uses the available Gleaner variant sampler report rather than requiring canonical `gleaner` and `random` rows.
- Values are deterministic means across the filtered sampling rates in `aggregated_perf.parquet`.
- Plot files are intentionally omitted to keep the artifact harness stable.
