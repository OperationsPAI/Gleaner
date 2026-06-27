# Artifact Status

This status file reflects the current committed / reviewer-verified local artifact state.

## Artifacts Evaluated - Functional

Current functional evidence:

- Reduced RQ1/RQ2/RQ3/RQ4 artifact scripts are implemented and connected to `scripts/run_rq*.sh` wrappers.
- Expected reduced outputs are provided under `artifact_expected/reduced/rq1/` through `artifact_expected/reduced/rq4/`.
- Each reduced RQ wrapper invokes `scripts/compare_expected.py` to validate expected vs actual outputs.
- `scripts/run_reduced_all.sh` is reviewer-verified as passing end to end in the current reduced state.
- Reduced RQ2 RCA evidence is committed under `data/artifact/reduced/rq2/`.
- Reduced manifest/checksum verification is provided by `data/artifact/reduced/MANIFEST.json`, `data/artifact/reduced/SHA256SUMS`, and `scripts/prepare_reduced_data.sh`.
- Host smoke testing has passed.
- Docker image build has passed with `docker build -t gleaner-issta2026-ae .`.
- Container smoke testing has passed with `docker run --rm gleaner-issta2026-ae bash scripts/smoke_test.sh`.
- Container reduced reproduction has passed with `docker run --rm gleaner-issta2026-ae bash scripts/run_reduced_all.sh`.
- Local release/archive packaging is implemented by `scripts/package_artifact.sh`; it generates a HEAD-derived tarball, internal manifest, and external SHA-256 checksum for local verification.
- The reduced path is CPU-only compatible: it runs with `CUDA_VISIBLE_DEVICES='' bash scripts/run_reduced_all.sh`.
- Third-party submodule pins, license-file evidence, public URL reachability, smoke-test coverage, and reduced-scope dependency risks are documented in `docs/THIRD_PARTY.md`.

Still open before claiming a final functional artifact:

- Full path is intentionally not final or reviewer-verified; `scripts/run_full_all.sh` is guarded to fail non-zero instead of succeeding as a placeholder.
- Public archive upload, DOI minting, and HotCRP artifact link submission are not prepared or performed.

## Artifacts Evaluated - Reusable

The reduced command entry points, expected-output validation, schema notes, claim mapping, and new-datapack reuse guidance are documented in `ARTIFACT_README.md`. The reusable scope is the reduced/offline artifact path: users can regenerate RQ summaries from compatible sampler-report and RCA parquet inputs, inspect expected-output comparisons, and extend baseline/RCA adapters by producing the documented report schemas. Full-dataset orchestration and full baseline environment integration remain outside the reviewer-verified scope.

Third-party reuse status is evidence-based in `docs/THIRD_PARTY.md`: ShapleyIQ and Nezha include license files in the vendored tree; TracePicker and TraStrainer do not include license files in the vendored snapshot and therefore remain unknown pending upstream/project-owner confirmation. Configured submodule URLs are reachable via public `git ls-remote` checks, but full third-party component execution remains outside the reduced reviewer-verified scope because TracePicker and TraStrainer have conflicting or heavy environment requirements.

## Artifacts Available

The reduced artifact manifest and checksum set are present for existing reduced evidence and expected outputs. A local package can be generated and verified with `bash scripts/package_artifact.sh`; the resulting archive contains `ARCHIVE_MANIFEST.tsv` and has a sibling `.sha256` file under `dist/`. Human external-upload instructions are provided in `docs/EXTERNAL_SUBMISSION_GUIDE.md`, but the final public archive upload, DOI/release metadata, and HotCRP link remain external P0 items. Do not treat the artifact as publicly archived or DOI-backed until those items are completed and verified.

## Badge Justification

- Functional: locally supportable for the reduced artifact path because smoke tests, RQ1-RQ4 reduced commands, expected-output comparisons, CPU-only execution, Docker execution, and archive packaging have been verified. The full reproduction path is explicitly not claimed.
- Reusable: partially supportable for the reduced/offline path because data schemas, command entry points, output locations, new-datapack guidance, extension points, and third-party readiness notes are documented. Full-dataset reuse, unknown-license follow-up for TracePicker/TraStrainer, and every third-party baseline execution environment are not fully verified.
- Available: not yet supportable as a public archival claim until a real public archive/release URL, DOI if required, and HotCRP artifact link are created and verified.
