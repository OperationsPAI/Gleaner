# Reduced Artifact Report

This report is generated from the reduced artifact summary CSVs.

Important caveat: the PNGs are reduced illustrative plots generated from the reduced artifact summaries. They are not claimed to be exact reproductions of the full-paper Fig. 4-Fig. 7 or paper-ready tables.

## Inputs

- `output/artifact/reduced/rq1/rq1_sampling_quality_summary.csv`
- `output/artifact/reduced/rq2/rq2_rca_effectiveness_summary.csv`
- `output/artifact/reduced/rq3/rq3_ablation_summary.csv`
- `output/artifact/reduced/rq4/rq4_efficiency_summary.csv`

## RQ Mapping

| Artifact output | Paper target | Generated plot | Plot data |
|---|---|---|---|
| RQ1 | Paper RQ1: Sampling Quality and Diversity (Fig. 4, Fig. 5, Finding 1) | `output/artifact/reduced/figures/rq1_sampling_quality_metrics.png` | `output/artifact/reduced/figures/rq1_sampling_quality_plot_data.csv` |
| RQ2 | Paper RQ3: Impact on Downstream Root Cause Analysis (Table 6, Table 7, Finding 3) | `output/artifact/reduced/figures/rq2_rca_effectiveness_ac.png` | `output/artifact/reduced/figures/rq2_rca_effectiveness_plot_data.csv` |
| RQ3 | Paper RQ2: Ablation Study (Table 5, Fig. 6, Fig. 7, Table 7, Finding 2) | `output/artifact/reduced/figures/rq3_ablation_metrics.png` | `output/artifact/reduced/figures/rq3_ablation_plot_data.csv` |
| RQ4 | Paper RQ4: Efficiency Analysis (Table 8, Finding 4) | `output/artifact/reduced/figures/rq4_efficiency_metrics.png` | `output/artifact/reduced/figures/rq4_efficiency_plot_data.csv` |

## Generated Outputs

### RQ1

- Plot: `output/artifact/reduced/figures/rq1_sampling_quality_metrics.png`
- Plot data: `output/artifact/reduced/figures/rq1_sampling_quality_plot_data.csv`
- Selected metrics: avg_api_coverage, avg_path_coverage_dedup, avg_unique_trace_coverage, avg_shannon_entropy, avg_proportion_anomaly
- Plot-data rows: 50

### RQ2

- Plot: `output/artifact/reduced/figures/rq2_rca_effectiveness_ac.png`
- Plot data: `output/artifact/reduced/figures/rq2_rca_effectiveness_plot_data.csv`
- Selected metrics: ac_at_1_mean, ac_at_3_mean
- Plot-data rows: 128

### RQ3

- Plot: `output/artifact/reduced/figures/rq3_ablation_metrics.png`
- Plot data: `output/artifact/reduced/figures/rq3_ablation_plot_data.csv`
- Selected metrics: avg_api_coverage, avg_unique_trace_coverage, avg_shannon_entropy, avg_proportion_anomaly, avg_path_coverage_dedup, avg_benefit_cost_ratio
- Plot-data rows: 60

### RQ4

- Plot: `output/artifact/reduced/figures/rq4_efficiency_metrics.png`
- Plot data: `output/artifact/reduced/figures/rq4_efficiency_plot_data.csv`
- Selected metrics: avg_runtime_per_trace_ms, avg_benefit_cost_ratio, avg_actual_sampling_rate, avg_controllability
- Plot-data rows: 40

## Validation Summary

- RQ summary generation: performed by `bash scripts/run_reduced_all.sh` before this plotting step.
- Plot-data comparison: `scripts/run_reduced_plots.sh` compares CSV/JSON/Markdown outputs against `artifact_expected/reduced/figures/` when expected files are present.
- Image validation: `scripts/run_reduced_plots.sh` checks each generated PNG exists and is non-empty; image bytes are not compared.
- Scope: reduced/offline artifact evidence only; full-dataset plotting and exact full-paper figure reproduction remain outside this snapshot.
