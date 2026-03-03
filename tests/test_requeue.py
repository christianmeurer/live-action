from __future__ import annotations

from live_action.eval.requeue import decide_requeue
from live_action.pipeline.config import PipelineRunConfig


def test_requeue_when_score_is_low_and_retries_available() -> None:
    config = PipelineRunConfig()
    decision = decide_requeue(
        score=0.2,
        threshold=0.9,
        attempt=0,
        run_config=config,
    )
    assert decision.should_requeue is True
    assert decision.next_denoise_strength < config.translation.denoise_strength


def test_no_requeue_when_max_retries_reached() -> None:
    config = PipelineRunConfig()
    decision = decide_requeue(
        score=0.2,
        threshold=0.9,
        attempt=config.translation.retry.max_retries,
        run_config=config,
    )
    assert decision.should_requeue is False

