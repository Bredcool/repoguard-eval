
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from repoguard_eval.providers.schemas.response import (
    Diagnosis,
    ProviderResponse,
    TokenUsage,
)
from repoguard_eval.reporting.aggregator import ExperimentAggregator
from repoguard_eval.reporting.artifacts import ReportArtifactWriter
from repoguard_eval.reporting.markdown import render_experiment_report
from repoguard_eval.reporting.raw_outputs import RawOutputStore
from repoguard_eval.reporting.schemas import (
    ExperimentReportMetadata,
    TaskReportResult,
)


def build_metadata(experiment_id, task_ids=("task-001",)):
    return ExperimentReportMetadata(
        experiment_id=experiment_id,
        benchmark_name="RepoGuard-Eval",
        benchmark_version="1.0.0",
        model="test-model",
        provider="test-provider",
        task_ids=task_ids,
        generated_at=datetime.now(timezone.utc),
        configuration={"max_concurrency": 2},
    )


def build_task(experiment_id, task_id="task-001"):
    return TaskReportResult(
        experiment_id=experiment_id,
        task_id=task_id,
        status="completed",
        provider="test-provider",
        model="test-model",
        language="go",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        duration_seconds=2.5,
        cost_usd=0.01,
        artifact_refs=("tasks/task-001/response.json",),
    )


def build_response(experiment_id, task_id="task-001"):
    return ProviderResponse(
        experiment_id=experiment_id,
        task_id=task_id,
        provider="test-provider",
        model="test-model",
        diagnosis=Diagnosis(
            root_cause="Missing validation",
            evidence=["validation.go:12"],
        ),
        usage=TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        ),
        response_id="response-001",
        finish_reason="stop",
        raw_response={"output": "test response"},
    )


def test_artifact_writer_persists_all_report_artifacts(tmp_path):
    experiment_id = uuid4()
    metadata = build_metadata(experiment_id)
    task = build_task(experiment_id)

    aggregate = ExperimentAggregator().aggregate(
        experiment_id=experiment_id,
        task_results=[task],
    )

    paths = ReportArtifactWriter(tmp_path).write(
        metadata=metadata,
        aggregate=aggregate,
    )

    assert set(paths) == {
        "metadata",
        "task_results",
        "aggregate",
        "report",
        "failure_analysis",
    }

    assert all(path.is_file() for path in paths.values())

    assert paths["metadata"].name == "metadata.json"
    assert paths["metadata"].parent.name == "reports"

    assert json.loads(paths["task_results"].read_text()) != []
    assert json.loads(paths["aggregate"].read_text())["total_tasks"] == 1

    assert "# Experiment Report: RepoGuard-Eval" in (
        paths["report"].read_text(encoding="utf-8")
    )


def test_artifact_writer_preserves_orchestration_metadata(tmp_path):
    experiment_id = uuid4()
    experiment_dir = tmp_path / str(experiment_id)
    experiment_dir.mkdir(parents=True)

    orchestration_metadata = {
        "experiment_id": str(experiment_id),
        "started_at": "2026-11-08T09:00:00+00:00",
        "max_concurrency": 4,
    }

    root_metadata = experiment_dir / "metadata.json"
    root_metadata.write_text(
        json.dumps(orchestration_metadata),
        encoding="utf-8",
    )

    metadata = build_metadata(experiment_id)
    task = build_task(experiment_id)

    aggregate = ExperimentAggregator().aggregate(
        experiment_id=experiment_id,
        task_results=[task],
    )

    ReportArtifactWriter(tmp_path).write(
        metadata=metadata,
        aggregate=aggregate,
    )

    persisted = json.loads(root_metadata.read_text(encoding="utf-8"))

    assert persisted == orchestration_metadata


def test_artifact_writer_rejects_mismatched_experiment_ids(tmp_path):
    metadata = build_metadata(uuid4())
    aggregate = ExperimentAggregator().aggregate(
        experiment_id=uuid4(),
        task_results=[],
    )

    with pytest.raises(ValueError, match="Experiment IDs do not match"):
        ReportArtifactWriter(tmp_path).write(
            metadata=metadata,
            aggregate=aggregate,
        )


def test_raw_output_store_appends_and_reads_records(tmp_path):
    experiment_id = uuid4()
    store = RawOutputStore(tmp_path)

    first = build_response(experiment_id, "task-001")
    second = build_response(experiment_id, "task-002")

    first_path = store.append(first)
    second_path = store.append(second)

    assert first_path == second_path
    assert first_path.is_file()

    records = store.read(experiment_id)

    assert len(records) == 2
    assert records[0]["task_id"] == "task-001"
    assert records[1]["task_id"] == "task-002"
    assert records[0]["experiment_id"] == str(experiment_id)
    assert records[0]["raw_response"] == {"output": "test response"}
    assert records[0]["usage"]["total_tokens"] == 150


def test_raw_output_store_returns_empty_for_missing_experiment(tmp_path):
    store = RawOutputStore(tmp_path)

    assert store.read(uuid4()) == []


def test_raw_output_store_rejects_corrupted_jsonl(tmp_path):
    experiment_id = uuid4()
    store = RawOutputStore(tmp_path)

    path = store.append(build_response(experiment_id))
    path.write_text(
        '{"task_id": "task-001"}\ninvalid-json\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid JSONL record"):
        store.read(experiment_id)


def test_markdown_renderer_includes_experiment_metrics():
    experiment_id = uuid4()
    metadata = build_metadata(experiment_id)
    task = build_task(experiment_id)

    aggregate = ExperimentAggregator().aggregate(
        experiment_id=experiment_id,
        task_results=[task],
    )

    report = render_experiment_report(metadata, aggregate)

    assert "# Experiment Report: RepoGuard-Eval" in report
    assert "## Experiment Metadata" in report
    assert "## Experiment Summary" in report
    assert "## Task Results" in report
    assert "## Failure Analysis" in report
    assert "## Reproducibility" in report
    assert "task-001" in report
    assert "test-model" in report


def test_markdown_renderer_rejects_mismatched_experiment_ids():
    metadata = build_metadata(uuid4())
    aggregate = ExperimentAggregator().aggregate(
        experiment_id=uuid4(),
        task_results=[],
    )

    with pytest.raises(ValueError, match="experiment IDs"):
        render_experiment_report(metadata, aggregate)
