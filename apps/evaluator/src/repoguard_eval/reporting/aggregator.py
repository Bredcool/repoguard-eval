"""Deterministic aggregation of experiment task results."""

from collections import Counter
from datetime import datetime, timezone
from statistics import mean, median

from repoguard_eval.grading.enums import ExecutionStatus
from repoguard_eval.reporting.schemas import (
    AggregateReport,
    CategorySummary,
    MetricSummary,
    RateSummary,
    TaskReportResult,
)


def _status_value(check) -> str | None:
    if check is None:
        return None

    status = check.status
    return status.value if hasattr(status, "value") else str(status)


def _rate(numerator: int, denominator: int) -> RateSummary:
    return RateSummary(
        numerator=numerator,
        denominator=denominator,
        rate=numerator / denominator if denominator else None,
    )


def _metric(values: list[float]) -> MetricSummary:
    if not values:
        return MetricSummary(count=0)

    return MetricSummary(
        count=len(values),
        average=mean(values),
        median=median(values),
        minimum=min(values),
        maximum=max(values),
    )


def _breakdown(values: list[str]) -> tuple[CategorySummary, ...]:
    counts = Counter(values)

    return tuple(
        CategorySummary(category=name, count=count)
        for name, count in sorted(counts.items())
    )


class ExperimentAggregator:
    """Build aggregate metrics exclusively from recorded task results."""

    def aggregate(
        self,
        *,
        experiment_id,
        task_results: tuple[TaskReportResult, ...] | list[TaskReportResult],
    ) -> AggregateReport:
        results = tuple(task_results)

        if any(item.experiment_id != experiment_id for item in results):
            raise ValueError("All task results must belong to the experiment.")

        scores = [
            item.evaluation.total_score
            for item in results
            if item.evaluation is not None
        ]

        functional_checks = [
            item.evaluation.execution_evidence.functional
            for item in results
            if item.evaluation is not None
            and item.evaluation.execution_evidence.functional is not None
        ]

        build_checks = [
            item.evaluation.execution_evidence.build
            for item in results
            if item.evaluation is not None
            and item.evaluation.execution_evidence.build is not None
        ]

        regression_checks = [
            item.evaluation.execution_evidence.regression
            for item in results
            if item.evaluation is not None
            and item.evaluation.execution_evidence.regression is not None
        ]

        functional_passes = sum(
            _status_value(check) == ExecutionStatus.PASSED.value
            for check in functional_checks
        )
        build_passes = sum(
            _status_value(check) == ExecutionStatus.PASSED.value
            for check in build_checks
        )
        regression_passes = sum(
            _status_value(check) == ExecutionStatus.PASSED.value
            for check in regression_checks
        )

        durations = [
            item.duration_seconds
            for item in results
            if item.duration_seconds is not None
        ]

        costs = [
            item.cost_usd
            for item in results
            if item.cost_usd is not None
        ]

        token_values = [
            item.total_tokens
            for item in results
            if item.total_tokens is not None
        ]

        failures = [
            classification.category.value
            for item in results
            if item.evaluation is not None
            for classification in item.evaluation.failure_classifications
        ]

        languages = [
            item.language
            for item in results
            if item.language is not None
        ]

        models = [
            item.model
            for item in results
            if item.model is not None
        ]

        completed = sum(
            item.status.lower() in {"completed", "success", "succeeded"}
            for item in results
        )
        failed = sum(
            item.status.lower() in {"failed", "error"}
            for item in results
        )

        return AggregateReport(
            experiment_id=experiment_id,
            generated_at=datetime.now(timezone.utc),
            total_tasks=len(results),
            completed_tasks=completed,
            failed_tasks=failed,
            score=_metric(scores),
            functional_pass_rate=_rate(
                functional_passes,
                len(functional_checks),
            ),
            build_success_rate=_rate(
                build_passes,
                len(build_checks),
            ),
            regression_pass_rate=_rate(
                regression_passes,
                len(regression_checks),
            ),
            total_duration_seconds=(
                sum(durations) if durations else None
            ),
            average_duration_seconds=(
                mean(durations) if durations else None
            ),
            total_cost_usd=sum(costs) if costs else None,
            total_tokens=sum(token_values) if token_values else None,
            language_breakdown=_breakdown(languages),
            failure_breakdown=_breakdown(failures),
            model_breakdown=_breakdown(models),
            task_results=results,
        )