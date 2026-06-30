#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

cat <<'EOF'
[reduced:data] live-input mode: no staged data/artifact evidence is required.
[reduced:data] Required local inputs are converted datasets under data/rcabench-platform-v2/:
[reduced:data]   - meta/gleaner_lite/index.parquet and data/gleaner_lite/
[reduced:data]   - meta/tracepicker_lite/index.parquet and data/tracepicker_lite/
EOF

test -f data/rcabench-platform-v2/meta/gleaner_lite/index.parquet
test -d data/rcabench-platform-v2/data/gleaner_lite
test -f data/rcabench-platform-v2/meta/tracepicker_lite/index.parquet
test -d data/rcabench-platform-v2/data/tracepicker_lite

echo "[reduced:data] OK live reduced inputs are present"
