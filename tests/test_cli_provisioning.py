from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from live_action.cli import app


@dataclass(frozen=True)
class _Record:
    downloaded: bool


@dataclass(frozen=True)
class _Result:
    records: list[_Record]


def test_cli_provisioning_sync_reports_download_count(monkeypatch: pytest.MonkeyPatch) -> None:

    def _fake_sync(*, force: bool = False, **_: object) -> _Result:
        del force
        return _Result(records=[_Record(downloaded=True), _Record(downloaded=False)])

    monkeypatch.setattr(
        "live_action.cli.sync_huggingface_models",
        lambda config, force=False: _fake_sync(force=force),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["provisioning", "sync", "--force"])

    assert result.exit_code == 0
    assert "provisioning completed: total=2 downloaded=1" in result.stdout


def test_cli_profiles_sota_2026_writes_json(tmp_path: Path) -> None:
    runner = CliRunner()
    output_path = tmp_path / "sota.json"
    result = runner.invoke(app, ["profiles", "sota-2026", str(output_path)])

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["translation"]["execution_mode"] == "command"
    assert payload["upscale"]["execution_mode"] == "command"

