FROM python:3.13-slim

ENV UV_SYSTEM_PYTHON=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /artifact

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.8.13

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY main.py ./main.py
COPY scripts ./scripts
COPY configs ./configs
COPY artifact_expected ./artifact_expected
COPY data/artifact ./data/artifact
COPY output/rcabench-platform-v2/sampler_reports/gleaner ./output/rcabench-platform-v2/sampler_reports/gleaner
COPY docs ./docs
COPY ARTIFACT_README.md REQUIREMENTS.md STATUS.md ./
COPY third_party ./third_party

RUN uv sync --locked

CMD ["bash"]
