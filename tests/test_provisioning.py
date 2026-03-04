from __future__ import annotations

from pathlib import Path

import pytest

from live_action.config import AppConfig, HuggingFaceSettings, ProvisioningSettings
from live_action.pipeline.config import PipelineRunConfig
from live_action.provisioning import huggingface as hf_module


def test_app_config_reads_nested_huggingface_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LIVE_ACTION_PROVISIONING__HUGGINGFACE__ENABLED", "true")
    monkeypatch.setenv("LIVE_ACTION_PROVISIONING__HUGGINGFACE__TOKEN", "hf_test_token")
    monkeypatch.setenv("LIVE_ACTION_PROVISIONING__HUGGINGFACE__CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("LIVE_ACTION_PROVISIONING__HUGGINGFACE__LOCAL_DIR", str(tmp_path / "models"))
    cfg = AppConfig()

    assert cfg.provisioning.huggingface.enabled is True
    assert cfg.provisioning.huggingface.token == "hf_test_token"
    assert cfg.provisioning.huggingface.cache_dir == tmp_path / "cache"
    assert cfg.provisioning.huggingface.local_dir == tmp_path / "models"


def test_sync_huggingface_models_returns_empty_when_disabled(tmp_path: Path) -> None:
    cfg = AppConfig(
        provisioning=ProvisioningSettings(
            auto_sync_on_startup=False,
            huggingface=HuggingFaceSettings(
                enabled=False,
                cache_dir=tmp_path / "cache",
                local_dir=tmp_path / "models",
            ),
        )
    )
    result = hf_module.sync_huggingface_models(cfg)
    assert result.records == []


def test_sync_huggingface_models_downloads_required_models(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[str, str, str]] = []

    def _fake_snapshot_download(
        *,
        repo_id: str,
        revision: str,
        local_dir: Path,
        cache_dir: Path,
        token: str | None,
        local_dir_use_symlinks: bool,
    ) -> str:
        del cache_dir, token, local_dir_use_symlinks
        local_dir.mkdir(parents=True, exist_ok=True)
        calls.append((repo_id, revision, str(local_dir)))
        return str(local_dir)

    monkeypatch.setattr(hf_module, "snapshot_download", _fake_snapshot_download)

    cfg = AppConfig(
        provisioning=ProvisioningSettings(
            auto_sync_on_startup=False,
            huggingface=HuggingFaceSettings(
                enabled=True,
                cache_dir=tmp_path / "cache",
                local_dir=tmp_path / "models",
                skip_if_present=False,
            ),
        )
    )

    result = hf_module.sync_huggingface_models(cfg)
    assert len(result.records) == 3
    assert len(calls) == 3
    assert all(record.downloaded for record in result.records)


def test_sync_huggingface_models_skips_existing_when_configured(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []

    def _fake_snapshot_download(
        *,
        repo_id: str,
        revision: str,
        local_dir: Path,
        cache_dir: Path,
        token: str | None,
        local_dir_use_symlinks: bool,
    ) -> str:
        del revision, cache_dir, token, local_dir_use_symlinks
        calls.append(repo_id)
        local_dir.mkdir(parents=True, exist_ok=True)
        return str(local_dir)

    monkeypatch.setattr(hf_module, "snapshot_download", _fake_snapshot_download)

    cfg = AppConfig(
        provisioning=ProvisioningSettings(
            auto_sync_on_startup=False,
            huggingface=HuggingFaceSettings(
                enabled=True,
                cache_dir=tmp_path / "cache",
                local_dir=tmp_path / "models",
                skip_if_present=True,
            ),
        )
    )
    run_cfg = PipelineRunConfig.model_validate(
        {
            "translation": {
                "fallback_provider": None,
            },
            "upscale": {"enabled": False},
        }
    )

    existing = cfg.provisioning.huggingface.local_dir / "translation" / "Wan-AI--Wan2.1-I2V-14B-720P"
    existing.mkdir(parents=True, exist_ok=True)

    result = hf_module.sync_huggingface_models(cfg, run_cfg)
    assert len(result.records) == 1
    assert result.records[0].downloaded is False
    assert calls == []

