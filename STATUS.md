# Artifact Status

This file states the ACM/ISSTA artifact badges requested and why the packaged artifact supports them. The artifact is packaged as Docker image archives and includes a reduced <=1-day scope plus a long-running full scope.

## Badges Requested

- Artifacts Evaluated - Functional
- Artifacts Evaluated - Reusable
- Artifacts Available

## Functional Justification

The artifact is documented, consistent, complete for its stated scopes, exercisable, and includes validation evidence.

- The reduced image is the primary ISSTA AE path. It contains `gleaner_lite` and `tracepicker_lite`, runs without GPUs, and is designed to complete in one day or less.
- The full image is provided for long-running complete-setting validation. It adds complete Gleaner Dataset A (`gleaner`), complete converted TracePicker Dataset B (`tracepicker`), full-path scripts, and isolated full-only baseline environments.
- The Getting Started path uses `scripts/smoke_test.sh`; successful output includes `gleaner import OK`, `rcabench-platform 0.4.1`, and `[smoke] smoke test complete`.
- The reduced reproduction entry point is `scripts/run_reduced_all.sh`. It runs reduced RQ1/RQ2/RQ3/RQ4 scripts, reduced plots, and `output/artifact/reduced/REPORT.md` generation.
- Reduced wrappers fail on missing inputs or empty required outputs. Strict frozen-output comparison is available with `GLEANER_COMPARE_EXPECTED=1` against `artifact_expected/reduced/`.
- `scripts/prepare_reduced_data.sh` checks that `gleaner_lite` and `tracepicker_lite` live converted inputs are present under `data/rcabench-platform-v2/`.
- Full reproduction is guarded by `GLEANER_RUN_FULL=1 bash scripts/run_full_all.sh`; without the guard it exits non-zero so placeholder full results cannot be mistaken for verified evidence.

## Paper-Claim Scope

- Reduced RQ1-A: sampling quality/diversity on `gleaner_lite` with Gleaner and the available reduced baseline `random`.
- Reduced RQ1-B: Dataset B Trace Pattern Coverage on `tracepicker_lite` (`trainticket`, `media`) with Gleaner w/o Logs & Alarms.
- Reduced RQ2: Gleaner ablation summaries using paper-facing variant names.
- Reduced RQ3: downstream RCA Accuracy@1/Accuracy@3 with MicroRCA, ShapleyIQ, and Nezha on full and sampled `gleaner_lite` inputs.
- Reduced RQ4: online efficiency at 5% target sampling rate for Gleaner and Gleaner WL Kernel.
- Full image: complete Dataset A, complete converted Dataset B, full-path sampler/RCA/baseline orchestration, and paper-facing rates for long-running validation.

## Reusable Justification

The artifact is structured and documented for reuse beyond the exact reduced scripts.

- `README.md` gives the main Getting Started and step-by-step reproduction instructions.
- `docs/RCABENCH_SAMPLE_CLI.md` documents sampler/RCA CLI usage, `sample single`, `sample batch`, `-s`, rates, modes, clear/rerun flags, CPU settings, and sampled-input auto-discovery.
- `docs/new-inputs.md` documents how to adapt TracePicker trace-only inputs and raw RCABench/ClickHouse OpenTelemetry datapacks.
- `docs/extending.md` documents sampler/RCA extension contracts and expected report schemas.
- `docs/troubleshooting.md` documents common conversion, detector, report, and dependency issues.
- Purpose-specific agent workflow notes are stored under `docs/agent_skills/`.
- `data/rcabench_dataset/` and `data/tracepicker/` are included as small raw-input examples in both images for reuse documentation.
- Third-party source/license notes are documented in `docs/THIRD_PARTY.md`; TracePicker and TraStrainer license status remains unknown because no license file is present in the vendored snapshots.

## Available Justification

This artifact is hosted on Zenodo and has a DOI recorded in the final artifact submission record. The Zenodo deposit contains:

- the reduced Docker image archive and `.sha256` file;
- the full Docker image archive and `.sha256` file;
- `README.md`, `REQUIREMENTS.md`, `STATUS.md`, and `LICENSE` as plain-text files;
- supporting documentation under `docs/`;
- public download access suitable for artifact evaluation.

## Packaging Status

- Docker image archive builder: `scripts/package_docker_images.sh`.
- Export format: `docker save | gzip`, with sibling SHA-256 files under `dist/`.
- Reduced archive naming: `gleaner-issta2026-ae-reduced-<version>.docker.tar.gz`.
- Full archive naming: `gleaner-issta2026-ae-full-<version>.docker.tar.gz`.
- Optional source archive builder: `scripts/package_artifact.sh`.
