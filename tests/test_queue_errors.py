from __future__ import annotations

import pytest

from live_action.server.queue import JobQueue


def test_queue_complete_unknown_job_raises() -> None:
    queue = JobQueue()
    with pytest.raises(ValueError):
        queue.complete("unknown-job")


def test_queue_fail_unknown_job_raises() -> None:
    queue = JobQueue()
    with pytest.raises(ValueError):
        queue.fail("unknown-job", "boom")

