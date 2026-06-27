# Final Commit Readiness

Audit date: 2026-06-28 (local Asia/Hong_Kong time).

## Verdict

The current staged artifact state is locally commit-ready, subject to the external release steps listed below. The pre-commit audit found no unstaged source drift: `git diff --name-only` was empty before this report was written, and the reduced verification commands completed successfully.

## Git State Evidence

Commands run from `/home/nn/workspace/Gleaner`:

- `git status --short`: showed only the existing staged artifact changes before this report was added.
- `git diff --name-only`: empty; no unstaged tracked-file drift.
- `git diff --cached --name-status`: showed the staged artifact package/docs/code/data state; no `dist/` archive or checksum files were staged.

After this audit, only `docs/FINAL_COMMIT_READINESS.md` should be newly staged by the final readiness worker.

## Local Archive Verification

Archive checked:

- `dist/gleaner-issta2026-ae-worktree.tar.gz`
- `dist/gleaner-issta2026-ae-worktree.tar.gz.sha256`

Commands/results:

- `cd dist && sha256sum -c gleaner-issta2026-ae-worktree.tar.gz.sha256` -> `gleaner-issta2026-ae-worktree.tar.gz: OK`.
- Tar listing required-path check passed for:
  - `ARTIFACT_README.md`
  - `REQUIREMENTS.md`
  - `STATUS.md`
  - `docs/RELEASE_PACKAGING.md`
  - `ARCHIVE_MANIFEST.tsv`
  - `data/artifact/reduced/MANIFEST.json`
  - `third_party/Nezha/`
  - `data/artifact/reduced/rq2/nezha/sampler.grouped.perf.parquet`
  - `data/artifact/reduced/rq2/shapleyiq_microrca/sampler.grouped.perf.parquet`
- Tar listing forbidden-path check passed: `.git/`, `.venv/`, `dist/`, and `output/artifact/` were absent.
- Archive listing contained 2042 entries.

Caveat: the checked archive is the current `worktree` archive because the artifact state is staged but not yet committed. After committing, rerun `bash scripts/package_artifact.sh` so the upload candidate is named with the commit SHA and reflects the committed tree.

## Local Command Verification

Commands run from `/home/nn/workspace/Gleaner`:

- `bash scripts/prepare_reduced_data.sh`: passed; verified 16 files from `data/artifact/reduced/MANIFEST.json`, total 450107 bytes.
- `bash scripts/smoke_test.sh`: passed; submodule pins matched and Python imports succeeded (`gleaner import OK`, `rcabench-platform 0.4.1`).
- `bash scripts/run_reduced_all.sh`: passed; RQ1/RQ2/RQ3/RQ4 reduced scripts wrote generated outputs under `output/artifact/reduced/` and each expected-output comparison passed for 3 files.

The reduced artifact path is therefore locally verified. Docker/container verification is already recorded in `STATUS.md` and `docs/ISSTA_AE_TODO.md`; this final pass did not rerun Docker.

## Known Scope Limits

- The full path is intentionally guarded and not verified in this artifact snapshot; `scripts/run_full_all.sh` is documented as non-final and should not be treated as reviewer-verified.
- Public release URL, DOI, and HotCRP artifact link are still external manual steps. No placeholder DOI, release URL, or HotCRP link has been added.
- `dist/` archives and checksum files remain local build products and should not be staged.

## Required Next Step After Commit

After committing the current staged artifact state, run:

```bash
bash scripts/package_artifact.sh
```

Use the resulting commit-SHA archive and sibling `.sha256` as the upload candidate, then perform the external upload/DOI/HotCRP steps with real links only.
