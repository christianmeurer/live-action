from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from live_action.config import AppConfig
from live_action.logging_utils import configure_logging, log_event
from live_action.server.queue import JobQueue
from live_action.server.schemas import IngestRequest, IngestResponse, JobStatusResponse

logger = logging.getLogger("live_action.server")
config = AppConfig()
job_queue = JobQueue(max_pending_jobs=config.queue.max_pending_jobs)


async def _worker_loop() -> None:
    while True:
        job = await job_queue.next_job()
        try:
            await asyncio.sleep(0.05)
            job_queue.complete(job.id)
            log_event(logger, "queue.job.completed", {"job_id": job.id})
        except Exception as exc:  # pragma: no cover
            job_queue.fail(job.id, str(exc))
            log_event(logger, "queue.job.failed", {"job_id": job.id, "error": str(exc)})


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    worker_task = asyncio.create_task(_worker_loop(), name="live-action-worker")
    try:
        yield
    finally:
        worker_task.cancel()
        with contextlib_suppress(asyncio.CancelledError):
            await worker_task


@asynccontextmanager
async def contextlib_suppress(*exceptions: type[BaseException]):
    try:
        yield
    except exceptions:
        return


app = FastAPI(title="live-action", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs", response_model=IngestResponse)
async def create_job(req: IngestRequest) -> IngestResponse:
    job = await job_queue.enqueue(payload=req.model_dump())
    log_event(logger, "queue.job.enqueued", {"job_id": job.id, "input_path": req.input_path})
    return IngestResponse(job_id=job.id, status=job.status)


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str) -> JobStatusResponse:
    job = job_queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return JobStatusResponse(job_id=job.id, status=job.status, error=job.error)

