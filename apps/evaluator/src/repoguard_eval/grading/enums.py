"""Enumerations used by the grading engine."""

from enum import StrEnum


class ExecutionStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    ERROR = "error"


class ScoreDimension(StrEnum):
    ROOT_CAUSE = "root_cause"
    TECHNICAL_CORRECTNESS = "technical_correctness"
    EVIDENCE = "evidence"
    REGRESSION = "regression"
    PATCH_SCOPE = "patch_scope"


class FailureCategory(StrEnum):
    BUILD_FAILURE = "build_failure"
    FUNCTIONAL_FAILURE = "functional_failure"
    HIDDEN_TEST_FAILURE = "hidden_test_failure"
    REGRESSION_FAILURE = "regression_failure"
    LANGUAGE_VALIDATION_FAILURE = "language_validation_failure"
    PATCH_APPLICATION_FAILURE = "patch_application_failure"
    PATCH_SCOPE_VIOLATION = "patch_scope_violation"
    ROOT_CAUSE_MISMATCH = "root_cause_mismatch"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    EVALUATION_ERROR = "evaluation_error"