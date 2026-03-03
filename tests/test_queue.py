from __future__ import annotations

import asyncio

from live_action.server.queue import JobQueue, JobStatus


def test_queue_enqueues_and_completes() -> None:
    async def _run() -> None:
        queue = JobQueue()
        job = await queue.enqueue(payload={"a": 1})
        assert job.status == JobStatus.QUEUED

        running = await queue.next_job()
        assert running.id == job.id
        assert running.status == JobStatus.RUNNING

        queue.complete(job.id)
        assert queue.get(job.id) is not None
        assert queue.get(job.id).status == JobStatus.SUCCEEDED

    asyncio.run(_run())

