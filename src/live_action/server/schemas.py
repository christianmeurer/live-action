from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic import field_validator

from live_action.server.queue import JobStatus


class IngestRequest(BaseModel):
    input_path: str = Field(min_length=1)
    config: dict[str, object] = Field(default_factory=dict)

    @field_validator("input_path")
    @classmethod
    def _validate_input_path(cls, value: str) -> str:
        if not Path(value).exists():
            raise ValueError(f"input_path does not exist: {value}")
        return value


class IngestResponse(BaseModel):
    job_id: str
    run_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    run_id: str | None = None
    error: str | None = None


class ChunkStatusResponse(BaseModel):
    chunk_index: int
    start_seconds: float
    end_seconds: float
    attempt: int
    status: str
    score: float | None = None
    provider: str | None = None
    translated_path: str | None = None
    upscaled_path: str | None = None
    error: str | None = None


class PipelineRunResponse(BaseModel):
    run_id: str
    input_path: str
    created_at: str
    updated_at: str
    status: str
    chunks: list[ChunkStatusResponse] = Field(default_factory=list)

