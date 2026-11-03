"""Centralized application exceptions."""


class RepoGuardError(Exception):
    """Base exception for RepoGuard-Eval."""


class ConfigurationError(RepoGuardError):
    """Raised when application configuration is invalid."""


class TaskLoadError(RepoGuardError):
    """Raised when a task file cannot be loaded or parsed."""


class ExperimentError(RepoGuardError):
    """Raised when experiment operations fail."""