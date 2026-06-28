# ISSTA 2026 Artifact Evaluation Checklist

This checklist tracks the Gleaner artifact preparation status for ISSTA 2026 AE. It reflects the current committed / reviewer-verified artifact state.

## Official Requirements

- [x] Confirmed artifact format requirement: Container (Docker/Podman) or VM (OVF/OVA).
- [x] Confirmed required files: README, REQUIREMENTS, STATUS, LICENSE.
- [x] Confirmed Getting Started path should be completable within 30 minutes.
- [x] Confirmed long-running experiments need a reduced scope that can be validated in one day or less.
- [x] Confirmed AE page does not require author anonymization of the artifact itself.
- [x] Confirmed artifact links should be hosted on a platform that does not track reviewer IP addresses.
- [ ] Decide final archival host and DOI plan for the artifact package.
- [ ] Decide final submission link strategy for HotCRP.
- [x] Document local archive builder state in `docs/RELEASE_PACKAGING.md` without placeholder DOI/release/HotCRP links.
- [x] Add human submitter external-upload guide with GitHub Release, Zenodo, post-upload verification, and HotCRP checklist steps while keeping real public links/DOIs open.

## Branch And Repository State

- [x] Created working branch: `issta-26-artifact`.
- [x] Added AE documentation skeleton.
- [x] Added reduced/full config skeleton.
- [x] Added Dockerfile skeleton.
- [x] Updated root dependency to `rcabench-platform==0.4.1`.
- [x] Regenerated `uv.lock`.
- [x] Ran `bash scripts/smoke_test.sh` successfully on host.
- [x] Added artifact-ready reduced RQ1/RQ2/RQ3/RQ4 scripts and wrappers.
- [x] Added reduced illustrative plot and final report generation to the reduced pipeline.
- [x] Reviewer-verified `bash scripts/run_reduced_all.sh` passes end to end in the current reduced state.
- [x] Built Docker image locally with `docker build -t gleaner-issta2026-ae .`.
- [x] Ran container smoke test with `docker run --rm gleaner-issta2026-ae bash scripts/smoke_test.sh`.
- [x] Ran reduced all-in-one command inside Docker with `docker run --rm gleaner-issta2026-ae bash scripts/run_reduced_all.sh`.
- [x] Commit reviewed AE artifact states; final upload packaging uses the dynamic HEAD-derived archive workflow.

## dev2 RQ Script Sources

- [x] Cloned `https://github.com/YifanYang6/Gleaner/tree/dev2` into a temporary directory for inspection.
- [x] Recorded source commit: `e6dd21211347802c6611db5c94454a64f8e4862b`.
- [x] Added dev2 script inventory: `docs/DEV2_RQ_SCRIPT_RECORD.md`.
- [x] Copied reference RQ scripts into `docs/reference/dev2_rq_scripts/`.
- [x] Marked RQ5 scripts as intentionally ignored for AE.
- [x] Converted dev2-derived RQ1 logic into an artifact-ready reduced script with configurable input/output paths.
- [x] Converted dev2-derived RQ2 corrected logic into an artifact-ready reduced RCA summary script.
- [x] Converted dev2-derived RQ3 logic into an artifact-ready reduced ablation script.
- [x] Converted dev2-derived RQ4 logic into an artifact-ready reduced efficiency script.
- [x] Replaced hard-coded `/home/nn/workspace/gleaner-rc` paths in the reduced artifact scripts with repo-relative paths or CLI arguments.
- [x] Routed reduced generated outputs into `output/artifact/reduced/rqX/`.
- [x] Added expected-output comparison around every reduced RQ wrapper via `scripts/compare_expected.py`.
- [x] Added `scripts/artifact/plot_reduced_rq_figures.py` and `scripts/run_reduced_plots.sh` for reduced illustrative PNGs, plot-data CSV/JSON, and `output/artifact/reduced/REPORT.md`.
- [x] Guard full-path entry point so it clearly fails instead of silently succeeding as a placeholder.
- [ ] Implement and reviewer-verify full-path behavior for every RQ.

## Third-party Components

- [x] Added `third_party/ShapleyIQ` as a submodule.
- [x] Pinned ShapleyIQ to `f45c02e55f5614f8c9e5d54ba1882780c694ce90`.
- [x] Added `third_party/Nezha` as a submodule.
- [x] Pinned Nezha to `f0de4db8123a566e13c5fcfe6ac0d9137009f99a`.
- [x] Added `third_party/TracePicker` as a submodule.
- [x] Pinned TracePicker to `31e5fc8130c9b2c315220bb91397f2756dda8378`.
- [x] Added `third_party/TraStrainer` as a submodule.
- [x] Pinned TraStrainer to latest main commit `82b133d9a0209997e3337506988776ab07ac4ada`.
- [x] Documented third-party sources in `docs/THIRD_PARTY.md`.
- [x] Checked license files and license notes for every submodule in `docs/THIRD_PARTY.md`; TracePicker and TraStrainer are documented as unknown because no license file is present in the vendored snapshot.
- [x] Confirmed configured submodule URLs are publicly reachable with non-mutating `git ls-remote` checks and recorded observed remote HEADs in `docs/THIRD_PARTY.md`.
- [x] Documented component-level smoke-test coverage and reduced-scope limits in `docs/THIRD_PARTY.md`.
- [ ] Add full component-level execution smoke tests for each third-party algorithm after per-baseline environments and full inputs are pinned.

## Known Dependency Risks

- [x] Avoided adding third-party repos directly as uv workspace members for now.
- [x] Documented the reduced-scope dependency-risk decision in `docs/THIRD_PARTY.md`: the verified artifact consumes committed parquet reports instead of rebuilding every third-party baseline environment.
- [ ] Resolve TracePicker Python version mismatch: TracePicker requests Python 3.12, while Gleaner uses Python 3.13.
- [ ] Resolve TracePicker heavy dependencies: torch, dgl, geatpy.
- [ ] Resolve TraStrainer platform mismatch: current TraStrainer pyproject still pins `rcabench-platform==0.3.34rc19`.
- [ ] Decide whether to use one unified Python 3.13 environment or per-baseline isolated environments.
- [x] Confirm all reduced experiments can run in CPU-only mode (`CUDA_VISIBLE_DEVICES='' bash scripts/run_reduced_all.sh`).

## Dataset Plan

- [x] Found local `data/rcabench-platform-v2` symlink to `/mnt/jfs/rcabench-platform-v2/`.
- [x] Confirmed local full TracePicker dataset path: `data/rcabench-platform-v2/data/tracepicker`.
- [x] Confirmed local full Gleaner dataset path: `data/rcabench-platform-v2/data/gleaner`.
- [x] Chosen reduced dataset strategy: full TracePicker dataset plus selected Gleaner datapacks.
- [x] Added committed reduced RQ2 RCA evidence under `data/artifact/reduced/rq2/` for ShapleyIQ/MicroRCA and Nezha.
- [x] Finalize and document the reduced dataset/data-evidence manifest for existing reduced evidence and expected outputs.
- [x] Add `scripts/prepare_reduced_data.sh`.
- [x] Compute reduced artifact manifest sizes for existing reduced evidence and expected outputs.
- [x] Compute checksums for reduced artifact manifest files.
- [x] Embedded reduced evidence and expected outputs needed by the reduced container path in Docker.
- [ ] Document full dataset download/extract/path setup.
- [ ] Add dataset provenance and storage requirements to `ARTIFACT_README.md` and `REQUIREMENTS.md`.

## Packaging

- [x] Added `.dockerignore`.
- [x] Added `Dockerfile`.
- [x] Tested `docker build -t gleaner-issta2026-ae .`.
- [x] Tested container command: `bash scripts/smoke_test.sh`.
- [x] Added final Docker build/run instructions to `ARTIFACT_README.md` after container smoke testing.
- [x] Decide final artifact package contents: source, third-party contents, reduced data/evidence, selected reduced sampler reports, expected outputs, docs, and scripts.
- [x] Prepare reduced artifact manifest with file sizes and checksums.
- [x] Add final local archive creation script: `scripts/package_artifact.sh`.
- [x] Generate local archive manifest and external checksum via `scripts/package_artifact.sh`.
- [ ] Upload the verified archive/checksum to the final public host.
- [ ] Mint or record DOI metadata after upload, if feasible.
- [ ] Prepare final HotCRP artifact link.

## Experiment Scripts

- [x] Added `scripts/smoke_test.sh`.
- [x] Added `scripts/run_reduced_all.sh`.
- [x] Added `scripts/run_full_all.sh`.
- [x] Added `scripts/run_rq1_sampling_quality.sh`.
- [x] Added `scripts/run_rq2_rca_effectiveness.sh`.
- [x] Added `scripts/run_rq3_ablation.sh`.
- [x] Added `scripts/run_rq4_efficiency.sh`.
- [x] Implemented reduced RQ1 sampling quality comparison.
- [x] Implemented reduced RQ2 RCA effectiveness under sampling.
- [x] Implemented reduced RQ3 Gleaner ablation study.
- [x] Implemented reduced RQ4 sampling efficiency/runtime/overhead.
- [x] Ensured each reduced RQ script writes to `output/artifact/reduced/rqX/` by default.
- [x] Each `scripts/run_rq*.sh` wrapper invokes `scripts/compare_expected.py` for expected-vs-actual validation.
- [x] Reviewer-verified `scripts/run_reduced_all.sh` completes the reduced end-to-end path.
- [x] `scripts/run_reduced_all.sh` generates reduced illustrative plots, plot-data files, and the final reduced report after RQ1-RQ4 summaries.
- [x] Make `scripts/run_full_all.sh` explicitly non-placeholder-safe with a non-zero not-implemented/not-verified exit.
- [ ] Add final full-suite execution behavior beyond the reduced reviewer path.
- [x] Benchmark and document reduced runtimes.

## Result Validation

- [x] Added `scripts/compare_expected.py`.
- [x] Generated expected reduced outputs under `artifact_expected/reduced/rq1/` through `artifact_expected/reduced/rq4/`.
- [x] Generated expected reduced plot-data/report outputs under `artifact_expected/reduced/figures/`.
- [x] Added expected-vs-actual comparison calls to each reduced RQ wrapper.
- [x] Reviewer-verified the current reduced all-in-one command passes with expected-output validation.
- [x] Define and document reduced sampler output schema.
- [x] Define and document reduced RCA ranking output schema.
- [x] Define and document reduced aggregate metric schema.
- [x] Define and document reduced plot-data/report schema; exact paper plotting scripts remain outside this snapshot.
- [x] Document numerical tolerance policy for expected-vs-actual comparisons.
- [x] Document what counts as a successful reduced reproduction.

## Paper Claim Mapping

- [x] Added claim mapping skeleton in `ARTIFACT_README.md`.
- [x] Mapped RQ1/RQ2/RQ3/RQ4 to reduced commands, output paths, and expected-output directories.
- [x] Map RQ1 to exact paper table/figure/section names recovered from `paper/main.pdf`.
- [x] Map RQ2 to exact paper table/figure/section names recovered from `paper/main.pdf`.
- [x] Map RQ3 to exact paper table/figure/section names recovered from `paper/main.pdf`.
- [x] Map RQ4 to exact paper table/figure/section names recovered from `paper/main.pdf`.
- [x] For each claim, document expected runtime.
- [x] List unsupported full-dataset / full-plot claims and explain reduced-scope limits.
- [x] Add reduced illustrative plots and final report generated from reduced summary CSVs.
- [ ] Integrate exact full-paper plotting scripts when available.

## Documentation

- [x] Added `ARTIFACT_README.md`.
- [x] Added `REQUIREMENTS.md`.
- [x] Added `STATUS.md`.
- [x] Added `docs/THIRD_PARTY.md`.
- [x] Added this checklist: `docs/ISSTA_AE_CHECKLIST.md`.
- [x] Added dev2 script record: `docs/DEV2_RQ_SCRIPT_RECORD.md`.
- [x] Linked this checklist from `ARTIFACT_README.md`.
- [x] Added reduced vs full explanation.
- [x] Added output and expected-output directory layout.
- [x] Add artifact entry point to root `README.md`.
- [x] Added final Docker instructions after Docker/container smoke verification.
- [x] Add troubleshooting section.
- [x] Add code layout and reuse guide for the reduced/offline artifact path.
- [x] Add instructions for running Gleaner summaries on new compatible datapack reports.
- [x] Add reduced data provenance and scope notes; third-party license checks remain tracked separately.
- [x] Add external submission guide for human upload/DOI/HotCRP steps without fake public identifiers.

## Badge Readiness

### Functional

- [x] Basic environment and submodule pin smoke test exists.
- [x] Reduced RQ1/RQ2/RQ3/RQ4 reproduction scripts are implemented.
- [x] Reduced RQ1/RQ2/RQ3/RQ4 wrappers validate actual outputs against expected outputs.
- [x] Reduced plot/report wrapper validates non-empty PNG files and compares plot-data/report expected outputs.
- [x] Expected reduced outputs are provided under `artifact_expected/reduced/`.
- [x] Current `scripts/run_reduced_all.sh` path is reviewer-verified as passing end to end.
- [x] Reduced reproduction runtime is benchmarked and documented.
- [x] Docker build, container smoke test, and container reduced-all run are verified.
- [x] Documentation maps claims to exact paper tables/figures recovered from `paper/main.pdf`.

### Reusable

- [x] Reduced adapter/report layout is documented.
- [x] Reduced data/report format is documented.
- [x] New-data usage is documented for compatible reduced/offline reports.
- [x] Baseline/RCA extension points are documented for the reduced/offline path.
- [x] Reduced scripts expose CLI input/output paths and strict validation for reviewer/user reruns.

### Available

- [ ] Public archival artifact link is prepared.
- [ ] DOI is prepared if feasible.
- [x] Local reduced manifest/checksums are documented; public dataset/archive link remains open.
- [ ] HotCRP submission link does not compromise reviewer anonymity.

## Immediate Next Steps

1. Regenerate the package after any final follow-up commit and use the new commit-SHA archive as the upload candidate.
2. Choose final artifact hosting location, upload the locally verified package, and record real DOI/release/HotCRP metadata.
3. Implement and reviewer-verify full-path behavior for `scripts/run_full_all.sh` and full RQ inputs if full reproduction is required.
4. If full reproduction is required later, add full plotting scripts and full-dataset adapter documentation beyond the reduced reviewer path.
