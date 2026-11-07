
"""Deterministic evidence assessment against trusted repository context."""

from __future__ import annotations

import re
from collections.abc import Sequence

from pydantic import Field

from repoguard_eval.context.schemas import RepositoryContext
from repoguard_eval.grading.enums import ExecutionStatus, ScoreDimension
from repoguard_eval.grading.schemas import (
    CriterionScore,
    DimensionScore,
    ExecutionCheckEvidence,
    GradingModel,
)
from pydantic import model_validator


class EvidenceAnchor(GradingModel):
    """Trusted source location expected to support the benchmark diagnosis."""

    path: str = Field(min_length=1)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    keywords: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_range(self):
        if self.end_line < self.start_line:
            raise ValueError("end_line cannot be before start_line.")
        return self


class EvidenceAssessor:
    """Score evidence relevance, provenance, traceability and reproducibility."""

    WEIGHTS = {
        "relevant_evidence": 6,
        "evidence_provenance": 6,
        "claim_traceability": 5,
        "reproducibility": 3,
    }

    EVIDENCE_PATTERN = re.compile(
        r"^(?P<path>.+?):(?P<start>\d+)(?:-(?P<end>\d+))?$"
    )

    STOP_WORDS = {
        "the", "and", "for", "with", "from", "that", "this",
        "was", "were", "are", "is", "of", "to", "in", "on",
        "a", "an", "by", "it", "its",
    }

    @classmethod
    def _tokens(cls, value: str) -> set[str]:
        tokens = re.findall(r"[a-z0-9]+", value.casefold())
        return {token for token in tokens if token not in cls.STOP_WORDS}

    @classmethod
    def _parse_reference(
        cls,
        value: str,
    ) -> tuple[str, int, int] | None:
        match = cls.EVIDENCE_PATTERN.fullmatch(value.strip())
        if not match:
            return None

        path = match.group("path").replace("\\", "/")
        start = int(match.group("start"))
        end = int(match.group("end") or start)

        if start < 1 or end < start:
            return None

        return path, start, end

    @staticmethod
    def _find_file(repository: RepositoryContext, path: str):
        normalized = path.replace("\\", "/").lstrip("./")

        for file in repository.files:
            candidate = file.path.replace("\\", "/").lstrip("./")
            if candidate == normalized:
                return file

        return None

    @classmethod
    def _resolve(
        cls,
        repository: RepositoryContext,
        reference: str,
    ) -> tuple[str, int, int, str] | None:
        parsed = cls._parse_reference(reference)
        if parsed is None:
            return None

        path, start, end = parsed
        file = cls._find_file(repository, path)

        if file is None:
            return None

        lines = file.content.splitlines()

        if end > len(lines):
            return None

        snippet = "\n".join(lines[start - 1:end])
        return path, start, end, snippet

    @staticmethod
    def _overlaps(
        first_start: int,
        first_end: int,
        second_start: int,
        second_end: int,
    ) -> bool:
        return first_start <= second_end and second_start <= first_end

    @classmethod
    def _relevant_score(
        cls,
        anchors: Sequence[EvidenceAnchor],
        resolved: Sequence[tuple[str, int, int, str]],
    ) -> tuple[int, str]:
        if not anchors or not resolved:
            return 0, "No benchmark anchors or valid agent evidence were supplied."

        matched = 0

        for anchor in anchors:
            for path, start, end, snippet in resolved:
                if (
                    path == anchor.path.replace("\\", "/")
                    and cls._overlaps(
                        start,
                        end,
                        anchor.start_line,
                        anchor.end_line,
                    )
                ):
                    expected_tokens = cls._tokens(" ".join(anchor.keywords))
                    actual_tokens = cls._tokens(snippet)

                    if not expected_tokens or expected_tokens & actual_tokens:
                        matched += 1
                        break

        points = int(cls.WEIGHTS["relevant_evidence"] * matched / len(anchors))
        return points, f"{matched}/{len(anchors)} trusted evidence anchors matched."

    @classmethod
    def _provenance_score(
        cls,
        references: Sequence[str],
        resolved: Sequence[tuple[str, int, int, str]],
    ) -> tuple[int, str]:
        if not references:
            return 0, "No evidence references were supplied."

        valid = len(resolved)
        points = int(cls.WEIGHTS["evidence_provenance"] * valid / len(references))

        return points, f"{valid}/{len(references)} references resolve to repository files and valid lines."

    @classmethod
    def _traceability_score(
        cls,
        claims: Sequence[str],
        resolved: Sequence[tuple[str, int, int, str]],
    ) -> tuple[int, str]:
        if not claims or not resolved:
            return 0, "Claims or verifiable evidence are missing."

        snippets = [item[3] for item in resolved]
        supported = 0

        for claim in claims:
            claim_tokens = cls._tokens(claim)

            if not claim_tokens:
                continue

            for snippet in snippets:
                snippet_tokens = cls._tokens(snippet)

                if not snippet_tokens:
                    continue

                overlap = len(claim_tokens & snippet_tokens) / len(claim_tokens)

                if overlap >= 0.25:
                    supported += 1
                    break

        points = int(cls.WEIGHTS["claim_traceability"] * supported / len(claims))
        return points, f"{supported}/{len(claims)} claims have lexical support in referenced code."

    @classmethod
    def _reproducibility_score(
        cls,
        checks: Sequence[ExecutionCheckEvidence],
    ) -> tuple[int, str]:
        if not checks:
            return 0, "No reproduction checks were supplied."

        passed = sum(check.status == ExecutionStatus.PASSED for check in checks)
        points = int(cls.WEIGHTS["reproducibility"] * passed / len(checks))

        return points, f"{passed}/{len(checks)} reproduction checks passed."

    def assess(
        self,
        repository: RepositoryContext,
        evidence_refs: Sequence[str],
        anchors: Sequence[EvidenceAnchor],
        claims: Sequence[str] = (),
        reproduction_checks: Sequence[ExecutionCheckEvidence] = (),
    ) -> DimensionScore:
        """Assess agent evidence using trusted anchors and repository contents."""

        resolved = [
            item
            for reference in evidence_refs
            if (item := self._resolve(repository, reference)) is not None
        ]

        assessments = (
            (
                "relevant_evidence",
                self._relevant_score(anchors, resolved),
            ),
            (
                "evidence_provenance",
                self._provenance_score(evidence_refs, resolved),
            ),
            (
                "claim_traceability",
                self._traceability_score(claims, resolved),
            ),
            (
                "reproducibility",
                self._reproducibility_score(reproduction_checks),
            ),
        )

        criteria = [
            CriterionScore(
                criterion_id=criterion_id,
                awarded_points=points,
                maximum_points=self.WEIGHTS[criterion_id],
                rationale=rationale,
                evidence_refs=evidence_refs,
            )
            for criterion_id, (points, rationale) in assessments
        ]

        return DimensionScore(
            dimension=ScoreDimension.EVIDENCE,
            score=sum(item.awarded_points for item in criteria),
            maximum_score=sum(self.WEIGHTS.values()),
            criteria=criteria,
        )
