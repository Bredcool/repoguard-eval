"""Deterministic root cause assessment."""

from __future__ import annotations

import re
from collections.abc import Sequence

from pydantic import Field

from repoguard_eval.grading.enums import ScoreDimension
from repoguard_eval.grading.schemas import (
    CriterionScore,
    DimensionScore,
    GradingModel,
)


class RootCauseReference(GradingModel):
    """Trusted benchmark diagnosis used as grading ground truth."""

    defect_identification: list[str] = Field(min_length=1)
    underlying_mechanism: list[str] = Field(min_length=1)
    affected_component: list[str] = Field(min_length=1)
    expected_behavior: list[str] = Field(min_length=1)


class RootCauseAssessor:
    """Assess an agent diagnosis against trusted benchmark facts."""

    WEIGHTS = {
        "defect_identification": 8,
        "underlying_mechanism": 6,
        "affected_component": 4,
        "expected_behavior": 2,
    }

    LABELS = {
        "defect_identification": "Defect identification",
        "underlying_mechanism": "Underlying mechanism",
        "affected_component": "Affected component",
        "expected_behavior": "Expected behavior",
    }

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

    @classmethod
    def _match(
        cls,
        diagnosis: str,
        accepted_answers: Sequence[str],
    ) -> tuple[float, str | None]:
        """Return deterministic match confidence and matched reference."""

        normalized_diagnosis = cls._normalize(diagnosis)
        if not normalized_diagnosis:
            return 0.0, None

        best_ratio = 0.0
        best_match = None

        for answer in accepted_answers:
            normalized_answer = cls._normalize(answer)
            if not normalized_answer:
                continue

            if normalized_answer in normalized_diagnosis:
                return 1.0, answer

            expected_tokens = set(normalized_answer.split())
            actual_tokens = set(normalized_diagnosis.split())

            if len(expected_tokens) < 2:
                continue

            ratio = len(expected_tokens & actual_tokens) / len(expected_tokens)

            if ratio > best_ratio:
                best_ratio = ratio
                best_match = answer

        if best_ratio >= 0.75:
            return 0.5, best_match

        return 0.0, None

    def assess(
        self,
        reference: RootCauseReference,
        diagnosis: str,
        evidence_refs: Sequence[str] = (),
    ) -> DimensionScore:
        """Produce a weighted root cause dimension score."""

        criteria: list[CriterionScore] = []

        for field, maximum in self.WEIGHTS.items():
            accepted_answers = getattr(reference, field)
            confidence, matched = self._match(
                diagnosis,
                accepted_answers,
            )

            awarded = int(maximum * confidence)

            if confidence == 1.0:
                rationale = f"Diagnosis matches benchmark concept: {matched}."
            elif confidence == 0.5:
                rationale = (
                    f"Diagnosis partially matches benchmark concept: "
                    f"{matched}. The match requires further verification."
                )
            else:
                rationale = (
                    "Diagnosis does not identify the expected benchmark concept."
                )

            criteria.append(
                CriterionScore(
                    criterion_id=field,
                    awarded_points=awarded,
                    maximum_points=maximum,
                    rationale=rationale,
                    evidence_refs=evidence_refs,
                )
            )

        total = sum(item.awarded_points for item in criteria)
        maximum = sum(self.WEIGHTS.values())

        return DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=total,
            maximum_score=maximum,
            criteria=criteria,
        )