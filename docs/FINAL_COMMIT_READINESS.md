# Final Commit Readiness

Audit date: 2026-06-28 (local Asia/Hong_Kong time).

## Verdict

The AE artifact was committed and locally packaged at HEAD `cfe2f7eec1ff423a42784f3c0d81440f68b47dd2` (`Prepare ISSTA AE artifact package`). The reduced verification path, local archive checksum, tar contents, and clean git state were verified for that post-commit package.

This document is being finalized in a doc-only follow-up. After the follow-up commit, rerun `bash scripts/package_artifact.sh` so the upload candidate is named with the new commit SHA and includes these final documentation updates.

## Git State Evidence

Commands run from `/home/nn/workspace/Gleaner`:

- `git status --short`: showed only the existing staged artifact changes before this report was added.
- `git diff --name-only`: empty; no unstaged tracked-file drift.
- `git diff --cached --name-status`: showed the staged artifact package/docs/code/data state; no `dist/` archive or checksum files were staged.

Post-commit verification subsequently confirmed a clean tree at `cfe2f7eec1ff423a42784f3c0d81440f68b47dd2`; `dist/` remained ignored and unstaged.

## Local Archive Verification

Archive checked:

- `dist/gleaner-issta2026-ae-cfe2f7e.tar.gz`
- `dist/gleaner-issta2026-ae-cfe2f7e.tar.gz.sha256`

Commands/results:

- `cd dist && sha256sum -c gleaner-issta2026-ae-cfe2f7e.tar.gz.sha256` -> `gleaner-issta2026-ae-cfe2f7e.tar.gz: OK`.
- Tar listing required-path check passed for:
  - `ARTIFACT_README.md`
  - `REQUIREMENTS.md`
  - `STATUS.md`
  - `docs/RELEASE_PACKAGING.md`
  - `ARCHIVE_MANIFEST.tsv`
  - `data/artifact/reduced/MANIFEST.json`
  - `third_party/Nezha/`
  - `output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet`
  - `output/rcabench-platform-v2/sampler_reports/gleaner/detailed_perf.parquet`
- Tar listing forbidden-path check passed: `.git/`, `.venv/`, `dist/`, `output/artifact/`, and `__pycache__/` were absent.

Caveat: this was the verified package for commit `cfe2f7e`. After this final documentation follow-up commit, regenerate the package and use the new commit-SHA archive as the upload candidate.

## Local Command Verification

Commands run from `/home/nn/workspace/Gleaner`:

- `bash scripts/prepare_reduced_data.sh`: passed; verified 16 files from `data/artifact/reduced/MANIFEST.json`, total 450107 bytes.
- `bash scripts/smoke_test.sh`: passed; submodule pins matched and Python imports succeeded (`gleaner import OK`, `rcabench-platform 0.4.1`).
- `bash scripts/run_reduced_all.sh`: passed; RQ1/RQ2/RQ3/RQ4 reduced scripts wrote generated outputs under `output/artifact/reduced/` and each expected-output comparison passed for 3 files.
- `time -p bash scripts/run_reduced_all.sh`: passed on the local host with `real 2.96`, `user 16.51`, `sys 10.91`.

The reduced artifact path is therefore locally verified. Docker/container verification is already recorded in `STATUS.md` and `docs/ISSTA_AE_TODO.md`; this final pass did not rerun Docker.

## Known Scope Limits

- The full path is intentionally guarded and not verified in this artifact snapshot; `scripts/run_full_all.sh` is documented as non-final and should not be treated as reviewer-verified.
- Public release URL, DOI, and HotCRP artifact link are still external manual steps. No placeholder DOI, release URL, or HotCRP link has been added.
- `dist/` archives and checksum files remain local build products and should not be staged.

## Required Next Step After Documentation Follow-up Commit

After committing the final documentation updates, run:

```bash
bash scripts/package_artifact.sh
```

Use the resulting commit-SHA archive and sibling `.sha256` as the upload candidate, then perform the external upload/DOI/HotCRP steps with real links only.
