from pathlib import Path

import pytest

from repoguard_eval.api.app import create_app
from repoguard_eval.api.exceptions import ArtifactAccessError
from repoguard_eval.api.services.artifacts import ArtifactService


def test_artifact_endpoint_returns_file(api_client, experiment_id):
    response = api_client.get(
        f"/artifacts/{experiment_id}/reports/report.md"
    )

    assert response.status_code == 200
    assert response.text == "# Integration Test Report"


def test_artifact_endpoint_rejects_path_traversal(
    api_client,
    experiment_id,
):
    response = api_client.get(
        f"/artifacts/{experiment_id}/../../outside.txt"
    )

    assert response.status_code in (400, 403, 404)


def test_artifact_service_rejects_parent_directory_escape(
    tmp_path,
    experiment_id,
):
    root = tmp_path / "experiments"
    experiment_dir = root / str(experiment_id)
    experiment_dir.mkdir(parents=True)

    outside = tmp_path / "outside.txt"
    outside.write_text("private", encoding="utf-8")

    service = ArtifactService(root)

    with pytest.raises(ArtifactAccessError):
        service.read_artifact(
            f"{experiment_id}/../../outside.txt"
        )


def test_artifact_endpoint_returns_404_for_missing_file(
    api_client,
    experiment_id,
):
    response = api_client.get(
        f"/artifacts/{experiment_id}/reports/missing.json"
    )

    assert response.status_code == 404


def test_artifact_service_rejects_absolute_path(
    tmp_path,
    experiment_id,
):
    root = tmp_path / "experiments"
    (root / str(experiment_id)).mkdir(parents=True)

    service = ArtifactService(root)

    with pytest.raises(ArtifactAccessError):
        service.read_artifact(
            f"{experiment_id}/../../secret.txt"
        )


def test_symlink_cannot_escape_experiment_directory(
    tmp_path,
    experiment_id,
):
    root = tmp_path / "experiments"
    experiment_dir = root / str(experiment_id)
    experiment_dir.mkdir(parents=True)

    outside = tmp_path / "outside.txt"
    outside.write_text("private", encoding="utf-8")

    link = experiment_dir / "outside.txt"

    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable on this platform.")

    service = ArtifactService(root)

    with pytest.raises(ArtifactAccessError):
        service.read_artifact(
            f"{experiment_id}/outside.txt"
        )