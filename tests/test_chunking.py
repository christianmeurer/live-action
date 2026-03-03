from __future__ import annotations

from live_action.pipeline.chunking import build_chunk_plan, gaussian_blend_weights


def test_build_chunk_plan_creates_overlap_sequence() -> None:
    chunks = build_chunk_plan(total_seconds=12.0, chunk_seconds=5.0, overlap_ratio=0.2)
    assert len(chunks) == 3
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 5.0
    assert chunks[1].start_seconds == 4.0
    assert chunks[1].end_seconds == 9.0
    assert chunks[2].start_seconds == 8.0
    assert chunks[2].end_seconds == 12.0


def test_gaussian_blend_weights_sum_to_one() -> None:
    weights = gaussian_blend_weights(length=101, edge_portion=0.25)
    assert len(weights) == 101
    assert abs(float(sum(weights)) - 1.0) < 1e-9

