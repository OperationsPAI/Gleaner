#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[smoke] verifying submodule pins"
check_sha() {
  local path="$1"
  local expected="$2"
  local actual
  actual="$(git -C "$path" rev-parse HEAD)"
  if [[ "$actual" != "$expected" ]]; then
    echo "[smoke] ERROR: $path is at $actual, expected $expected" >&2
    exit 1
  fi
  echo "[smoke] OK $path $actual"
}

check_present() {
  local path="$1"
  if [[ ! -d "$path" ]]; then
    echo "[smoke] ERROR: $path is missing" >&2
    exit 1
  fi
  if ! find "$path" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
    echo "[smoke] ERROR: $path is empty" >&2
    exit 1
  fi
  echo "[smoke] OK $path exists and is non-empty"
}

if git -C . rev-parse --git-dir >/dev/null 2>&1; then
  check_sha third_party/ShapleyIQ f45c02e55f5614f8c9e5d54ba1882780c694ce90
  check_sha third_party/Nezha f0de4db8123a566e13c5fcfe6ac0d9137009f99a
  check_sha third_party/TracePicker 31e5fc8130c9b2c315220bb91397f2756dda8378
  check_sha third_party/TraStrainer 82b133d9a0209997e3337506988776ab07ac4ada
else
  echo "[smoke] Git metadata unavailable; skipping strict third_party SHA verification."
  echo "[smoke] Verifying third_party directories exist and are non-empty instead."
  check_present third_party/ShapleyIQ
  check_present third_party/Nezha
  check_present third_party/TracePicker
  check_present third_party/TraStrainer
fi

echo "[smoke] verifying Python imports"
uv run python - <<'PY'
import importlib.metadata as md
import gleaner
print("gleaner import OK")
print("rcabench-platform", md.version("rcabench-platform"))
PY

echo "[smoke] smoke test complete"
