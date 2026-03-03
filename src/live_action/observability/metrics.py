from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import perf_counter


@dataclass
class MetricsSnapshot:
    jobs_enqueued: int
    jobs_completed: int
    jobs_failed: int
    total_processing_ms: int


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs_enqueued = 0
        self._jobs_completed = 0
        self._jobs_failed = 0
        self._total_processing_ms = 0

    def inc_enqueued(self) -> None:
        with self._lock:
            self._jobs_enqueued += 1

    def inc_completed(self, elapsed_ms: int) -> None:
        with self._lock:
            self._jobs_completed += 1
            self._total_processing_ms += elapsed_ms

    def inc_failed(self, elapsed_ms: int) -> None:
        with self._lock:
            self._jobs_failed += 1
            self._total_processing_ms += elapsed_ms

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            return MetricsSnapshot(
                jobs_enqueued=self._jobs_enqueued,
                jobs_completed=self._jobs_completed,
                jobs_failed=self._jobs_failed,
                total_processing_ms=self._total_processing_ms,
            )

    def timer(self) -> "TimerCtx":
        return TimerCtx()


class TimerCtx:
    def __init__(self) -> None:
        self._start = perf_counter()

    @property
    def elapsed_ms(self) -> int:
        return int((perf_counter() - self._start) * 1000)

