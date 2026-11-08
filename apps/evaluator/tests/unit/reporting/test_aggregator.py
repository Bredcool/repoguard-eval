from uuid import uuid4

from repoguard_eval.reporting.aggregator import ExperimentAggregator
from repoguard_eval.reporting.schemas import TaskReportResult


def test_aggregate_empty_results_preserves_unavailable_metrics():
    experiment_id = uuid4()

    result = ExperimentAggregator().aggregate(
        experiment_id=experiment_id,
        task_results=[],
    )

    assert result.total_tasks == 0
    assert result.score.average is None
    assert result.functional_pass_rate.rate is None
    assert result.build_success_rate.rate is None
    assert result.regression_pass_rate.rate is None
    assert result.total_duration_seconds is None
    assert result.total_cost_usd is None


def test_aggregate_task_metadata():
    experiment_id = uuid4()

    tasks = [
        TaskReportResult(
            experiment_id=experiment_id,
            task_id="task-001",
            status="completed",
            model="model-a",
            language="go",
            duration_seconds=10.0,
            cost_usd=0.02,
            total_tokens=100,
        ),
        TaskReportResult(
            experiment_id=experiment_id,
            task_id="task-002",
            status="failed",
            model="model-a",
            language="python",
            duration_seconds=20.0,
            cost_usd=0.03,
            total_tokens=200,
        ),
    ]

    result = ExperimentAggregator().aggregate(
        experiment_id=experiment_id,
        task_results=tasks,
    )

    assert result.total_tasks == 2
    assert result.completed_tasks == 1
    assert result.failed_tasks == 1
    assert result.total_duration_seconds == 30.0
    assert result.average_duration_seconds == 15.0
    assert result.total_cost_usd == 0.05
    assert result.total_tokens == 300
    assert len(result.language_breakdown) == 2
    assert result.model_breakdown[0].category == "model-a"