# Final Commit Readiness

Audit date: 2026-06-28 (local Asia/Hong_Kong time).

## Verdict

The AE artifact was committed, locally packaged, and reviewer-verified after the documentation finalization commit `edcd33fe6fde8b4b4173ef6b23585d6e4108bca2` (`Finalize AE submission documentation`). The verified package from that audit was:

- `dist/gleaner-issta2026-ae-edcd33f.tar.gz`
- `dist/gleaner-issta2026-ae-edcd33f.tar.gz.sha256`

That package passed checksum validation, tar required/forbidden path checks, reduced-data preparation, smoke testing, and the full reduced RQ1-RQ4 acceptance run.

This file is a readiness report, not a pinned release manifest. If this report or any other tracked artifact file is changed and committed after the audit above, rerun `bash scripts/package_artifact.sh` and use the newest `dist/gleaner-issta2026-ae-<short-sha>.tar.gz` plus sibling `.sha256` as the upload candidate.

## Git State Evidence

Commands run from `/home/nn/workspace/Gleaner` for the verified audit:

- `git status --short`: clean / no output after commit `edcd33fe6fde8b4b4173ef6b23585d6e4108bca2`.
- `git diff --name-only`: empty; no unstaged tracked-file drift.
- `git log -1 --pretty=%H%n%s`: `edcd33fe6fde8b4b4173ef6b23585d6e4108bca2` / `Finalize AE submission documentation`.
- `dist/` remained ignored and unstaged.

## Local Archive Verification

Archive checked in the verified audit:

- `dist/gleaner-issta2026-ae-edcd33f.tar.gz`
- `dist/gleaner-issta2026-ae-edcd33f.tar.gz.sha256`

Commands/results:

- `cd dist && sha256sum -c gleaner-issta2026-ae-edcd33f.tar.gz.sha256` -> `gleaner-issta2026-ae-edcd33f.tar.gz: OK`.
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

For any later commit, regenerate the package and repeat the checksum/tar checks before upload so the archive name and contents match the newest HEAD.

## Local Command Verification

Commands run from `/home/nn/workspace/Gleaner`:

- `bash scripts/prepare_reduced_data.sh`: passed; verified 16 files from `data/artifact/reduced/MANIFEST.json`, total 450107 bytes.
- `bash scripts/smoke_test.sh`: passed; submodule pins matched and Python imports succeeded (`gleaner import OK`, `rcabench-platform 0.4.1`).
- `bash scripts/run_reduced_all.sh`: passed; RQ1/RQ2/RQ3/RQ4 reduced scripts wrote generated outputs under `output/artifact/reduced/` and each expected-output comparison passed for 3 files.
- `time -p bash scripts/run_reduced_all.sh`: passed on the local host with `real 2.96`, `user 16.51`, `sys 10.91`.

The reduced artifact path is locally verified. Docker/container verification is recorded in `STATUS.md` and `docs/ISSTA_AE_TODO.md`; this final pass did not rerun Docker.

## Known Scope Limits

- The full path is intentionally guarded and not verified in this artifact snapshot; `scripts/run_full_all.sh` is documented as non-final and should not be treated as reviewer-verified.
- Public release URL, DOI, and HotCRP artifact link are still external manual steps. No placeholder DOI, release URL, or HotCRP link has been added.
- `dist/` archives and checksum files remain local build products and should not be staged.

## Required Next Step Before External Submission

Use the archive generated from the final tracked commit. If any tracked files changed after the verified audit above, first run:

```bash
bash scripts/package_artifact.sh
```

Then upload the resulting `dist/gleaner-issta2026-ae-<short-sha>.tar.gz` and sibling `.sha256`, and complete the external release/DOI/HotCRP steps with real links only.
