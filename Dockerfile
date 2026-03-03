FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip curl git ffmpeg ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash appuser
USER appuser
WORKDIR /workspace

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/appuser/.local/bin:${PATH}"

COPY --chown=appuser:appuser pyproject.toml README.md ./
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser scripts ./scripts

RUN uv sync

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uv", "run", "uvicorn", "live_action.server.main:app", "--host", "0.0.0.0", "--port", "8000"]

