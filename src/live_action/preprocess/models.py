from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class VideoInspectInput(BaseModel):
    input: Path
    output_json: Path

    @field_validator("input")
    @classmethod
    def _validate_input(cls, value: Path) -> Path:
        if not value.exists():
            raise ValueError(f"Input video does not exist: {value}")
        if value.suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm"}:
            raise ValueError(f"Unsupported video extension for {value}")
        return value


class NormalizeInput(BaseModel):
    input: Path
    output: Path
    fps: int = Field(default=24, ge=1, le=120)
    height: int = Field(default=720, ge=64)

    @field_validator("input")
    @classmethod
    def _validate_input(cls, value: Path) -> Path:
        if not value.exists():
            raise ValueError(f"Input video does not exist: {value}")
        return value


class AudioExtractInput(BaseModel):
    input: Path
    output_wav: Path

    @field_validator("input")
    @classmethod
    def _validate_input(cls, value: Path) -> Path:
        if not value.exists():
            raise ValueError(f"Input video does not exist: {value}")
        return value

