# Gleaner ISSTA 2026 Artifact

This document is the reviewer-facing entry point for the ISSTA 2026 artifact evaluation package.

## Artifact Overview

Progress checklist: see `docs/ISSTA_AE_CHECKLIST.md`.

The artifact evaluates Gleaner against baseline samplers and RCA algorithms using `rcabench-platform==0.4.1`.

Included components:

- Gleaner sampler and variants from this repository.
- RCA algorithms: MicroRCA and ShapleyIQ from ShapleyIQ, and Nezha from Nezha.
- Baseline samplers: TracePicker, TraStrainer, Sieve, and Sifter.
- Reduced artifact scripts for RQ1, RQ2, RQ3, and RQ4.
- Expected reduced outputs under `artifact_expected/reduced/rq1/` through `artifact_expected/reduced/rq4/`.
- Reduced RQ2 RCA evidence under `data/artifact/reduced/rq2/`.
- A guarded full-mode runner that intentionally exits non-zero because full reproduction is not implemented or reviewer-verified in this artifact snapshot.

Open items are tracked in `STATUS.md` and `docs/ISSTA_AE_TODO.md`. The reduced RQ1-RQ4 path is the verified reproduction path; full-path implementation/verification remains incomplete. Local archive packaging is available through `scripts/package_artifact.sh` and documented in `docs/RELEASE_PACKAGING.md`, but public upload, DOI minting, and HotCRP link submission remain external/manual and are not yet complete.

## Getting Started: 30-minute Path

```bash
git submodule update --init --recursive
uv sync --locked
bash scripts/smoke_test.sh
```

The smoke test verifies pinned submodule versions when Git metadata is available. In Docker/archive contexts without `.git`, it verifies the `third_party/` directories exist and are non-empty and clearly reports that SHA verification is skipped. The Python environment and artifact runner imports are also checked.


## Docker Path

Build the verified image:

```bash
docker build -t gleaner-issta2026-ae .
```

Run the verified container smoke test:

```bash
docker run --rm gleaner-issta2026-ae bash scripts/smoke_test.sh
```

Run the verified reduced reproduction inside the container:

```bash
docker run --rm gleaner-issta2026-ae bash scripts/run_reduced_all.sh
```

The Docker image embeds the reduced inputs needed by the verified path, including `artifact_expected/`, `data/artifact/`, and the reduced Gleaner sampler reports used by RQ1.

## Reduced Reproduction

Run all reduced experiments:

```bash
bash scripts/run_reduced_all.sh
```

The current `scripts/run_reduced_all.sh` path is reviewer-verified as passing end to end. It runs the smoke test and then RQ1/RQ2/RQ3/RQ4 in sequence. The reduced path is CPU-only compatible and has been verified with `CUDA_VISIBLE_DEVICES='' bash scripts/run_reduced_all.sh`.

Observed host runtime on 2026-06-28:

```text
time -p bash scripts/run_reduced_all.sh
real 2.96
user 16.51
sys 10.91
```

Reviewers should budget under 5 minutes for the reduced path on a typical x86_64 Linux machine. Container startup and first-time dependency setup may add extra time.

Or run individual RQs:

```bash
bash scripts/run_rq1_sampling_quality.sh
bash scripts/run_rq2_rca_effectiveness.sh
bash scripts/run_rq3_ablation.sh
bash scripts/run_rq4_efficiency.sh
```

Each individual wrapper runs its corresponding `scripts/artifact/rq*.py` script and then invokes `scripts/compare_expected.py` to compare actual outputs with the expected files under `artifact_expected/reduced/rqX/`.

Actual outputs are written under `output/artifact/reduced/`. Expected outputs are committed under `artifact_expected/reduced/`.

Expected-output checks are intentionally strict. JSON and CSV numeric values use default absolute and relative tolerances of `1e-12`; JSON `config.output_dir` is ignored by default; Markdown lines named `output directory` or `output_dir` are normalized by default; boolean JSON values are not treated as numeric aliases.

## Reduced Input Evidence

Verify the reduced evidence and expected-output files before running the reduced reproduction:

```bash
bash scripts/prepare_reduced_data.sh
```

The reduced manifest is `data/artifact/reduced/MANIFEST.json`, with optional checksum list `data/artifact/reduced/SHA256SUMS`. Its scope is the committed reduced evidence plus expected outputs: the reduced RQ1 Gleaner sampler reports, reduced RQ2 RCA evidence, and `artifact_expected/reduced/rq1/` through `artifact_expected/reduced/rq4/`. It does not include or synthesize raw 10-datapack directories.

The reduced RQ2 RCA evidence needed by `scripts/run_rq2_rca_effectiveness.sh` is committed at:

- `data/artifact/reduced/rq2/shapleyiq_microrca/sampler.grouped.perf.parquet`
- `data/artifact/reduced/rq2/nezha/sampler.grouped.perf.parquet`

## Full Reproduction

The full path is intentionally not presented as a runnable, verified reproduction in this artifact snapshot. Normal execution of `bash scripts/run_full_all.sh` prints a clear not-implemented/not-reviewer-verified message and exits non-zero so reviewers do not mistake a placeholder for success.

Use the verified reduced path instead:

```bash
bash scripts/run_reduced_all.sh
```

A future full path is expected to cover the complete TracePicker and Gleaner datasets and may take substantially longer than one day depending on hardware.

## Claim Mapping

The exact paper locations below were extracted from `paper/main.pdf` with `pdftotext`. The artifact wrapper numbering differs from the current paper for two middle results: the artifact keeps dev2 script names where `run_rq2_rca_effectiveness.sh` is RCA and `run_rq3_ablation.sh` is ablation; the paper labels ablation as RQ2 and downstream RCA as RQ3.

| Paper claim/result | Paper location recovered from `paper/main.pdf` | Reduced command | Actual output | Expected output | Current status |
|---|---|---|---|---|---|
| Sampling quality and diversity | Paper RQ1 "Sampling Quality and Diversity"; Fig. 4 "Sampling quality evaluation on Dataset A"; Fig. 5 "Cross-system evaluation on Dataset B (5 microservice benchmarks)"; Finding 1 | `bash scripts/run_rq1_sampling_quality.sh` | `output/artifact/reduced/rq1/` | `artifact_expected/reduced/rq1/` | Reduced script summarizes committed Gleaner variant reports. It does not reproduce the full cross-baseline Figure 4/Figure 5 plots. |
| Ablation study | Paper RQ2 "Ablation Study"; Table 5 "Summary of Gleaner variants designed for ablation study"; Fig. 6 "Ablation study Group 1"; Fig. 7 "Ablation study Group 2"; Table 7 "Ablation analysis on RCA accuracy"; Finding 2 | `bash scripts/run_rq3_ablation.sh` | `output/artifact/reduced/rq3/` | `artifact_expected/reduced/rq3/` | Reduced artifact computes tabular Gleaner-variant ablation summaries from `aggregated_perf.parquet`; paper plotting scripts are not included. |
| Downstream RCA accuracy | Paper RQ3 "Impact on Downstream Root Cause Analysis"; Table 6 "RCA accuracy comparison on Dataset A"; Table 7 "Ablation analysis on RCA accuracy"; Finding 3 | `bash scripts/run_rq2_rca_effectiveness.sh` | `output/artifact/reduced/rq2/` | `artifact_expected/reduced/rq2/` | Reduced script summarizes committed MicroRCA/ShapleyIQ and Nezha RCA parquet evidence for AC@1/AC@3 at 1% and 10%. |
| Efficiency analysis | Paper RQ4 "Efficiency Analysis"; Table 8 "Efficiency comparison on Dataset A at 5% target sampling rate"; Finding 4 | `bash scripts/run_rq4_efficiency.sh` | `output/artifact/reduced/rq4/` | `artifact_expected/reduced/rq4/` | Reduced script summarizes runtime, benefit-cost ratio, actual sampling rate, and controllability from the committed sampler report. |

The combined reduced path was measured at 2.96 seconds wall-clock time on the local host. Full-dataset claims, full cross-baseline plots, and paper-ready figure generation are not reviewer-verified by this artifact snapshot. The reduced outputs are intended as deterministic evidence that the included scripts and committed reduced inputs reproduce the summarized metrics.

## Output Schemas

- Sampler reports for RQ1/RQ3/RQ4 use parquet files with at least `sampler`, `mode`, and `sampling_rate`. `detailed_perf.parquet` additionally needs `datapack` for per-datapack counts. Optional metric columns consumed when present include coverage, entropy, anomaly proportion, benefit-cost, runtime, actual sampling rate, and controllability fields documented in the generated JSON `schema` blocks.
- RCA reports for RQ2 use parquet files with `algorithm`, `sampler.name`, `sampler.rate`, `AC@1`, and `AC@3`. The wrapper accepts ShapleyIQ/MicroRCA and Nezha parquet paths via CLI flags or the default reduced-data locations.
- Reduced outputs are emitted as Markdown, CSV, and JSON under `output/artifact/reduced/rqX/`. JSON files include configuration metadata and machine-readable rows; CSV files provide stable tabular comparison inputs; Markdown files are reviewer-readable summaries.
- Expected-output validation compares generated files against `artifact_expected/reduced/rqX/` with `scripts/compare_expected.py` using the strict tolerance policy described above.

## Reuse Guide For New Datapacks

1. Prepare compatible sampler reports for the new datapacks. For RQ1/RQ3/RQ4, write `aggregated_perf.parquet` and, for RQ1, `detailed_perf.parquet` with the schema described above. The default committed examples live under `output/rcabench-platform-v2/sampler_reports/gleaner/`.
2. Prepare compatible RCA reports if evaluating downstream localization. `scripts/run_rq2_rca_effectiveness.sh` looks for ShapleyIQ/MicroRCA and Nezha `sampler.grouped.perf.parquet` files in its default locations, or you can pass `--shapleyiq-microrca-parquet PATH` and `--nezha-parquet PATH`.
3. Run the reduced scripts with explicit input and output paths when testing new data, for example `uv run python scripts/artifact/rq1_sampling_quality.py --input-aggregated PATH/aggregated_perf.parquet --input-detailed PATH/detailed_perf.parquet --output-dir output/artifact/reduced/rq1-new`.
4. Use the wrapper scripts for committed reduced evidence and expected-output checks. For new datapacks, create a separate expected directory only after manually reviewing the first generated outputs; do not overwrite `artifact_expected/reduced/` unless intentionally updating the artifact baseline.
5. Extend sampler or baseline support by producing the same sampler-report schema for the new method. Extend RCA support by producing the same RCA parquet schema and, if needed, adding a wrapper flag/path in `scripts/run_rq2_rca_effectiveness.sh` plus expected outputs.
6. Keep validation evidence explicit: record input paths, generated output paths, command lines, and checksum or manifest updates for any new datapack bundle.

## Data Provenance And Scope

The committed reduced data is a compact evidence bundle derived from local RCAbench Platform v2/Gleaner outputs and expected-output files. `data/artifact/reduced/MANIFEST.json` and `data/artifact/reduced/SHA256SUMS` record file sizes and SHA256 values for the reduced evidence set. The package does not include the raw full datasets, does not synthesize missing raw datapacks, and does not claim full-dataset reproducibility.

## Troubleshooting

- If `bash scripts/prepare_reduced_data.sh` fails, compare the reported path against `data/artifact/reduced/MANIFEST.json`; the reduced files must match the recorded byte sizes and SHA256 values.
- If `scripts/compare_expected.py` fails, use its reported JSON path, CSV row/column, or Markdown diff to inspect the generated files under `output/artifact/reduced/`.
- If Markdown differs only by output directory, ensure the wrappers are using the default comparison mode; output-directory lines are normalized by default.
- If `scripts/smoke_test.sh` reports skipped submodule SHA checks, confirm the run is from a packaged archive/container without `.git` and that each `third_party/` directory is present and non-empty.

## Local Release Packaging

Build a local archive and checksum with:

```bash
bash scripts/package_artifact.sh
```

The script writes `dist/gleaner-issta2026-ae-<git-short-sha-or-worktree>.tar.gz`, an external `.sha256` file, and an internal `ARCHIVE_MANIFEST.tsv` inside the archive. It packages the reduced artifact contents, selected reduced sampler reports, and actual `third_party/` file contents while excluding `.git`, `.venv`, caches, generated `output/artifact/`, raw/full data, and `dist/` itself. See `docs/RELEASE_PACKAGING.md` for details.

No public archive URL, DOI, or HotCRP artifact link has been minted or submitted yet. Do not add placeholder links or identifiers.

## Anonymous Review Considerations

ISSTA 2026 AE does not appear to require author anonymization of the artifact itself. It does require that artifact links be hosted on a platform that does not track reviewer IP addresses, to protect reviewer anonymity.
