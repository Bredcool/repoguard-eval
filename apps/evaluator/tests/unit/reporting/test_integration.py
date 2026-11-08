import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from repoguard_eval.reporting.integration import (
    build_task_reports,
    generate_experiment_report,
)


def make_task_result(task_id="task-001", artifacts=None):
    return SimpleNamespace(
        task_id=task_id,
        status="completed",
        duration_seconds=3.5,
        artifacts=artifacts or {},
    )


def make_summary(experiment_id, task_results):
    return SimpleNamespace(
        experiment_id=experiment_id,
        task_results=task_results,
        metadata={
            "started_at": "2026-11-08T09:00:00+00:00",
            "completed_at": "2026-11-08T09:00:05+00:00",
            "duration_seconds": 5.0,
            "max_concurrency": 2,
            "python_version": "3.13.5",
            "platform": "win32",
        },
    )


def test_build_task_reports_reads_response_and_artifact_refs(tmp_path):
    experiment_id = uuid4()
    task_id = "task-001"

    task_dir = tmp_path / "tasks" / task_id
    task_dir.mkdir(parents=True)

    response_path = task_dir / "response.json"
    response_path.write_text(
        json.dumps({
            "provider": "test-provider",
            "model": "test-model",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
                "cost_usd": 0.02,
            },
        }),
        encoding="utf-8",
    )

    result = make_task_result(
        task_id,
        {"response": str(response_path)},
    )

    reports = build_task_reports(
        experiment_id=experiment_id,
        task_results=[result],
        experiment_dir=tmp_path,
        task_loader=lambda _: SimpleNamespace(language="go"),
    )

    assert len(reports) == 1

    report = reports[0]

    assert report.experiment_id == experiment_id
    assert report.task_id == task_id
    assert report.status == "completed"
    assert report.provider == "test-provider"
    assert report.model == "test-model"
    assert report.language == "go"
    assert report.input_tokens == 100
    assert report.output_tokens == 50
    assert report.total_tokens == 150
    assert report.cost_usd == 0.02
    assert report.duration_seconds == 3.5
    assert str(response_path.resolve()) in report.artifact_refs


def test_build_task_reports_handles_missing_optional_artifacts(tmp_path):
    experiment_id = uuid4()

    reports = build_task_reports(
        experiment_id=experiment_id,
        task_results=[make_task_result()],
        experiment_dir=tmp_path,
    )

    assert len(reports) == 1
    assert reports[0].task_id == "task-001"
    assert reports[0].evaluation is None
    assert reports[0].provider is None
    assert reports[0].model is None
    assert reports[0].language is None
    assert reports[0].artifact_refs == ()


def test_generate_experiment_report_writes_complete_report(tmp_path):
    experiment_id = uuid4()
    task_id = "task-001"

    experiment_dir = tmp_path / str(experiment_id)
    task_dir = experiment_dir / "tasks" / task_id
    task_dir.mkdir(parents=True)

    response_path = task_dir / "response.json"
    response_path.write_text(
        json.dumps({
            "provider": "test-provider",
            "model": "test-model",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
                "cost_usd": 0.02,
            },
        }),
        encoding="utf-8",
    )

    raw_dir = experiment_dir / "raw"
    raw_dir.mkdir(parents=True)

    raw_path = raw_dir / "model_outputs.jsonl"
    raw_path.write_text(
        '{"task_id":"task-001","raw_response":{"output":"test"}}\n',
        encoding="utf-8",
    )

    orchestration_metadata = {
        "experiment_id": str(experiment_id),
        "max_concurrency": 2,
        "custom_metadata": "preserve-me",
    }

    root_metadata_path = experiment_dir / "metadata.json"
    root_metadata_path.write_text(
        json.dumps(orchestration_metadata),
        encoding="utf-8",
    )

    summary = make_summary(
        experiment_id,
        [make_task_result(
            task_id,
            {"response": str(response_path)},
        )],
    )

    paths = generate_experiment_report(
        artifact_dir=tmp_path,
        summary=summary,
        benchmark_name="RepoGuard-Eval",
        benchmark_version="1.0.0",
        model="test-model",
        provider="test-provider",
        task_loader=lambda _: SimpleNamespace(language="go"),
    )

    assert {
        "metadata",
        "task_results",
        "aggregate",
        "report",
        "failure_analysis",
        "raw_outputs",
    } == set(paths)

    assert all(path.is_file() for path in paths.values())

    assert paths["metadata"].parent.name == "reports"
    assert paths["raw_outputs"] == raw_path

    aggregate = json.loads(
        paths["aggregate"].read_text(encoding="utf-8")
    )

    assert aggregate["experiment_id"] == str(experiment_id)
    assert aggregate["total_tasks"] == 1
    assert aggregate["total_tokens"] == 150

    report_text = paths["report"].read_text(encoding="utf-8")

    assert "RepoGuard-Eval" in report_text
    assert "test-model" in report_text
    assert "task-001" in report_text

    persisted_metadata = json.loads(
        root_metadata_path.read_text(encoding="utf-8")
    )

    assert persisted_metadata == orchestration_metadata