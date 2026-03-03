from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from live_action.pipeline.config import PipelineRunConfig, ProviderName


@dataclass(frozen=True)
class TranslationResult:
    provider_used: ProviderName
    output_path: Path
    metadata_path: Path


class TranslationProvider:
    name: ProviderName

    def translate_chunk(
        self,
        *,
        input_path: Path,
        output_path: Path,
        run_config: PipelineRunConfig,
        chunk_index: int,
    ) -> TranslationResult:
        raise NotImplementedError


class PassthroughProvider(TranslationProvider):
    def __init__(self, provider_name: ProviderName) -> None:
        self.name = provider_name

    def translate_chunk(
        self,
        *,
        input_path: Path,
        output_path: Path,
        run_config: PipelineRunConfig,
        chunk_index: int,
    ) -> TranslationResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_path, output_path)
        metadata_path = output_path.with_suffix(".translation.json")
        metadata = {
            "provider": self.name.value,
            "chunk_index": chunk_index,
            "precision": run_config.translation.precision.value,
            "guidance_scale": run_config.translation.guidance_scale,
            "denoise_strength": run_config.translation.denoise_strength,
            "seed": run_config.translation.seed,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return TranslationResult(provider_used=self.name, output_path=output_path, metadata_path=metadata_path)


class TranslationService:
    def __init__(self) -> None:
        self._providers: dict[ProviderName, TranslationProvider] = {
            ProviderName.WAN_DITTO: PassthroughProvider(ProviderName.WAN_DITTO),
            ProviderName.HUNYUAN: PassthroughProvider(ProviderName.HUNYUAN),
        }

    def translate_chunk(
        self,
        *,
        input_path: Path,
        output_path: Path,
        run_config: PipelineRunConfig,
        chunk_index: int,
    ) -> TranslationResult:
        primary = run_config.translation.primary_provider
        fallback = run_config.translation.fallback_provider

        try:
            return self._providers[primary].translate_chunk(
                input_path=input_path,
                output_path=output_path,
                run_config=run_config,
                chunk_index=chunk_index,
            )
        except Exception:
            if fallback is None:
                raise
            return self._providers[fallback].translate_chunk(
                input_path=input_path,
                output_path=output_path,
                run_config=run_config,
                chunk_index=chunk_index,
            )

