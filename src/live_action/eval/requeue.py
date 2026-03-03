from __future__ import annotations

from dataclasses import dataclass

from live_action.pipeline.config import PipelineRunConfig


@dataclass(frozen=True)
class RequeueDecision:
    should_requeue: bool
    next_denoise_strength: float
    reason: str


def decide_requeue(
    *,
    score: float,
    threshold: float,
    attempt: int,
    run_config: PipelineRunConfig,
) -> RequeueDecision:
    if score >= threshold:
        return RequeueDecision(
            should_requeue=False,
            next_denoise_strength=run_config.translation.denoise_strength,
            reason="score_above_threshold",
        )

    if attempt >= run_config.translation.retry.max_retries:
        return RequeueDecision(
            should_requeue=False,
            next_denoise_strength=run_config.translation.denoise_strength,
            reason="max_retries_reached",
        )

    next_strength = max(0.0, run_config.translation.denoise_strength - run_config.translation.retry.denoise_backoff)
    return RequeueDecision(
        should_requeue=True,
        next_denoise_strength=next_strength,
        reason="score_below_threshold",
    )

