# Gleaner

Gleaner is a semantically rich online sampler for microservice diagnostics. This repository is the ISSTA 2026 Artifact Evaluation workspace for reproducing the reduced evidence behind the paper claims and for reusing the sampler/RCA pipeline on new inputs.

This README is the main artifact entry point. Its structure follows the ISSTA AE requirement of a 30-minute Getting Started path plus step-by-step reproduction instructions, and borrows the correspondence/assumption style from the proof-artifact guidelines. The more detailed reference remains in `ARTIFACT_README.md`.

## Artifact Abstract

The artifact packages:

- Gleaner sampler implementations and reduced experiment scripts for RQ1-RQ4.
- `rcabench-platform==0.4.1` as a first-class platform dependency under `platform/rcabench-platform`.
- Third-party baseline/RCA repositories under `third_party/` as pinned submodules.
- Reduced input evidence under `data/artifact/reduced/` and expected outputs under `artifact_expected/reduced/`.
- Human-readable reuse docs plus purpose-specific agent skills for new inputs, samplers, and RCA algorithms.

The verified path is the reduced/offline AE path. It regenerates reduced summaries, reduced illustrative plots, and a final reduced report, then compares generated Markdown/CSV/JSON outputs against committed expected outputs. The full multi-day paper reproduction path is documented and guarded, but it is not claimed as reviewer-verified in this snapshot.

## Badge Status

| Badge | Current support | Notes |
|---|---|---|
| Functional | Supported for the reduced artifact path | `scripts/smoke_test.sh`, `scripts/run_reduced_all.sh`, expected-output comparisons, Docker smoke/reduced runs, and archive packaging are documented in `STATUS.md`. |
| Reusable | Partially supported for reduced/offline reuse | New-input conversion, sampler extension, RCA extension, schemas, troubleshooting, and agent skills are included. Full-dataset reuse is not fully verified. |
| Available | Not yet supported | A local archive can be built with `scripts/package_artifact.sh`, but public upload, DOI, and HotCRP artifact link are still external/manual steps. |

## Artifact Roadmap

| Path | Purpose |
|---|---|
| `ARTIFACT_README.md` | Detailed AE reference: reduced/full paths, claim mapping, schemas, packaging, and troubleshooting. |
| `REQUIREMENTS.md` | Hardware, software, runtime, validation, and packaging requirements. |
| `STATUS.md` | Badge readiness, verified evidence, and open blockers. |
| `LICENSE` | Distribution terms for the Gleaner artifact; third-party license notes are in `docs/THIRD_PARTY.md`. |
| `scripts/run_reduced_all.sh` | One-command reduced RQ1-RQ4 reproduction and plot/report generation. |
| `scripts/smoke_test.sh` | Installation and submodule/package smoke test. |
| `scripts/package_artifact.sh` | Local archive and checksum builder. |
| `data/artifact/reduced/` | Reduced evidence manifest, checksums, sampler/RCA inputs, and TracePicker cross-system summary evidence. |
| `artifact_expected/reduced/` | Expected reduced outputs used by strict comparison checks. |
| `output/artifact/reduced/` | Generated reduced outputs; ignored/recreated by runs. |
| `docs/new-inputs.md` | Reuse guide for TracePicker trace-only and raw RCABench/ClickHouse OpenTelemetry inputs. |
| `docs/extending.md` | Reuse guide for sampler/RCA smoke commands and extension contracts. |
| `docs/troubleshooting.md` | Common setup, conversion, detector, submodule, and report issues. |
| `agent_skills/gleaner-new-inputs/SKILL.md` | Agent workflow for adapting new inputs. |
| `agent_skills/gleaner-sampler/SKILL.md` | Agent workflow for adding/validating samplers. |
| `agent_skills/gleaner-rca/SKILL.md` | Agent workflow for adding/validating RCA algorithms. |
| `platform/rcabench-platform` | Shared RCAbench Platform v2 runtime, pinned to `rcabench-platform==0.4.1`. |
| `third_party/` | Pinned third-party baseline samplers and RCA implementations. |

## Security, Privacy, And Ethics

- The verified commands run locally and write generated files under `output/` or `dist/`; they do not delete user data.
- No private credentials, commercial services, reviewer identity services, or network APIs are required after dependencies and artifact files are obtained.
- The reduced evidence is a compact derived bundle; raw full datasets are not shipped in the reduced package.
- Third-party code is vendored for inspection and execution where supported. License-file evidence and unknown-license notes are recorded in `docs/THIRD_PARTY.md`.
- GPU is not required for the verified reduced path. Some full/upstream baseline environments may have heavier or CUDA-oriented dependencies and are outside the fast reduced validation path.

## Access And Archive Status

For a source checkout, use the `issta-26-artifact` branch and initialize submodules:

```bash
git submodule update --init --recursive
```

For an archive/container artifact, the submodule contents should already be vendored. In that case, skip the `git submodule` command and run the smoke test below.

No public archival URL or DOI is recorded yet. To build the local archive that should later be uploaded by a human submitter:

```bash
bash scripts/package_artifact.sh
```

The script writes a `dist/gleaner-issta2026-ae-*.tar.gz` archive, a sibling `.sha256` file, and an internal `ARCHIVE_MANIFEST.tsv`. See `docs/RELEASE_PACKAGING.md` and `docs/EXTERNAL_SUBMISSION_GUIDE.md` before creating final public links.

## Requirements

- OS/architecture: x86_64 Linux is the verified platform.
- Python: 3.13 for the Gleaner artifact runner.
- Package manager: `uv` for dependency installation and locked execution.
- Core dependency: `rcabench-platform==0.4.1` from `platform/rcabench-platform`.
- Runtime: CPU-only for the verified reduced path; Docker 24+ is recommended for a containerized path.
- Storage: budget several GB for Python packages, caches, Docker layers, and generated outputs; the committed reduced evidence itself is small and checksum-tracked.
- Network: required only to fetch dependencies or upload a final archive; not required by the verified reduced experiment commands after setup.

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the locked environment:

```bash
uv sync --locked
```

## Getting Started: 30-Minute Path

Run these commands from the repository root:

```bash
git submodule update --init --recursive
uv sync --locked
bash scripts/smoke_test.sh
```

Expected smoke-test signals include:

```text
gleaner import OK
rcabench-platform 0.4.1
[smoke] smoke test complete
```

In archive/container contexts without `.git`, strict submodule SHA checks are skipped and replaced with non-empty directory checks for `third_party/` and `platform/rcabench-platform`.

## Docker Path

Build the image:

```bash
docker build -t gleaner-issta2026-ae .
```

Run the smoke test:

```bash
docker run --rm gleaner-issta2026-ae bash scripts/smoke_test.sh
```

Run the verified reduced reproduction:

```bash
docker run --rm gleaner-issta2026-ae bash scripts/run_reduced_all.sh
```

## Evaluation Workflow

### Major Claims

| Claim | Paper result area | Artifact evidence | Reduced command | Scope note |
|---|---|---|---|---|
| C1 | Sampling quality and diversity, including Dataset A and Dataset B evidence | RQ1 summaries, RQ1-B TracePicker cross-system summaries, reduced plot data | `bash scripts/run_rq1_sampling_quality.sh`; `bash scripts/run_rq1b_cross_system.sh` | Reduced Dataset A uses a deterministic 20-datapack subset; Dataset B uses portable TracePicker summary evidence. |
| C2 | Ablation study of Gleaner variants | RQ3 summaries and reduced ablation plot data | `bash scripts/run_rq3_ablation.sh` | Artifact script name is RQ3, while the paper labels ablation as RQ2. |
| C3 | Downstream RCA accuracy under sampling | RQ2 RCA summaries from Nezha and ShapleyIQ/MicroRCA evidence | `bash scripts/run_rq2_rca_effectiveness.sh` | Artifact script name is RQ2, while the paper labels downstream RCA as RQ3. |
| C4 | Efficiency and sampling overhead | RQ4 runtime, benefit-cost, actual-rate, and controllability summaries | `bash scripts/run_rq4_efficiency.sh` | Reduced summaries are deterministic evidence, not full-dataset timing reproduction. |

The exact paper location mapping is maintained in `ARTIFACT_README.md`. Unsupported or not-yet-verified claims are also stated there and in `STATUS.md`.

### E0: Installation And Smoke Test

- Preparation: install `uv`; initialize submodules if running from a Git checkout.
- Execution: run `uv sync --locked` and `bash scripts/smoke_test.sh`.
- Results: confirm the smoke-test output reports `gleaner import OK`, `rcabench-platform 0.4.1`, and `[smoke] smoke test complete`.
- Expected time: under 30 person-minutes after the artifact is available; first dependency download can dominate wall-clock time.

### E1: One-Command Reduced Reproduction

Run all reduced experiments and expected-output checks:

```bash
bash scripts/run_reduced_all.sh
```

Expected final signal:

```text
[reduced] all reduced RQ scripts and plots completed
```

This command runs the smoke test, prepares reduced sampler reports, runs RQ1/RQ1-B/RQ2/RQ3/RQ4, generates reduced plots, writes `output/artifact/reduced/REPORT.md`, and compares generated outputs against `artifact_expected/reduced/`. The locally recorded runtime on 2026-06-28 was under 10 seconds after setup; reviewers should budget under 5 minutes on a typical x86_64 Linux machine.

### E2: Individual Reduced Experiments

Run individual experiments when inspecting a specific claim:

```bash
bash scripts/run_rq1_sampling_quality.sh
bash scripts/run_rq1b_cross_system.sh
bash scripts/run_rq2_rca_effectiveness.sh
bash scripts/run_rq3_ablation.sh
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

Expected outputs are committed under `artifact_expected/reduced/`. Each wrapper compares Markdown/CSV/JSON outputs with strict numeric tolerances. Plot PNGs are checked for existence and non-empty size; plot-data CSV/JSON and the report are compared against expected files.

### E3: Reduced Input Evidence Check

Before or after reproduction, verify the reduced input manifest and checksums:

```bash
bash scripts/prepare_reduced_data.sh
```

The manifest is `data/artifact/reduced/MANIFEST.json`; optional checksums are in `data/artifact/reduced/SHA256SUMS`.

### E4: Full Reproduction Guard

The full path is intentionally separated from the reviewer-verified reduced path:

```bash
GLEANER_RUN_FULL=1 bash scripts/run_full_all.sh
```

This path is for future/full orchestration only. It may require full datasets, isolated third-party environments, and multiple days. Running `bash scripts/run_full_all.sh` without `GLEANER_RUN_FULL=1` exits non-zero by design so placeholder full results cannot be mistaken for verified evidence.

## Reusing Gleaner

Reusable support is split into human-readable docs and agent-oriented workflows.

Human docs:

- `docs/new-inputs.md`: two new-input paths, including TracePicker trace-only conversion through `make_tracepicker.py` and raw RCABench/ClickHouse OpenTelemetry conversion through `platform/rcabench-platform/cli/dataset_transform/make_rcabench.py`.
- `docs/extending.md`: local `random` sampler/RCA smoke commands, sample/eval single and batch flows, perf-report commands, sampler contract, RCA contract, and report schemas.
- `docs/troubleshooting.md`: setup, submodule, conversion, detector/conclusion, Drain3 template, optional dependency, and report-generation issues.

Agent skills:

- `agent_skills/gleaner-new-inputs/SKILL.md`: inspect and convert new input datasets.
- `agent_skills/gleaner-sampler/SKILL.md`: add/register/validate samplers.
- `agent_skills/gleaner-rca/SKILL.md`: add/register/validate RCA algorithms.

Minimal local reuse checks:

```bash
uv run python make_tracepicker.py local-test

DATA_ROOT=temp/rcabench-platform-v2 \
uv run python platform/rcabench-platform/cli/dataset_transform/make_rcabench.py run \
  --parallel 4 \
  --no-skip-finished

GLEANER_PLATFORM_LOG_LEVEL=INFO \
uv run python scripts/full/platform_cli.py sample show-samplers

GLEANER_PLATFORM_LOG_LEVEL=INFO \
uv run python scripts/full/platform_cli.py eval show-algorithms
```

For local offline sample/eval commands on this artifact branch, prefer `scripts/full/platform_cli.py` over root `main.py`; the wrapper avoids upstream online/container imports and focuses on local sample/eval workflows.

## Data Format

Gleaner consumes RCAbench Platform v2 datapacks with traces, metrics, logs, labels, and attributes where available. The reduced AE scripts primarily consume generated report files, while the reuse path can convert raw inputs into the platform layout.

### Traces

| Column | Type | Description |
|---|---|---|
| `time` | datetime | Span start time in UTC. |
| `trace_id` | string | Unique trace identifier. |
| `span_id` | string | Unique span identifier. |
| `parent_span_id` | string | Parent span identifier. |
| `service_name` | string | Service that generated the span. |
| `span_name` | string | Operation represented by the span. |
| `duration` | uint64 | Span duration in nanoseconds. |
| `attr.*` | any | Additional span attributes. |

### Metrics

| Column | Type | Description |
|---|---|---|
| `time` | datetime | Metric timestamp in UTC. |
| `metric` | string | Metric name. |
| `value` | float64 | Metric value. |
| `service_name` | string | Service that generated the metric. |
| `attr.*` | any | Additional metric attributes. |

### Logs

| Column | Type | Description |
|---|---|---|
| `time` | datetime | Log timestamp in UTC. |
| `trace_id` | string | Related trace identifier, when available. |
| `span_id` | string | Related span identifier, when available. |
| `service_name` | string | Service that generated the log. |
| `level` | string | Log level. |
| `message` | string | Log message. |
| `attr.*` | any | Additional log attributes. |

Report schemas consumed by reduced experiments are documented in `ARTIFACT_README.md` and `docs/extending.md`.

## Troubleshooting

Start with `docs/troubleshooting.md`. Common quick checks:

```bash
git submodule status --recursive
uv lock --check
bash scripts/smoke_test.sh
bash scripts/prepare_reduced_data.sh
```

If expected-output comparison fails, inspect the path reported by `scripts/compare_expected.py` and compare generated files in `output/artifact/reduced/` with committed files in `artifact_expected/reduced/`.

## Citation

If you use Gleaner in your research, please cite:

```bibtex
@misc{yang2026gleanersemanticallyrichefficientonline,
  title={Gleaner: A Semantically-Rich and Efficient Online Sampler for Microservice Diagnostics},
  author={Yifan Yang and Aoyang FANG and Songhan Zhang and Pinjia He},
  year={2026},
  eprint={2604.16810},
  archivePrefix={arXiv},
  primaryClass={cs.SE},
  url={https://arxiv.org/abs/2604.16810},
}
```
