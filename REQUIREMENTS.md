# Requirements

## Platform

- Architecture: x86_64 Linux.
- Container runtime: Docker 24+ recommended for the verified container path; Podman 4+ may work but has not been separately verified.
- Python: the Gleaner artifact runner uses Python 3.13.
- Core platform dependency: `rcabench-platform==0.4.1`.

## Reduced Evaluation

- Command: `bash scripts/run_reduced_all.sh`.
- Current verification: reviewer-verified as passing end to end on host and verified inside Docker with `docker run --rm gleaner-issta2026-ae bash scripts/run_reduced_all.sh`.
- RQ coverage: reduced RQ1, RQ2, RQ3, and RQ4 scripts are implemented and connected to wrappers; `scripts/run_reduced_plots.sh` generates reduced illustrative plots and `output/artifact/reduced/REPORT.md` after the summaries exist.
- Validation: each `scripts/run_rq*.sh` wrapper invokes `scripts/compare_expected.py` against expected outputs under `artifact_expected/reduced/rqX/`; the plot/report wrapper validates non-empty PNGs and compares plot-data/report files against `artifact_expected/reduced/figures/`.
- Reduced RQ2 evidence: staged parquet inputs are under `data/artifact/reduced/rq2/`.
- GPU: not required unless a baseline's original implementation is explicitly configured to use GPU.
- Network: not required after the container/artifact and datasets have been obtained.
- Expected runtime: the full reduced command, including reduced plot/report generation, completed on the local host in 4.31 seconds wall-clock time (`time -p bash scripts/run_reduced_all.sh`, 2026-06-28). Reviewers should budget under 5 minutes for this path on a typical x86_64 Linux machine, including environment startup variability.
- Reduced evidence manifest: `data/artifact/reduced/MANIFEST.json`.
- Reduced evidence checksum list: `data/artifact/reduced/SHA256SUMS`.
- Reduced evidence verification: `bash scripts/prepare_reduced_data.sh`.
- Reduced manifest totals: 23 files, 513364 bytes. Scope is existing reduced evidence, expected outputs, and expected plot-data/report files, not raw full/reduced datapack directories.

## Validation And Tolerances

- Successful reduced reproduction means `bash scripts/prepare_reduced_data.sh`, `bash scripts/smoke_test.sh`, and `bash scripts/run_reduced_all.sh` all exit with status 0.
- `scripts/compare_expected.py` compares JSON, CSV, and Markdown outputs against `artifact_expected/reduced/rqX/` and `artifact_expected/reduced/figures/`.
- Numeric JSON/CSV values use strict default tolerances of `abs_tol=1e-12` and `rel_tol=1e-12`.
- JSON comparison ignores `config.output_dir` by default so reviewers can choose a different output directory.
- Markdown comparison normalizes lines named `output directory` or `output_dir` by default; all other Markdown content must match.
- Boolean JSON values are type-checked separately from numbers, so `true`/`false` cannot silently match `1`/`0`.
- Plot images are validated by existence and non-empty file size; image bytes are not compared because rendering metadata can vary across environments.

## Troubleshooting

- If `scripts/prepare_reduced_data.sh` reports a checksum or size mismatch, restore the reduced files listed in `data/artifact/reduced/MANIFEST.json` before rerunning experiments.
- If an expected-output comparison fails, inspect the reported JSON path, CSV row/column, or Markdown unified diff; generated outputs remain under `output/artifact/reduced/`.
- If the smoke test reports skipped SHA verification, the run is likely from an archive or container without `.git`; this is expected only when `third_party/` directories are present and non-empty.

## Full Evaluation

- Command: `bash scripts/run_full_all.sh`.
- Current behavior: intentionally exits non-zero with a not-implemented/not-reviewer-verified message.
- Current verification: not a runnable verified reproduction path in this artifact snapshot.
- Intended future scope: full TracePicker dataset plus full Gleaner dataset.
- Expected runtime and storage: substantially larger than the reduced evaluation; exact numbers will be added only after implementation and benchmarking.
- Reviewer guidance: use `bash scripts/run_reduced_all.sh` as the verified RQ1-RQ4 AE reproduction path.

## Packaging And Archive

- Verified Docker build: `docker build -t gleaner-issta2026-ae .`.
- Verified container smoke: `docker run --rm gleaner-issta2026-ae bash scripts/smoke_test.sh`.
- Verified container reduced run: `docker run --rm gleaner-issta2026-ae bash scripts/run_reduced_all.sh`.
- Local archive/package script: `bash scripts/package_artifact.sh`.
- Local archive manifest/checksum: generated and verified by the package script as `ARCHIVE_MANIFEST.tsv` inside the tarball and a sibling `.sha256` file under `dist/`.
- Public archive/release upload: not yet prepared or performed.
- DOI and HotCRP artifact link: not yet minted or submitted.
