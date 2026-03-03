from __future__ import annotations

import shutil
from pathlib import Path

from live_action.config import AppConfig


def run_startup_checks(config: AppConfig) -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("ffmpeg/ffprobe are required in PATH")

    for path in (config.paths.artifacts_dir, config.paths.outputs_dir, config.paths.temp_dir):
        path.mkdir(parents=True, exist_ok=True)
        _check_writable(path)


def _check_writable(path: Path) -> None:
    probe = path / ".write-check"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink(missing_ok=True)

