from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class FFmpegUnavailableError(RuntimeError):
    pass


class FFmpegCommandError(RuntimeError):
    pass


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise FFmpegUnavailableError("ffmpeg executable not found in PATH")
    if shutil.which("ffprobe") is None:
        raise FFmpegUnavailableError("ffprobe executable not found in PATH")


def inspect_video(input_path: Path) -> dict[str, Any]:
    ensure_ffmpeg()
    cmd: list[str] = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(input_path),
    ]
    result = _run_command(cmd, capture_output=True)
    return json.loads(result.stdout)


def normalize_video(input_path: Path, output_path: Path, fps: int, height: int) -> None:
    ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    vf = f"fps={fps},scale=-2:{height}:flags=lanczos"
    cmd: list[str] = [
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
    _run_command(cmd)


def extract_audio_wav(input_path: Path, output_path: Path) -> None:
    ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd: list[str] = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "48000",
        "-ac",
        "2",
        str(output_path),
    ]
    _run_command(cmd)


def extract_subclip(input_path: Path, output_path: Path, start_seconds: float, duration_seconds: float) -> None:
    ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd: list[str] = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{start_seconds:.6f}",
        "-i",
        str(input_path),
        "-t",
        f"{duration_seconds:.6f}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-an",
        str(output_path),
    ]
    _run_command(cmd)


def _run_command(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=capture_output,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr or ""
        stdout = exc.stdout or ""
        message = (
            "FFmpeg command failed. "
            f"command={' '.join(cmd)} stdout={stdout.strip()} stderr={stderr.strip()}"
        )
        raise FFmpegCommandError(message) from exc

