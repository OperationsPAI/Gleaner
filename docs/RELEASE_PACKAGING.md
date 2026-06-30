# Release Packaging

This document describes the local package builders for the Gleaner ISSTA 2026 artifact evaluation package.

## Current State

- Preferred review deliverables: Docker image archives produced by `scripts/package_docker_images.sh` using `docker save | gzip`.
- Optional source archive: `scripts/package_artifact.sh`.
- Public deposit metadata is not stored in this repository. The submitted artifact record should provide the actual downloadable files, checksums, and any required DOI metadata.

## Build Docker Image Archives

From the repository root:

```bash
bash scripts/package_docker_images.sh
```

By default the script builds and exports both scopes:

```text
dist/gleaner-issta2026-ae-reduced-<git-short-sha-or-worktree>.docker.tar.gz
dist/gleaner-issta2026-ae-reduced-<git-short-sha-or-worktree>.docker.tar.gz.sha256
dist/gleaner-issta2026-ae-full-<git-short-sha-or-worktree>.docker.tar.gz
dist/gleaner-issta2026-ae-full-<git-short-sha-or-worktree>.docker.tar.gz.sha256
```

Set `GLEANER_BUILD_FULL_IMAGE=0` to build only the reduced image during iteration:

```bash
GLEANER_BUILD_FULL_IMAGE=0 bash scripts/package_docker_images.sh
```

Set `GLEANER_BUILD_REDUCED_IMAGE=0` to build only the full image after the reduced/base layers are already available:

```bash
GLEANER_BUILD_REDUCED_IMAGE=0 GLEANER_BUILD_FULL_IMAGE=1 bash scripts/package_docker_images.sh
```

The script compresses the `docker save` tar stream with gzip level 6 by default. Override with `GLEANER_DOCKER_GZIP_LEVEL=N` if final size or compression time is more important.

The full image prebuilds TracePicker's isolated Python 3.12/CUDA-oriented environment by default. Disable it only for local debugging:

```bash
GLEANER_FULL_INSTALL_TRACEPICKER_ENV=0 bash scripts/package_docker_images.sh
```

## Image Contents

Reduced image:

- Source, scripts, docs, configs, and pinned third-party source trees.
- Main Python 3.13 uv environment for Gleaner, RCAbench Platform, Nezha, and ShapleyIQ/MicroRCA. Heavy baseline dependencies such as TraStrainer/Sifter/Sieve are intentionally excluded from the reduced image.
- Live converted reduced datasets:
  - `data/rcabench-platform-v2/data/gleaner_lite`
  - `data/rcabench-platform-v2/meta/gleaner_lite`
  - `data/rcabench-platform-v2/data/tracepicker_lite`
  - `data/rcabench-platform-v2/meta/tracepicker_lite`

Full image:

- Everything in the reduced image.
- Complete Gleaner Dataset A:
  - `data/rcabench-platform-v2/data/gleaner`
  - `data/rcabench-platform-v2/meta/gleaner`
- Complete converted TracePicker Dataset B for full/diagnostic cross-system runs:
  - `data/rcabench-platform-v2/data/tracepicker`
  - `data/rcabench-platform-v2/meta/tracepicker`
- Full-path scripts for long-running validation.
- Full-image-only isolated TraStrainer/Sifter/Sieve and TracePicker environments for full baseline validation.

Both images exclude `.git`, `.venv`, caches, generated `output/`, `dist/`, and generated `sampled/` directories.

## Load And Verify

```bash
sha256sum -c dist/gleaner-issta2026-ae-reduced-*.docker.tar.gz.sha256
gunzip -c dist/gleaner-issta2026-ae-reduced-*.docker.tar.gz | docker load

docker run --rm gleaner-issta2026-ae:reduced-worktree bash scripts/prepare_reduced_data.sh
docker run --rm gleaner-issta2026-ae:reduced-worktree bash scripts/smoke_test.sh
```

If the worktree was clean during packaging, replace `worktree` with the short git SHA printed by the packaging script.

Run the reduced scope:

```bash
docker run --rm gleaner-issta2026-ae:reduced-worktree bash scripts/run_reduced_all.sh
```

Run the full scope from the full image:

```bash
sha256sum -c dist/gleaner-issta2026-ae-full-*.docker.tar.gz.sha256
gunzip -c dist/gleaner-issta2026-ae-full-*.docker.tar.gz | docker load
docker run --rm gleaner-issta2026-ae:full-worktree bash -lc 'GLEANER_RUN_FULL=1 bash scripts/run_full_all.sh'
```

The full image command uses the paper settings by default: sampler rates `0.001,0.01,0.025,0.05,0.075,0.1`, RCA rates `0.01,0.1`, and online 5% efficiency reporting. Override sampler rates with `GLEANER_FULL_RATES` and RCA rates with `GLEANER_FULL_RCA_RATES` only for diagnostic reruns.

## Optional Source Archive

A source archive can still be built with:

```bash
bash scripts/package_artifact.sh
```

It writes:

```text
dist/gleaner-issta2026-ae-<git-short-sha-or-worktree>.tar.gz
dist/gleaner-issta2026-ae-<git-short-sha-or-worktree>.tar.gz.sha256
```

The Docker image archives are the preferred reviewer deliverables because they preserve the runtime environment and datasets in a directly loadable form.

## Final Deposit Note

Do not add placeholder archive URLs or DOI strings to the repository. After upload, keep the real public metadata in the conference submission system or artifact deposit record.
