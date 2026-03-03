from __future__ import annotations

import pytest

from live_action.pipeline.config import ExecutionMode, PipelineRunConfig


def test_pipeline_config_requires_translation_command_template() -> None:
    with pytest.raises(ValueError):
        PipelineRunConfig.model_validate(
            {
                "translation": {
                    "execution_mode": ExecutionMode.COMMAND.value,
                }
            }
        )


def test_pipeline_config_accepts_command_templates() -> None:
    cfg = PipelineRunConfig.model_validate(
        {
            "translation": {
                "execution_mode": ExecutionMode.COMMAND.value,
                "command_template": ["python", "translate.py", "--in", "{input}", "--out", "{output}"],
            },
            "upscale": {
                "execution_mode": ExecutionMode.COMMAND.value,
                "command_template": ["python", "upscale.py", "--in", "{input}", "--out", "{output}"],
            },
        }
    )
    assert cfg.translation.command_template is not None
    assert cfg.upscale.command_template is not None

