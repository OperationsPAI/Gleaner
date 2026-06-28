# RQ1: Sampling Quality

## Configuration

- Input aggregated parquet: `output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/aggregated_perf.parquet`
- Input detailed parquet: `output/rcabench-platform-v2/sampler_reports/gleaner_reduced20/detailed_perf.parquet`
- Output directory: `output/artifact/reduced/rq1`
- Mode: `offline`
- Available sampling rates: `0.01`, `0.1`
- Samplers included: Gleaner Latency-Dominant, Gleaner Log-Dominant, Gleaner w/o AD, Gleaner w/o DPP, Gleaner w/o Logs, Gleaner w/o Logs + AD, Gleaner w/o Rebalance, Gleaner Pure Diversity, Gleaner Top Score, Gleaner WL Kernel

## Summary

| Sampler | Display Name | Sample Rates | Datapacks | API Coverage | Path Coverage Dedup | Event Coverage | Unique Trace Coverage | Shannon Entropy | Proportion Anomaly | GT Trace Proportion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gleaner_latency_dominate | Gleaner Latency-Dominant | 2 | 20 | 0.9541 | 0.8438 | 0.8441 | 0.2085 | 6.7167 | 0.1261 | 0.2465 |
| gleaner_log_dominate | Gleaner Log-Dominant | 2 | 20 | 0.9541 | 0.8392 | 0.8431 | 0.2092 | 6.7206 | 0.1261 | 0.2487 |
| gleaner_no_ad | Gleaner w/o AD | 2 | 20 | 0.9497 | 0.8244 | 0.8459 | 0.2099 | 6.7418 | 0.0924 | 0.2330 |
| gleaner_no_dpp | Gleaner w/o DPP | 2 | 20 | 0.9757 | 0.8036 | 0.8476 | 0.1926 | 6.6340 | 0.1153 | 0.2425 |
| gleaner_no_logs | Gleaner w/o Logs | 2 | 20 | 0.9599 | 0.8400 | 0.8414 | 0.2057 | 6.7094 | 0.1278 | 0.2533 |
| gleaner_no_logs_no_ad | Gleaner w/o Logs + AD | 2 | 20 | 0.9620 | 0.8537 | 0.8425 | 0.1975 | 6.6571 | 0.0981 | 0.2283 |
| gleaner_no_rebalance | Gleaner w/o Rebalance | 2 | 20 | 0.9778 | 0.8577 | 0.8495 | 0.2151 | 6.7869 | 0.1090 | 0.2537 |
| gleaner_pure_diversity | Gleaner Pure Diversity | 2 | 20 | 0.7877 | 0.6617 | 0.6321 | 0.1849 | 6.2084 | 0.0210 | 0.0881 |
| gleaner_top_score | Gleaner Top Score | 2 | 20 | 0.4616 | 0.4913 | 0.6058 | 0.2195 | 6.8468 | 0.2172 | 0.4635 |
| gleaner_wl_kernel | Gleaner WL Kernel | 2 | 20 | 0.9768 | 0.8572 | 0.8374 | 0.1870 | 6.5415 | 0.1076 | 0.2550 |

## Leaders

- API Coverage (higher is better): Gleaner w/o Rebalance (0.9778)
- Path Coverage Dedup (higher is better): Gleaner w/o Rebalance (0.8577)
- Event Coverage (higher is better): Gleaner w/o Rebalance (0.8495)
- Unique Trace Coverage (higher is better): Gleaner Top Score (0.2195)
- Shannon Entropy (higher is better): Gleaner Top Score (6.8468)
- Proportion Anomaly (higher is better): Gleaner Top Score (0.2172)
- GT Trace Proportion (higher is better): Gleaner Top Score (0.4635)

## Limitations

- Reduced RQ1 currently summarizes existing Gleaner sampler variants; full cross-baseline sampler comparison needs additional TracePicker/TraStrainer/Sieve/Sifter reports.
- Plot files are intentionally omitted to keep expected-output comparison stable.
