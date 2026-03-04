from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from live_action.adapters.command import render_command, run_command
from live_action.adapters.local_video import translate_video_local
from live_action.pipeline.config import ExecutionMode, PipelineRunConfig, ProviderName


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


class CommandTemplateProvider(TranslationProvider):
    def __init__(self, provider_name: ProviderName, command_template: list[str]) -> None:
        self.name = provider_name
        self._command_template = command_template

    def translate_chunk(
        self,
        *,
        input_path: Path,
        output_path: Path,
        run_config: PipelineRunConfig,
        chunk_index: int,
    ) -> TranslationResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = _render_command(
            template=self._command_template,
            variables={
                "input": str(input_path),
                "output": str(output_path),
                "chunk_index": str(chunk_index),
                "seed": str(run_config.translation.seed),
                "denoise": str(run_config.translation.denoise_strength),
                "guidance": str(run_config.translation.guidance_scale),
                "provider": self.name.value,
            },
        )
        run_command(command, stage="translation")
        metadata_path = output_path.with_suffix(".translation.json")
        metadata = {
            "provider": self.name.value,
            "chunk_index": chunk_index,
            "execution_mode": ExecutionMode.COMMAND.value,
            "command": command,
            "precision": run_config.translation.precision.value,
            "guidance_scale": run_config.translation.guidance_scale,
            "denoise_strength": run_config.translation.denoise_strength,
            "seed": run_config.translation.seed,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return TranslationResult(provider_used=self.name, output_path=output_path, metadata_path=metadata_path)


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
            "execution_mode": ExecutionMode.DRY_RUN.value,
            "precision": run_config.translation.precision.value,
            "guidance_scale": run_config.translation.guidance_scale,
            "denoise_strength": run_config.translation.denoise_strength,
            "seed": run_config.translation.seed,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return TranslationResult(provider_used=self.name, output_path=output_path, metadata_path=metadata_path)


class LocalProvider(TranslationProvider):
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
        translate_video_local(
            input_path=input_path,
            output_path=output_path,
            denoise_strength=run_config.translation.denoise_strength,
            guidance_scale=run_config.translation.guidance_scale,
            seed=run_config.translation.seed,
        )
        metadata_path = output_path.with_suffix(".translation.json")
        metadata = {
            "provider": self.name.value,
            "chunk_index": chunk_index,
            "execution_mode": ExecutionMode.LOCAL.value,
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

    def _build_provider(self, provider: ProviderName, run_config: PipelineRunConfig) -> TranslationProvider:
        if run_config.translation.execution_mode == ExecutionMode.COMMAND:
            if run_config.translation.command_template is None:
                msg = "translation.command_template must be provided for command execution mode"
                raise ValueError(msg)
            return CommandTemplateProvider(provider, run_config.translation.command_template)
        if run_config.translation.execution_mode == ExecutionMode.LOCAL:
            return LocalProvider(provider)
        return self._providers[provider]

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
            provider = self._build_provider(primary, run_config)
            return provider.translate_chunk(
                input_path=input_path,
                output_path=output_path,
                run_config=run_config,
                chunk_index=chunk_index,
            )
        except Exception:
            if fallback is None:
                raise
            provider = self._build_provider(fallback, run_config)
            return provider.translate_chunk(
                input_path=input_path,
                output_path=output_path,
                run_config=run_config,
                chunk_index=chunk_index,
            )


def _render_command(template: list[str], variables: dict[str, str]) -> list[str]:
    return render_command(template, variables)

