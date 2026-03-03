from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Any

from live_action.preprocess.ffmpeg import inspect_video


@dataclass(frozen=True)
class SimilarityResult:
    score: float
    passed: bool
    details: dict[str, Any]


def compute_structural_similarity(
    *, source_video_path: Path, generated_video_path: Path, threshold: float
) -> SimilarityResult:
    source_meta = inspect_video(source_video_path)
    generated_meta = inspect_video(generated_video_path)
    source_vec = _vectorize(source_meta)
    generated_vec = _vectorize(generated_meta)
    score = _cosine_similarity(source_vec, generated_vec)
    details: dict[str, Any] = {
        "threshold": threshold,
        "source_duration": source_meta.get("format", {}).get("duration"),
        "generated_duration": generated_meta.get("format", {}).get("duration"),
    }
    return SimilarityResult(score=score, passed=score >= threshold, details=details)


def _vectorize(meta: dict[str, Any]) -> np.ndarray:
    streams = meta.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    width = float(video_stream.get("width", 0))
    height = float(video_stream.get("height", 0))
    fps_text = str(video_stream.get("avg_frame_rate", "0/1"))
    fps = _parse_fps(fps_text)
    duration = float(meta.get("format", {}).get("duration", 0.0))
    return [width, height, fps, duration]


def _parse_fps(raw: str) -> float:
    if "/" not in raw:
        return float(raw or 0.0)
    num, den = raw.split("/", maxsplit=1)
    den_v = float(den or 1.0)
    if den_v == 0.0:
        return 0.0
    return float(num or 0.0) / den_v


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_norm = sqrt(sum(v * v for v in a))
    b_norm = sqrt(sum(v * v for v in b))
    if a_norm == 0.0 or b_norm == 0.0:
        return 0.0
    dot = sum(av * bv for av, bv in zip(a, b, strict=True))
    return float(dot / (a_norm * b_norm))

