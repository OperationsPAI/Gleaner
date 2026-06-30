#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT}/dist"
BASE_NAME="gleaner-issta2026-ae"
BUILD_FULL="${GLEANER_BUILD_FULL_IMAGE:-1}"
BUILD_REDUCED="${GLEANER_BUILD_REDUCED_IMAGE:-1}"
INSTALL_TRACEPICKER_ENV="${GLEANER_FULL_INSTALL_TRACEPICKER_ENV:-1}"
GZIP_LEVEL="${GLEANER_DOCKER_GZIP_LEVEL:-6}"

if git -C "${ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_SHA="$(git -C "${ROOT}" rev-parse --short HEAD)"
  if git -C "${ROOT}" diff --quiet --ignore-submodules=dirty HEAD -- && [[ -z "$(git -C "${ROOT}" ls-files --others --exclude-standard)" ]]; then
    VERSION="${GIT_SHA}"
  else
    VERSION="worktree"
  fi
else
  VERSION="worktree"
fi

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing command: $1" >&2; exit 1; }
}
need docker
need tar
need gzip
need sha256sum

mkdir -p "${DIST_DIR}"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/gleaner-docker-context.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

make_context() {
  local flavor="$1"
  local ctx="${TMP_DIR}/${flavor}"
  mkdir -p "${ctx}"

  local excludes=(
    --exclude='./.git'
    --exclude='./.venv'
    --exclude='*/.venv'
    --exclude='*/__pycache__'
    --exclude='./.pytest_cache'
    --exclude='*/.pytest_cache'
    --exclude='./.ruff_cache'
    --exclude='*/.ruff_cache'
    --exclude='./.mypy_cache'
    --exclude='*/.mypy_cache'
    --exclude='*/.cache'
    --exclude='./dist'
    --exclude='./output'
    --exclude='./build'
    --exclude='./tmp'
    --exclude='./temp'
    --exclude='./paper'
    --exclude='./plots'
    --exclude='./third_party/TraStrainer/data'
    --exclude='./third_party/TraStrainer/data/**'
    --exclude='./third_party/TraStrainer/checkpoints'
    --exclude='./third_party/TraStrainer/checkpoints/**'
    --exclude='./.claude'
    --exclude='./data/rcabench-platform-v2'
    --exclude='./data/rcabench-platform-v2/data/*/sampled'
    --exclude='./data/rcabench-platform-v2/data/*/sampled/*'
  )
  if [[ "${flavor}" == "reduced" ]]; then
    excludes+=(
      --exclude='./data/rcabench-platform-v2/data/gleaner'
      --exclude='./data/rcabench-platform-v2/meta/gleaner'
    )
  fi
  tar -C "${ROOT}" "${excludes[@]}" -cf - . | tar -C "${ctx}" -xf -

  copy_dataset_dir() {
    local rel="$1"
    if [[ ! -e "${ROOT}/${rel}" ]]; then
      echo "ERROR: required dataset path missing: ${rel}" >&2
      exit 1
    fi
    mkdir -p "${ctx}/$(dirname "${rel}")"
    cp -aL "${ROOT}/${rel}" "${ctx}/${rel}"
    find "${ctx}/${rel}" -type d -name sampled -prune -exec rm -rf {} +
  }

  copy_dataset_dir "data/rcabench-platform-v2/meta/gleaner_lite"
  copy_dataset_dir "data/rcabench-platform-v2/data/gleaner_lite"
  copy_dataset_dir "data/rcabench-platform-v2/meta/tracepicker_lite"
  copy_dataset_dir "data/rcabench-platform-v2/data/tracepicker_lite"
  if [[ "${flavor}" == "full" ]]; then
    copy_dataset_dir "data/rcabench-platform-v2/meta/tracepicker"
    copy_dataset_dir "data/rcabench-platform-v2/data/tracepicker"
    copy_dataset_dir "data/rcabench-platform-v2/meta/gleaner"
    copy_dataset_dir "data/rcabench-platform-v2/data/gleaner"
  fi

  # The checked-out submodule path may be empty in this workspace. The Dockerfile
  # expects pyproject's editable source path to exist, so mirror the vendored copy.
  if [[ ! -f "${ctx}/platform/rcabench-platform/pyproject.toml" && -f "${ctx}/third_party/rcabench-platform/pyproject.toml" ]]; then
    rm -rf "${ctx}/platform/rcabench-platform"
    mkdir -p "${ctx}/platform"
    cp -a "${ctx}/third_party/rcabench-platform" "${ctx}/platform/rcabench-platform"
  fi

  echo "${ctx}"
}

build_and_save() {
  local flavor="$1"
  local target="$2"
  local ctx="$3"
  local image="${BASE_NAME}:${flavor}-${VERSION}"
  local out="${DIST_DIR}/${BASE_NAME}-${flavor}-${VERSION}.docker.tar.gz"

  echo "[docker-package] building ${image} from ${ctx} target=${target}"
  docker build \
    --target "${target}" \
    --build-arg "INSTALL_TRACEPICKER_ENV=${INSTALL_TRACEPICKER_ENV}" \
    -t "${image}" \
    "${ctx}"

  echo "[docker-package] saving ${image} -> ${out}"
  docker save "${image}" | gzip "-${GZIP_LEVEL}" > "${out}"
  sha256sum "${out}" > "${out}.sha256"
  echo "[docker-package] wrote ${out}"
  cat "${out}.sha256"
}

if [[ "${BUILD_REDUCED}" == "1" ]]; then
  reduced_ctx="$(make_context reduced)"
  build_and_save reduced reduced "${reduced_ctx}"
else
  echo "[docker-package] skipping reduced image because GLEANER_BUILD_REDUCED_IMAGE=${BUILD_REDUCED}"
fi

if [[ "${BUILD_FULL}" == "1" ]]; then
  full_ctx="$(make_context full)"
  build_and_save full full "${full_ctx}"
else
  echo "[docker-package] skipping full image because GLEANER_BUILD_FULL_IMAGE=${BUILD_FULL}"
fi
