from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class Precision(StrEnum):
    BF16 = "bf16"
    FP8_E4M3FN = "fp8_e4m3fn"


class ProviderName(StrEnum):
    WAN_DITTO = "wan2.1-ditto"
    HUNYUAN = "hunyuan-video-1.5"


class ExecutionMode(StrEnum):
    DRY_RUN = "dry-run"
    COMMAND = "command"
    LOCAL = "local"


class RetryPolicy(BaseModel):
    max_retries: int = Field(default=2, ge=0, le=10)
    denoise_backoff: float = Field(default=0.05, gt=0.0, le=0.3)


class ChunkingConfig(BaseModel):
    chunk_seconds: float = Field(default=5.0, gt=0.2, le=60.0)
    overlap_ratio: float = Field(default=0.25, ge=0.0, lt=0.95)
    target_fps: int = Field(default=24, ge=1, le=120)


class TranslationConfig(BaseModel):
    primary_provider: ProviderName = ProviderName.WAN_DITTO
    fallback_provider: ProviderName | None = ProviderName.HUNYUAN
    provider_model_map: dict[ProviderName, str] = Field(
        default_factory=lambda: {
            ProviderName.WAN_DITTO: "Wan-AI/Wan2.1-I2V-14B-720P",
            ProviderName.HUNYUAN: "tencent/HunyuanVideo-1.5",
        }
    )
    model_revision: str = "main"
    execution_mode: ExecutionMode = ExecutionMode.LOCAL
    command_template: list[str] | None = None
    precision: Precision = Precision.BF16
    denoise_strength: float = Field(default=0.8, ge=0.0, le=1.0)
    guidance_scale: float = Field(default=7.0, ge=1.0, le=30.0)
    seed: int = Field(default=1234, ge=0)
    retry: RetryPolicy = Field(default_factory=RetryPolicy)


class UpscaleConfig(BaseModel):
    enabled: bool = True
    model_name: str = "seedvr2"
    model_repo_id: str = "ByteDance-Seed/SeedVR2-3B"
    model_revision: str = "main"
    execution_mode: ExecutionMode = ExecutionMode.LOCAL
    command_template: list[str] | None = None
    target_height: int = Field(default=1080, ge=256, le=4320)


class EvalConfig(BaseModel):
    enabled: bool = True
    backend: str = "metadata-cosine"
    structural_similarity_threshold: float = Field(default=0.90, ge=0.0, le=1.0)


class PipelineRunConfig(BaseModel):
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    upscale: UpscaleConfig = Field(default_factory=UpscaleConfig)
    evaluation: EvalConfig = Field(default_factory=EvalConfig)

    @model_validator(mode="after")
    def _validate_fallback(self) -> "PipelineRunConfig":
        if self.translation.fallback_provider == self.translation.primary_provider:
            self.translation.fallback_provider = None
        if self.translation.execution_mode == ExecutionMode.COMMAND and not self.translation.command_template:
            raise ValueError("translation.command_template is required when execution_mode=command")
        if (
            self.upscale.enabled
            and self.upscale.execution_mode == ExecutionMode.COMMAND
            and not self.upscale.command_template
        ):
            raise ValueError("upscale.command_template is required when execution_mode=command")
        return self


def build_sota_2026_profile() -> PipelineRunConfig:
    return PipelineRunConfig.model_validate(
        {
            "translation": {
                "primary_provider": ProviderName.WAN_DITTO.value,
                "fallback_provider": ProviderName.HUNYUAN.value,
                "provider_model_map": {
                    ProviderName.WAN_DITTO.value: "Wan-AI/Wan2.1-I2V-14B-720P",
                    ProviderName.HUNYUAN.value: "tencent/HunyuanVideo-1.5",
                },
                "model_revision": "main",
                "execution_mode": ExecutionMode.COMMAND.value,
                "command_template": [
                    "python3",
                    "scripts/sota_translate.py",
                    "--input",
                    "{input}",
                    "--output",
                    "{output}",
                    "--provider",
                    "{provider}",
                    "--seed",
                    "{seed}",
                    "--guidance",
                    "{guidance}",
                    "--denoise",
                    "{denoise}",
                ],
                "precision": Precision.BF16.value,
            },
            "upscale": {
                "enabled": True,
                "model_name": "seedvr2-3b",
                "model_repo_id": "ByteDance-Seed/SeedVR2-3B",
                "model_revision": "main",
                "execution_mode": ExecutionMode.COMMAND.value,
                "command_template": [
                    "python3",
                    "scripts/sota_upscale.py",
                    "--input",
                    "{input}",
                    "--output",
                    "{output}",
                    "--height",
                    "{target_height}",
                    "--model",
                    "{model}",
                ],
                "target_height": 1080,
            },
            "evaluation": {
                "enabled": True,
                "backend": "clip",
                "structural_similarity_threshold": 0.9,
            },
        }
    )

