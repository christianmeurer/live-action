from __future__ import annotations

import asyncio

from live_action.server.queue import JobQueue


def test_queue_find_by_run_id() -> None:
    async def _run() -> None:
        queue = JobQueue()
        first = await queue.enqueue(payload={"i": 1})
        second = await queue.enqueue(payload={"i": 2})
        first.run_id = "run-a"
        second.run_id = "run-b"

        run_a_jobs = queue.find_by_run_id("run-a")
        run_b_jobs = queue.find_by_run_id("run-b")
        assert len(run_a_jobs) == 1
        assert run_a_jobs[0].id == first.id
        assert len(run_b_jobs) == 1
        assert run_b_jobs[0].id == second.id

    asyncio.run(_run())

