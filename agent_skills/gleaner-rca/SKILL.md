---
name: gleaner-rca
description: Add, register, run, or validate RCA algorithms for Gleaner and RCAbench Platform. Use when asked to implement an RCA algorithm, wrap an external RCA baseline, register algorithms, run eval single/batch/perf-report, evaluate RCA on sampled traces, debug RCA output reports, or produce RCA report schemas for artifact reuse.
---

# Gleaner RCA

Use this skill when the task is about root-cause-analysis algorithms, RCA adapters, or RCA performance reports.

## References

- Human workflow: `docs/extending.md`
- Minimal platform RCA algorithm: `platform/rcabench-platform/src/rcabench_platform/v2/algorithms/random_.py`
- Platform evaluation runner: `platform/rcabench-platform/src/rcabench_platform/v2/experiments/single.py`
- External adapters: `third_party/Nezha`, `third_party/ShapleyIQ`
- Local offline CLI wrapper: `scripts/full/platform_cli.py`

## RCA Algorithm Contract

Implement `Algorithm` and return ranked `AlgorithmAnswer` objects:

```python
from rcabench_platform.v2.algorithms.spec import Algorithm, AlgorithmArgs, AlgorithmAnswer

class MyAlgorithm(Algorithm):
    def needs_cpu_count(self) -> int | None:
        return 4

    def __call__(self, args: AlgorithmArgs) -> list[AlgorithmAnswer]:
        # Read traces/logs/metrics from args.input_folder.
        # Write optional debug artifacts to args.output_folder.
        return [AlgorithmAnswer(level="service", name="example-service", rank=1)]
```

Register algorithms in `scripts/full/platform_cli.py` for local reuse workflows:

```python
from rcabench_platform.v2.algorithms.spec import global_algorithm_registry
registry = global_algorithm_registry()
registry["my_algorithm"] = MyAlgorithm
```

## Smoke Commands

Use a converted RCABench-style dataset and scratch output root:

```bash
export DATA_ROOT=temp/rcabench-platform-v2
export OUTPUT_ROOT=temp/rcabench-output
export DATASET=rcabench
export DATAPACK=ts9-ts-basic-service-response-delay-hfvbg6
```

Show algorithms:

```bash
GLEANER_PLATFORM_LOG_LEVEL=INFO \
uv run python scripts/full/platform_cli.py eval show-algorithms
```

Run single:

```bash
uv run python scripts/full/platform_cli.py eval single \
  random $DATASET $DATAPACK \
  --clear
```

Run batch:

```bash
uv run python scripts/full/platform_cli.py eval batch \
  -a random \
  -d $DATASET \
  --sample 1 \
  --use-cpus 4 \
  --clear
```

Generate report:

```bash
uv run python scripts/full/platform_cli.py eval perf-report $DATASET
```

## RCA On Sampled Traces

After running a sampler, evaluate RCA on sampled inputs:

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

## Output Expectations

`eval single` writes:

```text
$OUTPUT_ROOT/<dataset>/<datapack>/<algorithm>/output.parquet
$OUTPUT_ROOT/<dataset>/<datapack>/<algorithm>/perf.parquet
```

Sampled RCA output directories include the sampler suffix. `eval perf-report --include-sampled` writes grouped reports under:

```text
$OUTPUT_ROOT/meta/<dataset>/
```

Reduced artifact RQ2 can consume RCA reports with:

```text
algorithm, sampler.name, sampler.rate, AC@1, AC@3
```

## Validation

After RCA changes, run:

```bash
uv lock --check
bash -n scripts/smoke_test.sh scripts/package_artifact.sh
uv run python scripts/full/platform_cli.py eval single <algorithm> $DATASET $DATAPACK --clear
uv run python scripts/full/platform_cli.py eval perf-report $DATASET
```

If the algorithm is expected to run on sampled traces, also validate one sampled RCA path with `--sampler`, `--sampling-rate`, and `--sampling-mode`.
