# External Submission Guide

This guide is for the human submitter after the final tracked commit. It gives concrete upload and verification steps, but it does not perform any upload, mint a DOI, submit HotCRP metadata, or invent public links.

Official references:

- GitHub Releases documentation: <https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository>
- GitHub release asset upload API documentation, if a scripted upload is preferred: <https://docs.github.com/en/rest/releases/assets?apiVersion=2022-11-28>
- GitHub documentation on Zenodo citation integration: <https://docs.github.com/repositories/archiving-a-github-repository/referencing-and-citing-content>
- Zenodo GitHub integration documentation: <https://help.zenodo.org/docs/github/>
- Zenodo GitHub repository enablement: <https://help.zenodo.org/docs/github/enable-repository/>
- Zenodo GitHub release archiving: <https://help.zenodo.org/docs/github/archive-software/github-upload/>
- Zenodo new-upload documentation: <https://help.zenodo.org/docs/deposit/create-new-upload/>
- Zenodo DOI documentation: <https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/>

## 1. Build The Final Local Package

Run these commands from the repository root after the final tracked commit:

```bash
sha="$(git rev-parse --short HEAD)"
bash scripts/package_artifact.sh
archive="dist/gleaner-issta2026-ae-${sha}.tar.gz"
checksum="${archive}.sha256"
test -s "$archive" && test -s "$checksum"
(cd dist && sha256sum -c "$(basename "$checksum")")
```

The two files to upload are:

```text
dist/gleaner-issta2026-ae-${sha}.tar.gz
dist/gleaner-issta2026-ae-${sha}.tar.gz.sha256
```

Do not upload an older archive whose name contains a different commit short SHA, and do not upload a `worktree` archive for final submission.

## 2. Sanity-check The Archive Before Upload

```bash
tar -tzf "$archive" | grep -Fx ARTIFACT_README.md
tar -tzf "$archive" | grep -Fx REQUIREMENTS.md
tar -tzf "$archive" | grep -Fx STATUS.md
tar -tzf "$archive" | grep -Fx docs/RELEASE_PACKAGING.md
tar -tzf "$archive" | grep -Fx docs/SUBMITTER_HANDOFF.md
tar -tzf "$archive" | grep -Fx docs/THIRD_PARTY.md
tar -tzf "$archive" | grep -Fx docs/EXTERNAL_SUBMISSION_GUIDE.md
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

## 3. GitHub Release Upload Option

Use this option if the artifact should be distributed through a public GitHub repository release.

Human-fill fields:

- Repository owner/name: `TBD_BY_SUBMITTER`
- Release tag: `TBD_BY_SUBMITTER` (for example, a tag derived from the paper/artifact submission, not required to equal the commit short SHA)
- Release title: `TBD_BY_SUBMITTER`
- Public release URL after publication: `TBD_BY_SUBMITTER`

Suggested manual steps:

1. Open the target repository in GitHub. The repository must be publicly accessible to reviewers without login.
2. Create a new release from the chosen tag, or create the tag during release creation.
3. Use release notes that identify this as the ISSTA 2026 AE artifact and include the final commit SHA, the archive filename, and the checksum filename.
4. Upload both files as release assets:
   - `dist/gleaner-issta2026-ae-${sha}.tar.gz`
   - `dist/gleaner-issta2026-ae-${sha}.tar.gz.sha256`
5. Publish the release.
6. In a private/incognito browser window, verify that the release page and both assets are downloadable without authentication.

If using the GitHub CLI or API, still perform the private/incognito public-access check after upload. Do not commit a release URL to this repository until it is real and reviewer-accessible.

## 4. Zenodo DOI Option

Use this option if the venue or artifact policy requires archival DOI metadata, or if the submitter wants a DOI-backed artifact. DOI may be optional if the venue does not require it, but public reviewer access and the HotCRP artifact link remain external/manual requirements.

Human-fill metadata fields:

- Zenodo deposition URL: `TBD_BY_SUBMITTER`
- DOI: `TBD_BY_SUBMITTER` or `not required by venue`
- Title: `TBD_BY_SUBMITTER`
- Creators/authors: `TBD_BY_SUBMITTER`
- Description/abstract: `TBD_BY_SUBMITTER`
- Version: `TBD_BY_SUBMITTER`
- License/access rights: `TBD_BY_SUBMITTER`
- Related identifiers, if any: `TBD_BY_SUBMITTER`

Two common workflows are acceptable:

1. GitHub-Zenodo integration: connect the public repository to Zenodo, publish a GitHub release, then let Zenodo archive that release and mint the DOI.
2. Direct Zenodo deposition: create a deposition in Zenodo, upload the final archive and `.sha256`, fill metadata, publish the deposition, and record the DOI assigned by Zenodo.

After Zenodo publication, verify in a private/incognito browser window that the DOI/deposition page is public and that the uploaded files are downloadable without authentication.

## 5. Post-upload Verification

After the archive and checksum are public, download them into a clean temporary directory and verify the checksum:

```bash
mkdir -p /tmp/gleaner-ae-download-check
cd /tmp/gleaner-ae-download-check
# Replace these with the real public asset URLs after upload.
curl -L -o "gleaner-issta2026-ae-${sha}.tar.gz" "TBD_PUBLIC_ARCHIVE_URL"
curl -L -o "gleaner-issta2026-ae-${sha}.tar.gz.sha256" "TBD_PUBLIC_CHECKSUM_URL"
sha256sum -c "gleaner-issta2026-ae-${sha}.tar.gz.sha256"
tar -tzf "gleaner-issta2026-ae-${sha}.tar.gz" | grep -Fx ARTIFACT_README.md
```

The `TBD_PUBLIC_ARCHIVE_URL` and `TBD_PUBLIC_CHECKSUM_URL` tokens above are human-fill fields for local verification commands only. Do not commit them as if they were real links.

Record only real final values after the upload is complete:

- Public archive/release URL: `TBD_BY_SUBMITTER`
- Public checksum URL: `TBD_BY_SUBMITTER`
- DOI, if required: `TBD_BY_SUBMITTER` or `not required by venue`
- Verified checksum output: `TBD_BY_SUBMITTER`
- Verification date/time: `TBD_BY_SUBMITTER`

## 6. HotCRP Artifact-link Checklist

Before submitting the artifact link in HotCRP:

- Confirm the public archive/release URL works without login.
- Confirm the checksum file works without login.
- Confirm `sha256sum -c` passes on a fresh download.
- Confirm the archive opens and contains `ARTIFACT_README.md` at the top level.
- Confirm the link target does not require reviewer authentication and does not expose reviewer identities or IP-tracking dashboards to authors.
- If a DOI is required, confirm the DOI resolves publicly before entering it in HotCRP.
- Submit the real public artifact link in HotCRP only after these checks pass.

Final HotCRP fields to complete manually:

- HotCRP artifact URL submitted: `TBD_BY_SUBMITTER`
- DOI field, if any: `TBD_BY_SUBMITTER` or `not required by venue`
- Submission timestamp: `TBD_BY_SUBMITTER`
- Submitter initials: `TBD_BY_SUBMITTER`
