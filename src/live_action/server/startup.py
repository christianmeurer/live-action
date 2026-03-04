from __future__ import annotations

import shutil
from pathlib import Path

from live_action.config import AppConfig
from live_action.provisioning.huggingface import sync_huggingface_models


def run_startup_checks(config: AppConfig) -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("ffmpeg/ffprobe are required in PATH")

    for path in (config.paths.artifacts_dir, config.paths.outputs_dir, config.paths.temp_dir):
        path.mkdir(parents=True, exist_ok=True)
        _check_writable(path)


def run_startup_provisioning(config: AppConfig) -> int:
    if config.provisioning.auto_sync_on_startup:
        result = sync_huggingface_models(config)
        return sum(1 for record in result.records if record.downloaded)
    return 0


def _check_writable(path: Path) -> None:
    probe = path / ".write-check"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink(missing_ok=True)

