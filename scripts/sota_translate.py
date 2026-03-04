from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SOTA-2026 translation adapter — Wan2.1-I2V")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--guidance", required=True, type=float)
    parser.add_argument("--denoise", required=True, type=float)
    return parser.parse_args()


def _wan21_inference(
    input_path: Path,
    output_path: Path,
    seed: int,
    guidance: float,
    denoise: float,
    repo_dir: Path,
    model_dir: Path,
) -> None:
    """Run Wan2.1 I2V inference via torchrun."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    script = repo_dir / "generate.py"
    if not script.exists():
        # fallback: look for the inference entry point
        for candidate in ["generate.py", "run_i2v.py", "inference.py"]:
            if (repo_dir / candidate).exists():
                script = repo_dir / candidate
                break
        else:
            raise FileNotFoundError(
                f"No inference script found in {repo_dir}. "
                f"Contents: {list(repo_dir.iterdir())}"
            )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_dir)

    cmd = [
        "torchrun",
        "--nproc_per_node=1",
        str(script),
        "--task", "i2v-14B",
        "--size", "720*1280",
        "--ckpt_dir", str(model_dir),
        "--image", str(input_path),
        "--save_file", str(output_path),
        "--sample_shift", str(denoise),
        "--sample_guide_scale", str(guidance),
        "--seed", str(seed),
        "--frame_num", "17",
    ]

    result = subprocess.run(cmd, env=env, cwd=str(repo_dir), check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Wan2.1 inference failed (rc={result.returncode}). "
            f"cmd={' '.join(cmd)}"
        )


def _hunyuan_inference(
    input_path: Path,
    output_path: Path,
    seed: int,
    guidance: float,
    denoise: float,
    model_dir: Path,
) -> None:
    """Run HunyuanVideo 1.5 inference (fallback provider)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # HunyuanVideo weights are in model_dir; use their sample_video.py if present
    repo_dir = Path("/opt/HunyuanVideo")
    script = repo_dir / "sample_video.py" if repo_dir.exists() else None

    if script and script.exists():
        cmd = [
            sys.executable,
            str(script),
            "--video-size", "720", "1280",
            "--video-length", "17",
            "--infer-steps", "50",
            "--prompt", "high quality live action footage",
            "--seed", str(seed),
            "--cfg-scale", str(guidance),
            "--dit", str(model_dir),
            "--save-path", str(output_path.parent),
        ]
        subprocess.run(cmd, cwd=str(repo_dir), check=True)
    else:
        raise RuntimeError(
            f"HunyuanVideo inference repo not found at {repo_dir}. "
            "Cannot run fallback provider."
        )


def main() -> None:
    args = _parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"input does not exist: {input_path}")

    # Model and repo paths provisioned by HuggingFace sync
    models_root = Path("/opt/live-action/models")
    wan21_model = models_root / "translation" / "Wan-AI--Wan2.1-I2V-14B-720P"
    hunyuan_model = models_root / "translation" / "tencent--HunyuanVideo-1.5"
    wan21_repo = Path("/opt/wan2.1")

    provider = args.provider.lower()

    if "wan" in provider:
        if not wan21_model.exists():
            raise FileNotFoundError(f"Wan2.1 model weights not found at {wan21_model}")
        if not wan21_repo.exists():
            raise FileNotFoundError(
                f"Wan2.1 inference repo not found at {wan21_repo}. "
                "Run: git clone https://github.com/Wan-AI/Wan2.1.git /opt/wan2.1"
            )
        _wan21_inference(
            input_path=input_path,
            output_path=output_path,
            seed=args.seed,
            guidance=args.guidance,
            denoise=args.denoise,
            repo_dir=wan21_repo,
            model_dir=wan21_model,
        )
    elif "hunyuan" in provider:
        if not hunyuan_model.exists():
            raise FileNotFoundError(f"HunyuanVideo model weights not found at {hunyuan_model}")
        _hunyuan_inference(
            input_path=input_path,
            output_path=output_path,
            seed=args.seed,
            guidance=args.guidance,
            denoise=args.denoise,
            model_dir=hunyuan_model,
        )
    else:
        raise ValueError(f"Unknown provider: {args.provider}")


if __name__ == "__main__":
    main()
