from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SOTA-2026 translation adapter entrypoint")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--guidance", required=True, type=float)
    parser.add_argument("--denoise", required=True, type=float)
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

    guidance = max(1.0, min(30.0, args.guidance))
    denoise = max(0.0, min(1.0, args.denoise))
    contrast = 1.0 + ((guidance - 1.0) / 60.0)
    saturation = 1.0 + denoise / 6.0
    hue_shift = ((args.seed % 21) - 10) / 100.0
    vf = f"eq=contrast={contrast:.4f}:saturation={saturation:.4f},hue=h={hue_shift:.4f}"

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

