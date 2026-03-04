#!/usr/bin/env bash

set -euo pipefail

REPO_URL=""
REPO_DIR="/opt/live-action"
HOST="0.0.0.0"
PORT="8000"
BOOTSTRAP_ONLY="false"

usage() {
  cat <<'EOF'
Usage: start_live_action_vm.sh --repo-url <url> [options]

Options:
  --repo-url <url>         Git repository URL (required)
  --repo-dir <path>        Target directory (default: /opt/live-action)
  --host <host>            Uvicorn bind host (default: 0.0.0.0)
  --port <port>            Uvicorn bind port (default: 8000)
  --bootstrap-only         Install/sync and exit without launching API
  --help                   Show this help

Environment variables (optional):
  LIVE_ACTION_API_KEY
  LIVE_ACTION_PROVISIONING__AUTO_SYNC_ON_STARTUP
  LIVE_ACTION_PROVISIONING__HUGGINGFACE__ENABLED
  LIVE_ACTION_PROVISIONING__HUGGINGFACE__TOKEN
  LIVE_ACTION_PROVISIONING__HUGGINGFACE__CACHE_DIR
  LIVE_ACTION_PROVISIONING__HUGGINGFACE__LOCAL_DIR
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-url)
      REPO_URL="${2:-}"
      shift 2
      ;;
    --repo-dir)
      REPO_DIR="${2:-}"
      shift 2
      ;;
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --port)
      PORT="${2:-}"
      shift 2
      ;;
    --bootstrap-only)
      BOOTSTRAP_ONLY="true"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$REPO_URL" ]]; then
  echo "--repo-url is required" >&2
  usage
  exit 2
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo is required on Ubuntu VM" >&2
  exit 1
fi

echo "[1/6] Installing OS prerequisites"
sudo apt update
sudo apt install -y git ffmpeg python3.11 python3.11-venv curl

if ! command -v uv >/dev/null 2>&1; then
  echo "[2/6] Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "[3/6] Cloning/updating repository"
if [[ ! -d "$REPO_DIR/.git" ]]; then
  sudo mkdir -p "$(dirname "$REPO_DIR")"
  sudo chown -R "$USER":"$USER" "$(dirname "$REPO_DIR")"
  git clone "$REPO_URL" "$REPO_DIR"
else
  git -C "$REPO_DIR" pull --ff-only
fi

cd "$REPO_DIR"

echo "[4/6] Syncing dependencies"
uv sync --extra dev

echo "[5/6] Running tests"
uv run pytest -q

echo "[6/6] Generating SOTA profile"
mkdir -p ./config
uv run live-action profiles sota-2026 ./config/sota-2026.json

if [[ "$BOOTSTRAP_ONLY" == "true" ]]; then
  echo "Bootstrap-only mode complete"
  exit 0
fi

echo "Starting API on ${HOST}:${PORT}"
exec uv run uvicorn live_action.server.main:app --host "$HOST" --port "$PORT"

