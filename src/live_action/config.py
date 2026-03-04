from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppPaths(BaseModel):
    artifacts_dir: Path = Field(default=Path("artifacts"))
    outputs_dir: Path = Field(default=Path("outputs"))
    temp_dir: Path = Field(default=Path("artifacts/tmp"))


class QueueSettings(BaseModel):
    max_pending_jobs: int = Field(default=128, ge=1)


class HuggingFaceSettings(BaseModel):
    token: str = Field(default="")
    cache_dir: Path = Field(default=Path("artifacts/huggingface"))
    local_dir: Path = Field(default=Path("models"))
    enabled: bool = False
    skip_if_present: bool = True


class ProvisioningSettings(BaseModel):
    auto_sync_on_startup: bool = True
    huggingface: HuggingFaceSettings = Field(default_factory=HuggingFaceSettings)


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LIVE_ACTION_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    paths: AppPaths = Field(default_factory=AppPaths)
    queue: QueueSettings = Field(default_factory=QueueSettings)
    provisioning: ProvisioningSettings = Field(default_factory=ProvisioningSettings)

