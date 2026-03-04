from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SOTA-2026 upscale adapter — SeedVR2-3B")
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

    # SeedVR2 weights provisioned by HuggingFace sync
    models_root = Path("/opt/live-action/models")
    model_dir = models_root / "upscale" / "ByteDance-Seed--SeedVR2-3B"
    seedvr_repo = Path("/opt/seedvr")

    if not model_dir.exists():
        raise FileNotFoundError(
            f"SeedVR2-3B model weights not found at {model_dir}"
        )
    if not seedvr_repo.exists():
        raise FileNotFoundError(
            f"SeedVR inference repo not found at {seedvr_repo}. "
            "Run: git clone https://github.com/ByteDance-Seed/SeedVR.git /opt/seedvr"
        )

    # SeedVR2 inference script — projects/inference_seedvr2_3b.py
    script = seedvr_repo / "projects" / "inference_seedvr2_3b.py"
    if not script.exists():
        # fallback: search for any inference_seedvr2 script
        candidates = list(seedvr_repo.rglob("inference_seedvr2*.py"))
        if not candidates:
            raise FileNotFoundError(
                f"No SeedVR2 inference script found under {seedvr_repo}"
            )
        script = candidates[0]

    target_height = max(256, min(4320, args.height))
    # SeedVR2 expects width to maintain aspect ratio; -2 convention not supported,
    # compute proportional width from 1280x704 source
    src_w, src_h = 1280, 704
    scale = target_height / src_h
    target_width = int(src_w * scale)
    # round to multiple of 16
    target_width = (target_width // 16) * 16

    env = os.environ.copy()
    env["PYTHONPATH"] = str(seedvr_repo)

    # SeedVR2-3B uses distributed torchrun even on single GPU
    cmd = [
        "torchrun",
        "--nproc-per-node=1",
        str(script),
        "--video_path", str(input_path),
        "--output_dir", str(output_path.parent),
        "--seed", "666",
        "--res_h", str(target_height),
        "--res_w", str(target_width),
        "--sp_size", "1",
    ]

    result = subprocess.run(cmd, env=env, cwd=str(seedvr_repo), check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"SeedVR2-3B inference failed (rc={result.returncode}). "
            f"cmd={' '.join(cmd)}"
        )

    # SeedVR writes output to output_dir/<input_stem>/<input_filename>
    # Locate and move it to the expected output_path
    stem = input_path.stem
    candidate = output_path.parent / stem / input_path.name
    if candidate.exists() and candidate != output_path:
        candidate.rename(output_path)
    elif not output_path.exists():
        # try any mp4 in output_dir/stem/
        subdirs = list((output_path.parent / stem).glob("*.mp4"))
        if subdirs:
            subdirs[0].rename(output_path)
        else:
            raise FileNotFoundError(
                f"SeedVR2-3B did not produce output at expected path {output_path}"
            )


if __name__ == "__main__":
    main()
