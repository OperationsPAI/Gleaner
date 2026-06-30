# Gleaner ISSTA 2026 Artifact

Gleaner is a semantically rich online sampler for microservice diagnostics. This artifact supports the ISSTA 2026 Artifact Evaluation by packaging the Gleaner implementation, Platform integration, reduced live inputs, full-dataset inputs, third-party baseline/RCA code, and scripts that regenerate the artifact evidence for the paper's main experimental claims.

## Which Archive Should I Use?

The Zenodo artifact contains two Docker image archives plus the plain-text artifact files (`README.md`, `REQUIREMENTS.md`, `STATUS.md`, `LICENSE`, and supporting `docs/`). Use the reduced image first.

| Archive | Reviewer use | Contents | Expected scope |
|---|---|---|---|
| `gleaner-issta2026-ae-reduced-*.docker.tar.gz` | Primary AE artifact | Code, reduced Dataset A (`gleaner_lite`), TracePicker Dataset B reduced input (`tracepicker_lite`), reduced scripts | Getting Started plus reduced reproduction within one day |
| `gleaner-issta2026-ae-full-*.docker.tar.gz` | Optional/full validation | Everything in reduced plus complete Gleaner Dataset A (`gleaner`), full-path scripts, full baseline dependency support, a prebuilt isolated TraStrainer/Sifter/Sieve environment, and a prebuilt isolated TracePicker environment | Long-running full paper setting; may take multiple days |

The reduced image is the artifact path intended for reviewers. The full image is packaged separately so reviewers can inspect or launch the complete-paper setting without making the reduced path too large or slow. Compared with the reduced image, it adds the complete Dataset A and heavyweight baseline dependencies needed by the full pipeline. TraStrainer/Sifter/Sieve and TracePicker are installed in isolated full-image environments so their heavy baseline-specific dependencies do not pollute the reduced reviewer image.

## Part 1: Getting Started Guide

### Artifact Description

- Dataset A in the paper corresponds to the Gleaner dataset. The reduced Dataset A input is `gleaner_lite`, a deterministic 20-datapack subset selected by fault-category coverage and RCA trend matching.
- Dataset B in the paper corresponds to the TracePicker baseline paper dataset. The reduced Dataset B/cross-system reduced input is `tracepicker_lite`, taken from the TracePicker dataset and limited to two paper microservice systems (`trainticket`, `media`) so RQ1-B remains within the reduced runtime budget.
- Reduced RQ scripts regenerate sampler reports, downstream RCA summaries, efficiency summaries, reduced plots, and a final reduced report under `output/artifact/reduced/`.

### Installation

The recommended reviewer path uses Docker and does not require installing Python packages on the host. Load the reduced image:

```bash
gunzip -c gleaner-issta2026-ae-reduced-*.docker.tar.gz | docker load
```

If the archive also includes a checksum file, verify it before loading:

```bash
sha256sum -c gleaner-issta2026-ae-reduced-*.docker.tar.gz.sha256
```

The image tag is printed by `docker load`. In the examples below, replace `gleaner-issta2026-ae:reduced-<version>` with the loaded tag printed by `docker load`.

### Smoke Test

Run the smoke test inside the reduced image:

```bash
docker run --rm gleaner-issta2026-ae:reduced-<version> bash scripts/smoke_test.sh
```

Expected output includes:

```text
gleaner import OK
rcabench-platform 0.4.1
[smoke] smoke test complete
```

Reviewers should be able to finish the Docker load and smoke test within 30 minutes on a typical x86_64 Linux machine with Docker installed. First-time Docker image loading time depends on local disk speed.

## Part 2: Step-By-Step Reproduction Instructions

### One-Command Reduced Reproduction

Run all reduced experiments in the reduced image:

```bash
mkdir -p output
docker run --rm \
  -v "$PWD/output:/artifact/output" \
  gleaner-issta2026-ae:reduced-<version> \
  bash scripts/run_reduced_all.sh
```

Expected final signal:

```text
[reduced] all reduced RQ scripts and plots completed
```

This command runs the smoke test, checks reduced inputs, prepares `gleaner_lite` sampler reports, runs the reduced RQ scripts, and generates reduced plots plus `output/artifact/reduced/REPORT.md`. Sampler-report preparation uses half of the CPUs available to the process by default; override with `GLEANER_REDUCED_CPUS=N` if needed.

Example with an explicit CPU limit:

```bash
docker run --rm -e GLEANER_REDUCED_CPUS=8 \
  -v "$PWD/output:/artifact/output" \
  gleaner-issta2026-ae:reduced-<version> \
  bash scripts/run_reduced_all.sh
```

### Individual Reduced Experiments

Run these commands when inspecting a specific paper claim:

```bash
docker run --rm -it -v "$PWD/output:/artifact/output" \
  gleaner-issta2026-ae:reduced-<version> bash
```

Then run the desired command inside the container:

```bash
bash scripts/run_rq1_sampling_quality.sh
bash scripts/run_rq1b_cross_system.sh
bash scripts/run_rq2_ablation.sh
bash scripts/run_rq3_rca_effectiveness.sh
bash scripts/run_rq4_efficiency.sh
bash scripts/run_reduced_plots.sh
```

Generated outputs are written under:

```text
output/artifact/reduced/rq1/
output/artifact/reduced/rq1_cross_system/
output/artifact/reduced/rq2/
output/artifact/reduced/rq3/
output/artifact/reduced/rq4/
output/artifact/reduced/figures/
output/artifact/reduced/REPORT.md
```

### Paper Claims Supported By The Reduced Artifact

| Claim | Paper result area | Reduced evidence | Command(s) | Scope |
|---|---|---|---|---|
| C1 | RQ1 sampling quality and diversity; Dataset A and Dataset B evidence | Dataset A RQ1 tables/CSV/JSON; Dataset B Trace Pattern Coverage summary; reduced plot data | `run_rq1_sampling_quality.sh`, `run_rq1b_cross_system.sh` | Dataset A uses `gleaner_lite`; Dataset B uses the `tracepicker_lite` TracePicker input. RQ1-A reports Gleaner and available baselines |
| C2 | Paper RQ2 ablation study | Gleaner variant ablation summaries and reduced illustrative plot | `run_rq2_ablation.sh` | Variants follow the paper Table 5 naming. |
| C3 | Paper RQ3 downstream RCA accuracy | MicroRCA, ShapleyIQ, and Nezha Accuracy@1/Accuracy@3 summaries on full and sampled `gleaner_lite` inputs | `run_rq3_rca_effectiveness.sh` | RCA sampled inputs are selected by sampler/rate/mode; random is included as the reduced baseline. |
| C4 | RQ4 efficiency | Gleaner and Gleaner WL Kernel online runtime per trace, actual sampling rate, and benefit-cost ratio at 5% target rate | `run_rq4_efficiency.sh` | Reduced RQ4 reports Gleaner and Gleaner WL Kernel, matching the paper runtime comparison scope without running every ablation variant. |

The reduced outputs are intended to validate the artifact workflow and paper-style metrics on a one-day-or-less reduced scope. They are not claimed to exactly reproduce every full-paper figure pixel-for-pixel.

### Paper Claims Not Fully Supported By The Reduced Artifact

- Full-dataset numeric reproduction is not part of the primary reduced reviewer path; use the full image and `GLEANER_RUN_FULL=1 bash scripts/run_full_all.sh` for the long-running setting.
- Full cross-baseline Dataset B comparisons are reserved for the full path; the reduced path reports Dataset B Trace Pattern Coverage from `tracepicker_lite`.
- Exact camera-ready figure layout reproduction is not claimed; reduced plot scripts generate reviewer-readable illustrative PNGs and CSV plot data.
- Public archival metadata is not embedded in this repository; reviewers should use the files provided with the final artifact deposit.

### Reduced Dataset Selection Criteria

`gleaner_lite` is a deterministic 20-datapack subset of the full Gleaner Dataset A. The manifest is `configs/reduced/reduced20_datapacks.json`, generated/applied by `scripts/data/make_gleaner_lite.py`.

The selection criterion is fault-category coverage plus reduced RCA trend matching: cover the represented fault categories while choosing a one-day subset whose reduced RCA Accuracy@1/Accuracy@3 trends are close to the historical full Dataset A RCA results stored under `rca/`. The current manifest covers 15 fault categories. Five categories have two datapacks each (`corrupt`, `delay`, `partition`, `replace-body`, `stress`), and ten categories have one datapack each (`container-kill`, `exception`, `latency`, `loss`, `other`, `replace-code`, `replace-method`, `request-delay`, `response-delay`, `return`).

Dataset B is not fault-category sampled. The reduced Dataset B input is `tracepicker_lite`, a two-system subset (`trainticket`, `media`) taken directly from the TracePicker baseline paper dataset for cross-system Trace Pattern Coverage. The full `tracepicker` converted dataset remains available for full/diagnostic runs.

### RCA Sampled-Input Selection

Reduced RCA runs full-input RCA first, then runs sampled-input RCA with `eval batch --include-sampled`. Sampled inputs are selected by:

- sampler: `--sampler` / `-s`, e.g. `gleaner`, Gleaner paper variants, or `random`;
- rate: `--sampling-rate`; if omitted, all available sampled rates are auto-discovered under the selected sampler scope;
- mode: `--sampling-mode`; if omitted, all available sampled modes are auto-discovered under the selected sampler scope.

For example, specifying `--sampler gleaner` without a rate or mode runs RCA on all existing `gleaner_<rate>_<mode>` sampled folders. Use `GLEANER_REDUCED_RATES` and `GLEANER_REDUCED_MODES` only to narrow the scope.

More details are in `docs/RCABENCH_SAMPLE_CLI.md`.

### Full Reproduction Path

Load the full image when launching the complete long-running setting:

```bash
gunzip -c gleaner-issta2026-ae-full-*.docker.tar.gz | docker load
```

Run the guarded full path:

```bash
docker run --rm -e GLEANER_RUN_FULL=1 \
  -v "$PWD/output:/artifact/output" \
  gleaner-issta2026-ae:full-<version> \
  bash scripts/run_full_all.sh
```

Without `GLEANER_RUN_FULL=1`, the full command exits non-zero by design so placeholder full results cannot be mistaken for verified evidence. The full path uses complete Gleaner Dataset A, full baseline/RCA orchestration, paper sampling rates (`0.1%`, `1%`, `2.5%`, `5%`, `7.5%`, `10%`), RCA rates (`1%`, `10%`), and RQ4 online 5% efficiency reporting for Gleaner and Gleaner WL Kernel.

## Requirements, Status, And License

- `REQUIREMENTS.md` records architecture, hardware/software requirements, Docker/Python requirements, storage expectations, runtime notes, and parallel CPU behavior.
- `STATUS.md` records the badges requested and the current justification/status for each badge.
- `LICENSE` records the Gleaner artifact distribution terms. Third-party license notes are summarized in `docs/THIRD_PARTY.md`.

## Data Provenance, Ethics, And Storage

- The reduced image contains converted RCAbench Platform v2 reduced inputs: `gleaner_lite` and `tracepicker_lite`.
- The full image additionally contains complete Gleaner Dataset A (`data/rcabench-platform-v2/data/gleaner`, `data/rcabench-platform-v2/meta/gleaner`) and the complete converted TracePicker Dataset B (`data/rcabench-platform-v2/data/tracepicker`, `data/rcabench-platform-v2/meta/tracepicker`).
- The artifact does not require private credentials, commercial services, reviewer identity services, or network APIs after the image archive is available.
- Commands write generated outputs under `output/`; packaging scripts write archives/checksums under `dist/`.
- See `REQUIREMENTS.md` for storage estimates and `docs/THIRD_PARTY.md` for third-party source/license notes.

## Project Layout And Reuse Documentation

| Path | Purpose |
|---|---|
| `scripts/run_reduced_all.sh` | One-command reduced reproduction. |
| `scripts/run_rq*.sh` | Individual reduced claim wrappers. |
| `scripts/full/platform_cli.py` | Local RCAbench Platform sample/eval wrapper used by artifact scripts. |
| `scripts/data/make_gleaner_lite.py` | Builds/applies the reduced Dataset A manifest. |
| `scripts/data/make_tracepicker.py` | Builds TracePicker-format converted inputs. |
| `configs/reduced/reduced20_datapacks.json` | Reduced Dataset A datapack manifest and fault-category counts. |
| `docs/RCABENCH_SAMPLE_CLI.md` | Sampling/RCA CLI usage, `sample single`, `sample batch`, `-s`, rates, modes, CPU, and clear/rerun flags. |
| `docs/new-inputs.md` | How to adapt new TracePicker or RCAbench/ClickHouse inputs. |
| `docs/extending.md` | How to add samplers/RCA algorithms and expected schemas. |
| `docs/troubleshooting.md` | Common setup, conversion, detector, and report issues. |
| `docs/RELEASE_PACKAGING.md` | Docker image build/export details for submitters. |

For local sample/eval commands, prefer `scripts/full/platform_cli.py` over root `main.py`; the wrapper avoids upstream online/container imports and focuses on the local artifact workflows.

## Submitter Packaging Note

Reviewers normally do not need to rebuild images. Submitters can rebuild and export the Docker archives with:

```bash
bash scripts/package_docker_images.sh
```

The packaging script uses `docker save | gzip` and writes reduced/full image archives plus `.sha256` files under `dist/`. Detailed local build/export instructions are in `docs/RELEASE_PACKAGING.md`.
