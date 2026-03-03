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

## CLI usage

Show commands:

```bash
uv run live-action --help
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

## Docker

Build and run:

```bash
docker compose up --build
```

Health check endpoint:

```bash
GET /health
```

