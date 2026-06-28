# Release Packaging

This document describes the local archive builder for the Gleaner ISSTA 2026 artifact evaluation package.

## Current State

- Local archive/package builder: available as `scripts/package_artifact.sh`.
- Public archive upload: not yet performed.
- DOI: not yet minted.
- HotCRP artifact link: not yet prepared.

Do not cite a DOI, release URL, or HotCRP link until the package is uploaded to the final archival host and the external submission metadata is completed.

## Build A Local Archive

From the repository root:

```bash
bash scripts/package_artifact.sh
```

By default the script writes:

```text
dist/gleaner-issta2026-ae-<git-short-sha-or-worktree>.tar.gz
dist/gleaner-issta2026-ae-<git-short-sha-or-worktree>.tar.gz.sha256
```

If the repository has tracked or untracked worktree changes, the archive name uses `worktree` instead of a commit SHA. The script prints `git status --short` and warns about unstaged/untracked changes, but it does not fail solely because the current artifact review flow has staged or unstaged files.

## Package Contents

The archive is built from a temporary staging directory, so `dist/` is never copied into itself. The package includes:

- Reviewer-facing docs: `ARTIFACT_README.md`, `REQUIREMENTS.md`, `STATUS.md`, and `docs/`.
- Source and configuration: `src/`, `main.py`, `scripts/`, `configs/`, `Dockerfile`, `pyproject.toml`, and `uv.lock`.
- Reduced expected outputs: `artifact_expected/reduced/`.
- Reduced data evidence: `data/artifact/reduced/`.
- Reduced Gleaner sampler parquet reports used by the artifact: `output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet` and `output/rcabench-platform-v2/sampler_reports/gleaner/detailed_perf.parquet`.
- Actual file contents for the four third-party component directories under `third_party/`, plus `platform/rcabench-platform`, excluding their `.git` metadata.

The package intentionally excludes `.git`, `.venv`, Python/tool caches, temporary/build/dist directories, generated `output/artifact/` results, raw/full data, and local untracked parquet leftovers outside the explicit reduced sampler report paths.

## Manifests And Checksums

Each archive contains `ARCHIVE_MANIFEST.tsv`, an internal manifest with one row per regular file and these columns:

```text
path	bytes	sha256
```

The packaging script also writes an external SHA-256 checksum file next to the archive:

```bash
sha256sum -c dist/gleaner-issta2026-ae-<git-short-sha-or-worktree>.tar.gz.sha256
```

## Local Verification

The package script performs preflight checks for required paths and non-empty third-party directories, then performs postflight checks on the tar listing to ensure required paths are present and excluded paths such as `.git/`, `.venv/`, `dist/`, and `output/artifact/` are absent.

Additional local validation before any external release upload:

```bash
bash scripts/package_artifact.sh
test -s dist/*.tar.gz
test -s dist/*.sha256
tar -tzf dist/*.tar.gz | grep -Fx ARTIFACT_README.md
tar -tzf dist/*.tar.gz | grep -Fx third_party/Nezha/
tar -tzf dist/*.tar.gz | grep -Fx platform/rcabench-platform/
tar -tzf dist/*.tar.gz | grep -Fx data/artifact/reduced/MANIFEST.json
tar -tzf dist/*.tar.gz | grep -Fx output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet
! tar -tzf dist/*.tar.gz | grep -E '(^|/)\.git(/|$)'
! tar -tzf dist/*.tar.gz | grep -E '(^|/)\.venv(/|$)'
bash scripts/prepare_reduced_data.sh
bash scripts/smoke_test.sh
```

## External Release Blockers

The following steps remain manual and external to this repository:

- Select the final archival host.
- Upload the verified archive and checksum.
- Mint or record the DOI, if feasible.
- Prepare the HotCRP artifact link without compromising reviewer anonymity.
- Update artifact metadata only after real links and identifiers exist.
