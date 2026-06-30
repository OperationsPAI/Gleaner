# Requirements

This file describes the architecture, hardware, software, storage, and runtime requirements for the Gleaner ISSTA 2026 artifact.

## Packaged Architecture

- CPU architecture: x86_64 Linux.
- Container format: Docker image archives generated with `docker save | gzip`.
- Python runtime inside images: Python 3.13 for the main Gleaner artifact environment.
- Package manager inside images: `uv`, copied from the official `ghcr.io/astral-sh/uv:0.8.13` image.
- Main platform dependency: `rcabench-platform==0.4.1` from the vendored editable submodule at `platform/rcabench-platform`.

## Required Host Software

- Docker 24+ recommended.
- `gunzip` or compatible gzip decompressor for loading image archives.
- `sha256sum` or compatible checksum tool for verifying archives.
- No host Python installation is required for the reviewer path.
- Network access is not required to run either the reduced or full artifact path after the Docker archives and checksum files have been obtained.

## Hardware Requirements

- GPU: not required for the reduced AE path.
- CPU: commodity multi-core x86_64 CPU recommended. The reduced path is CPU-only and benefits from multiple cores.
- Memory: at least 16 GB RAM recommended for reduced runs; 32 GB or more recommended for full/diagnostic runs.
- Storage: reserve space for both compressed archives, loaded Docker images, and generated outputs. The full image is substantially larger because it includes full datasets and heavyweight baseline environments.
- Special hardware: no specific CPU model, GPU, accelerator, or non-commodity peripheral is required for the reduced path.

## Docker Images

The final artifact deposit should provide two image archives:

| Image archive | Purpose | Contents |
|---|---|---|
| `gleaner-issta2026-ae-reduced-*.docker.tar.gz` | Primary <=1-day AE path | Source, docs, `gleaner_lite`, `tracepicker_lite`, reduced scripts, main CPU Python environment |
| `gleaner-issta2026-ae-full-*.docker.tar.gz` | Long-running full validation | Everything in reduced plus complete `gleaner`, complete converted `tracepicker`, full-path scripts, and isolated full-only baseline environments |

Load and verify an image with:

```bash
sha256sum -c gleaner-issta2026-ae-reduced-*.docker.tar.gz.sha256
gunzip -c gleaner-issta2026-ae-reduced-*.docker.tar.gz | docker load
```

## Reduced Evaluation Requirements

- Main command: `bash scripts/run_reduced_all.sh`.
- Smoke test command: `bash scripts/smoke_test.sh`.
- Dataset A reduced input: `data/rcabench-platform-v2/data/gleaner_lite` and `meta/gleaner_lite`.
- Dataset B reduced input: `data/rcabench-platform-v2/data/tracepicker_lite` and `meta/tracepicker_lite`.
- Reduced Dataset A selection: 20 datapacks selected for fault-category coverage and reduced RCA trend matching against historical full Dataset A RCA results under `rca/`.
- Reduced Dataset B selection: two TracePicker systems (`trainticket`, `media`) so RQ1-B live rerun remains within the reduced runtime budget.
- Expected runtime: designed to complete in one day or less on a typical multi-core x86_64 Linux machine.
- Output location: generated files are written under `output/`.
- Validation: reduced scripts fail on missing required inputs or empty required outputs. Optional strict comparison can be enabled with `GLEANER_COMPARE_EXPECTED=1`.

## Parallelism And CPU Controls

Reduced sampler/RCA preparation uses parallel worker processes where the platform supports it.

- Default reduced CPU count: half of the CPUs available to the current process/cgroup, computed as `max(1, available_cpus // 2)`.
- Override for all reduced scripts: `GLEANER_REDUCED_CPUS=N bash scripts/run_reduced_all.sh`.
- Override for sampler preparation only: `GLEANER_REDUCED_CPUS=N bash scripts/prepare_reduced_reports.sh`.
- The one-command reduced runner overlaps independent work: `prepare_reduced_reports.sh` for `gleaner_lite` and RQ1-B sampling/reporting for `tracepicker_lite` run concurrently, with logs under `output/artifact/reduced/logs/`.
- RQ1-B uses `sample batch` over `tracepicker_lite` and passes the auto-detected CPU count through `--use-cpus`.

## Full Evaluation Requirements

- Main command: `GLEANER_RUN_FULL=1 bash scripts/run_full_all.sh`.
- Guard behavior: without `GLEANER_RUN_FULL=1`, the full command exits non-zero by design.
- Scope: complete Gleaner Dataset A, complete converted TracePicker Dataset B, full sampler/RCA orchestration, Gleaner variants, baseline samplers, MicroRCA, ShapleyIQ, Nezha, full paper-facing rates, and online 5% RQ4 efficiency for Gleaner and Gleaner WL Kernel.
- Runtime: long-running; may take multiple days depending on CPU count, disk speed, and selected baseline environments.
- Full-only baseline environments: TraStrainer/Sifter/Sieve and TracePicker are installed in isolated environments in the full image so heavyweight dependencies stay out of the reduced image.

## Data And Reuse Fixtures

Both images include small raw-input examples used by the reuse documentation:

- `data/rcabench_dataset/`: raw RCABench/ClickHouse-style example datapack plus Drain template state.
- `data/tracepicker/`: TracePicker trace-only CSV example.

The converted platform datasets used by reduced/full experiments are under `data/rcabench-platform-v2/`.

## Packaging Requirements For Submitters

- Build/export command: `bash scripts/package_docker_images.sh`.
- Reduced-only build: `GLEANER_BUILD_FULL_IMAGE=0 bash scripts/package_docker_images.sh`.
- Full-only build: `GLEANER_BUILD_REDUCED_IMAGE=0 GLEANER_BUILD_FULL_IMAGE=1 bash scripts/package_docker_images.sh`.
- Compression level: `GLEANER_DOCKER_GZIP_LEVEL=N` controls gzip level, default 6.
- TracePicker full env: included by default in the full image; set `GLEANER_FULL_INSTALL_TRACEPICKER_ENV=0` only for local debugging.

## External Services And Network

- Neither the reduced nor the full artifact path requires commercial services, private credentials, external APIs, or internet downloads after the Docker archives are available.
- The artifact does not require closed-source software.
- The final public artifact deposit provides the actual archive files, checksums, and DOI metadata through Zenodo. This repository intentionally does not hard-code duplicate archive URLs or DOI strings.
