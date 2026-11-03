
"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from repoguard_eval.config.app import AppSettings, get_settings


def test_default_settings() -> None:
    """Application settings should provide valid defaults."""

    settings = AppSettings(_env_file=None)

    assert settings.app_name == "RepoGuard-Eval"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.log_level == "INFO"


def test_custom_settings() -> None:
    """Application settings should accept custom values."""

    settings = AppSettings(
        _env_file=None,
        app_name="Custom Evaluator",
        environment="testing",
        debug=True,
        log_level="DEBUG",
    )

    assert settings.app_name == "Custom Evaluator"
    assert settings.environment == "testing"
    assert settings.debug is True
    assert settings.log_level == "DEBUG"


def test_invalid_environment() -> None:
    """Invalid environment values should be rejected."""

    with pytest.raises(ValidationError):
        AppSettings(
            _env_file=None,
            environment="staging",
        )


def test_invalid_log_level() -> None:
    """Invalid logging levels should be rejected."""

    with pytest.raises(ValidationError):
        AppSettings(
            _env_file=None,
            log_level="TRACE",
        )


def test_empty_app_name() -> None:
    """Empty application names should be rejected."""

    with pytest.raises(ValidationError):
        AppSettings(
            _env_file=None,
            app_name="   ",
        )


def test_directory_paths_are_normalized() -> None:
    """Directory paths should support pathlib operations."""

    settings = AppSettings(
        _env_file=None,
        data_dir="custom-data",
    )

    assert settings.data_dir.name == "custom-data"
    assert settings.data_dir == settings.data_dir.expanduser()


def test_ensure_directories(tmp_path) -> None:
    """Application directories should be created explicitly."""

    settings = AppSettings(
        _env_file=None,
        data_dir=tmp_path / "data",
        tasks_dir=tmp_path / "data" / "tasks",
        experiments_dir=tmp_path / "data" / "experiments",
        config_dir=tmp_path / "config",
    )

    settings.ensure_directories()

    assert settings.data_dir.is_dir()
    assert settings.tasks_dir.is_dir()
    assert settings.experiments_dir.is_dir()
    assert settings.config_dir.is_dir()


def test_get_settings_returns_cached_instance(monkeypatch) -> None:
    """Settings should be cached between calls."""

    get_settings.cache_clear()

    monkeypatch.setenv("RG_APP_NAME", "Cached Test App")

    try:
        first = get_settings()
        second = get_settings()

        assert first is second
        assert first.app_name == "Cached Test App"
    finally:
        get_settings.cache_clear()
