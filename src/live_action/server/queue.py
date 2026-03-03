from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    status: JobStatus = JobStatus.QUEUED
    error: str | None = None


class JobQueue:
    def __init__(self, max_pending_jobs: int = 128) -> None:
        self._queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=max_pending_jobs)
        self._jobs: dict[str, Job] = {}

    async def enqueue(self, payload: dict[str, Any]) -> Job:
        job = Job(payload=payload)
        self._jobs[job.id] = job
        await self._queue.put(job)
        return job

    async def next_job(self) -> Job:
        job = await self._queue.get()
        job.status = JobStatus.RUNNING
        return job

    def complete(self, job_id: str) -> None:
        self._jobs[job_id].status = JobStatus.SUCCEEDED

    def fail(self, job_id: str, error: str) -> None:
        job = self._jobs[job_id]
        job.status = JobStatus.FAILED
        job.error = error

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

