from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from live_action.logging_utils import log_event
from live_action.preprocess.ffmpeg import extract_audio_wav, inspect_video, normalize_video


@dataclass(frozen=True)
class StageResult:
    stage: str
    elapsed_ms: int
    output_path: Path


def run_inspect(input_path: Path, output_json: Path, logger_name: str = "live_action") -> StageResult:
    import logging

    logger = logging.getLogger(logger_name)
    started = perf_counter()
    payload = inspect_video(input_path)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    elapsed_ms = int((perf_counter() - started) * 1000)
    log_event(
        logger,
        "preprocess.inspect.completed",
        {"input": str(input_path), "output_json": str(output_json), "elapsed_ms": elapsed_ms},
    )
    return StageResult(stage="inspect", elapsed_ms=elapsed_ms, output_path=output_json)


def run_normalize(
    input_path: Path,
    output_path: Path,
    fps: int,
    height: int,
    logger_name: str = "live_action",
) -> StageResult:
    import logging

    logger = logging.getLogger(logger_name)
    started = perf_counter()
    normalize_video(input_path, output_path, fps=fps, height=height)
    elapsed_ms = int((perf_counter() - started) * 1000)
    log_event(
        logger,
        "preprocess.normalize.completed",
        {
            "input": str(input_path),
            "output": str(output_path),
            "fps": fps,
            "height": height,
            "elapsed_ms": elapsed_ms,
        },
    )
    return StageResult(stage="normalize", elapsed_ms=elapsed_ms, output_path=output_path)


def run_extract_audio(
    input_path: Path,
    output_wav: Path,
    logger_name: str = "live_action",
) -> StageResult:
    import logging

    logger = logging.getLogger(logger_name)
    started = perf_counter()
    extract_audio_wav(input_path, output_wav)
    elapsed_ms = int((perf_counter() - started) * 1000)
    log_event(
        logger,
        "preprocess.extract_audio.completed",
        {"input": str(input_path), "output_wav": str(output_wav), "elapsed_ms": elapsed_ms},
    )
    return StageResult(stage="extract_audio", elapsed_ms=elapsed_ms, output_path=output_wav)

