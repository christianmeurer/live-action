from __future__ import annotations

from pydantic import BaseModel, Field

from live_action.server.queue import JobStatus


class IngestRequest(BaseModel):
    input_path: str = Field(min_length=1)
    config: dict[str, object] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    error: str | None = None

