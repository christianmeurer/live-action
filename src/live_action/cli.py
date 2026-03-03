from __future__ import annotations

from pathlib import Path

import typer

from live_action.logging_utils import configure_logging
from live_action.preprocess.models import AudioExtractInput, NormalizeInput, VideoInspectInput
from live_action.preprocess.service import run_extract_audio, run_inspect, run_normalize

app = typer.Typer(help="live-action pipeline CLI")
preprocess_app = typer.Typer(help="FFmpeg preprocessing commands")
app.add_typer(preprocess_app, name="preprocess")


@app.callback()
def _root() -> None:
    configure_logging()


@preprocess_app.command("inspect")
def preprocess_inspect(input: Path, output_json: Path) -> None:
    params = VideoInspectInput(input=input, output_json=output_json)
    result = run_inspect(params.input, params.output_json)
    typer.echo(f"inspect completed: {result.output_path} ({result.elapsed_ms} ms)")


@preprocess_app.command("normalize")
def preprocess_normalize(input: Path, output: Path, fps: int = 24, height: int = 720) -> None:
    params = NormalizeInput(input=input, output=output, fps=fps, height=height)
    result = run_normalize(params.input, params.output, params.fps, params.height)
    typer.echo(f"normalize completed: {result.output_path} ({result.elapsed_ms} ms)")


@preprocess_app.command("extract-audio")
def preprocess_extract_audio(input: Path, output_wav: Path) -> None:
    params = AudioExtractInput(input=input, output_wav=output_wav)
    result = run_extract_audio(params.input, params.output_wav)
    typer.echo(f"extract-audio completed: {result.output_path} ({result.elapsed_ms} ms)")


if __name__ == "__main__":
    app()

