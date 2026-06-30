# RCAbench Platform Sampling CLI Notes

Use `scripts/full/platform_cli.py` for local artifact runs. It wraps the RCAbench Platform v2 sample/eval commands without importing upstream online/container modules.

## Single Datapack Sampling

Run one sampler on one datapack:

```bash
uv run python scripts/full/platform_cli.py sample single \
  SAMPLER DATASET DATAPACK \
  --sampling-rate 0.05 \
  --mode offline \
  --clear
```

Example for TracePicker Dataset B:

```bash
uv run python scripts/full/platform_cli.py sample single \
  gleaner_no_logs_no_ad tracepicker trainticket \
  --sampling-rate 0.1 \
  --mode offline \
  --clear
```

- `SAMPLER`: sampler implementation name, e.g. `gleaner`, `gleaner_no_logs_no_ad`, `random`.
- `DATASET`: platform dataset name under `data/rcabench-platform-v2/data/`, e.g. `gleaner_lite`, `gleaner`, `tracepicker`.
- `DATAPACK`: datapack/system directory inside the dataset, e.g. `ts2-ts-basic-service-latency-ndg28l` or `trainticket`.
- `--sampling-rate`: target sampling rate for `sample single`.
- `--mode`: use `offline` for RQ1/RQ2/RQ3/RCA artifact runs; use `online` for RQ4 efficiency at the 5% target rate.
- `--clear`: remove an existing sampled output for the same sampler/rate/mode before rerunning.
- `--skip-finished` / `--no-skip-finished`: default skips completed outputs; use `--no-skip-finished` to force the command logic to revisit them.

## Batch Sampling

Run multiple samplers/datasets/rates:

```bash
uv run python scripts/full/platform_cli.py sample batch \
  -d gleaner_lite \
  -s gleaner \
  -s gleaner_no_logs \
  -s random \
  --rate 0.01 \
  --rate 0.05 \
  --mode offline \
  --use-cpus 8 \
  --clear
```

Important options:

- `-s` / `--sampler`: repeat to choose samplers or Gleaner variants.
- `-d` / `--dataset`: repeat to choose datasets.
- `-r` / `--rate`: repeat to choose target rates in batch mode.
- `--sample-datapacks N`: run only `N` datapacks for debugging.
- `--use-cpus N`: parallel worker count. Reduced scripts auto-detect half of available CPUs unless `GLEANER_REDUCED_CPUS=N` is set.
- `--clear`: clear prior sampled outputs before rerunning.

## Performance Reports

After sampling, build sampler reports:

```bash
uv run python scripts/full/platform_cli.py sample perf-report \
  -d gleaner_lite \
  --samplers gleaner \
  --samplers random \
  --sampling-rates 0.05 \
  --modes offline \
  --warn-missing
```

Reports are written under `output/rcabench-platform-v2/sampler_reports/<dataset>/`.

## RCA On Sampled Inputs

RCA evaluation has two input scopes:

- Full input: omit `--include-sampled`; this evaluates each RCA algorithm on the unsampled datapack.
- Sampled input: pass `--include-sampled` and choose the sampled version with `--sampler`, `--sampling-rate`, and `--sampling-mode`.

Reduced RCA uses Dataset A reduced scope (`gleaner_lite`) and evaluates MicroRCA, ShapleyIQ, and Nezha on the full input plus selected sampled inputs. The wrapper fixes the dataset, algorithms, and sampler family, but leaves rates and modes open by default:

```text
dataset: gleaner_lite
samplers: gleaner, paper Gleaner variants, random
rates: auto-discover all available sampled rates unless GLEANER_REDUCED_RATES is set
modes: auto-discover all available sampled modes unless GLEANER_REDUCED_MODES is set
```

The corresponding platform command shape is:

```bash
uv run python scripts/full/platform_cli.py eval batch \
  -d gleaner_lite \
  --algorithms microrca --algorithms shapleyiq --algorithms nezha \
  --include-sampled \
  --sampler gleaner \
  --sampling-rate 0.05 \
  --sampling-mode offline \
  --use-cpus 8
```

If `--include-sampled` is set but `--sampling-rate` and/or `--sampling-mode` are omitted, `eval batch` scans the selected dataset's `sampled/` directories and runs all available configurations that match the selected sampler(s). For example, specifying `--sampler gleaner` without a rate or mode runs RCA on every available `gleaner_<rate>_<mode>` sampled folder.

`scripts/run_rq3_rca_effectiveness.sh` exposes the same choices through environment variables:

- `GLEANER_REDUCED_RATES=0.01,0.1`: narrow sampled rates for RCA generation and summary filtering; unset means auto-discover all available rates.
- `GLEANER_REDUCED_MODES=offline`: narrow sampled-output modes consumed by RCA; unset means auto-discover all available modes.
- `GLEANER_REDUCED_RCA_SAMPLE_DATAPACKS=N`: debug on only `N` datapacks.
- `GLEANER_REDUCED_RCA_CLEAR=1`: clear existing RCA outputs before rerunning.
- `GLEANER_REDUCED_CPUS=N`: override the default half-of-available-CPUs worker count.

After `eval batch`, regenerate the RCA grouped report with:

```bash
uv run python scripts/full/platform_cli.py eval perf-report gleaner_lite \
  --include-sampled \
  --warn-missing
```

The artifact summary script reads `output/rcabench-platform-v2/meta/gleaner_lite/sampler.grouped.perf.parquet`, filters rows by `sampler.name` and `sampler.rate`, and exposes platform `AC@1`/`AC@3` as paper-facing `Accuracy@1`/`Accuracy@3`.

## Gleaner Variants

Choose variants with `-s` / `--sampler`; no code change is needed for normal runs. The paper-aligned Gleaner variants are:

```text
gleaner
gleaner_no_logs
gleaner_no_ad
gleaner_no_logs_no_ad
gleaner_wl_kernel
gleaner_pure_diversity
gleaner_top_score
gleaner_anomaly_pure_diversity
gleaner_no_dpp
```

Reviewer-facing names are defined in the artifact scripts, e.g. `gleaner_top_score` is shown as `Gleaner Pure Anomaly`, and `gleaner_anomaly_pure_diversity` is shown as `Gleaner w/o Anomaly`.

To add a new Gleaner variant, implement/register it in the Gleaner sampler package and add its registry name to the relevant script list (`configs/reduced/algorithms.yaml`, `scripts/run_full_sampling.sh`, or `scripts/run_full_rca.sh`). Use the same `-s new_sampler_name` interface once registered.

## Dataset Conversion Helpers

Dataset conversion helpers live under `scripts/data/`:

```bash
uv run python scripts/data/make_gleaner_lite.py
uv run python scripts/data/make_tracepicker.py local-test
```

The root-level compatibility wrappers were removed; use the `scripts/data/` paths in documentation and automation.
