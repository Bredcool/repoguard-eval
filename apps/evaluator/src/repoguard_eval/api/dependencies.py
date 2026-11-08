"""Dependency providers for the dashboard API."""

from functools import lru_cache

from repoguard_eval.api.services.artifacts import ArtifactService
from repoguard_eval.config.app import get_settings


@lru_cache(maxsize=1)
def get_artifact_service() -> ArtifactService:
    settings = get_settings()
    return ArtifactService(settings.experiments_dir)