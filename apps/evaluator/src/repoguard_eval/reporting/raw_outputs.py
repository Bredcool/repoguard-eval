"""Append-only storage for original provider responses."""

import json
import os
from pathlib import Path
from typing import Any

from repoguard_eval.providers.schemas.response import ProviderResponse


class RawOutputStore:
    """Persist original provider responses as immutable JSONL records."""

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, experiment_id) -> Path:
        return (
            self.directory
            / str(experiment_id)
            / "raw"
            / "model_outputs.jsonl"
        )

    def append(self, response) -> Path:
        path = self._path(response.experiment_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        record: dict[str, Any] = {
            "experiment_id": str(response.experiment_id),
            "task_id": response.task_id,
            "provider": response.provider,
            "model": response.model,
            "response_id": response.response_id,
            "finish_reason": response.finish_reason,
            "diagnosis": (
                response.diagnosis.model_dump(mode="json")
                if response.diagnosis is not None
                else None
            ),
            "patch": (
                response.patch.model_dump(mode="json")
                if response.patch is not None
                else None
            ),
            "usage": (
                response.usage.model_dump(mode="json")
                if response.usage is not None
                else None
            ),
            "raw_response": response.raw_response,
        }

        payload = (
            json.dumps(
                record,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )
            + "\n"
        ).encode("utf-8")

        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )

        try:
            with os.fdopen(descriptor, "ab") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
        except Exception:
            raise

        return path

    def read(self, experiment_id) -> list[dict[str, Any]]:
        path = self._path(experiment_id)

        if not path.exists():
            return []

        records = []

        with path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue

                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSONL record at line {line_number}: {exc}"
                    ) from exc

        return records