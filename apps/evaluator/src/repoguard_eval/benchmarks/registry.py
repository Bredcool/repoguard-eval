"""Load and validate the benchmark manifest."""

import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from repoguard_eval.exceptions import TaskLoadError


class BenchmarkValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str
    baseline: str
    test_count: int


class BenchmarkEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    pack: str
    language: str
    category: str
    difficulty: str
    version: str
    status: str
    validation: BenchmarkValidation | None = None


class BenchmarkManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    description: str
    tasks: list[BenchmarkEntry]


class BenchmarkRegistry:
    """Resolve benchmark task locations from a manifest."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve(strict=True)
        self.manifest_path = self.root / "manifest.json"

    def load(self) -> BenchmarkManifest:
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            manifest = BenchmarkManifest.model_validate(data)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise TaskLoadError(f"Unable to load benchmark manifest: {exc}") from exc

        ids = [task.id for task in manifest.tasks]
        if len(ids) != len(set(ids)):
            raise TaskLoadError("Duplicate benchmark task IDs.")

        for entry in manifest.tasks:
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", entry.id):
                raise TaskLoadError(f"Invalid benchmark task ID: {entry.id}")

            pack = Path(entry.pack)
            if pack.is_absolute() or ".." in pack.parts:
                raise TaskLoadError(f"Invalid benchmark pack path: {entry.pack}")

        return manifest

    def get(self, task_id: str) -> BenchmarkEntry:
        manifest = self.load()

        for entry in manifest.tasks:
            if entry.id == task_id:
                return entry

        raise TaskLoadError(f"Benchmark task not found: {task_id}")

    def task_directory(self, entry: BenchmarkEntry) -> Path:
        candidate = self.root / "packs" / entry.pack / entry.id

        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(self.root)
        except (OSError, ValueError) as exc:
            raise TaskLoadError(
                f"Invalid benchmark task directory: {candidate}"
            ) from exc

        if not resolved.is_dir():
            raise TaskLoadError("Benchmark task path is not a directory.")

        return resolved
