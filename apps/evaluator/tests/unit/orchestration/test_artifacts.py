from uuid import uuid4

import pytest

from repoguard_eval.orchestration.artifacts import ArtifactStore


@pytest.fixture
def store(tmp_path):
    return ArtifactStore(tmp_path)


def test_save_json(store):
    experiment_id = uuid4()

    path = store.save_json(
        experiment_id,
        "metadata.json",
        {"model": "test-model"},
    )

    assert path.exists()
    assert '"model": "test-model"' in path.read_text(encoding="utf-8")


def test_save_text_for_task(store):
    experiment_id = uuid4()

    path = store.save_text(
        experiment_id,
        "patch.diff",
        "diff --git a/main.py b/main.py",
        task_id="task-001",
    )

    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("diff --git")


def test_append_log(store):
    experiment_id = uuid4()

    path = store.append_log(
        experiment_id,
        "task_started",
        "Execution started",
        task_id="task-001",
    )

    content = path.read_text(encoding="utf-8")

    assert '"event": "task_started"' in content
    assert '"message": "Execution started"' in content


def test_reject_path_traversal(store):
    with pytest.raises(ValueError):
        store.save_text(
            uuid4(),
            "../outside.txt",
            "malicious",
        )


def test_reject_invalid_task_id(store):
    with pytest.raises(ValueError):
        store.task_dir(uuid4(), "../outside")


def test_atomic_write_replaces_existing_file(store):
    experiment_id = uuid4()

    store.save_text(experiment_id, "result.txt", "old")
    path = store.save_text(experiment_id, "result.txt", "new")

    assert path.read_text(encoding="utf-8") == "new"
    assert not path.with_name("result.txt.tmp").exists()