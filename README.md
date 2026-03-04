# live-action

Production-oriented automated animation-to-live-action pipeline service.

## Capabilities

- Deterministic preprocess utilities (inspect/normalize/audio extraction)
- Chunked run orchestration with overlap-aware planning
- Translation and upscale provider abstraction with:
  - `dry-run` execution mode (safe defaults)
  - `command` execution mode (external inference adapters)
- Evaluation + requeue policy with deterministic fallback backend
- Single-worker queue semantics and API run visibility
- Dockerized service deployment baseline (CUDA image)

## Local setup

1. Install Python 3.11 and `uv`
2. Install dependencies

```bash
uv sync
```

3. Run tests

```bash
pytest -q
```

4. Start API

```bash
uv run uvicorn live_action.server.main:app --host 0.0.0.0 --port 8000
```

## Environment variables

- `LIVE_ACTION_API_KEY`: optional API key for protected endpoints.
- `LIVE_ACTION_PROVISIONING__AUTO_SYNC_ON_STARTUP`: when `true`, startup performs model sync.
- `LIVE_ACTION_PROVISIONING__HUGGINGFACE__ENABLED`: enables Hugging Face provisioning.
- `LIVE_ACTION_PROVISIONING__HUGGINGFACE__TOKEN`: Hugging Face token for private/gated models.
- `LIVE_ACTION_PROVISIONING__HUGGINGFACE__CACHE_DIR`: snapshot cache directory.
- `LIVE_ACTION_PROVISIONING__HUGGINGFACE__LOCAL_DIR`: local model materialization directory.

## CLI usage

Show commands:

```bash
uv run live-action --help
```

Provisioning sync:

```bash
uv run live-action provisioning sync --force
```

Preprocess inspect:

```bash
uv run live-action preprocess inspect --input ./input/sample.mp4 --output-json ./artifacts/sample.meta.json
```

Single orchestrated run:

```bash
uv run live-action run single --input ./input/sample.mp4
```

Single run with custom config:

```bash
uv run live-action run single --input ./input/sample.mp4 --config-json ./config/run.json
```

## API quickstart

Create job:

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -d "{\"request_id\":\"demo-001\",\"input_path\":\"./input/sample.mp4\",\"config\":{}}"
```

Check job:

```bash
curl http://127.0.0.1:8000/jobs/<job_id>
```

Check run:

```bash
curl http://127.0.0.1:8000/runs/<run_id>
```

## Command execution mode (production adapter contract)

To wire real model backends without modifying service internals, use `command` mode in runtime config.

Example (`run.json`):

```json
{
  "translation": {
    "execution_mode": "command",
    "command_template": [
      "python",
      "./adapters/translate.py",
      "--input",
      "{input}",
      "--output",
      "{output}",
      "--seed",
      "{seed}",
      "--denoise",
      "{denoise}",
      "--guidance",
      "{guidance}",
      "--provider",
      "{provider}"
    ]
  },
  "upscale": {
    "enabled": true,
    "execution_mode": "command",
    "command_template": [
      "python",
      "./adapters/upscale.py",
      "--input",
      "{input}",
      "--output",
      "{output}",
      "--height",
      "{target_height}",
      "--model",
      "{model}"
    ]
  },
  "evaluation": {
    "backend": "clip",
    "structural_similarity_threshold": 0.9
  }
}
```

## Turnkey local execution mode

Default runtime execution mode is `local` for both translation and upscale. This mode uses built-in FFmpeg-based local adapters in [`translate_video_local()`](src/live_action/adapters/local_video.py:13) and [`upscale_video_local()`](src/live_action/adapters/local_video.py:58), so the service runs end-to-end without external command templates.

Use this with:

```json
{
  "translation": {
    "execution_mode": "local"
  },
  "upscale": {
    "enabled": true,
    "execution_mode": "local",
    "target_height": 1080
  }
}
```

## Docker

Build and run:

```bash
docker compose up --build
```

Health check endpoint:

```bash
GET /health
```

