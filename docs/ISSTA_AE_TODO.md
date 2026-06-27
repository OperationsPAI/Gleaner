# ISSTA 2026 AE TODO

This is the short action list. The full progress checklist is in `docs/ISSTA_AE_CHECKLIST.md`. It summarizes local reviewer-verified artifact readiness without pinning a current upload package SHA.

## Current Reviewer-Verified State

- [x] Docker image build, container smoke test, and container reduced run are verified.
- [x] Reduced RQ1/RQ2/RQ3/RQ4 artifact scripts exist and are connected to `scripts/run_rq*.sh` wrappers.
- [x] Expected reduced outputs are committed under `artifact_expected/reduced/rq1/` through `artifact_expected/reduced/rq4/`.
- [x] Each `scripts/run_rq*.sh` wrapper calls `scripts/compare_expected.py` to validate expected vs actual outputs.
- [x] `scripts/run_reduced_all.sh` is reviewer-verified as passing end to end in the current reduced state.
- [x] Reduced RQ2 RCA evidence is committed under `data/artifact/reduced/rq2/`.
- [x] Reduced manifest and checksum files are committed and verified by `scripts/prepare_reduced_data.sh`.
- [x] Reduced evidence, CPU-only, claim-mapping, and reuse docs are present in `ARTIFACT_README.md`, `REQUIREMENTS.md`, and `STATUS.md`.
- [x] Third-party license-file evidence, submodule URL accessibility, smoke-test coverage, and dependency-risk decisions are documented in `docs/THIRD_PARTY.md`.
- [x] Local archive/package script and release packaging documentation are present.
- [x] Human submitter guide for external GitHub/Zenodo upload, post-upload checksum verification, and HotCRP link submission is present in `docs/EXTERNAL_SUBMISSION_GUIDE.md`.
- [x] Commit-SHA archive/checksum packaging workflow is locally verified. For final upload, regenerate after the final tracked commit with `bash scripts/package_artifact.sh`, then use `dist/gleaner-issta2026-ae-$(git rev-parse --short HEAD).tar.gz` plus `dist/gleaner-issta2026-ae-$(git rev-parse --short HEAD).tar.gz.sha256` and verify with `(cd dist && sha256sum -c gleaner-issta2026-ae-$(git rev-parse --short HEAD).tar.gz.sha256)`.

## P0: Still Open Before AE Submission

- [x] Create local archive/package script.
- [x] Generate local archive manifest and checksum via the dynamic HEAD-derived packaging workflow.
- [ ] Decide final archive/DOI/release plan and prepare the submission link using `docs/EXTERNAL_SUBMISSION_GUIDE.md`.
- [x] Record reviewer-facing reduced runtime estimates in `REQUIREMENTS.md`.
- [x] Commit the reviewed artifact state.

## P0: Full Path And Dataset Documentation

- [x] Make `scripts/run_full_all.sh` explicitly fail non-zero because the full path is not implemented/reviewer-verified in this artifact snapshot.
- [ ] Implement and reviewer-verify final `scripts/run_full_all.sh` behavior.
- [ ] Document full dataset download/extract/path setup.
- [x] Document reduced generated inputs, committed evidence, and reviewer refresh/reverification path via `bash scripts/prepare_reduced_data.sh`, manifest checksums, and the artifact docs.
- [x] Confirm all reduced experiments can run in CPU-only mode (`CUDA_VISIBLE_DEVICES='' bash scripts/run_reduced_all.sh`).

## P1: Validation And Claims

- [x] `scripts/compare_expected.py` exists.
- [x] Expected reduced outputs exist for each RQ.
- [x] Validation calls are present in the reduced RQ wrappers.
- [x] Reviewer-verify `scripts/run_reduced_all.sh` end to end.
- [x] Define and document numerical tolerances or trend-based checks.
- [x] Fill exact paper claim/table/figure mapping in `ARTIFACT_README.md` from `pdftotext paper/main.pdf -` output.
- [x] Add troubleshooting section.
- [x] Add reuse guide for running Gleaner on new datapacks.
- [x] Finalize local `STATUS.md` badge justification; available/public-archive badge remains open until real upload/DOI/HotCRP metadata exists.
- [x] Finalize third-party readiness notes for the reduced/offline path: license-file evidence, public submodule URL checks, smoke-test scope, and known dependency risks.

## P2: Release Package

- [ ] Decide final artifact hosting location.
- [x] Create archive/package script.
- [x] Generate local manifest with checksums via the dynamic HEAD-derived packaging workflow.
- [x] Generate and verify a commit-SHA local archive/checksum after tracked commits; final upload uses the regenerated HEAD-derived archive and checksum.
- [ ] Upload source/package/data or Docker image tarball.
- [ ] Prepare DOI/release metadata if feasible.
- [ ] Verify final link does not require login and does not compromise reviewer anonymity.

## P2: Third-party Full-path Follow-up

- [x] Document third-party license-file evidence and unknown-license cases without inferring absent license terms.
- [x] Verify configured submodule URLs with non-mutating public `git ls-remote` checks.
- [x] Document what `scripts/smoke_test.sh` checks for third-party components.
- [ ] Build isolated full execution environments for TracePicker, TraStrainer, Nezha, MicroRCA, and ShapleyIQ if full-path reproduction is required.
- [ ] Add component-level full-pipeline smoke tests after those environments and full raw inputs are available.
