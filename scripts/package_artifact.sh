#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT}/dist"
PACKAGE_BASENAME="gleaner-issta2026-ae"

if git -C "${ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_SHA="$(git -C "${ROOT}" rev-parse --short HEAD)"
  if git -C "${ROOT}" diff --quiet --ignore-submodules=dirty HEAD -- && \
     [[ -z "$(git -C "${ROOT}" ls-files --others --exclude-standard)" ]]; then
    VERSION="${GIT_SHA}"
  else
    VERSION="worktree"
  fi
else
  VERSION="worktree"
fi

ARCHIVE_NAME="${PACKAGE_BASENAME}-${VERSION}.tar.gz"
ARCHIVE_PATH="${DIST_DIR}/${ARCHIVE_NAME}"
SHA_PATH="${ARCHIVE_PATH}.sha256"

REQUIRED_PATHS=(
  "ARTIFACT_README.md"
  "REQUIREMENTS.md"
  "STATUS.md"
  "README.md"
  "LICENSE"
  "Dockerfile"
  "pyproject.toml"
  "uv.lock"
  "src"
  "scripts"
  "configs"
  "docs"
  "artifact_expected/reduced"
  "data/artifact/reduced/MANIFEST.json"
  "data/artifact/reduced/SHA256SUMS"
  "data/artifact/reduced/rq1/gleaner_source.aggregated_perf.parquet"
  "data/artifact/reduced/rq1/gleaner_source.detailed_perf.parquet"
)

THIRD_PARTY_DIRS=(
  "third_party/Nezha"
  "third_party/ShapleyIQ"
  "third_party/TracePicker"
  "third_party/TraStrainer"
)

copy_path() {
  local rel="$1"
  local src="${ROOT}/${rel}"
  local dst="${STAGE}/${rel}"
  mkdir -p "$(dirname "${dst}")"
  if [[ -d "${src}" ]]; then
    mkdir -p "${dst}"
    tar -C "${src}" \
      --exclude='.git' \
      --exclude='.git/*' \
      --exclude='.venv' \
      --exclude='.venv/*' \
      --exclude='__pycache__' \
      --exclude='__pycache__/*' \
      --exclude='.pytest_cache' \
      --exclude='.pytest_cache/*' \
      --exclude='.ruff_cache' \
      --exclude='.ruff_cache/*' \
      --exclude='.mypy_cache' \
      --exclude='.mypy_cache/*' \
      --exclude='.cache' \
      --exclude='.cache/*' \
      --exclude='*.pyc' \
      --exclude='*.pyo' \
      --exclude='*.tmp' \
      --exclude='*.temp' \
      -cf - . | tar -C "${dst}" -xf -
  else
    cp -p "${src}" "${dst}"
  fi
}

printf 'Repository status before packaging:\n'
git -C "${ROOT}" status --short || true
if ! git -C "${ROOT}" diff --quiet --; then
  printf 'WARNING: unstaged changes are present; packaging current worktree contents.\n' >&2
fi
if [[ -n "$(git -C "${ROOT}" ls-files --others --exclude-standard)" ]]; then
  printf 'WARNING: untracked files are present; only explicit artifact paths are packaged.\n' >&2
fi

for rel in "${REQUIRED_PATHS[@]}"; do
  if [[ ! -e "${ROOT}/${rel}" ]]; then
    printf 'ERROR: required path is missing: %s\n' "${rel}" >&2
    exit 1
  fi
done

for rel in "${THIRD_PARTY_DIRS[@]}"; do
  if [[ ! -d "${ROOT}/${rel}" ]]; then
    printf 'ERROR: required third-party directory is missing: %s\n' "${rel}" >&2
    exit 1
  fi
  if ! find "${ROOT}/${rel}" -mindepth 1 ! -name '.git' -print -quit | grep -q .; then
    printf 'ERROR: required third-party directory is empty: %s\n' "${rel}" >&2
    exit 1
  fi
done

if ! command -v sha256sum >/dev/null 2>&1; then
  printf 'ERROR: sha256sum is required to generate checksums.\n' >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  printf 'ERROR: python3 is required to generate the internal archive manifest.\n' >&2
  exit 1
fi

mkdir -p "${DIST_DIR}"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/gleaner-ae-package.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT
STAGE="${TMP_DIR}/${PACKAGE_BASENAME}"
mkdir -p "${STAGE}"

TOP_LEVEL_FILES=(
  "ARTIFACT_README.md"
  "REQUIREMENTS.md"
  "STATUS.md"
  "README.md"
  "LICENSE"
  "CITATION.cff"
  "Dockerfile"
  "pyproject.toml"
  "uv.lock"
  ".gitattributes"
  ".gitmodules"
  "main.py"
)
TOP_LEVEL_DIRS=("src" "scripts" "configs" "docs")

for rel in "${TOP_LEVEL_FILES[@]}"; do
  [[ -e "${ROOT}/${rel}" ]] && copy_path "${rel}"
done
for rel in "${TOP_LEVEL_DIRS[@]}"; do
  copy_path "${rel}"
done

copy_path "artifact_expected/reduced"
copy_path "data/artifact/reduced"
for rel in "${THIRD_PARTY_DIRS[@]}"; do
  copy_path "${rel}"
done

# Defense in depth: remove VCS metadata/caches and local generated output from staging.
find "${STAGE}" \( \
  -name '.git' -o \
  -name '.venv' -o \
  -name '__pycache__' -o \
  -name '.pytest_cache' -o \
  -name '.ruff_cache' -o \
  -name '.mypy_cache' -o \
  -name '.cache' \
\) -prune -exec rm -rf {} +
rm -rf "${STAGE}/output/artifact" "${STAGE}/dist" "${STAGE}/build" "${STAGE}/tmp" "${STAGE}/temp"

MANIFEST="${STAGE}/ARCHIVE_MANIFEST.tsv"
python3 - "${STAGE}" "${MANIFEST}" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

stage = Path(sys.argv[1])
manifest = Path(sys.argv[2])
rows = []
for path in sorted(p for p in stage.rglob('*') if p.is_file()):
    if path == manifest:
        continue
    rel = path.relative_to(stage).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows.append((rel, path.stat().st_size, digest))
with manifest.open('w', encoding='utf-8', newline='\n') as fh:
    fh.write('path\tbytes\tsha256\n')
    for rel, size, digest in rows:
        fh.write(f'{rel}\t{size}\t{digest}\n')
PY

rm -f "${ARCHIVE_PATH}" "${SHA_PATH}"
mapfile -t TAR_ROOTS < <(cd "${STAGE}" && find . -mindepth 1 -maxdepth 1 -printf '%P\n' | LC_ALL=C sort)
tar -C "${STAGE}" -czf "${ARCHIVE_PATH}" "${TAR_ROOTS[@]}"
(cd "${DIST_DIR}" && sha256sum "${ARCHIVE_NAME}" > "$(basename "${SHA_PATH}")")

TAR_LIST_TEXT="$(tar -tzf "${ARCHIVE_PATH}")"
require_in_archive() {
  local rel="$1"
  if ! grep -Fxq -- "${rel}" <<<"${TAR_LIST_TEXT}"; then
    printf 'ERROR: archive is missing required path: %s\n' "${rel}" >&2
    exit 1
  fi
}
require_absent_regex() {
  local pattern="$1"
  local label="$2"
  if grep -Eq -- "${pattern}" <<<"${TAR_LIST_TEXT}"; then
    printf 'ERROR: archive contains excluded path: %s\n' "${label}" >&2
    exit 1
  fi
}

require_in_archive "ARTIFACT_README.md"
require_in_archive "ARCHIVE_MANIFEST.tsv"
require_in_archive "third_party/Nezha/"
require_in_archive "data/artifact/reduced/MANIFEST.json"
require_in_archive "data/artifact/reduced/rq1/gleaner_source.aggregated_perf.parquet"
require_in_archive "data/artifact/reduced/rq1/gleaner_source.detailed_perf.parquet"
require_absent_regex '(^|/)\.git(/|$)' '.git/'
require_absent_regex '(^|/)\.venv(/|$)' '.venv/'
require_absent_regex '^dist(/|$)' 'dist/'
require_absent_regex '^output/artifact(/|$)' 'output/artifact/'
require_absent_regex '(^|/)__pycache__(/|$)' '__pycache__/'

printf 'Created archive: %s\n' "${ARCHIVE_PATH}"
printf 'Created checksum: %s\n' "${SHA_PATH}"
printf 'Archive sha256: '
cut -d' ' -f1 "${SHA_PATH}"
printf 'Archive size bytes: '
stat -c '%s' "${ARCHIVE_PATH}"
