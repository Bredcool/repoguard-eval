
"""Patch data models for repository modifications."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Patch:
    """Represent an untrusted unified diff patch."""

    content: str


@dataclass(frozen=True, slots=True)
class PatchFile:
    """Represent one file targeted by a patch."""

    old_path: str | None
    new_path: str | None


@dataclass(frozen=True, slots=True)
class ValidatedPatch:
    """Represent a patch that has passed structural and security validation."""

    content: str
    files: tuple[PatchFile, ...]
    total_bytes: int
