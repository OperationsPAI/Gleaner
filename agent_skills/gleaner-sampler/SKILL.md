---
name: gleaner-sampler
description: Add, register, run, or validate Gleaner-compatible trace samplers. Use when asked to implement a sampler, add a sampling baseline, register a sampler in main.py or scripts/full/platform_cli.py, run sample single/batch/perf-report, debug sampler output folders, or generate sampler reports for reduced artifact reuse.
---

# Gleaner Sampler

Use this skill when the task is about trace sampling, sampler extensions, or sampler performance reports.

## References

- Human workflow: `docs/extending.md`
- Minimal platform sampler: `platform/rcabench-platform/src/rcabench_platform/v2/samplers/random_.py`
- Gleaner sampler implementation: `src/gleaner/core/sampler.py`
- Local offline CLI wrapper: `scripts/full/platform_cli.py`

## Sampler Contract

Implement `TraceSampler` and return `list[SampleResult]`:

```python
from rcabench_platform.v2.samplers.spec import SamplerArgs, SampleResult, TraceSampler

class MySampler(TraceSampler):
    def needs_cpu_count(self) -> int | None:
        return 4

    def __call__(self, args: SamplerArgs) -> list[SampleResult]:
        # Read args.input_folder / "normal_traces.parquet" and "abnormal_traces.parquet".
        # Return trace IDs and scores; the platform handles sampled files and perf metrics.
        return [SampleResult(trace_id="example", sample_score=1.0)]
```

Register Gleaner-local samplers in `main.py` and, for full/reuse workflows, in `scripts/full/platform_cli.py`:

```python
from rcabench_platform.v2.samplers.spec import global_sampler_registry
registry = global_sampler_registry()
registry["my_sampler"] = MySampler
```

## Smoke Commands

Use a converted dataset and scratch output root:

```bash
export DATA_ROOT=temp/rcabench-platform-v2
export OUTPUT_ROOT=temp/rcabench-output
export DATASET=rcabench
export DATAPACK=ts9-ts-basic-service-response-delay-hfvbg6
```

Show samplers:

```bash
GLEANER_PLATFORM_LOG_LEVEL=INFO \
uv run python scripts/full/platform_cli.py sample show-samplers
```

Run single:

```bash
uv run python scripts/full/platform_cli.py sample single \
  random $DATASET $DATAPACK \
  --sampling-rate 0.1 \
  --mode offline \
  --clear
```

Run batch:

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

Generate report:

```bash
uv run python scripts/full/platform_cli.py sample perf-report \
  -d $DATASET \
  -s random \
  -r 0.1 \
  -m offline
```

## Output Expectations

Sampler single/batch writes sampled traces and `perf.parquet` under:

```text
$OUTPUT_ROOT/<dataset>/<datapack>/sampled/<sampler>_<rate>_<mode>/
```

`sample perf-report` writes dataset-level reports under:

```text
$OUTPUT_ROOT/sampler_reports/<dataset>/
```

Reduced artifact scripts can consume compatible `aggregated_perf.parquet` and `detailed_perf.parquet` reports even when the sampler itself is external.

## Validation

After sampler changes, run:

```bash
uv lock --check
bash -n scripts/smoke_test.sh scripts/package_artifact.sh
uv run python scripts/full/platform_cli.py sample single <sampler> $DATASET $DATAPACK --sampling-rate 0.1 --mode offline --clear
uv run python scripts/full/platform_cli.py sample perf-report -d $DATASET -s <sampler> -r 0.1 -m offline
```
