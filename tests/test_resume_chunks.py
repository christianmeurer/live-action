from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from live_action.config import AppConfig, AppPaths
from live_action.server.orchestrator import ChunkRunRecord, Orchestrator


def test_process_run_skips_completed_chunks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("live_action.server.orchestrator.inspect_video", lambda _: {"format": {"duration": "6.0"}})
    monkeypatch.setattr("live_action.server.orchestrator.extract_audio_wav", lambda *_: None)
    monkeypatch.setattr("live_action.server.orchestrator.extract_subclip", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("live_action.server.orchestrator.concat_videos", lambda _inputs, out: out.write_bytes(b"ok"))
    monkeypatch.setattr(
        "live_action.server.orchestrator.remux_audio",
        lambda video, _audio, out: out.write_bytes(video.read_bytes()),
    )

    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    upscaled_existing = tmp_path / "artifacts" / "runs" / "r" / "chunk-0000.upscaled.mp4"
    upscaled_existing.parent.mkdir(parents=True, exist_ok=True)
    upscaled_existing.write_bytes(b"done")

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
            "chunking": {"chunk_seconds": 3.0, "overlap_ratio": 0.0},
            "translation": {"execution_mode": "dry-run"},
            "upscale": {"execution_mode": "dry-run", "enabled": True},
            "evaluation": {"enabled": False},
        },
        request_id="resume-001",
    )

    first_chunk = run.chunks[0]
    first_chunk.status = "succeeded"
    first_chunk.upscaled_path = str(upscaled_existing)

    calls: list[int] = []

    async def _fake_process_chunk(_run: object, chunk: ChunkRunRecord, _cfg: object) -> None:
        calls.append(chunk.chunk_index)
        chunk.status = "succeeded"
        path = tmp_path / "artifacts" / "runs" / run.run_id / f"chunk-{chunk.chunk_index:04d}.upscaled.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"new")
        chunk.upscaled_path = str(path)

    monkeypatch.setattr(orchestrator, "_process_chunk", _fake_process_chunk)

    asyncio.run(orchestrator.process_run(run.run_id))

    assert 0 not in calls
    assert len(calls) >= 1

