from __future__ import annotations

from pathlib import Path

import pytest

from live_action.config import AppConfig, AppPaths
from live_action.server.startup import run_startup_checks


def test_startup_checks_validate_writable_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _: "ok")
    config = AppConfig(
        paths=AppPaths(
            artifacts_dir=tmp_path / "artifacts",
            outputs_dir=tmp_path / "outputs",
            temp_dir=tmp_path / "tmp",
        )
    )
    run_startup_checks(config)


def test_startup_checks_require_ffmpeg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _: None)
    config = AppConfig(
        paths=AppPaths(
            artifacts_dir=tmp_path / "artifacts",
            outputs_dir=tmp_path / "outputs",
            temp_dir=tmp_path / "tmp",
        )
    )
    with pytest.raises(RuntimeError):
        run_startup_checks(config)

