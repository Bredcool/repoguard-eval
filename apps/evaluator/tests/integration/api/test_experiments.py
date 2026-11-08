def test_list_experiments(api_client, experiment_id):
    response = api_client.get("/experiments")

    assert response.status_code == 200

    payload = response.json()

    assert payload["pagination"]["total"] == 1
    assert payload["items"][0]["experiment_id"] == str(experiment_id)


def test_get_experiment(api_client, experiment_id):
    response = api_client.get(f"/experiments/{experiment_id}")

    assert response.status_code == 200

    payload = response.json()

    assert payload["experiment"]["experiment_id"] == str(experiment_id)
    assert payload["experiment"]["model"] == "test-model"
    assert payload["result"]["total_tasks"] == 2


def test_get_experiment_not_found(api_client):
    from uuid import uuid4

    response = api_client.get(f"/experiments/{uuid4()}")

    assert response.status_code == 404


def test_experiment_pagination(api_client):
    response = api_client.get("/experiments?limit=1&offset=0")

    assert response.status_code == 200
    assert response.json()["pagination"]["limit"] == 1


def test_experiment_filter_by_model(api_client):
    response = api_client.get("/experiments?model=test-model")

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1


def test_task_listing(api_client, experiment_id):
    response = api_client.get(
        f"/experiments/{experiment_id}/tasks"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["pagination"]["total"] == 2
    assert len(payload["items"]) == 2


def test_task_status_filter(api_client, experiment_id):
    response = api_client.get(
        f"/experiments/{experiment_id}/tasks?status=completed"
    )

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 2


def test_invalid_experiment_id_returns_422(api_client):
    response = api_client.get("/experiments/invalid-id")

    assert response.status_code == 422


def test_invalid_pagination_returns_422(api_client):
    response = api_client.get("/experiments?limit=0")

    assert response.status_code == 422