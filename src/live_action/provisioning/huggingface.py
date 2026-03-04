from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import snapshot_download

from live_action.config import AppConfig
from live_action.pipeline.config import PipelineRunConfig, ProviderName


@dataclass(frozen=True)
class ModelProvisionRecord:
    repo_id: str
    revision: str
    local_path: Path
    downloaded: bool


@dataclass(frozen=True)
class ProvisioningResult:
    records: list[ModelProvisionRecord]


def sync_huggingface_models(
    app_config: AppConfig,
    run_config: PipelineRunConfig | None = None,
    force: bool = False,
) -> ProvisioningResult:
    hf_cfg = app_config.provisioning.huggingface
    if not hf_cfg.enabled:
        return ProvisioningResult(records=[])

    selected_run_config = run_config or PipelineRunConfig()
    planned = _collect_required_models(selected_run_config)

    hf_cfg.cache_dir.mkdir(parents=True, exist_ok=True)
    hf_cfg.local_dir.mkdir(parents=True, exist_ok=True)

    records: list[ModelProvisionRecord] = []
    for repo_id, revision, relative_dir in planned:
        local_path = hf_cfg.local_dir / relative_dir
        local_path.parent.mkdir(parents=True, exist_ok=True)

        already_present = local_path.exists()
        if hf_cfg.skip_if_present and already_present and not force:
            records.append(
                ModelProvisionRecord(
                    repo_id=repo_id,
                    revision=revision,
                    local_path=local_path,
                    downloaded=False,
                )
            )
            continue

        snapshot_download(
            repo_id=repo_id,
            revision=revision,
            local_dir=local_path,
            cache_dir=hf_cfg.cache_dir,
            token=hf_cfg.token or None,
            local_dir_use_symlinks=False,
        )
        records.append(
            ModelProvisionRecord(
                repo_id=repo_id,
                revision=revision,
                local_path=local_path,
                downloaded=True,
            )
        )

    return ProvisioningResult(records=records)


def _collect_required_models(run_config: PipelineRunConfig) -> list[tuple[str, str, Path]]:
    planned: list[tuple[str, str, Path]] = []
    seen: set[tuple[str, str]] = set()

    for provider in _translation_providers(run_config):
        repo_id = run_config.translation.provider_model_map[provider]
        key = (repo_id, run_config.translation.model_revision)
        if key in seen:
            continue
        seen.add(key)
        planned.append(
            (
                repo_id,
                run_config.translation.model_revision,
                Path("translation") / _sanitize_model_dirname(repo_id),
            )
        )

    if run_config.upscale.enabled:
        key = (run_config.upscale.model_repo_id, run_config.upscale.model_revision)
        if key not in seen:
            seen.add(key)
            planned.append(
                (
                    run_config.upscale.model_repo_id,
                    run_config.upscale.model_revision,
                    Path("upscale") / _sanitize_model_dirname(run_config.upscale.model_repo_id),
                )
            )

    return planned


def _translation_providers(run_config: PipelineRunConfig) -> list[ProviderName]:
    providers: list[ProviderName] = [run_config.translation.primary_provider]
    if run_config.translation.fallback_provider is not None:
        providers.append(run_config.translation.fallback_provider)
    return providers


def _sanitize_model_dirname(repo_id: str) -> str:
    return repo_id.replace("/", "--")

