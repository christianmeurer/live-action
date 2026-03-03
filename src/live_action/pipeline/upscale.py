from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from live_action.pipeline.config import PipelineRunConfig


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
        shutil.copy2(input_path, output_path)
        metadata_path = output_path.with_suffix(".upscale.json")
        metadata = {
            "model": run_config.upscale.model_name,
            "enabled": run_config.upscale.enabled,
            "target_height": run_config.upscale.target_height,
            "chunk_index": chunk_index,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return UpscaleResult(output_path=output_path, metadata_path=metadata_path)

