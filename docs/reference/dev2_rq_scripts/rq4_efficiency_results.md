# RQ4: Efficiency Evaluation

This table shows the efficiency performance of different sampling algorithms.
**Configuration**: Sampling Rate = 0.05, Mode = Online
**Metrics**: runtime_per_trace_ms, benefit_cost_ratio, actual_sampling_rate, controllability

## Efficiency Performance Summary

| Algorithm | Runtime Per Trace Ms | Benefit Cost Ratio | Actual Sampling Rate | Controllability |
|-----------|------------|------------|------------|------------|
| Gleaner | 1.214 | 0.85 | 4.9% | 0.0128 |
| Random | 0.008 | 0.41 | 5.0% | 0.0390 |
| Sieve | 0.629 | 0.33 | 33.2% | 5.6422 |
| Sifter | 1.220 | 0.21 | 94.3% | 17.8924 |
| TracePicker | 1.008 | 0.76 | 5.0% | 0.0007 |
| TrasTrainer | 69.954 | 0.44 | 11.3% | 1.2582 |
| TrasTrainer w/o Metrics | 1.349 | 0.17 | 72.0% | 13.4144 |

## Performance Analysis

### Runtime Per Trace Ms

**Fastest**: Random (0.008 ms)
**Slowest**: TrasTrainer (69.954 ms)

### Benefit Cost Ratio

**Best**: Gleaner (0.8543)
**Worst**: TrasTrainer w/o Metrics (0.1698)

### Actual Sampling Rate

**Best**: Sifter (94.3%)
**Worst**: Gleaner (4.9%)

### Controllability

**Best**: Sifter (17.8924)
**Worst**: TracePicker (0.0007)

## Overall Efficiency Ranking

**Ranking methodology**: Combined score considering all metrics
(Lower runtime is better, higher values are better for other metrics)

1. **Sifter** (Score: 0.759)
2. **TrasTrainer w/o Metrics** (Score: 0.620)
3. **Gleaner** (Score: 0.496)
4. **Sieve** (Score: 0.465)
5. **TracePicker** (Score: 0.464)
6. **Random** (Score: 0.340)
7. **TrasTrainer** (Score: 0.134)
