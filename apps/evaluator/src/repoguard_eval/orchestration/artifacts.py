from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID


class ArtifactStore:
    """Manage experiment artifacts and execution logs."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def experiment_dir(self, experiment_id: UUID) -> Path:
        path = self.root / str(experiment_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def task_dir(self, experiment_id: UUID, task_id: str) -> Path:
        if not task_id or "/" in task_id or "\\" in task_id:
            raise ValueError("Invalid task ID")

        path = self.experiment_dir(experiment_id) / "tasks" / task_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_json(
        self,
        experiment_id: UUID,
        filename: str,
        data: Any,
        task_id: str | None = None,
    ) -> Path:
        directory = (
            self.task_dir(experiment_id, task_id)
            if task_id
            else self.experiment_dir(experiment_id)
        )

        path = self._safe_path(directory, filename)
        self._atomic_write(
            path,
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
        )
        return path

    def save_text(
        self,
        experiment_id: UUID,
        filename: str,
        content: str,
        task_id: str | None = None,
    ) -> Path:
        directory = (
            self.task_dir(experiment_id, task_id)
            if task_id
            else self.experiment_dir(experiment_id)
        )

        path = self._safe_path(directory, filename)
        self._atomic_write(path, content)
        return path

    def append_log(
        self,
        experiment_id: UUID,
        event: str,
        message: str,
        task_id: str | None = None,
    ) -> Path:
        directory = (
            self.task_dir(experiment_id, task_id)
            if task_id
            else self.experiment_dir(experiment_id)
        )

        path = directory / "logs.jsonl"

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "message": message,
        }

        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return path

    @staticmethod
    def _safe_path(directory: Path, filename: str) -> Path:
        candidate = (directory / filename).resolve()

        if not candidate.is_relative_to(directory.resolve()):
            raise ValueError("Artifact path escapes experiment directory")

        return candidate

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary = path.with_name(path.name + ".tmp")

        try:
            temporary.write_text(content, encoding="utf-8")
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()