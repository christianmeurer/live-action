from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from live_action.config import AppConfig
from live_action.eval.metrics import compute_structural_similarity
from live_action.eval.requeue import decide_requeue
from live_action.pipeline.chunking import build_chunk_plan
from live_action.pipeline.config import PipelineRunConfig
from live_action.pipeline.translator import TranslationService
from live_action.pipeline.upscale import UpscaleService
from live_action.preprocess.ffmpeg import (
    concat_videos,
    extract_audio_wav,
    extract_subclip,
    inspect_video,
    remux_audio,
)
from live_action.runtime.gpu import GpuRuntime


@dataclass
class ChunkRunRecord:
    chunk_index: int
    start_seconds: float
    end_seconds: float
    attempt: int = 0
    status: str = "queued"
    score: float | None = None
    provider: str | None = None
    translated_path: str | None = None
    upscaled_path: str | None = None
    error: str | None = None


@dataclass
class PipelineRunRecord:
    run_id: str
    request_id: str | None
    input_path: str
    created_at: str
    updated_at: str
    status: str
    config: dict[str, object]
    final_output_path: str | None = None
    chunks: list[ChunkRunRecord] = field(default_factory=list)


class Orchestrator:
    def __init__(self, app_config: AppConfig) -> None:
        self._app_config = app_config
        self._runs: dict[str, PipelineRunRecord] = {}
        self._request_to_run: dict[str, str] = {}
        self._translator = TranslationService()
        self._upscaler = UpscaleService()
        self._gpu_runtime = GpuRuntime()

    def create_run(
        self,
        *,
        input_path: str,
        config_payload: dict[str, object],
        request_id: str | None = None,
    ) -> PipelineRunRecord:
        if request_id is not None and request_id in self._request_to_run:
            run_id = self._request_to_run[request_id]
            return self._runs[run_id]

        run_config = PipelineRunConfig.model_validate(config_payload)
        now = datetime.now(tz=UTC).isoformat()
        run_id = str(uuid4())

        metadata = inspect_video(Path(input_path))
        duration = float(metadata.get("format", {}).get("duration", 0.0))
        chunks = build_chunk_plan(
            total_seconds=duration,
            chunk_seconds=run_config.chunking.chunk_seconds,
            overlap_ratio=run_config.chunking.overlap_ratio,
        )
        chunk_records = [
            ChunkRunRecord(
                chunk_index=chunk.index,
                start_seconds=chunk.start_seconds,
                end_seconds=chunk.end_seconds,
            )
            for chunk in chunks
        ]
        run = PipelineRunRecord(
            run_id=run_id,
            request_id=request_id,
            input_path=input_path,
            created_at=now,
            updated_at=now,
            status="queued",
            config=run_config.model_dump(mode="json"),
            chunks=chunk_records,
        )
        self._runs[run_id] = run
        if request_id is not None:
            self._request_to_run[request_id] = run_id
        self._write_run_report(run)
        return run

    def get_run(self, run_id: str) -> PipelineRunRecord | None:
        return self._runs.get(run_id)

    def list_runs(self) -> list[PipelineRunRecord]:
        return list(self._runs.values())

    def get_run_by_request_id(self, request_id: str) -> PipelineRunRecord | None:
        run_id = self._request_to_run.get(request_id)
        if run_id is None:
            return None
        return self._runs.get(run_id)

    async def process_run(self, run_id: str) -> None:
        run = self._runs[run_id]
        if run.status in {"running", "succeeded"}:
            return
        run.status = "running"
        run.updated_at = datetime.now(tz=UTC).isoformat()
        run_config = PipelineRunConfig.model_validate(run.config)
        run_dir = self._app_config.paths.artifacts_dir / "runs" / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        source_path = Path(run.input_path)
        audio_path = run_dir / "source.audio.wav"
        try:
            extract_audio_wav(source_path, audio_path)
        except Exception:
            audio_path = Path()

        for chunk in run.chunks:
            await self._process_chunk(run, chunk, run_config)

        if any(chunk.status != "succeeded" for chunk in run.chunks):
            run.status = "failed"
        else:
            output_chunks = [
                Path(chunk.upscaled_path)
                for chunk in run.chunks
                if chunk.upscaled_path is not None and Path(chunk.upscaled_path).exists()
            ]
            if output_chunks:
                stitched_path = run_dir / "stitched.video.mp4"
                concat_videos(output_chunks, stitched_path)
                if audio_path.exists():
                    final_path = self._app_config.paths.outputs_dir / f"{run.run_id}.mp4"
                    remux_audio(stitched_path, audio_path, final_path)
                else:
                    final_path = self._app_config.paths.outputs_dir / f"{run.run_id}.mp4"
                    final_path.parent.mkdir(parents=True, exist_ok=True)
                    final_path.write_bytes(stitched_path.read_bytes())
                run.final_output_path = str(final_path)
            run.status = "succeeded"
        run.updated_at = datetime.now(tz=UTC).isoformat()
        self._write_run_report(run)

    async def _process_chunk(
        self,
        run: PipelineRunRecord,
        chunk: ChunkRunRecord,
        run_config: PipelineRunConfig,
    ) -> None:
        chunk.status = "running"
        run.updated_at = datetime.now(tz=UTC).isoformat()

        run_dir = self._app_config.paths.artifacts_dir / "runs" / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        source = Path(run.input_path)
        chunk_source = run_dir / f"chunk-{chunk.chunk_index:04d}.source.mp4"
        translated_path = run_dir / f"chunk-{chunk.chunk_index:04d}.translated.mp4"
        upscaled_path = run_dir / f"chunk-{chunk.chunk_index:04d}.upscaled.mp4"

        try:
            extract_subclip(
                source,
                chunk_source,
                start_seconds=chunk.start_seconds,
                duration_seconds=max(chunk.end_seconds - chunk.start_seconds, 0.05),
            )
            with self._gpu_runtime.stage_boundary():
                translation = self._translator.translate_chunk(
                    input_path=chunk_source,
                    output_path=translated_path,
                    run_config=run_config,
                    chunk_index=chunk.chunk_index,
                )
            chunk.provider = translation.provider_used.value
            chunk.translated_path = str(translation.output_path)

            with self._gpu_runtime.stage_boundary():
                upscaled = self._upscaler.upscale_chunk(
                    input_path=translation.output_path,
                    output_path=upscaled_path,
                    run_config=run_config,
                    chunk_index=chunk.chunk_index,
                )
            chunk.upscaled_path = str(upscaled.output_path)

            if run_config.evaluation.enabled:
                similarity = compute_structural_similarity(
                    source_video_path=chunk_source,
                    generated_video_path=upscaled.output_path,
                    threshold=run_config.evaluation.structural_similarity_threshold,
                    backend=run_config.evaluation.backend,
                )
                chunk.score = similarity.score
                if not similarity.passed:
                    decision = decide_requeue(
                        score=similarity.score,
                        threshold=run_config.evaluation.structural_similarity_threshold,
                        attempt=chunk.attempt,
                        run_config=run_config,
                    )
                    if decision.should_requeue:
                        chunk.attempt += 1
                        next_config = run_config.model_copy(deep=True)
                        next_config.translation.denoise_strength = decision.next_denoise_strength
                        await self._process_chunk(run, chunk, next_config)
                        return

            chunk.status = "succeeded"
            chunk.error = None
        except Exception as exc:
            chunk.status = "failed"
            chunk.error = str(exc)
        finally:
            run.updated_at = datetime.now(tz=UTC).isoformat()
            self._write_run_report(run)

    def _write_run_report(self, run: PipelineRunRecord) -> None:
        run_dir = self._app_config.paths.artifacts_dir / "runs" / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "run-report.json"
        report_path.write_text(json.dumps(self._serialize_run(run), indent=2), encoding="utf-8")

    @staticmethod
    def _serialize_run(run: PipelineRunRecord) -> dict[str, object]:
        return {
            "run_id": run.run_id,
            "request_id": run.request_id,
            "input_path": run.input_path,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
            "status": run.status,
            "final_output_path": run.final_output_path,
            "config": run.config,
            "chunks": [
                {
                    "chunk_index": chunk.chunk_index,
                    "start_seconds": chunk.start_seconds,
                    "end_seconds": chunk.end_seconds,
                    "attempt": chunk.attempt,
                    "status": chunk.status,
                    "score": chunk.score,
                    "provider": chunk.provider,
                    "translated_path": chunk.translated_path,
                    "upscaled_path": chunk.upscaled_path,
                    "error": chunk.error,
                }
                for chunk in run.chunks
            ],
        }

