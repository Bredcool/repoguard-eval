
from uuid import uuid4

import pytest

from repoguard_eval.grading.enums import (
    ExecutionStatus,
    FailureCategory,
    ScoreDimension,
)
from repoguard_eval.grading.failure_classifier import (
    FailureClassificationEngine,
)
from repoguard_eval.grading.schemas import (
    DimensionScore,
    ExecutionCheckEvidence,
    ExecutionEvidence,
)


@pytest.fixture
def classifier():
    return FailureClassificationEngine()


def check(
    name: str,
    status: ExecutionStatus,
    *,
    failed_tests: int = 0,
    evidence_refs: tuple[str, ...] = (),
) -> ExecutionCheckEvidence:
    return ExecutionCheckEvidence(
        name=name,
        status=status,
        total_tests=failed_tests,
        failed_tests=failed_tests,
        evidence_refs=evidence_refs,
    )


def test_classifies_build_failure(classifier):
    evidence = ExecutionEvidence(
        build=check("go build ./...", ExecutionStatus.FAILED),
    )

    result = classifier.classify(execution_evidence=evidence)

    assert len(result) == 1
    assert result[0].category == FailureCategory.BUILD_FAILURE


def test_classifies_functional_failure(classifier):
    evidence = ExecutionEvidence(
        functional=check(
            "functional tests",
            ExecutionStatus.FAILED,
            failed_tests=2,
            evidence_refs=("tests/test_api.py:12",),
        ),
    )

    result = classifier.classify(execution_evidence=evidence)

    assert result[0].category == FailureCategory.FUNCTIONAL_FAILURE
    assert result[0].evidence_refs == ("tests/test_api.py:12",)


def test_classifies_hidden_test_failure(classifier):
    evidence = ExecutionEvidence(
        hidden=check("hidden tests", ExecutionStatus.FAILED),
    )

    result = classifier.classify(execution_evidence=evidence)

    assert result[0].category == FailureCategory.HIDDEN_TEST_FAILURE


def test_classifies_regression_failure(classifier):
    evidence = ExecutionEvidence(
        regression=check("regression tests", ExecutionStatus.FAILED),
    )

    result = classifier.classify(execution_evidence=evidence)

    assert result[0].category == FailureCategory.REGRESSION_FAILURE


def test_classifies_language_validation_failure(classifier):
    evidence = ExecutionEvidence(
        language_checks=(
            check("go vet ./...", ExecutionStatus.FAILED),
        ),
    )

    result = classifier.classify(execution_evidence=evidence)

    assert result[0].category == FailureCategory.LANGUAGE_VALIDATION_FAILURE


def test_classifies_infrastructure_error_without_agent_failure(classifier):
    evidence = ExecutionEvidence(
        build=check("docker exec", ExecutionStatus.ERROR),
    )

    result = classifier.classify(execution_evidence=evidence)

    assert len(result) == 1
    assert result[0].category == FailureCategory.INFRASTRUCTURE_ERROR
    assert FailureCategory.BUILD_FAILURE not in {
        item.category for item in result
    }


@pytest.mark.parametrize(
    "status",
    [ExecutionStatus.SKIPPED, ExecutionStatus.BLOCKED],
)
def test_skipped_and_blocked_checks_are_not_failures(classifier, status):
    evidence = ExecutionEvidence(
        functional=check("functional tests", status),
    )

    result = classifier.classify(execution_evidence=evidence)

    assert result == ()


def test_classifies_multiple_failure_categories(classifier):
    evidence = ExecutionEvidence(
        build=check("build", ExecutionStatus.PASSED),
        functional=check("functional", ExecutionStatus.FAILED),
        hidden=check("hidden", ExecutionStatus.FAILED),
        regression=check("regression", ExecutionStatus.PASSED),
    )

    result = classifier.classify(execution_evidence=evidence)

    categories = {item.category for item in result}

    assert categories == {
        FailureCategory.FUNCTIONAL_FAILURE,
        FailureCategory.HIDDEN_TEST_FAILURE,
    }


def test_classifies_partial_root_cause_evidence_and_scope_scores(classifier):
    dimensions = (
        DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=10,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.EVIDENCE,
            score=12,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.PATCH_SCOPE,
            score=8,
            maximum_score=10,
        ),
    )

    result = classifier.classify(
        execution_evidence=ExecutionEvidence(),
        dimensions=dimensions,
    )

    assert {item.category for item in result} == {
        FailureCategory.ROOT_CAUSE_MISMATCH,
        FailureCategory.INSUFFICIENT_EVIDENCE,
        FailureCategory.PATCH_SCOPE_VIOLATION,
    }


def test_perfect_dimensions_do_not_create_failures(classifier):
    dimensions = (
        DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=20,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.EVIDENCE,
            score=20,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.PATCH_SCOPE,
            score=10,
            maximum_score=10,
        ),
    )

    result = classifier.classify(
        execution_evidence=ExecutionEvidence(),
        dimensions=dimensions,
    )

    assert result == ()


def test_infrastructure_errors_are_aggregated(classifier):
    evidence = ExecutionEvidence(
        build=check(
            "docker build",
            ExecutionStatus.ERROR,
            evidence_refs=("runtime/build.log",),
        ),
        functional=check(
            "docker exec",
            ExecutionStatus.ERROR,
            evidence_refs=("runtime/test.log",),
        ),
    )

    result = classifier.classify(execution_evidence=evidence)

    assert len(result) == 1
    assert result[0].category == FailureCategory.INFRASTRUCTURE_ERROR
    assert set(result[0].evidence_refs) == {
        "runtime/build.log",
        "runtime/test.log",
    }


def test_duplicate_categories_are_deduplicated(classifier):
    evidence = ExecutionEvidence(
        language_checks=(
            check("go vet", ExecutionStatus.FAILED),
            check("go build", ExecutionStatus.FAILED),
        ),
    )

    result = classifier.classify(execution_evidence=evidence)

    assert len(result) == 1
    assert result[0].category == FailureCategory.LANGUAGE_VALIDATION_FAILURE
    assert "go vet" in result[0].description
    assert "go build" in result[0].description
