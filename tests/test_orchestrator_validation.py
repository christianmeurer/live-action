from __future__ import annotations

from pathlib import Path

import pytest

from live_action.config import AppConfig, AppPaths
from live_action.server.orchestrator import Orchestrator


def test_create_run_rejects_non_positive_duration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("live_action.server.orchestrator.inspect_video", lambda _: {"format": {"duration": "0"}})

    source = tmp_path / "source.mp4"
    source.write_bytes(b"data")

    orchestrator = Orchestrator(
        AppConfig(
            paths=AppPaths(
                artifacts_dir=tmp_path / "artifacts",
                outputs_dir=tmp_path / "outputs",
                temp_dir=tmp_path / "tmp",
            )
        )
    )

    with pytest.raises(ValueError):
        orchestrator.create_run(input_path=str(source), config_payload={})

