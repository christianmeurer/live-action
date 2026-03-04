from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from live_action.config import AppConfig, AppPaths
from live_action.server.orchestrator import Orchestrator


def test_end_to_end_orchestrator_smoke(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("live_action.server.orchestrator.inspect_video", lambda _: {"format": {"duration": "3.0"}})
    monkeypatch.setattr("live_action.server.orchestrator.extract_audio_wav", lambda *_: None)
    monkeypatch.setattr(
        "live_action.server.orchestrator.extract_subclip",
        lambda _src, out, **_: out.write_bytes(b"chunk"),
    )
    monkeypatch.setattr(
        "live_action.server.orchestrator.concat_videos",
        lambda _inputs, out: out.write_bytes(b"stitched"),
    )
    monkeypatch.setattr(
        "live_action.server.orchestrator.remux_audio",
        lambda video, _audio, out: out.write_bytes(video.read_bytes()),
    )

    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")

    orchestrator = Orchestrator(
        AppConfig(
            paths=AppPaths(
                artifacts_dir=tmp_path / "artifacts",
                outputs_dir=tmp_path / "outputs",
                temp_dir=tmp_path / "tmp",
            )
        )
    )

    run = orchestrator.create_run(
        input_path=str(source),
        config_payload={
            "translation": {"execution_mode": "dry-run"},
            "upscale": {"execution_mode": "dry-run", "enabled": True},
            "evaluation": {"enabled": False},
        },
        request_id="smoke-001",
    )

    asyncio.run(orchestrator.process_run(run.run_id))
    loaded = orchestrator.get_run(run.run_id)

    assert loaded is not None
    assert loaded.status == "succeeded"
    assert loaded.final_output_path is not None
    assert Path(loaded.final_output_path).exists()
    assert all(chunk.status == "succeeded" for chunk in loaded.chunks)

