from __future__ import annotations

import gc
import os
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter


@dataclass(frozen=True)
class GpuSnapshot:
    available: bool
    device_name: str
    allocated_bytes: int
    reserved_bytes: int
    elapsed_ms: int


class GpuRuntime:
    def __init__(self) -> None:
        self._torch = self._load_torch()
        self._forced_precision = os.getenv("LIVE_ACTION_PRECISION", "").strip().lower()

    @staticmethod
    def _load_torch():
        try:
            import torch  # type: ignore

            return torch
        except Exception:
            return None

    def snapshot(self) -> GpuSnapshot:
        started = perf_counter()
        if self._torch is None or not self._torch.cuda.is_available():
            return GpuSnapshot(
                available=False,
                device_name="cpu",
                allocated_bytes=0,
                reserved_bytes=0,
                elapsed_ms=0,
            )
        allocated = int(self._torch.cuda.memory_allocated())
        reserved = int(self._torch.cuda.memory_reserved())
        device_name = str(self._torch.cuda.get_device_name(0))
        elapsed_ms = int((perf_counter() - started) * 1000)
        return GpuSnapshot(
            available=True,
            device_name=device_name,
            allocated_bytes=allocated,
            reserved_bytes=reserved,
            elapsed_ms=elapsed_ms,
        )

    @property
    def forced_precision(self) -> str:
        return self._forced_precision

    @contextmanager
    def stage_boundary(self):
        try:
            yield
        finally:
            gc.collect()
            if self._torch is not None and self._torch.cuda.is_available():
                self._torch.cuda.empty_cache()

