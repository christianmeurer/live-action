from __future__ import annotations

import pytest

from live_action.pipeline.config import ExecutionMode, PipelineRunConfig, build_sota_2026_profile


def test_pipeline_config_defaults_to_local_execution_mode() -> None:
    cfg = PipelineRunConfig()
    assert cfg.translation.execution_mode == ExecutionMode.LOCAL
    assert cfg.upscale.execution_mode == ExecutionMode.LOCAL


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


def test_build_sota_2026_profile_uses_command_mode() -> None:
    cfg = build_sota_2026_profile()
    assert cfg.translation.execution_mode == ExecutionMode.COMMAND
    assert cfg.upscale.execution_mode == ExecutionMode.COMMAND
    assert cfg.translation.command_template is not None
    assert cfg.upscale.command_template is not None

