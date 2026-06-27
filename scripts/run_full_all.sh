#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'USAGE'
Usage: bash scripts/run_full_all.sh

Full reproduction is intentionally not implemented or reviewer-verified in this
artifact snapshot. Use the verified reduced AE path instead:

  bash scripts/run_reduced_all.sh
USAGE
  exit 0
fi

cat >&2 <<'MESSAGE'
[full] Full path is not implemented or reviewer-verified in this artifact.
[full] This entry point intentionally exits non-zero to avoid placeholder success.
[full] Use the verified reduced AE path instead:
[full]   bash scripts/run_reduced_all.sh
MESSAGE
exit 2
