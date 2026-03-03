from __future__ import annotations

from dataclasses import dataclass
from math import exp


@dataclass(frozen=True)
class ChunkSpec:
    index: int
    start_seconds: float
    end_seconds: float
    overlap_ratio: float

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


def build_chunk_plan(total_seconds: float, chunk_seconds: float, overlap_ratio: float) -> list[ChunkSpec]:
    if total_seconds <= 0:
        return []
    if chunk_seconds <= 0:
        msg = f"chunk_seconds must be positive, got {chunk_seconds}"
        raise ValueError(msg)
    if not 0.0 <= overlap_ratio < 1.0:
        msg = f"overlap_ratio must be in [0, 1), got {overlap_ratio}"
        raise ValueError(msg)

    step = chunk_seconds * (1.0 - overlap_ratio)
    if step <= 0:
        msg = "overlap_ratio too high; computed non-positive step"
        raise ValueError(msg)

    chunks: list[ChunkSpec] = []
    current_start = 0.0
    chunk_idx = 0
    while current_start < total_seconds:
        current_end = min(current_start + chunk_seconds, total_seconds)
        chunks.append(
            ChunkSpec(
                index=chunk_idx,
                start_seconds=round(current_start, 6),
                end_seconds=round(current_end, 6),
                overlap_ratio=overlap_ratio,
            )
        )
        if current_end >= total_seconds:
            break
        current_start = current_start + step
        chunk_idx += 1
    return chunks


def gaussian_blend_weights(length: int, edge_portion: float = 0.25) -> list[float]:
    if length <= 0:
        msg = f"length must be positive, got {length}"
        raise ValueError(msg)
    if not 0.0 < edge_portion <= 0.5:
        msg = f"edge_portion must be in (0, 0.5], got {edge_portion}"
        raise ValueError(msg)

    center = (length - 1) / 2.0
    sigma = max(length * edge_portion, 1.0)
    values = [exp(-(((idx - center) ** 2) / (2.0 * sigma**2))) for idx in range(length)]
    values_sum = float(sum(values))
    if values_sum <= 0.0:
        msg = "invalid gaussian weights; sum is zero"
        raise RuntimeError(msg)
    return [value / values_sum for value in values]

