# Requirements

## Platform

- Architecture: x86_64 Linux.
- Container runtime: Docker 24+ recommended for the verified container path; Podman 4+ may work but has not been separately verified.
- Python: the Gleaner artifact runner uses Python 3.13.
- Core platform dependency: `rcabench-platform==0.4.1`.

## Reduced Evaluation

- Command: `bash scripts/run_reduced_all.sh`.
- Current verification: reviewer-verified as passing end to end on host and verified inside Docker with `docker run --rm gleaner-issta2026-ae bash scripts/run_reduced_all.sh`.
- RQ coverage: reduced RQ1, RQ2, RQ3, and RQ4 scripts are implemented and connected to wrappers.
- Validation: each `scripts/run_rq*.sh` wrapper invokes `scripts/compare_expected.py` against expected outputs under `artifact_expected/reduced/rqX/`.
- Reduced RQ2 evidence: staged parquet inputs are under `data/artifact/reduced/rq2/`.
- GPU: not required unless a baseline's original implementation is explicitly configured to use GPU.
- Network: not required after the container/artifact and datasets have been obtained.
- Expected runtime: to be filled after the reduced scripts are benchmarked.
- Reduced evidence manifest: `data/artifact/reduced/MANIFEST.json`.
- Reduced evidence checksum list: `data/artifact/reduced/SHA256SUMS`.
- Reduced evidence verification: `bash scripts/prepare_reduced_data.sh`.
- Reduced manifest totals: 16 files, 450107 bytes. Scope is existing reduced evidence and expected outputs, not raw full/reduced datapack directories.

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
