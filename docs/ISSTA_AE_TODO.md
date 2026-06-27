# ISSTA 2026 AE TODO

This is the short action list. The full progress checklist is in `docs/ISSTA_AE_CHECKLIST.md`. It reflects the current committed / reviewer-verified artifact state.

## Current Reviewer-Verified State

- [x] Docker image build, container smoke test, and container reduced run are verified.
- [x] Reduced RQ1/RQ2/RQ3/RQ4 artifact scripts exist and are connected to `scripts/run_rq*.sh` wrappers.
- [x] Expected reduced outputs are staged under `artifact_expected/reduced/rq1/` through `artifact_expected/reduced/rq4/`.
- [x] Each `scripts/run_rq*.sh` wrapper calls `scripts/compare_expected.py` to validate expected vs actual outputs.
- [x] `scripts/run_reduced_all.sh` is reviewer-verified as passing end to end in the current reduced state.
- [x] Reduced RQ2 RCA evidence is committed under `data/artifact/reduced/rq2/`.
- [x] Reduced manifest and checksum files are committed and verified by `scripts/prepare_reduced_data.sh`.
- [x] Reduced evidence docs are present in `ARTIFACT_README.md`, `REQUIREMENTS.md`, and `STATUS.md`.
- [x] Local archive/package script and release packaging documentation are present.
- [x] Commit-SHA archive/checksum packaging was locally verified for commit `edcd33fe6fde8b4b4173ef6b23585d6e4108bca2` using `dist/gleaner-issta2026-ae-edcd33f.tar.gz` and sibling `.sha256` (`sha256sum -c`: OK). For final upload, use the newest package regenerated after the final tracked commit: `dist/gleaner-issta2026-ae-<short-sha>.tar.gz` plus `.sha256`.

## P0: Still Open Before AE Submission

- [x] Create local archive/package script.
- [x] Generate local final archive manifest and checksum.
- [ ] Decide final archive/DOI/release plan and prepare the submission link.
- [x] Record reviewer-facing reduced runtime estimates in `REQUIREMENTS.md`.
- [x] Commit the reviewed artifact state.

## P0: Full Path And Dataset Documentation

- [x] Make `scripts/run_full_all.sh` explicitly fail non-zero because the full path is not implemented/reviewer-verified in this artifact snapshot.
- [ ] Implement and reviewer-verify final `scripts/run_full_all.sh` behavior.
- [ ] Document full dataset download/extract/path setup.
- [x] Document reduced generated inputs, staged evidence, and reviewer refresh/reverification path via `bash scripts/prepare_reduced_data.sh`, manifest checksums, and the artifact docs.
- [ ] Confirm all reduced experiments can run in CPU-only mode.

## P1: Validation And Claims

- [x] `scripts/compare_expected.py` exists.
- [x] Expected reduced outputs exist for each RQ.
- [x] Validation calls are present in the reduced RQ wrappers.
- [x] Reviewer-verify `scripts/run_reduced_all.sh` end to end.
- [x] Define and document numerical tolerances or trend-based checks.
- [ ] Fill exact paper claim/table/figure mapping in `ARTIFACT_README.md`.
- [x] Add troubleshooting section.
- [ ] Add reuse guide for running Gleaner on new datapacks.
- [ ] Finalize `STATUS.md` badge justification after archive/release packaging checks.

## P2: Release Package

- [ ] Decide final artifact hosting location.
- [x] Create archive/package script.
- [x] Generate local final manifest with checksums.
- [x] Generate and verify a commit-SHA local archive/checksum after the artifact commit.
- [ ] Upload source/package/data or Docker image tarball.
- [ ] Prepare DOI/release metadata if feasible.
- [ ] Verify final link does not require login and does not compromise reviewer anonymity.
