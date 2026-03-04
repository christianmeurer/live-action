from __future__ import annotations

from dataclasses import dataclass

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

