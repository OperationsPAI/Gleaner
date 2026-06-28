# Full Paper Reproduction Scripts

These scripts describe the full paper setting, including full Dataset A, full Dataset B cross-system evaluation, baseline samplers, RCA algorithms, and paper figure/table generation.

The full path is intentionally not the reviewer-fast AE path. It can take days on CPU-only machines and depends on third-party baseline environments for TracePicker, TraStrainer, Sieve, Sifter, MicroRCA, ShapleyIQ, and Nezha.

## Baseline Environments

Baseline samplers are not all installed into the same Python environment:

- Nezha lives in `third_party/Nezha` and is included as a uv workspace member.
- ShapleyIQ/MicroRCA lives in `third_party/ShapleyIQ` and is included as a uv workspace member.
- TraStrainer, Sifter, and Sieve live in `third_party/TraStrainer` and are included as a uv workspace member because the updated submodule uses Python `>=3.13` and `rcabench-platform==0.4.1`.
- TracePicker lives in `third_party/TracePicker` and remains excluded from the workspace because it requires Python `==3.12.*` plus CUDA-oriented `torch`, `dgl`, and `geatpy` wheels.
- The shared platform runtime lives in `platform/rcabench-platform` and is used by the main uv workspace as an editable `rcabench-platform==0.4.1` source.

Check the baseline environment split with:

```bash
bash scripts/full/setup_baseline_envs.sh
```

Sync and import-check the main workspace baseline packages only when needed:

```bash
GLEANER_SYNC_BASELINE_WORKSPACE=1 bash scripts/full/setup_baseline_envs.sh
```

Create or update the isolated TracePicker environment only when needed:

```bash
GLEANER_SETUP_TRACEPICKER_ENV=1 bash scripts/full/setup_baseline_envs.sh
```

## Commands

Use the reduced path for fast artifact validation:

```bash
bash scripts/run_reduced_all.sh
```

Use the full path only when you intentionally want a long-running full paper reproduction. The runner rejects placeholder success and validates required reports/figures/tables at the end:

```bash
GLEANER_RUN_FULL=1 bash scripts/run_full_all.sh
```
