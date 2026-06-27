#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

manifest="data/artifact/reduced/MANIFEST.json"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest)
      if [[ $# -lt 2 ]]; then
        echo "FAIL --manifest requires a path" >&2
        exit 2
      fi
      manifest="$2"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: bash scripts/prepare_reduced_data.sh [--manifest PATH]

Verify the reduced artifact evidence listed in MANIFEST.json.
This script does not download, generate, or synthesize any data.
EOF
      exit 0
      ;;
    *)
      echo "FAIL unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

python3 - "$manifest" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
print(f"Verifying reduced artifact manifest: {manifest_path}")
print("Mode: verify-only; no downloads, generation, or data synthesis are performed.")

if not manifest_path.is_file():
    print(f"FAIL manifest missing: {manifest_path}")
    sys.exit(1)

with manifest_path.open("r", encoding="utf-8") as f:
    manifest = json.load(f)

ok = True
seen = 0
actual_total = 0
expected_total = 0

for item in manifest.get("files", []):
    path = Path(item["path"])
    expected_bytes = int(item["bytes"])
    expected_sha256 = item["sha256"]
    expected_total += expected_bytes
    seen += 1

    if not path.is_file():
        print(f"FAIL {path} missing")
        ok = False
        continue

    actual_bytes = path.stat().st_size
    actual_total += actual_bytes
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    actual_sha256 = h.hexdigest()

    if actual_bytes != expected_bytes:
        print(f"FAIL {path} bytes expected={expected_bytes} actual={actual_bytes}")
        ok = False
    elif actual_sha256 != expected_sha256:
        print(f"FAIL {path} sha256 expected={expected_sha256} actual={actual_sha256}")
        ok = False
    else:
        print(f"OK   {path} bytes={actual_bytes} sha256={actual_sha256}")

manifest_totals = manifest.get("totals", {})
if int(manifest_totals.get("file_count", seen)) != seen:
    print(f"FAIL totals.file_count expected={manifest_totals.get('file_count')} actual={seen}")
    ok = False
if int(manifest_totals.get("bytes", expected_total)) != expected_total:
    print(f"FAIL totals.bytes expected={manifest_totals.get('bytes')} actual={expected_total}")
    ok = False

print(f"Total files: {seen}")
print(f"Total bytes: {expected_total}")
if actual_total != expected_total:
    print(f"Actual bytes present: {actual_total}")

sys.exit(0 if ok else 1)
PY
