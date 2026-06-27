# Submitter Handoff

This file records the final local steps for the human submitter. It intentionally leaves public metadata blank until the real upload/DOI/HotCRP steps are completed.

For exact external upload, DOI, post-upload verification, and HotCRP checklist steps, see `docs/EXTERNAL_SUBMISSION_GUIDE.md`.

## Local Package Commands

After the final tracked commit, regenerate the upload candidate:

```bash
sha="$(git rev-parse --short HEAD)"
bash scripts/package_artifact.sh
archive="dist/gleaner-issta2026-ae-${sha}.tar.gz"
checksum="${archive}.sha256"
test -s "$archive" && test -s "$checksum"
(cd dist && sha256sum -c "$(basename "$checksum")")
```

Sanity-check archive contents:

```bash
tar -tzf "$archive" | grep -Fx ARTIFACT_README.md
tar -tzf "$archive" | grep -Fx REQUIREMENTS.md
tar -tzf "$archive" | grep -Fx STATUS.md
tar -tzf "$archive" | grep -Fx docs/RELEASE_PACKAGING.md
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

## Final External Fields

- Public archive/release URL: not created yet.
- DOI, if required: not minted yet.
- HotCRP artifact link: not submitted yet.

Do not replace these fields with placeholders. Record only real, reviewer-accessible links or identifiers after upload.
