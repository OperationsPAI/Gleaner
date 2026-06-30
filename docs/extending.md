# Extending Gleaner Samplers And RCA Algorithms

This guide shows how to run the platform smoke commands and where to add new samplers or RCA algorithms. It uses the offline wrapper `scripts/full/platform_cli.py` because it exposes only local `sample` and `eval` commands and avoids the upstream online/container CLI imports.

The examples assume a converted RCABench-style dataset exists. To build one from the local raw fixture first, run:

```bash
DATA_ROOT=temp/rcabench-platform-v2 \
uv run python platform/rcabench-platform/cli/dataset_transform/make_rcabench.py run \
  --parallel 4 \
  --no-skip-finished
```

Then set:

```bash
export DATA_ROOT=temp/rcabench-platform-v2
export OUTPUT_ROOT=temp/rcabench-output
export DATASET=rcabench
export DATAPACK=ts9-ts-basic-service-response-delay-hfvbg6
```

Use `GLEANER_PLATFORM_LOG_LEVEL=INFO` when you want command output from the Typer wrapper.

## Inspect Available Components

```bash
GLEANER_PLATFORM_LOG_LEVEL=INFO \
uv run python scripts/full/platform_cli.py sample show-samplers

GLEANER_PLATFORM_LOG_LEVEL=INFO \
uv run python scripts/full/platform_cli.py eval show-algorithms

GLEANER_PLATFORM_LOG_LEVEL=INFO \
uv run python scripts/full/platform_cli.py eval show-datasets
```

In a minimal environment, optional third-party samplers can be skipped if their dependencies are not installed. The built-in `random` sampler and Gleaner variants remain available.

## Random Sampler Smoke Commands

Run one sampler on one datapack:

```bash
uv run python scripts/full/platform_cli.py sample single \
  random $DATASET $DATAPACK \
  --sampling-rate 0.1 \
  --mode offline \
  --clear
```

Run one or more samplers over a dataset:

```bash
uv run python scripts/full/platform_cli.py sample batch \
  -s random \
  -d $DATASET \
  -r 0.1 \
  -m offline \
  --sample-datapacks 1 \
  --use-cpus 4 \
  --clear
```

Generate sampler reports:

```bash
uv run python scripts/full/platform_cli.py sample perf-report \
  -d $DATASET \
  -s random \
  -r 0.1 \
  -m offline
```

Sampler outputs are written below:

```text
$OUTPUT_ROOT/<dataset>/<datapack>/sampled/<sampler>_<rate>_<mode>/
$OUTPUT_ROOT/sampler_reports/<dataset>/
```

## Random RCA Smoke Commands

Run one RCA algorithm on one datapack:

```bash
uv run python scripts/full/platform_cli.py eval single \
  random $DATASET $DATAPACK \
  --clear
```

Run RCA over a dataset:

```bash
uv run python scripts/full/platform_cli.py eval batch \
  -a random \
  -d $DATASET \
  --sample 1 \
  --use-cpus 4 \
  --clear
```

Generate RCA reports:

```bash
uv run python scripts/full/platform_cli.py eval perf-report $DATASET
```

RCA outputs are written below:

```text
$OUTPUT_ROOT/<dataset>/<datapack>/<algorithm>/
$OUTPUT_ROOT/meta/<dataset>/
```

## Evaluate RCA On Sampled Traces

After running a sampler, RCA can consume sampled traces by passing sampler metadata:

```bash
uv run python scripts/full/platform_cli.py eval single \
  random $DATASET $DATAPACK \
  --sampler random \
  --sampling-rate 0.1 \
  --sampling-mode offline \
  --clear

uv run python scripts/full/platform_cli.py eval perf-report \
  $DATASET \
  --include-sampled
```

For batch mode with auto-detected sampled outputs:

```bash
uv run python scripts/full/platform_cli.py eval batch \
  -a random \
  -d $DATASET \
  --include-sampled \
  --sampler random \
  --sampling-rate 0.1 \
  --sampling-mode offline \
  --sample 1 \
  --use-cpus 4 \
  --clear
```

## Add A New Sampler

Implement the platform sampler contract:

```python
from rcabench_platform.v2.samplers.spec import SamplerArgs, SampleResult, TraceSampler

class MySampler(TraceSampler):
    def needs_cpu_count(self) -> int | None:
        return 4

    def __call__(self, args: SamplerArgs) -> list[SampleResult]:
        # Read args.input_folder / "normal_traces.parquet" and "abnormal_traces.parquet".
        # Return trace IDs with scores; the platform writes sampled parquet files and perf metrics.
        return [SampleResult(trace_id="example", sample_score=1.0)]
```

Register it before invoking the platform CLI. For Gleaner-local samplers, add the class under `src/gleaner/` and register it in `main.py` or `scripts/full/platform_cli.py`:

```python
from rcabench_platform.v2.samplers.spec import global_sampler_registry

registry = global_sampler_registry()
registry["my_sampler"] = MySampler
```

Use `platform/rcabench-platform/src/rcabench_platform/v2/samplers/random_.py` as the minimal reference implementation and `src/gleaner/core/sampler.py` for the Gleaner implementation pattern.

Validation sequence:

```bash
uv run python scripts/full/platform_cli.py sample single my_sampler $DATASET $DATAPACK --sampling-rate 0.1 --mode offline --clear
uv run python scripts/full/platform_cli.py sample perf-report -d $DATASET -s my_sampler -r 0.1 -m offline
```

## Add A New RCA Algorithm

Implement the platform RCA contract:

```python
from rcabench_platform.v2.algorithms.spec import Algorithm, AlgorithmArgs, AlgorithmAnswer

class MyAlgorithm(Algorithm):
    def needs_cpu_count(self) -> int | None:
        return 4

    def __call__(self, args: AlgorithmArgs) -> list[AlgorithmAnswer]:
        # Read traces/logs/metrics from args.input_folder and write optional debug data to args.output_folder.
        return [AlgorithmAnswer(level="service", name="example-service", rank=1)]
```

Register it before invoking the platform CLI:

```python
from rcabench_platform.v2.algorithms.spec import global_algorithm_registry

registry = global_algorithm_registry()
registry["my_algorithm"] = MyAlgorithm
```

Use `platform/rcabench-platform/src/rcabench_platform/v2/algorithms/random_.py` as the minimal reference implementation and the adapters under `third_party/Nezha` and `third_party/ShapleyIQ` as examples of wrapping external algorithms.

Validation sequence:

```bash
uv run python scripts/full/platform_cli.py eval single my_algorithm $DATASET $DATAPACK --clear
uv run python scripts/full/platform_cli.py eval perf-report $DATASET
```

## Report Schema Contract

If a new sampler or RCA algorithm is not integrated into the platform runner, it can still participate in reduced artifact scripts by producing compatible reports:

- sampler reports: `aggregated_perf.parquet` and, for per-datapack RQ1 checks, `detailed_perf.parquet` with `sampler`, `mode`, `sampling_rate`, and `datapack` where applicable;
- RCA reports: `sampler.grouped.perf.parquet` with `algorithm`, `sampler.name`, `sampler.rate`, `Accuracy@1`, and `Accuracy@3`.

The reduced scripts in `scripts/artifact/` accept explicit paths for these reports and write Markdown/CSV/JSON summaries under `output/artifact/reduced/`.
