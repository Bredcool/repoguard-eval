"""Data models for repository context preparation."""

from pydantic import BaseModel, ConfigDict, Field


class RepositoryFile(BaseModel):
    """A single text file included in repository context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    content: str
    size_bytes: int = Field(ge=0)


class RepositoryContext(BaseModel):
    """Collection of files prepared for an AI agent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    files: tuple[RepositoryFile, ...] = ()
    total_bytes: int = Field(default=0, ge=0)
    skipped_files: int = Field(default=0, ge=0)

    @property
    def file_count(self) -> int:
        """Return the number of included files."""
        return len(self.files)