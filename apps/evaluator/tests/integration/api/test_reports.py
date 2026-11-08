def test_get_report(api_client, experiment_id):
    response = api_client.get(
        f"/experiments/{experiment_id}/report"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["experiment_id"] == str(experiment_id)
    assert payload["aggregate"]["total_tasks"] == 2
    assert payload["report_markdown"] == "# Integration Test Report"


def test_get_failures(api_client, experiment_id):
    response = api_client.get(
        f"/experiments/{experiment_id}/failures"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["failure_analysis"]["failure_breakdown"] == []


def test_compare_models(api_client, experiment_id):
    response = api_client.get("/models/compare")

    assert response.status_code == 200

    payload = response.json()

    assert payload["pagination"]["total"] == 1
    assert payload["items"][0]["experiment_id"] == str(experiment_id)
    assert payload["items"][0]["model"] == "test-model"


def test_compare_models_with_benchmark_filter(api_client):
    response = api_client.get(
        "/models/compare?benchmark=repoguard"
    )

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1