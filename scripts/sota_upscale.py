from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SOTA-2026 upscale adapter entrypoint")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--height", required=True, type=int)
    parser.add_argument("--model", required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"input does not exist: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if shutil.which("ffmpeg") is None:
        shutil.copy2(input_path, output_path)
        return

    target_height = max(256, min(4320, args.height))
    vf = f"scale=-2:{target_height}:flags=lanczos"
    cmd = [
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
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

