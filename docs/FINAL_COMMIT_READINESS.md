# Final Commit Readiness

Audit date: 2026-06-28 (local Asia/Hong_Kong time).

## Verdict

The local reduced AE artifact path has been implemented, committed, packaged, and reviewer-verified. The verified scope includes reduced-data preparation, smoke testing, RQ1-RQ4 reduced acceptance scripts, expected-output comparisons, archive checksum verification, and archive required/forbidden path checks.

This file is a readiness report, not a pinned release manifest. Tracked documentation must not name an exact archive SHA as the current upload candidate, because any later tracked commit changes the authoritative package name. The final upload package must be regenerated after the last tracked commit by running:

```bash
bash scripts/package_artifact.sh
sha="$(git rev-parse --short HEAD)"
archive="dist/gleaner-issta2026-ae-${sha}.tar.gz"
checksum="${archive}.sha256"
test -s "$archive"
test -s "$checksum"
(cd dist && sha256sum -c "$(basename "$checksum")")
```

Upload the archive and checksum derived from the final `git rev-parse --short HEAD` value only.

## Local Verification Evidence

Commands run from `/home/nn/workspace/Gleaner` in the final local acceptance passes:

- `git status --short`: clean / no output after tracked commits used for the audit.
- `git diff --name-only`: empty; no unstaged tracked-file drift.
- `git diff --check`: passed before committing tracked documentation updates.
- `dist/` remained ignored and unstaged.

Reduced-path commands:

- `bash scripts/prepare_reduced_data.sh`: passed; verified 16 files from `data/artifact/reduced/MANIFEST.json`, total 450107 bytes.
- `bash scripts/smoke_test.sh`: passed; submodule pins matched and Python imports succeeded (`gleaner import OK`, `rcabench-platform 0.4.1`).
- `bash scripts/run_reduced_all.sh`: passed; RQ1/RQ2/RQ3/RQ4 reduced scripts wrote generated outputs under `output/artifact/reduced/` and each expected-output comparison passed for 3 files.
- `time -p bash scripts/run_reduced_all.sh`: passed on the local host with `real 2.96`, `user 16.51`, `sys 10.91`.

The reduced artifact path is locally verified. Docker/container verification is recorded in `STATUS.md` and `docs/ISSTA_AE_TODO.md`; this final readiness report does not require rerunning Docker unless the container inputs change.

## Final Package Verification Rule

After the final tracked commit, regenerate and verify the upload package with the dynamic HEAD-derived names:

```bash
bash scripts/package_artifact.sh
sha="$(git rev-parse --short HEAD)"
archive="dist/gleaner-issta2026-ae-${sha}.tar.gz"
checksum="${archive}.sha256"
test -s "$archive"
test -s "$checksum"
(cd dist && sha256sum -c "$(basename "$checksum")")
```

Then check archive contents before upload:

```bash
tar -tzf "$archive" | grep -Fx ARTIFACT_README.md
tar -tzf "$archive" | grep -Fx REQUIREMENTS.md
tar -tzf "$archive" | grep -Fx STATUS.md
tar -tzf "$archive" | grep -Fx docs/RELEASE_PACKAGING.md
tar -tzf "$archive" | grep -Fx ARCHIVE_MANIFEST.tsv
tar -tzf "$archive" | grep -Fx data/artifact/reduced/MANIFEST.json
tar -tzf "$archive" | grep -Fx third_party/Nezha/
tar -tzf "$archive" | grep -Fx output/rcabench-platform-v2/sampler_reports/gleaner/aggregated_perf.parquet
tar -tzf "$archive" | grep -Fx output/rcabench-platform-v2/sampler_reports/gleaner/detailed_perf.parquet
! tar -tzf "$archive" | grep -E '(^|/)\.git(/|$)'
! tar -tzf "$archive" | grep -E '(^|/)\.venv(/|$)'
! tar -tzf "$archive" | grep -E '^dist(/|$)'
! tar -tzf "$archive" | grep -E '^output/artifact(/|$)'
! tar -tzf "$archive" | grep -E '(^|/)__pycache__(/|$)'
```

## Known Scope Limits

- The full path is intentionally guarded and not verified in this artifact snapshot; `scripts/run_full_all.sh` is documented as non-final and should not be treated as reviewer-verified.
- Public release URL, DOI if required, and HotCRP artifact link submission are still external manual steps. No placeholder DOI, release URL, or HotCRP link has been added.
- `dist/` archives and checksum files remain local build products and should not be staged.

## Required Next Step Before External Submission

Use the archive generated from the final tracked commit. If any tracked file changes, commit it first, rerun `bash scripts/package_artifact.sh`, verify the checksum and tar contents with the commands above, then upload the resulting `dist/gleaner-issta2026-ae-$(git rev-parse --short HEAD).tar.gz` and sibling `.sha256`. Complete the external release/DOI/HotCRP steps with real links only.
