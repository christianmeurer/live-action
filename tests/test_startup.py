from __future__ import annotations

from pathlib import Path

import pytest

from live_action.config import AppConfig, AppPaths, HuggingFaceSettings, ProvisioningSettings
from live_action.server.startup import run_startup_checks, run_startup_provisioning


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


def test_run_startup_provisioning_syncs_when_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[bool] = []

    class _Record:
        def __init__(self, downloaded: bool) -> None:
            self.downloaded = downloaded

    class _Result:
        def __init__(self) -> None:
            self.records = [_Record(downloaded=True), _Record(downloaded=False)]

    def _fake_sync(_: AppConfig) -> _Result:
        calls.append(True)
        return _Result()

    monkeypatch.setattr("live_action.server.startup.sync_huggingface_models", _fake_sync)
    config = AppConfig(
        paths=AppPaths(
            artifacts_dir=tmp_path / "artifacts",
            outputs_dir=tmp_path / "outputs",
            temp_dir=tmp_path / "tmp",
        ),
        provisioning=ProvisioningSettings(
            auto_sync_on_startup=True,
            huggingface=HuggingFaceSettings(enabled=True),
        ),
    )

    assert run_startup_provisioning(config) == 1
    assert calls == [True]


def test_run_startup_provisioning_skips_when_disabled(tmp_path: Path) -> None:
    config = AppConfig(
        paths=AppPaths(
            artifacts_dir=tmp_path / "artifacts",
            outputs_dir=tmp_path / "outputs",
            temp_dir=tmp_path / "tmp",
        ),
        provisioning=ProvisioningSettings(auto_sync_on_startup=False),
    )
    assert run_startup_provisioning(config) == 0

