---
name: gleaner-new-inputs
description: Convert or adapt new input datasets for Gleaner. Use when asked to ingest TracePicker trace-only CSV data, raw RCABench/ClickHouse OpenTelemetry datapacks, regenerate RCAbench Platform datasets, run make_tracepicker.py, run make_rcabench.py, handle detector/conclusion.csv conversion, or troubleshoot DATA_ROOT/meta/index dataset layout for new inputs.
---

# Gleaner New Inputs

Use this skill when the task is about getting data into the RCAbench Platform v2 layout that Gleaner consumes. Work from the repository root.

## Start Here

1. Read `docs/new-inputs.md` for the full human-facing workflow.
2. Keep experiments in scratch roots unless the user explicitly wants committed fixtures changed:
   ```bash
   export DATA_ROOT=temp/reuse-data
   export OUTPUT_ROOT=temp/reuse-output
   ```
3. Confirm the platform submodule is present:
   ```bash
   test -d platform/rcabench-platform && git submodule status platform/rcabench-platform
   ```

## Choose The Input Path

- **TracePicker trace-only input**: source has `traces_spans.csv`; use `make_tracepicker.py`.
- **Raw RCABench/ClickHouse OTel input**: source has normal/abnormal traces, logs, metrics, `env.json`, `injection.json`, `k8s.json`, and usually `conclusion.csv`; use platform `make_rcabench.py`.
- **Missing or stale detector output**: run `platform/rcabench-platform/cli/detector.py` before dataset conversion.

## TracePicker Trace-Only Workflow

Expected input:

```text
data/tracepicker/<datapack>/traces_spans.csv
```

Run:

```bash
uv run python make_tracepicker.py local-test

DATA_ROOT=temp/tracepicker-platform \
uv run python make_tracepicker.py run \
  --src-folder data/tracepicker \
  --dataset-name tracepicker
```

Verify:

```bash
find temp/tracepicker-platform/meta/tracepicker -maxdepth 1 -type f -print
find temp/tracepicker-platform/data/tracepicker -maxdepth 2 -name normal_traces.parquet -print | head
```

Report the limitation: this path creates a normal-stage trace-only dataset with empty logs, metrics, and abnormal traces. Prefer sampler checks and Gleaner no-log/no-alarm variants such as `gleaner_no_logs_no_ad`.

## Raw RCABench / ClickHouse OTel Workflow

Expected input root:

```text
data/rcabench_dataset/<datapack>/
```

The datapack should contain raw `normal_*` and `abnormal_*` parquet files, `env.json`, `injection.json`, `k8s.json`, and `conclusion.csv`. Drain3 template state should exist under `data/rcabench_dataset/drain_template/`.

If `conclusion.csv` must be regenerated, run the detector on a scratch copy when possible:

```bash
DATAPACK=ts9-ts-basic-service-response-delay-hfvbg6
uv run python platform/rcabench-platform/cli/detector.py run \
  --in-p data/rcabench_dataset/$DATAPACK \
  --ou-p data/rcabench_dataset/$DATAPACK \
  --convert
```

Convert the dataset:

```bash
DATA_ROOT=temp/rcabench-platform-v2 \
uv run python platform/rcabench-platform/cli/dataset_transform/make_rcabench.py run \
  --parallel 4 \
  --no-skip-finished
```

Verify:

```bash
find temp/rcabench-platform-v2/meta/rcabench -maxdepth 1 -type f -print
find temp/rcabench-platform-v2/data/rcabench -maxdepth 2 -name abnormal_traces.parquet -print | head
```

## Validation

Run at least one cheap smoke command after conversion:

```bash
DATA_ROOT=temp/rcabench-platform-v2 OUTPUT_ROOT=temp/rcabench-output \
uv run python scripts/full/platform_cli.py sample single \
  random rcabench ts9-ts-basic-service-response-delay-hfvbg6 \
  --sampling-rate 0.1 --mode offline --clear
```

If the task touches docs or scripts, also run:

```bash
uv run python make_tracepicker.py local-test
bash -n scripts/smoke_test.sh scripts/package_artifact.sh
```
