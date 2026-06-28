# RQ1-B: Dataset B Cross-System Evidence

## Configuration

- Input root: `../TracePicker/TracePicker/data`
- Output directory: `output/artifact/reduced/rq1_cross_system`
- Systems: Train Ticket, Media, Online Boutique, Sock Shop, Social Network
- Scope: reduced cross-system evidence from TracePicker Dataset B raw traces; full sampler-baseline cross-system reproduction is reserved for the full pipeline.

## Cross-System Summary

| System | Traces | Spans | Services | Operations | Path Types | Avg Spans/Trace | Trace Error Rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Train Ticket | 22000 | 1661000 | 30 | 64 | 145 | 75.5000 | 0.0528 |
| Media | 28710 | 486074 | 7 | 18 | 9 | 16.9305 | 0.0000 |
| Online Boutique | 42074 | 1019375 | 10 | 40 | 72 | 24.2281 | 0.0001 |
| Sock Shop | 43472 | 235062 | 6 | 34 | 143 | 5.4072 | 0.0000 |
| Social Network | 32123 | 287044 | 12 | 30 | 33 | 8.9358 | 0.0000 |

## Interpretation

- Dataset B spans five heterogeneous microservice systems with different trace volumes, service counts, path types, and span depths.
- This reduced evidence supports the cross-system part of RQ1 at the dataset-diversity/input-coverage level without rerunning expensive baseline samplers.
- Full paper-equivalent cross-system sampler comparison should use the full pipeline to regenerate TracePicker sampler reports and paper figures.
