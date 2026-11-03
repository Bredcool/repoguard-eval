"""Tests for structured logging."""

import json
import logging

import pytest

from repoguard_eval.logging import (
    JsonFormatter,
    configure_logging,
    get_logger,
)


def test_json_formatter() -> None:
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="repoguard.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=None,
        exc_info=None,
    )

    output = json.loads(formatter.format(record))

    assert output["level"] == "INFO"
    assert output["logger"] == "repoguard.test"
    assert output["message"] == "Test message"
    assert "timestamp" in output


def test_json_formatter_with_exception() -> None:
    formatter = JsonFormatter()

    try:
        raise ValueError("Test exception")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="repoguard.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=20,
            msg="Operation failed",
            args=None,
            exc_info=sys.exc_info(),
        )

    output = json.loads(formatter.format(record))

    assert output["level"] == "ERROR"
    assert "exception" in output
    assert "Test exception" in output["exception"]


def test_configure_logging_json(monkeypatch) -> None:
    monkeypatch.setattr(
        "repoguard_eval.logging.logger.get_settings",
        lambda: type("Settings", (), {"log_level": "DEBUG"})(),
    )

    configure_logging()

    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert isinstance(
        root_logger.handlers[0].formatter,
        JsonFormatter,
    )


def test_configure_logging_text(monkeypatch) -> None:
    monkeypatch.setattr(
        "repoguard_eval.logging.logger.get_settings",
        lambda: type("Settings", (), {"log_level": "INFO"})(),
    )

    configure_logging(json_format=False)

    root_logger = logging.getLogger()

    assert root_logger.level == logging.INFO
    assert not isinstance(
        root_logger.handlers[0].formatter,
        JsonFormatter,
    )


def test_configure_logging_invalid_level(monkeypatch) -> None:
    monkeypatch.setattr(
        "repoguard_eval.logging.logger.get_settings",
        lambda: type("Settings", (), {"log_level": "INFO"})(),
    )

    with pytest.raises(ValueError, match="Invalid log level"):
        configure_logging(level="INVALID")


def test_get_logger() -> None:
    logger = get_logger("repoguard.test")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "repoguard.test"