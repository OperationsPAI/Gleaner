#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cat <<'MSG'
[full:env] Baseline environment policy
[full:env]   - Gleaner, Nezha, and ShapleyIQ: main uv workspace.
[full:env]   - TraStrainer/Sifter/Sieve: isolated Python 3.13 environment under third_party/TraStrainer/.venv.
[full:env]   - TracePicker: isolated Python 3.12 environment under third_party/TracePicker/.venv.
[full:env] TracePicker and TraStrainer are intentionally excluded from the main reduced workspace because they bring heavy baseline-specific dependencies.
MSG

if ! command -v uv >/dev/null 2>&1; then
  echo "[full:env] ERROR: uv is required." >&2
  exit 1
fi

echo "[full:env] checking main workspace resolution..."
(
  cd "${ROOT}"
  uv tree --depth 0
)

if [[ "${GLEANER_SYNC_BASELINE_WORKSPACE:-0}" == "1" ]]; then
  echo "[full:env] syncing/import-checking main workspace packages..."
  (
    cd "${ROOT}"
    uv run --all-packages python - <<'PY'
import importlib.metadata as md
import importlib
packages = ["Gleaner", "nezha", "shapleyiq", "rcabench-platform"]
for package in packages:
    try:
        print(f"{package}: {md.version(package)}")
    except md.PackageNotFoundError:
        raise SystemExit(f"missing package in workspace: {package}")
modules = [
    "gleaner",
    "nezha.rcabench_adapter",
    "shapleyiq.platform.algorithms",
]
for module in modules:
    importlib.import_module(module)
    print(f"import OK: {module}")
PY
  )
else
  cat <<'MSG'
[full:env] skipping workspace sync/import check by default.
[full:env] To sync and import-check all workspace baselines, run:
[full:env]   GLEANER_SYNC_BASELINE_WORKSPACE=1 bash scripts/full/setup_baseline_envs.sh
MSG
fi

if [[ "${GLEANER_SETUP_TRASTRAINER_ENV:-0}" == "1" ]]; then
  echo "[full:env] creating/updating TraStrainer isolated env..."
  (
    cd "${ROOT}/third_party/TraStrainer"
    uv sync --locked --no-dev
    PYTHONPATH="${ROOT}/src:${ROOT}/platform/rcabench-platform/src:${ROOT}/third_party/TraStrainer/src" \
      uv run python - <<'PY'
import sys
import importlib.metadata as md
import trastrainer.register_samplers  # noqa: F401
print(f"python: {sys.version.split()[0]}")
for package in ["TraStrainer", "rcabench-platform", "torch"]:
    print(f"{package}: {md.version(package)}")
print("import OK: trastrainer.register_samplers")
PY
  )
else
  cat <<'MSG'
[full:env] skipping TraStrainer env setup by default.
[full:env] To build it intentionally, run:
[full:env]   GLEANER_SETUP_TRASTRAINER_ENV=1 bash scripts/full/setup_baseline_envs.sh
MSG
fi

if [[ "${GLEANER_SETUP_TRACEPICKER_ENV:-0}" == "1" ]]; then
  echo "[full:env] creating/updating TracePicker isolated env..."
  (
    cd "${ROOT}/third_party/TracePicker"
    uv sync --python 3.12
    PYTHONPATH=src uv run python - <<'PY'
import sys
import importlib.metadata as md
import tracepicker
print(f"python: {sys.version.split()[0]}")
print(f"rcabench-platform: {md.version('rcabench-platform')}")
print("import OK: tracepicker")
PY
  )
else
  cat <<'MSG'
[full:env] skipping TracePicker env setup by default.
[full:env] To build it intentionally, run:
[full:env]   GLEANER_SETUP_TRACEPICKER_ENV=1 bash scripts/full/setup_baseline_envs.sh
MSG
fi
