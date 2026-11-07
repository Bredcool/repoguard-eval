"""Grading and scoring components."""

from repoguard_eval.grading.enums import (
    ExecutionStatus,
    FailureCategory,
    ScoreDimension,
)
from repoguard_eval.grading.schemas import (
    CriterionScore,
    DimensionScore,
    EvaluationResult,
    ExecutionCheckEvidence,
    ExecutionEvidence,
    FailureClassification,
)
from repoguard_eval.grading.evidence import EvidenceAnchor, EvidenceAssessor
from repoguard_eval.grading.patch_scope import (
    PatchScopeAssessor,
    PatchScopeReference,
)
from repoguard_eval.grading.scoring_engine import WeightedScoringEngine
from repoguard_eval.grading.failure_classifier import (
    FailureClassificationEngine,
)
from repoguard_eval.grading.scoring_boundaries import (
    InfrastructureEvaluationError,
    validate_execution_boundaries,
)

__all__ = [
    "CriterionScore",
    "DimensionScore",
    "EvaluationResult",
    "ExecutionCheckEvidence",
    "ExecutionEvidence",
    "ExecutionStatus",
    "FailureCategory",
    "FailureClassification",
    "ScoreDimension",
    "EvidenceAnchor",
    "EvidenceAssessor",
    "PatchScopeAssessor",
    "PatchScopeReference",
    "WeightedScoringEngine",
    "FailureClassificationEngine",
    "InfrastructureEvaluationError",
    "validate_execution_boundaries",
]