# RQ1: Sampling Quality

## Configuration

- Input aggregated parquet: `output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet`
- Input detailed parquet: `output/rcabench-platform-v2/sampler_reports/gleaner/detailed_perf.parquet`
- Output directory: `output/artifact/reduced/rq1`
- Mode: `offline`
- Available sampling rates: `0.01`, `0.1`
- Samplers included: Gleaner Latency-Dominant, Gleaner Log-Dominant, Gleaner w/o AD, Gleaner w/o DPP, Gleaner w/o Logs, Gleaner w/o Logs + AD, Gleaner w/o Rebalance, Gleaner Pure Diversity, Gleaner Top Score, Gleaner WL Kernel

## Summary

| Sampler | Display Name | Sample Rates | Datapacks | API Coverage | Path Coverage Dedup | Event Coverage | Unique Trace Coverage | Shannon Entropy | Proportion Anomaly | GT Trace Proportion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gleaner_latency_dominate | Gleaner Latency-Dominant | 2 | 161 | 0.9936 | 0.8922 | 0.8906 | 0.2144 | 7.4328 | 0.1121 | 0.2575 |
| gleaner_log_dominate | Gleaner Log-Dominant | 2 | 161 | 0.9936 | 0.8880 | 0.8898 | 0.2153 | 7.4374 | 0.1121 | 0.2576 |
| gleaner_no_ad | Gleaner w/o AD | 2 | 161 | 0.9933 | 0.8944 | 0.9089 | 0.2193 | 7.5133 | 0.0714 | 0.2241 |
| gleaner_no_dpp | Gleaner w/o DPP | 2 | 161 | 0.9966 | 0.8513 | 0.8890 | 0.1917 | 7.2504 | 0.1065 | 0.2652 |
| gleaner_no_logs | Gleaner w/o Logs | 2 | 161 | 0.9947 | 0.8875 | 0.8870 | 0.2100 | 7.4044 | 0.1077 | 0.2595 |
| gleaner_no_logs_no_ad | Gleaner w/o Logs + AD | 2 | 161 | 0.9947 | 0.9082 | 0.9015 | 0.2044 | 7.3932 | 0.0740 | 0.2202 |
| gleaner_no_rebalance | Gleaner w/o Rebalance | 2 | 161 | 0.9967 | 0.8956 | 0.8954 | 0.2210 | 7.4991 | 0.1009 | 0.2710 |
| gleaner_pure_diversity | Gleaner Pure Diversity | 2 | 161 | 0.8077 | 0.6601 | 0.6514 | 0.1823 | 6.7227 | 0.0176 | 0.0795 |
| gleaner_top_score | Gleaner Top Score | 2 | 161 | 0.4795 | 0.5199 | 0.6261 | 0.2275 | 7.5940 | 0.1446 | 0.4628 |
| gleaner_wl_kernel | Gleaner WL Kernel | 2 | 161 | 0.9967 | 0.8958 | 0.8769 | 0.1874 | 7.1623 | 0.0981 | 0.2727 |

## Leaders

- API Coverage (higher is better): Gleaner WL Kernel (0.9967)
- Path Coverage Dedup (higher is better): Gleaner w/o Logs + AD (0.9082)
- Event Coverage (higher is better): Gleaner w/o AD (0.9089)
- Unique Trace Coverage (higher is better): Gleaner Top Score (0.2275)
- Shannon Entropy (higher is better): Gleaner Top Score (7.5940)
- Proportion Anomaly (higher is better): Gleaner Top Score (0.1446)
- GT Trace Proportion (higher is better): Gleaner Top Score (0.4628)

## Limitations

- Reduced RQ1 currently summarizes existing Gleaner sampler variants; full cross-baseline sampler comparison needs additional TracePicker/TraStrainer/Sieve/Sifter reports.
- Plot files are intentionally omitted to keep expected-output comparison stable.
