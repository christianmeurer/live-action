from __future__ import annotations

import subprocess
from pathlib import Path

from live_action.preprocess.ffmpeg import ensure_ffmpeg


class LocalAdapterError(RuntimeError):
    pass


def translate_video_local(
    *,
    input_path: Path,
    output_path: Path,
    denoise_strength: float,
    guidance_scale: float,
    seed: int,
) -> None:
    ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    denoise = max(0.0, min(1.0, denoise_strength))
    guidance = max(1.0, min(30.0, guidance_scale))
    contrast = 1.0 + ((guidance - 1.0) / 60.0)
    saturation = 1.0 + (denoise / 6.0)
    sharpness = 1.0 + (denoise / 2.0)
    hue_shift = ((seed % 21) - 10) / 100.0

    vf = (
        f"eq=contrast={contrast:.4f}:saturation={saturation:.4f},"
        f"unsharp=5:5:{sharpness:.4f}:5:5:0.0,"
        f"hue=h={hue_shift:.4f}"
    )

    command: list[str] = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        vf,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]
    _run(command=command, stage="translation-local")


def upscale_video_local(*, input_path: Path, output_path: Path, target_height: int) -> None:
    ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    vf = f"scale=-2:{target_height}:flags=lanczos"
    command: list[str] = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        vf,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]
    _run(command=command, stage="upscale-local")


def _run(*, command: list[str], stage: str) -> None:
    try:
        subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr or ""
        stdout = exc.stdout or ""
        msg = f"{stage} failed: {' '.join(command)} stdout={stdout.strip()} stderr={stderr.strip()}"
        raise LocalAdapterError(msg) from exc

