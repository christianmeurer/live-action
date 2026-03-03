from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class AppPaths(BaseModel):
    artifacts_dir: Path = Field(default=Path("artifacts"))
    outputs_dir: Path = Field(default=Path("outputs"))
    temp_dir: Path = Field(default=Path("artifacts/tmp"))


class QueueSettings(BaseModel):
    max_pending_jobs: int = Field(default=128, ge=1)


class AppConfig(BaseModel):
    paths: AppPaths = Field(default_factory=AppPaths)
    queue: QueueSettings = Field(default_factory=QueueSettings)

