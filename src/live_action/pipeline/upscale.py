from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from live_action.adapters.command import render_command, run_command
from live_action.pipeline.config import ExecutionMode, PipelineRunConfig


@dataclass(frozen=True)
class UpscaleResult:
    output_path: Path
    metadata_path: Path


class UpscaleService:
    def upscale_chunk(
        self,
        *,
        input_path: Path,
        output_path: Path,
        run_config: PipelineRunConfig,
        chunk_index: int,
    ) -> UpscaleResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if run_config.upscale.execution_mode == ExecutionMode.COMMAND:
            if run_config.upscale.command_template is None:
                msg = "upscale.command_template must be provided when execution_mode=command"
                raise ValueError(msg)
            command = _render_command(
                template=run_config.upscale.command_template,
                variables={
                    "input": str(input_path),
                    "output": str(output_path),
                    "chunk_index": str(chunk_index),
                    "target_height": str(run_config.upscale.target_height),
                    "model": run_config.upscale.model_name,
                },
            )
            run_command(command, stage="upscale")
        else:
            shutil.copy2(input_path, output_path)

        metadata_path = output_path.with_suffix(".upscale.json")
        metadata = {
            "model": run_config.upscale.model_name,
            "enabled": run_config.upscale.enabled,
            "execution_mode": run_config.upscale.execution_mode.value,
            "target_height": run_config.upscale.target_height,
            "chunk_index": chunk_index,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return UpscaleResult(output_path=output_path, metadata_path=metadata_path)


def _render_command(template: list[str], variables: dict[str, str]) -> list[str]:
    return render_command(template, variables)

