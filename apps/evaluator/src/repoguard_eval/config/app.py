
"""Application configuration for RepoGuard-Eval."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_prefix="RG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_assignment=True,
    )

    app_name: str = "RepoGuard-Eval"

    app_version: str = "0.1.0"

    environment: Literal[
        "development",
        "testing",
        "production",
    ] = "development"

    debug: bool = False

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    data_dir: Path = Field(
        default=Path("data"),
        description="Root directory for application data.",
    )

    tasks_dir: Path = Field(
        default=Path("data/tasks"),
        description="Directory containing benchmark tasks.",
    )

    experiments_dir: Path = Field(
        default=Path("data/experiments"),
        description="Directory containing experiment data.",
    )

    config_dir: Path = Field(
        default=Path("config"),
        description="Directory containing application configuration files.",
    )

    @field_validator("app_name", "app_version")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Reject empty application identifiers."""

        normalized = value.strip()

        if not normalized:
            raise ValueError("Value cannot be empty.")

        return normalized

    @field_validator(
        "data_dir",
        "tasks_dir",
        "experiments_dir",
        "config_dir",
    )
    @classmethod
    def validate_directory_paths(cls, value: Path) -> Path:
        """Normalize directory paths."""

        return value.expanduser()

    def ensure_directories(self) -> None:
        """Create application directories when required."""

        for directory in (
            self.data_dir,
            self.tasks_dir,
            self.experiments_dir,
            self.config_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return a cached application settings instance."""

    return AppSettings()
