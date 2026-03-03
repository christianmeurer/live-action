# live-action

Milestone 1 scaffold for an automated animation-to-live-action pipeline.

This milestone includes:

- Project-local Roo configuration (`.roomodes`, `.roo/*`, `.clinerules*`)
- Python 3.11 + `uv` project skeleton
- FFmpeg preprocessing CLI (metadata, fps normalization, scaling, audio extraction)
- FastAPI server scaffold with a single-worker async queue
- Docker baseline for CUDA-oriented future expansion

## Quickstart (local)

1. Install Python 3.11 and `uv`.
2. Sync environment:

```bash
uv sync
```

3. Show CLI help:

```bash
uv run live-action --help
```

4. Inspect video metadata:

```bash
uv run live-action preprocess inspect --input ./input/sample.mp4 --output-json ./artifacts/sample.meta.json
```

5. Run API server:

```bash
uv run uvicorn live_action.server.main:app --host 0.0.0.0 --port 8000
```

## Milestone 1 scope

No model inference is included yet.

The scaffold is designed for deterministic preprocessing and safe single-job orchestration before adding model stages.

