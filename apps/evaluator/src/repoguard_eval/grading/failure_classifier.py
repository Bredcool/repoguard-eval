
"""Deterministic failure classification from grading evidence."""

from collections.abc import Sequence

from repoguard_eval.grading.enums import (
    ExecutionStatus,
    FailureCategory,
    ScoreDimension,
)
from repoguard_eval.grading.schemas import (
    DimensionScore,
    ExecutionCheckEvidence,
    ExecutionEvidence,
    FailureClassification,
)


class FailureClassificationEngine:
    """Classifies observed failures without treating unavailable checks as agent failures."""

    _EXECUTION_CATEGORIES = {
        "build": FailureCategory.BUILD_FAILURE,
        "functional": FailureCategory.FUNCTIONAL_FAILURE,
        "hidden": FailureCategory.HIDDEN_TEST_FAILURE,
        "regression": FailureCategory.REGRESSION_FAILURE,
    }

    def classify(
        self,
        *,
        execution_evidence: ExecutionEvidence,
        dimensions: Sequence[DimensionScore] = (),
    ) -> tuple[FailureClassification, ...]:
        """Return deterministic, deduplicated failure classifications."""

        failures: list[FailureClassification] = []

        for stage, category in self._EXECUTION_CATEGORIES.items():
            check = getattr(execution_evidence, stage)
            if check is not None:
                failure = self._classify_check(check, category)
                if failure is not None:
                    failures.append(failure)

        language_failures = [
            check
            for check in execution_evidence.language_checks
            if check.status == ExecutionStatus.FAILED
        ]
        if language_failures:
            failures.append(
                self._classification(
                    category=FailureCategory.LANGUAGE_VALIDATION_FAILURE,
                    description=self._describe_checks(
                        "Language validation failed",
                        language_failures,
                    ),
                    checks=language_failures,
                )
            )

        infrastructure_errors = [
            check
            for check in self._all_checks(execution_evidence)
            if check.status == ExecutionStatus.ERROR
        ]
        if infrastructure_errors:
            failures.append(
                self._classification(
                    category=FailureCategory.INFRASTRUCTURE_ERROR,
                    description=self._describe_checks(
                        "Execution infrastructure error",
                        infrastructure_errors,
                    ),
                    checks=infrastructure_errors,
                )
            )

        failures.extend(self._classify_dimensions(dimensions))

        return self._deduplicate(failures)

    def _classify_check(
        self,
        check: ExecutionCheckEvidence,
        category: FailureCategory,
    ) -> FailureClassification | None:
        if check.status != ExecutionStatus.FAILED:
            return None

        return self._classification(
            category=category,
            description=(
                f"{check.name} failed"
                + (
                    f" with {check.failed_tests} failed test(s)"
                    if check.failed_tests
                    else ""
                )
            ),
            checks=(check,),
        )

    def _classify_dimensions(
        self,
        dimensions: Sequence[DimensionScore],
    ) -> list[FailureClassification]:
        category_by_dimension = {
            ScoreDimension.ROOT_CAUSE: FailureCategory.ROOT_CAUSE_MISMATCH,
            ScoreDimension.EVIDENCE: FailureCategory.INSUFFICIENT_EVIDENCE,
            ScoreDimension.PATCH_SCOPE: FailureCategory.PATCH_SCOPE_VIOLATION,
        }

        failures = []

        for dimension in dimensions:
            category = category_by_dimension.get(dimension.dimension)

            if category is None or dimension.score >= dimension.maximum_score:
                continue

            failures.append(
                FailureClassification(
                    category=category,
                    description=(
                        f"{dimension.dimension.value} assessment scored "
                        f"{dimension.score}/{dimension.maximum_score}."
                    ),
                    evidence_refs=tuple(
                        dict.fromkeys(
                            ref
                            for criterion in dimension.criteria
                            for ref in criterion.evidence_refs
                        )
                    ),
                )
            )

        return failures

    @staticmethod
    def _all_checks(
        evidence: ExecutionEvidence,
    ) -> tuple[ExecutionCheckEvidence, ...]:
        checks = [
            evidence.build,
            evidence.functional,
            evidence.hidden,
            evidence.regression,
        ]
        checks.extend(evidence.language_checks)

        return tuple(check for check in checks if check is not None)

    @staticmethod
    def _describe_checks(
        prefix: str,
        checks: Sequence[ExecutionCheckEvidence],
    ) -> str:
        names = ", ".join(check.name for check in checks)
        return f"{prefix}: {names}."

    @staticmethod
    def _classification(
        *,
        category: FailureCategory,
        description: str,
        checks: Sequence[ExecutionCheckEvidence],
    ) -> FailureClassification:
        return FailureClassification(
            category=category,
            description=description,
            evidence_refs=tuple(
                dict.fromkeys(
                    ref
                    for check in checks
                    for ref in check.evidence_refs
                )
            ),
        )

    @staticmethod
    def _deduplicate(
        failures: Sequence[FailureClassification],
    ) -> tuple[FailureClassification, ...]:
        unique: dict[FailureCategory, FailureClassification] = {}

        for failure in failures:
            existing = unique.get(failure.category)

            if existing is None:
                unique[failure.category] = failure
                continue

            unique[failure.category] = FailureClassification(
                category=failure.category,
                description=(
                    f"{existing.description} {failure.description}"
                ),
                evidence_refs=tuple(
                    dict.fromkeys(
                        existing.evidence_refs + failure.evidence_refs
                    )
                ),
            )

        return tuple(unique.values())
