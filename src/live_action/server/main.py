from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from live_action.config import AppConfig
from live_action.logging_utils import configure_logging, log_event
from live_action.observability.metrics import MetricsRegistry
from live_action.server.auth import require_api_key
from live_action.server.orchestrator import Orchestrator
from live_action.server.queue import JobQueue
from live_action.server.schemas import (
    ChunkStatusResponse,
    IngestRequest,
    IngestResponse,
    JobStatusResponse,
    PipelineRunResponse,
)
from live_action.server.startup import run_startup_checks, run_startup_provisioning

logger = logging.getLogger("live_action.server")
config = AppConfig()
job_queue = JobQueue(max_pending_jobs=config.queue.max_pending_jobs)
orchestrator = Orchestrator(config)
metrics = MetricsRegistry()
ApiKeyDep = Annotated[None, Depends(require_api_key)]


async def _worker_loop() -> None:
    while True:
        job = await job_queue.next_job()
        timer = metrics.timer()
        try:
            run_id = job.run_id
            if run_id is None:
                raise RuntimeError(f"Missing run_id for job {job.id}")
            await orchestrator.process_run(run_id)
            job_queue.complete(job.id)
            metrics.inc_completed(timer.elapsed_ms)
            log_event(logger, "queue.job.completed", {"job_id": job.id, "run_id": run_id})
        except Exception as exc:  # pragma: no cover
            job_queue.fail(job.id, str(exc))
            metrics.inc_failed(timer.elapsed_ms)
            log_event(logger, "queue.job.failed", {"job_id": job.id, "error": str(exc)})


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    run_startup_checks(config)
    downloaded = run_startup_provisioning(config)
    log_event(logger, "startup.provisioning.completed", {"downloaded_models": downloaded})
    worker_task = asyncio.create_task(_worker_loop(), name="live-action-worker")
    try:
        yield
    finally:
        worker_task.cancel()
        with suppress(asyncio.CancelledError):
            await worker_task


app = FastAPI(title="live-action", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def get_metrics(_: ApiKeyDep) -> dict[str, int]:
    snap = metrics.snapshot()
    return {
        "jobs_enqueued": snap.jobs_enqueued,
        "jobs_completed": snap.jobs_completed,
        "jobs_failed": snap.jobs_failed,
        "total_processing_ms": snap.total_processing_ms,
    }


@app.post("/jobs", response_model=IngestResponse)
async def create_job(req: IngestRequest, _: ApiKeyDep) -> IngestResponse:
    if req.request_id is not None:
        existing = orchestrator.get_run_by_request_id(req.request_id)
        if existing is not None:
            for existing_job in job_queue.find_by_run_id(existing.run_id):
                if existing_job is not None:
                    return IngestResponse(
                        job_id=existing_job.id,
                        run_id=existing.run_id,
                        request_id=req.request_id,
                        status=existing_job.status,
                    )

    run = orchestrator.create_run(
        input_path=req.input_path,
        config_payload=req.config,
        request_id=req.request_id,
    )
    job = await job_queue.enqueue(payload=req.model_dump())
    metrics.inc_enqueued()
    job.run_id = run.run_id
    log_event(
        logger,
        "queue.job.enqueued",
        {"job_id": job.id, "run_id": run.run_id, "input_path": req.input_path},
    )
    return IngestResponse(job_id=job.id, run_id=run.run_id, request_id=req.request_id, status=job.status)


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str, _: ApiKeyDep) -> JobStatusResponse:
    job = job_queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return JobStatusResponse(job_id=job.id, run_id=job.run_id, status=job.status, error=job.error)


@app.get("/runs", response_model=list[PipelineRunResponse])
async def list_runs(_: ApiKeyDep) -> list[PipelineRunResponse]:
    runs = orchestrator.list_runs()
    responses: list[PipelineRunResponse] = []
    for run in runs:
        responses.append(
            PipelineRunResponse(
                run_id=run.run_id,
                request_id=run.request_id,
                input_path=run.input_path,
                created_at=run.created_at,
                updated_at=run.updated_at,
                status=run.status,
                final_output_path=run.final_output_path,
                chunks=[_to_chunk_status_response(chunk) for chunk in run.chunks],
            )
        )
    return responses


@app.get("/runs/{run_id}", response_model=PipelineRunResponse)
async def get_run(run_id: str, _: ApiKeyDep) -> PipelineRunResponse:
    run = orchestrator.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return PipelineRunResponse(
        run_id=run.run_id,
        request_id=run.request_id,
        input_path=run.input_path,
        created_at=run.created_at,
        updated_at=run.updated_at,
        status=run.status,
        final_output_path=run.final_output_path,
        chunks=[_to_chunk_status_response(chunk) for chunk in run.chunks],
    )


def _to_chunk_status_response(chunk: object) -> ChunkStatusResponse:
    return ChunkStatusResponse.model_validate(chunk, from_attributes=True)

