# RQ2: RCA Effectiveness

This reduced artifact summarizes RCA accuracy after sampling.
- Sampling rates: 0.010, 0.100
- Metrics: AC@1 and AC@3 means grouped by RCA algorithm, sampler, and rate.
- Matched input rows: 64

## microrca

| Sampler | Rate | Rows | AC@1 Mean | AC@3 Mean |
|---|---:|---:|---:|---:|
| gleaner_latency_dominate | 0.010 | 1 | 0.3500 | 0.3500 |
| gleaner_latency_dominate | 0.100 | 1 | 0.3500 | 0.4000 |
| gleaner_log_dominate | 0.010 | 1 | 0.3500 | 0.3500 |
| gleaner_log_dominate | 0.100 | 1 | 0.3500 | 0.4000 |
| gleaner_no_ad | 0.010 | 1 | 0.3500 | 0.3500 |
| gleaner_no_ad | 0.100 | 1 | 0.3500 | 0.4000 |
| gleaner_no_dpp | 0.010 | 1 | 0.3500 | 0.4000 |
| gleaner_no_dpp | 0.100 | 1 | 0.3500 | 0.4000 |
| gleaner_no_logs | 0.010 | 1 | 0.3500 | 0.3500 |
| gleaner_no_logs | 0.100 | 1 | 0.3500 | 0.4000 |
| gleaner_no_logs_no_ad | 0.010 | 1 | 0.3500 | 0.3500 |
| gleaner_no_logs_no_ad | 0.100 | 1 | 0.3500 | 0.4000 |
| gleaner_no_rebalance | 0.010 | 1 | 0.3500 | 0.3500 |
| gleaner_no_rebalance | 0.100 | 1 | 0.3500 | 0.4000 |
| gleaner_pure_diversity | 0.010 | 1 | 0.1500 | 0.2000 |
| gleaner_pure_diversity | 0.100 | 1 | 0.3500 | 0.3500 |
| gleaner_top_score | 0.010 | 1 | 0.2500 | 0.3500 |
| gleaner_top_score | 0.100 | 1 | 0.3500 | 0.4500 |
| gleaner_wl_kernel | 0.010 | 1 | 0.3500 | 0.3500 |
| gleaner_wl_kernel | 0.100 | 1 | 0.3500 | 0.4000 |

## nezha

| Sampler | Rate | Rows | AC@1 Mean | AC@3 Mean |
|---|---:|---:|---:|---:|
| gleaner_anomaly_pure_diversity | 0.010 | 1 | 0.1000 | 0.2000 |
| gleaner_anomaly_pure_diversity | 0.100 | 1 | 0.0500 | 0.1500 |
| gleaner_latency_dominate | 0.010 | 1 | 0.1000 | 0.3000 |
| gleaner_latency_dominate | 0.100 | 1 | 0.1500 | 0.2500 |
| gleaner_log_dominate | 0.010 | 1 | 0.1500 | 0.3000 |
| gleaner_log_dominate | 0.100 | 1 | 0.1000 | 0.2000 |
| gleaner_no_ad | 0.010 | 1 | 0.1500 | 0.4000 |
| gleaner_no_ad | 0.100 | 1 | 0.1000 | 0.1000 |
| gleaner_no_dpp | 0.010 | 1 | 0.0500 | 0.1500 |
| gleaner_no_dpp | 0.100 | 1 | 0.1000 | 0.3000 |
| gleaner_no_logs | 0.010 | 1 | 0.2000 | 0.4000 |
| gleaner_no_logs | 0.100 | 1 | 0.1000 | 0.1500 |
| gleaner_no_logs_no_ad | 0.010 | 1 | 0.1500 | 0.4500 |
| gleaner_no_logs_no_ad | 0.100 | 1 | 0.1000 | 0.2500 |
| gleaner_no_rebalance | 0.010 | 1 | 0.0500 | 0.4000 |
| gleaner_no_rebalance | 0.100 | 1 | 0.2000 | 0.2000 |
| gleaner_pure_diversity | 0.010 | 1 | 0.0500 | 0.1000 |
| gleaner_pure_diversity | 0.100 | 1 | 0.1000 | 0.2000 |
| gleaner_top_score | 0.010 | 1 | 0.0000 | 0.1500 |
| gleaner_top_score | 0.100 | 1 | 0.1500 | 0.2500 |
| gleaner_wl_kernel | 0.010 | 1 | 0.0500 | 0.1500 |
| gleaner_wl_kernel | 0.100 | 1 | 0.1000 | 0.1500 |

## shapleyiq

| Sampler | Rate | Rows | AC@1 Mean | AC@3 Mean |
|---|---:|---:|---:|---:|
| gleaner_anomaly_pure_diversity | 0.010 | 1 | 0.5500 | 0.7000 |
| gleaner_anomaly_pure_diversity | 0.100 | 1 | 0.4500 | 0.6000 |
| gleaner_latency_dominate | 0.010 | 1 | 0.4500 | 0.7000 |
| gleaner_latency_dominate | 0.100 | 1 | 0.4500 | 0.6000 |
| gleaner_log_dominate | 0.010 | 1 | 0.4500 | 0.7000 |
| gleaner_log_dominate | 0.100 | 1 | 0.4500 | 0.6000 |
| gleaner_no_ad | 0.010 | 1 | 0.4500 | 0.7000 |
| gleaner_no_ad | 0.100 | 1 | 0.4500 | 0.5500 |
| gleaner_no_dpp | 0.010 | 1 | 0.4000 | 0.5500 |
| gleaner_no_dpp | 0.100 | 1 | 0.4500 | 0.6000 |
| gleaner_no_logs | 0.010 | 1 | 0.5000 | 0.6500 |
| gleaner_no_logs | 0.100 | 1 | 0.4500 | 0.6000 |
| gleaner_no_logs_no_ad | 0.010 | 1 | 0.4500 | 0.6000 |
| gleaner_no_logs_no_ad | 0.100 | 1 | 0.4500 | 0.6000 |
| gleaner_no_rebalance | 0.010 | 1 | 0.4500 | 0.6500 |
| gleaner_no_rebalance | 0.100 | 1 | 0.4500 | 0.6000 |
| gleaner_pure_diversity | 0.010 | 1 | 0.0500 | 0.2000 |
| gleaner_pure_diversity | 0.100 | 1 | 0.4000 | 0.4500 |
| gleaner_top_score | 0.010 | 1 | 0.3500 | 0.5000 |
| gleaner_top_score | 0.100 | 1 | 0.4500 | 0.6000 |
| gleaner_wl_kernel | 0.010 | 1 | 0.4500 | 0.6500 |
| gleaner_wl_kernel | 0.100 | 1 | 0.4500 | 0.5500 |

## Best Samplers By Rate

### microrca
- Rate 0.010: AC@1 gleaner_latency_dominate (0.3500); AC@3 gleaner_no_dpp (0.4000)
- Rate 0.100: AC@1 gleaner_latency_dominate (0.3500); AC@3 gleaner_top_score (0.4500)

### nezha
- Rate 0.010: AC@1 gleaner_no_logs (0.2000); AC@3 gleaner_no_logs_no_ad (0.4500)
- Rate 0.100: AC@1 gleaner_no_rebalance (0.2000); AC@3 gleaner_no_dpp (0.3000)

### shapleyiq
- Rate 0.010: AC@1 gleaner_anomaly_pure_diversity (0.5500); AC@3 gleaner_anomaly_pure_diversity (0.7000)
- Rate 0.100: AC@1 gleaner_anomaly_pure_diversity (0.4500); AC@3 gleaner_anomaly_pure_diversity (0.6000)
