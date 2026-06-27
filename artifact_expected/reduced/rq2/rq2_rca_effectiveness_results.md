# RQ2: RCA Effectiveness

This reduced artifact summarizes RCA accuracy after sampling.
- Sampling rates: 0.010, 0.100
- Metrics: AC@1 and AC@3 means grouped by RCA algorithm, sampler, and rate.
- Matched input rows: 64

## microrca

| Sampler | Rate | Rows | AC@1 Mean | AC@3 Mean |
|---|---:|---:|---:|---:|
| gleaner_latency_dominate | 0.010 | 1 | 0.4534 | 0.4907 |
| gleaner_latency_dominate | 0.100 | 1 | 0.4534 | 0.4907 |
| gleaner_log_dominate | 0.010 | 1 | 0.4534 | 0.4907 |
| gleaner_log_dominate | 0.100 | 1 | 0.4534 | 0.4907 |
| gleaner_no_ad | 0.010 | 1 | 0.4534 | 0.4907 |
| gleaner_no_ad | 0.100 | 1 | 0.4534 | 0.5155 |
| gleaner_no_dpp | 0.010 | 1 | 0.4534 | 0.4907 |
| gleaner_no_dpp | 0.100 | 1 | 0.4534 | 0.4907 |
| gleaner_no_logs | 0.010 | 1 | 0.4534 | 0.5031 |
| gleaner_no_logs | 0.100 | 1 | 0.4534 | 0.4969 |
| gleaner_no_logs_no_ad | 0.010 | 1 | 0.4534 | 0.4907 |
| gleaner_no_logs_no_ad | 0.100 | 1 | 0.4534 | 0.5031 |
| gleaner_no_rebalance | 0.010 | 1 | 0.4534 | 0.5031 |
| gleaner_no_rebalance | 0.100 | 1 | 0.4534 | 0.4969 |
| gleaner_pure_diversity | 0.010 | 1 | 0.3416 | 0.4037 |
| gleaner_pure_diversity | 0.100 | 1 | 0.4534 | 0.4783 |
| gleaner_top_score | 0.010 | 1 | 0.3354 | 0.4037 |
| gleaner_top_score | 0.100 | 1 | 0.4534 | 0.4969 |
| gleaner_wl_kernel | 0.010 | 1 | 0.4534 | 0.4845 |
| gleaner_wl_kernel | 0.100 | 1 | 0.4534 | 0.4907 |

## nezha

| Sampler | Rate | Rows | AC@1 Mean | AC@3 Mean |
|---|---:|---:|---:|---:|
| gleaner_anomaly_pure_diversity | 0.010 | 1 | 0.1366 | 0.2919 |
| gleaner_anomaly_pure_diversity | 0.100 | 1 | 0.1118 | 0.2360 |
| gleaner_latency_dominate | 0.010 | 1 | 0.1739 | 0.4099 |
| gleaner_latency_dominate | 0.100 | 1 | 0.1304 | 0.3168 |
| gleaner_log_dominate | 0.010 | 1 | 0.1801 | 0.4099 |
| gleaner_log_dominate | 0.100 | 1 | 0.1304 | 0.3168 |
| gleaner_no_ad | 0.010 | 1 | 0.1242 | 0.3168 |
| gleaner_no_ad | 0.100 | 1 | 0.1304 | 0.3106 |
| gleaner_no_dpp | 0.010 | 1 | 0.0994 | 0.2298 |
| gleaner_no_dpp | 0.100 | 1 | 0.0683 | 0.1925 |
| gleaner_no_logs | 0.010 | 1 | 0.1304 | 0.3230 |
| gleaner_no_logs | 0.100 | 1 | 0.1118 | 0.2671 |
| gleaner_no_logs_no_ad | 0.010 | 1 | 0.1366 | 0.2795 |
| gleaner_no_logs_no_ad | 0.100 | 1 | 0.1304 | 0.3043 |
| gleaner_no_rebalance | 0.010 | 1 | 0.1553 | 0.4099 |
| gleaner_no_rebalance | 0.100 | 1 | 0.1366 | 0.3043 |
| gleaner_pure_diversity | 0.010 | 1 | 0.0497 | 0.1429 |
| gleaner_pure_diversity | 0.100 | 1 | 0.0870 | 0.2174 |
| gleaner_top_score | 0.010 | 1 | 0.0311 | 0.1242 |
| gleaner_top_score | 0.100 | 1 | 0.1304 | 0.2422 |
| gleaner_wl_kernel | 0.010 | 1 | 0.1056 | 0.2981 |
| gleaner_wl_kernel | 0.100 | 1 | 0.0932 | 0.1925 |

## shapleyiq

| Sampler | Rate | Rows | AC@1 Mean | AC@3 Mean |
|---|---:|---:|---:|---:|
| gleaner_anomaly_pure_diversity | 0.010 | 1 | 0.5652 | 0.6522 |
| gleaner_anomaly_pure_diversity | 0.100 | 1 | 0.5155 | 0.6025 |
| gleaner_latency_dominate | 0.010 | 1 | 0.5404 | 0.6398 |
| gleaner_latency_dominate | 0.100 | 1 | 0.5155 | 0.6211 |
| gleaner_log_dominate | 0.010 | 1 | 0.5404 | 0.6460 |
| gleaner_log_dominate | 0.100 | 1 | 0.5217 | 0.6087 |
| gleaner_no_ad | 0.010 | 1 | 0.4161 | 0.5776 |
| gleaner_no_ad | 0.100 | 1 | 0.4472 | 0.5963 |
| gleaner_no_dpp | 0.010 | 1 | 0.4472 | 0.5963 |
| gleaner_no_dpp | 0.100 | 1 | 0.4907 | 0.6025 |
| gleaner_no_logs | 0.010 | 1 | 0.5031 | 0.6211 |
| gleaner_no_logs | 0.100 | 1 | 0.5093 | 0.6211 |
| gleaner_no_logs_no_ad | 0.010 | 1 | 0.4472 | 0.5839 |
| gleaner_no_logs_no_ad | 0.100 | 1 | 0.4845 | 0.6087 |
| gleaner_no_rebalance | 0.010 | 1 | 0.5404 | 0.6522 |
| gleaner_no_rebalance | 0.100 | 1 | 0.4969 | 0.6087 |
| gleaner_pure_diversity | 0.010 | 1 | 0.1056 | 0.2050 |
| gleaner_pure_diversity | 0.100 | 1 | 0.4721 | 0.5776 |
| gleaner_top_score | 0.010 | 1 | 0.3540 | 0.4348 |
| gleaner_top_score | 0.100 | 1 | 0.4907 | 0.5901 |
| gleaner_wl_kernel | 0.010 | 1 | 0.5155 | 0.6398 |
| gleaner_wl_kernel | 0.100 | 1 | 0.5031 | 0.6025 |

## Best Samplers By Rate

### microrca
- Rate 0.010: AC@1 gleaner_latency_dominate (0.4534); AC@3 gleaner_no_logs (0.5031)
- Rate 0.100: AC@1 gleaner_latency_dominate (0.4534); AC@3 gleaner_no_ad (0.5155)

### nezha
- Rate 0.010: AC@1 gleaner_log_dominate (0.1801); AC@3 gleaner_latency_dominate (0.4099)
- Rate 0.100: AC@1 gleaner_no_rebalance (0.1366); AC@3 gleaner_latency_dominate (0.3168)

### shapleyiq
- Rate 0.010: AC@1 gleaner_anomaly_pure_diversity (0.5652); AC@3 gleaner_anomaly_pure_diversity (0.6522)
- Rate 0.100: AC@1 gleaner_log_dominate (0.5217); AC@3 gleaner_latency_dominate (0.6211)
