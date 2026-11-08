import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from repoguard_eval.api.app import create_app


@pytest.fixture
def experiment_id():
    return uuid4()


@pytest.fixture
def api_client(tmp_path, experiment_id):
    root = tmp_path / "experiments"
    experiment_dir = root / str(experiment_id)

    reports_dir = experiment_dir / "reports"
    results_dir = experiment_dir / "results"

    reports_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)

    definition = {
        "id": str(experiment_id),
        "name": "API Integration Test",
        "status": "completed",
        "metadata": {
            "model": "test-model",
            "benchmark_name": "repoguard",
        },
    }

    metadata = {
        "experiment_id": str(experiment_id),
        "model": "test-model",
        "provider": "test-provider",
        "benchmark": "repoguard",
        "benchmark_version": "1.0.0",
        "task_ids": ["task-001", "task-002"],
    }

    result = {
        "experiment_id": str(experiment_id),
        "status": "completed",
        "total_tasks": 2,
        "completed_tasks": 2,
        "failed_tasks": 0,
        "task_results": [
            {
                "task_id": "task-001",
                "status": "completed",
                "score": 90,
            },
            {
                "task_id": "task-002",
                "status": "completed",
                "score": 85,
            },
        ],
    }

    aggregate = {
        "experiment_id": str(experiment_id),
        "total_tasks": 2,
        "completed_tasks": 2,
        "failed_tasks": 0,
        "score": {
            "count": 2,
            "average": 87.5,
        },
        "functional_pass_rate": {
            "numerator": 2,
            "denominator": 2,
            "rate": 1.0,
        },
        "build_success_rate": {
            "numerator": 2,
            "denominator": 2,
            "rate": 1.0,
        },
        "regression_pass_rate": {
            "numerator": 2,
            "denominator": 2,
            "rate": 1.0,
        },
    }

    failure_analysis = {
        "experiment_id": str(experiment_id),
        "failure_breakdown": [],
        "task_failures": [],
    }

    (root).mkdir(parents=True, exist_ok=True)

    (root / f"{experiment_id}.json").write_text(
        json.dumps(definition),
        encoding="utf-8",
    )

    (experiment_dir / "metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    (experiment_dir / "result.json").write_text(
        json.dumps(result),
        encoding="utf-8",
    )

    (results_dir / "task_results.json").write_text(
        json.dumps(result["task_results"]),
        encoding="utf-8",
    )

    (results_dir / "aggregate.json").write_text(
        json.dumps(aggregate),
        encoding="utf-8",
    )

    (reports_dir / "metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    (reports_dir / "report.md").write_text(
        "# Integration Test Report",
        encoding="utf-8",
    )

    (reports_dir / "failure_analysis.json").write_text(
        json.dumps(failure_analysis),
        encoding="utf-8",
    )

    client = TestClient(create_app(root))

    yield client

    client.close()