from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from repoguard_eval.reporting.schemas import (
    AggregateReport,
    MetricSummary,
    RateSummary,
    TaskReportResult,
)


def test_rate_summary_with_no_observations():
    result = RateSummary(
        numerator=0,
        denominator=0,
        rate=None,
    )

    assert result.rate is None


def test_rate_summary_calculates_expected_rate():
    result = RateSummary(
        numerator=3,
        denominator=4,
        rate=0.75,
    )

    assert result.rate == 0.75


def test_rate_summary_rejects_inconsistent_rate():
    with pytest.raises(ValidationError):
        RateSummary(
            numerator=3,
            denominator=4,
            rate=0.5,
        )


def test_metric_summary_allows_unavailable_values():
    result = MetricSummary(count=0)

    assert result.average is None
    assert result.median is None


def test_aggregate_rejects_mismatched_experiment():
    experiment_id = uuid4()

    task_result = TaskReportResult(
        experiment_id=uuid4(),
        task_id="task-001",
        status="completed",
    )

    with pytest.raises(ValidationError):
        AggregateReport(
            experiment_id=experiment_id,
            generated_at=datetime.now(timezone.utc),
            total_tasks=1,
            completed_tasks=1,
            failed_tasks=0,
            score=MetricSummary(count=0),
            functional_pass_rate=RateSummary(
                numerator=0,
                denominator=0,
            ),
            build_success_rate=RateSummary(
                numerator=0,
                denominator=0,
            ),
            regression_pass_rate=RateSummary(
                numerator=0,
                denominator=0,
            ),
            task_results=(task_result,),
        )