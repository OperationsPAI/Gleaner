# RQ3: Ablation Study

## Configuration

- Input parquet: `output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/aggregated_perf.parquet`
- Output directory: `output/artifact/reduced/rq3`
- Mode: `offline`
- Excluded sampling rates: `0.005`
- Sampling rates: `0.01`, `0.1`
- Samplers: Gleaner Latency-Dominant, Gleaner Log-Dominant, Gleaner w/o AD, Gleaner w/o DPP, Gleaner w/o Logs, Gleaner w/o Logs + AD, Gleaner w/o Rebalance, Gleaner Pure Diversity, Gleaner Top Score, Gleaner WL Kernel

## Overview Metrics

| Sampler | Display Name | Sample Rate Count | API Coverage | Unique Trace Coverage | Shannon Entropy | Proportion Anomaly | Path Coverage Dedup | Benefit-Cost Ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gleaner_latency_dominate | Gleaner Latency-Dominant | 2 | 0.9541 | 0.2085 | 6.7167 | 0.1261 | 0.8438 | 0.8476 |
| gleaner_log_dominate | Gleaner Log-Dominant | 2 | 0.9541 | 0.2092 | 6.7206 | 0.1261 | 0.8392 | 0.8490 |
| gleaner_no_ad | Gleaner w/o AD | 2 | 0.9497 | 0.2099 | 6.7418 | 0.0924 | 0.8244 | 0.8500 |
| gleaner_no_dpp | Gleaner w/o DPP | 2 | 0.9757 | 0.1926 | 6.6340 | 0.1153 | 0.8036 | 0.8259 |
| gleaner_no_logs | Gleaner w/o Logs | 2 | 0.9599 | 0.2057 | 6.7094 | 0.1278 | 0.8400 | 0.8396 |
| gleaner_no_logs_no_ad | Gleaner w/o Logs + AD | 2 | 0.9620 | 0.1975 | 6.6571 | 0.0981 | 0.8537 | 0.8230 |
| gleaner_no_rebalance | Gleaner w/o Rebalance | 2 | 0.9778 | 0.2151 | 6.7869 | 0.1090 | 0.8577 | 0.8679 |
| gleaner_pure_diversity | Gleaner Pure Diversity | 2 | 0.7877 | 0.1849 | 6.2084 | 0.0210 | 0.6617 | 0.6567 |
| gleaner_top_score | Gleaner Top Score | 2 | 0.4616 | 0.2195 | 6.8468 | 0.2172 | 0.4913 | 0.8912 |
| gleaner_wl_kernel | Gleaner WL Kernel | 2 | 0.9768 | 0.1870 | 6.5415 | 0.1076 | 0.8572 | 0.8081 |

## Best Per Metric

- API Coverage (higher is better): Gleaner w/o Rebalance (0.9778)
- Unique Trace Coverage (higher is better): Gleaner Top Score (0.2195)
- Shannon Entropy (higher is better): Gleaner Top Score (6.8468)
- Proportion Anomaly (higher is better): Gleaner Top Score (0.2172)
- Path Coverage Dedup (higher is better): Gleaner w/o Rebalance (0.8577)
- Benefit-Cost Ratio (higher is better): Gleaner Top Score (0.8912)

## Notes

- This reduced RQ3 artifact uses the available Gleaner variant sampler report rather than requiring canonical `gleaner` and `random` rows.
- Values are deterministic means across the filtered sampling rates in `aggregated_perf.parquet`.
- Plot files are intentionally omitted to keep the artifact harness stable.
