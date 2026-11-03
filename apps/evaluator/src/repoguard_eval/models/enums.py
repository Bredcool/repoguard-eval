"""Enumerations used by RepoGuard-Eval models."""

from enum import StrEnum


class TaskDifficulty(StrEnum):
    """Supported task difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TaskStatus(StrEnum):
    """Task lifecycle status."""

    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


class EvaluationType(StrEnum):
    """Supported evaluation categories."""

    BUG_FIX = "bug_fix"
    FEATURE_IMPLEMENTATION = "feature_implementation"
    REFACTORING = "refactoring"
    CODE_ANALYSIS = "code_analysis"