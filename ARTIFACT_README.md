# Gleaner ISSTA 2026 Artifact

This document is the reviewer-facing entry point for the ISSTA 2026 artifact evaluation package.

## Artifact Overview

Progress checklist: see `docs/ISSTA_AE_CHECKLIST.md`.

The artifact evaluates Gleaner against baseline samplers and RCA algorithms using `rcabench-platform==0.4.1`.

Included components:

- Gleaner sampler and variants from this repository.
- RCA algorithms: MicroRCA and ShapleyIQ from ShapleyIQ, and Nezha from Nezha.
- Baseline samplers: TracePicker, TraStrainer, Sieve, and Sifter.
- Reduced artifact scripts for RQ1, RQ2, RQ3, and RQ4.
- Expected reduced outputs under `artifact_expected/reduced/rq1/` through `artifact_expected/reduced/rq4/`.
- Reduced RQ2 RCA evidence under `data/artifact/reduced/rq2/`.
- A guarded full-mode runner that intentionally exits non-zero because full reproduction is not implemented or reviewer-verified in this artifact snapshot.

Open items are tracked in `STATUS.md` and `docs/ISSTA_AE_TODO.md`. The reduced RQ1-RQ4 path is the verified reproduction path; full-path implementation/verification remains incomplete. Local archive packaging is available through `scripts/package_artifact.sh` and documented in `docs/RELEASE_PACKAGING.md`, but public upload, DOI minting, and HotCRP link submission remain external/manual and are not yet complete.

## Getting Started: 30-minute Path

```bash
git submodule update --init --recursive
uv sync --locked
bash scripts/smoke_test.sh
```

The smoke test verifies pinned submodule versions when Git metadata is available. In Docker/archive contexts without `.git`, it verifies the `third_party/` directories exist and are non-empty and clearly reports that SHA verification is skipped. The Python environment and artifact runner imports are also checked.


## Docker Path

Build the verified image:

```bash
docker build -t gleaner-issta2026-ae .
```

Run the verified container smoke test:

```bash
docker run --rm gleaner-issta2026-ae bash scripts/smoke_test.sh
```

Run the verified reduced reproduction inside the container:

```bash
docker run --rm gleaner-issta2026-ae bash scripts/run_reduced_all.sh
```

The Docker image embeds the reduced inputs needed by the verified path, including `artifact_expected/`, `data/artifact/`, and the reduced Gleaner sampler reports used by RQ1.

## Reduced Reproduction

Run all reduced experiments:

```bash
bash scripts/run_reduced_all.sh
```

The current `scripts/run_reduced_all.sh` path is reviewer-verified as passing end to end. It runs the smoke test and then RQ1/RQ2/RQ3/RQ4 in sequence.

Observed host runtime on 2026-06-28:

```text
time -p bash scripts/run_reduced_all.sh
real 2.96
user 16.51
sys 10.91
```

Reviewers should budget under 5 minutes for the reduced path on a typical x86_64 Linux machine. Container startup and first-time dependency setup may add extra time.

Or run individual RQs:

```bash
bash scripts/run_rq1_sampling_quality.sh
bash scripts/run_rq2_rca_effectiveness.sh
bash scripts/run_rq3_ablation.sh
bash scripts/run_rq4_efficiency.sh
```

Each individual wrapper runs its corresponding `scripts/artifact/rq*.py` script and then invokes `scripts/compare_expected.py` to compare actual outputs with the expected files under `artifact_expected/reduced/rqX/`.

Actual outputs are written under `output/artifact/reduced/`. Expected outputs are staged under `artifact_expected/reduced/`.

Expected-output checks are intentionally strict. JSON and CSV numeric values use default absolute and relative tolerances of `1e-12`; JSON `config.output_dir` is ignored by default; Markdown lines named `output directory` or `output_dir` are normalized by default; boolean JSON values are not treated as numeric aliases.

## Reduced Input Evidence

Verify the reduced evidence and expected-output files before running the reduced reproduction:

```bash
bash scripts/prepare_reduced_data.sh
```

The reduced manifest is `data/artifact/reduced/MANIFEST.json`, with optional checksum list `data/artifact/reduced/SHA256SUMS`. Its scope is the currently staged reduced evidence plus expected outputs: the reduced RQ1 Gleaner sampler reports, reduced RQ2 RCA evidence, and `artifact_expected/reduced/rq1/` through `artifact_expected/reduced/rq4/`. It does not include or synthesize raw 10-datapack directories.

The reduced RQ2 RCA evidence needed by `scripts/run_rq2_rca_effectiveness.sh` is staged at:

- `data/artifact/reduced/rq2/shapleyiq_microrca/sampler.grouped.perf.parquet`
- `data/artifact/reduced/rq2/nezha/sampler.grouped.perf.parquet`

## Full Reproduction

The full path is intentionally not presented as a runnable, verified reproduction in this artifact snapshot. Normal execution of `bash scripts/run_full_all.sh` prints a clear not-implemented/not-reviewer-verified message and exits non-zero so reviewers do not mistake a placeholder for success.

Use the verified reduced path instead:

```bash
bash scripts/run_reduced_all.sh
```

A future full path is expected to cover the complete TracePicker and Gleaner datasets and may take substantially longer than one day depending on hardware.

## Claim Mapping

| Paper claim/result | Reduced command | Actual output | Expected output | Current status |
|---|---|---|---|---|
| RQ1 sampling quality comparison | `bash scripts/run_rq1_sampling_quality.sh` | `output/artifact/reduced/rq1/` | `artifact_expected/reduced/rq1/` | Reduced script implemented and wrapper validates expected vs actual. |
| RQ2 RCA effectiveness under sampling | `bash scripts/run_rq2_rca_effectiveness.sh` | `output/artifact/reduced/rq2/` | `artifact_expected/reduced/rq2/` | Reduced script implemented; staged RQ2 RCA evidence is under `data/artifact/reduced/rq2/`. |
| RQ3 Gleaner ablations | `bash scripts/run_rq3_ablation.sh` | `output/artifact/reduced/rq3/` | `artifact_expected/reduced/rq3/` | Reduced script implemented and wrapper validates expected vs actual. |
| RQ4 sampling efficiency | `bash scripts/run_rq4_efficiency.sh` | `output/artifact/reduced/rq4/` | `artifact_expected/reduced/rq4/` | Reduced script implemented and wrapper validates expected vs actual. |

The combined reduced path was measured at 2.96 seconds wall-clock time on the local host. Exact paper table/figure names still need to be filled after paper integration. Full-dataset claims are not reviewer-verified by this artifact snapshot.

## Troubleshooting

- If `bash scripts/prepare_reduced_data.sh` fails, compare the reported path against `data/artifact/reduced/MANIFEST.json`; the reduced files must match the recorded byte sizes and SHA256 values.
- If `scripts/compare_expected.py` fails, use its reported JSON path, CSV row/column, or Markdown diff to inspect the generated files under `output/artifact/reduced/`.
- If Markdown differs only by output directory, ensure the wrappers are using the default comparison mode; output-directory lines are normalized by default.
- If `scripts/smoke_test.sh` reports skipped submodule SHA checks, confirm the run is from a packaged archive/container without `.git` and that each `third_party/` directory is present and non-empty.

## Local Release Packaging

Build a local archive and checksum with:

```bash
bash scripts/package_artifact.sh
```

The script writes `dist/gleaner-issta2026-ae-<git-short-sha-or-worktree>.tar.gz`, an external `.sha256` file, and an internal `ARCHIVE_MANIFEST.tsv` inside the archive. It packages the reduced artifact contents, selected reduced sampler reports, and actual `third_party/` file contents while excluding `.git`, `.venv`, caches, generated `output/artifact/`, raw/full data, and `dist/` itself. See `docs/RELEASE_PACKAGING.md` for details.

No public archive URL, DOI, or HotCRP artifact link has been minted or submitted yet. Do not add placeholder links or identifiers.

## Anonymous Review Considerations

ISSTA 2026 AE does not appear to require author anonymization of the artifact itself. It does require that artifact links be hosted on a platform that does not track reviewer IP addresses, to protect reviewer anonymity.
