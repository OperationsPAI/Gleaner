# Troubleshooting

## Root `main.py` Fails On Online Container Imports

If `uv run python main.py ...` fails with an import from `rcabench.openapi`, use the offline wrapper for local reusable workflows:

```bash
uv run python scripts/full/platform_cli.py sample show-samplers
uv run python scripts/full/platform_cli.py eval show-algorithms
```

`main.py` uses the upstream full CLI, which imports online/container commands. The wrapper exposes only local `sample` and `eval` commands.

## Submodules Are Missing Or Empty

Initialize submodules after checkout:

```bash
git submodule update --init --recursive
```

The platform runtime should be at:

```text
platform/rcabench-platform
```

Third-party baselines remain under:

```text
third_party/Nezha
third_party/ShapleyIQ
third_party/TracePicker
third_party/TraStrainer
```

Run:

```bash
git submodule status
```

and confirm `platform/rcabench-platform` is pinned to `efd9e06688b70ff0b5e7a2d1821fd63c068ff6c4` (`v0.4.1`).

## Optional Third-Party Imports Are Missing

A minimal Gleaner environment may not install every full-path baseline dependency. For example, `scripts/full/platform_cli.py` may warn that optional TraStrainer samplers are skipped because `treelib` is missing.

For random/Gleaner-only smoke tests, this warning is safe. For full baseline work, sync the workspace and expect heavier dependencies:

```bash
uv sync --all-packages
```

TracePicker remains isolated in `third_party/TracePicker/.venv` because it requires Python `==3.12.*` and CUDA-oriented wheels.

## Dataset Is Not Found

If a command fails because `meta/<dataset>/index.parquet` is missing, the dataset has not been converted under the active `DATA_ROOT`.

Check environment variables:

```bash
echo "$DATA_ROOT"
echo "$OUTPUT_ROOT"
```

List converted datasets:

```bash
find "${DATA_ROOT:-data/rcabench-platform-v2}/meta" -maxdepth 2 -name index.parquet -print
```

For TracePicker trace-only data, run:

```bash
DATA_ROOT=temp/tracepicker-platform uv run python make_tracepicker.py run --src-folder data/tracepicker --dataset-name tracepicker
```

For raw RCABench data, run:

```bash
DATA_ROOT=temp/rcabench-platform-v2 uv run python platform/rcabench-platform/cli/dataset_transform/make_rcabench.py run --parallel 4 --no-skip-finished
```

## `make_tracepicker.py local-test` Cannot Find Input

The local test expects:

```text
data/tracepicker/sockshop/traces_spans.csv
```

If you are using a different TracePicker export, either place it under `data/tracepicker/<datapack>/traces_spans.csv` or pass it through `make_tracepicker.py run --src-folder <path>`.

## Raw RCABench Datapack Is Skipped

`make_rcabench.py` scans `data/rcabench_dataset/` and skips directories that do not have both `injection.json` and a usable `conclusion.csv`. It also skips datapacks whose `conclusion.csv` has only empty `Issues`.

If `conclusion.csv` is missing or stale, regenerate it with the detector flow:

```bash
DATAPACK=ts9-ts-basic-service-response-delay-hfvbg6
uv run python platform/rcabench-platform/cli/detector.py run \
  --in-p data/rcabench_dataset/$DATAPACK \
  --ou-p data/rcabench_dataset/$DATAPACK \
  --convert
```

Use a scratch copy if you are experimenting. Do not delete or regenerate committed fixture files unless that is the intended artifact update.

## Drain Templates Are Missing

Raw log conversion expects:

```text
data/rcabench_dataset/drain_template/drain_ts.ini
data/rcabench_dataset/drain_template/drain_ts.bin
```

If log messages changed, rebuild templates intentionally:

```bash
uv run python platform/rcabench-platform/cli/dataset_transform/make_rcabench.py build-template
```

Because this mutates `drain_ts.bin`, prefer a copied raw-data directory for experiments.

## Random RCA Fails With `NotImplementedError`

The built-in random RCA algorithm currently supports dataset names beginning with `rcabench` or `rcaeval`. Use it against the raw RCABench conversion path (`dataset=rcabench`) rather than the TracePicker trace-only conversion (`dataset=tracepicker`).

For TracePicker trace-only data, start with sampler smoke tests or implement an RCA algorithm that knows how to interpret normal-only labels.

## Sampler Perf Report Has No Files

`sample perf-report` reads prior sampler outputs. Run `sample single` or `sample batch` first with matching sampler/rate/mode filters.

Example:

```bash
uv run python scripts/full/platform_cli.py sample single random rcabench ts9-ts-basic-service-response-delay-hfvbg6 --sampling-rate 0.1 --mode offline --clear
uv run python scripts/full/platform_cli.py sample perf-report -d rcabench -s random -r 0.1 -m offline
```

## RCA Perf Report Has No Files

`eval perf-report` reads prior `eval single` or `eval batch` outputs. Run evaluation first:

```bash
uv run python scripts/full/platform_cli.py eval single random rcabench ts9-ts-basic-service-response-delay-hfvbg6 --clear
uv run python scripts/full/platform_cli.py eval perf-report rcabench
```

Use `--include-sampled` only after sampled RCA outputs exist.

## Generated Files Appear In `git status`

The repo intentionally ignores most generated data, output, caches, and virtual environments. If new generated parquet files appear unexpectedly, confirm whether they are part of the artifact evidence bundle before adding them.

Safe scratch locations:

```text
temp/
output/artifact/
dist/
```

## Expected-Output Comparison Fails

Use the diff path printed by `scripts/compare_expected.py`. Common causes are:

- output was written to a non-default directory and the Markdown path line changed;
- a random or sampled run updated reports before expected baselines were refreshed;
- reduced data files differ from `data/artifact/reduced/SHA256SUMS`.

Re-run the reduced manifest check:

```bash
bash scripts/prepare_reduced_data.sh
```
