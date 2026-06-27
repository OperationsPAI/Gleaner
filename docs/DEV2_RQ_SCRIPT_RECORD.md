# dev2 RQ Script Record

Source branch: https://github.com/YifanYang6/Gleaner/tree/dev2
Source commit: `e6dd21211347802c6611db5c94454a64f8e4862b`
Recorded on: 2026-06-27

This record preserves the old RQ plotting/table scripts from the `dev2` branch so that the ISSTA 2026 artifact scripts can be regenerated with artifact-friendly paths, configs, and expected outputs.

## Scripts To Reuse

| RQ | Old script | Purpose | Main input assumed by old script | Main outputs |
|---|---|---|---|---|
| RQ1 | `rq1_quality_evaluation_compact.py` | Sampling quality overview: coverage, diversity, anomaly metrics | `output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet` from old `/home/nn/workspace/gleaner-rc` path | `plots/rq1_comprehensive_quality_compact.{png,pdf}`, `plots/rq1_anomaly_detection_compact.{png,pdf}`, `plots/rq1_quality_combined.{png,pdf}`, `plots/rq1_data.md` |
| RQ1 | `rq1_quality_evaluation_improved.py` | Older/improved split RQ1 figures for coverage, diversity, anomaly, overview | Same aggregated sampler report | `plots/rq1_coverage_quality_improved.{png,pdf}`, `plots/rq1_diversity_quality_improved.{png,pdf}`, `plots/rq1_anomaly_detection_quality_improved.{png,pdf}`, `plots/rq1_quality_overview_improved.{png,pdf}` |
| RQ1 | `rq1_diversity_markdown_table.py` | Shannon entropy markdown table | Same aggregated sampler report | `plots/rq1_diversity_quality_table.md` |
| RQ1 | `rq1_per_datapack_quality.py` | Per-datapack/cross-system quality analysis | `output/rcabench-platform-v2/sampler_reports/tracepicker/detailed_perf.parquet` plus old tracepicker datapack paths | `plots/rq1_cross_system_coverage.{png,pdf}`, `plots/rq1_cross_system_data.md`, `plots/datapack_statistics.md` |
| RQ2 | `rq2_rca_impact_corrected.py` | RCA impact table using ShapleyIQ, MicroRCA, and Nezha | `rca/shapleyiq/sampler.grouped.perf.parquet`, `rca/nezha/sampler.grouped.perf.parquet` | `rq2_rca_impact_results_corrected.md` |
| RQ2 | `rq2_rca_impact.py` | Older RCA impact table using ShapleyIQ and Nezha | Same RCA parquet files | `rq2_rca_impact_results.md` |
| RQ3 | `rq3_ablation_study.py` | Ablation markdown table | Same aggregated sampler report | `tables/rq3_ablation_table.md` |
| RQ3 | `rq3_ablation_study_plot.py` | Ablation overview plot and data markdown | Same aggregated sampler report | `plots/rq3_overview_ablation.{png,pdf}`, `plots/rq3_data.md` |
| RQ4 | `rq4_efficiency_evaluation.py` | Efficiency table for online mode at sampling rate 0.05 | Same aggregated sampler report | `rq4_efficiency_results.md` |

## Old Assumptions To Fix For AE

- Hard-coded absolute paths under `/home/nn/workspace/gleaner-rc` must become config/CLI arguments.
- Outputs should move from root-level `plots/`, `tables/`, and `*.md` into `output/artifact/reduced/rqX/`.
- Scripts should accept reduced/full modes and read `configs/reduced/*.yaml` or `configs/full/*.yaml`.
- RQ2 should use the corrected script as the baseline because it explicitly handles ShapleyIQ, MicroRCA, and Nezha.
- RQ5 scripts are intentionally ignored for AE because they are not needed for the planned artifact claims.
- The new artifact scripts should preserve the old metric choices and display names where possible, while adding validation against expected outputs.

## Reference Copies

Reference copies are stored under:

`docs/reference/dev2_rq_scripts/`

These copies are not intended to be run directly. They are source material for regenerating artifact-ready RQ scripts.
