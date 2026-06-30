# syntax=docker/dockerfile:1
FROM python:3.13-slim AS common
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/

ENV UV_SYSTEM_PYTHON=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /artifact


COPY pyproject.toml uv.lock README.md LICENSE CITATION.cff ./
COPY src ./src
COPY main.py ./main.py
COPY scripts ./scripts
COPY configs ./configs
COPY artifact_expected ./artifact_expected
COPY docs ./docs
COPY REQUIREMENTS.md STATUS.md ./
COPY data/rcabench_dataset ./data/rcabench_dataset
COPY data/tracepicker ./data/tracepicker
COPY third_party ./third_party
COPY platform ./platform


FROM common AS deps
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --all-packages --no-dev \
    && rm -rf /tmp/*
ENV UV_NO_DEV=1


FROM deps AS reduced_inputs
COPY data/rcabench-platform-v2/meta/gleaner_lite ./data/rcabench-platform-v2/meta/gleaner_lite
COPY data/rcabench-platform-v2/data/gleaner_lite ./data/rcabench-platform-v2/data/gleaner_lite
COPY data/rcabench-platform-v2/meta/tracepicker_lite ./data/rcabench-platform-v2/meta/tracepicker_lite
COPY data/rcabench-platform-v2/data/tracepicker_lite ./data/rcabench-platform-v2/data/tracepicker_lite


FROM reduced_inputs AS reduced
LABEL org.opencontainers.image.title="Gleaner ISSTA 2026 AE reduced artifact"
LABEL org.opencontainers.image.description="Reduced <=1 day live-input artifact image with gleaner_lite and TracePicker reduced datasets"
CMD ["bash"]

FROM reduced_inputs AS full
ARG INSTALL_TRACEPICKER_ENV=1
RUN --mount=type=cache,target=/root/.cache/uv \
    GLEANER_SETUP_TRASTRAINER_ENV=1 bash scripts/full/setup_baseline_envs.sh \
    && rm -rf /tmp/* \
    && if [ "${INSTALL_TRACEPICKER_ENV}" = "1" ]; then \
      GLEANER_SETUP_TRACEPICKER_ENV=1 bash scripts/full/setup_baseline_envs.sh; \
    else \
      echo "[docker:full] TracePicker isolated Python 3.12 env skipped by build arg INSTALL_TRACEPICKER_ENV=0."; \
    fi \
    && rm -rf /tmp/*
COPY data/rcabench-platform-v2/meta/tracepicker ./data/rcabench-platform-v2/meta/tracepicker
COPY data/rcabench-platform-v2/data/tracepicker ./data/rcabench-platform-v2/data/tracepicker
COPY data/rcabench-platform-v2/meta/gleaner ./data/rcabench-platform-v2/meta/gleaner
COPY data/rcabench-platform-v2/data/gleaner ./data/rcabench-platform-v2/data/gleaner
LABEL org.opencontainers.image.title="Gleaner ISSTA 2026 AE full artifact"
LABEL org.opencontainers.image.description="Long-running full-scope artifact image with complete Gleaner Dataset A and full-path scripts"
CMD ["bash"]
