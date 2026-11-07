"""Tests for grading rubric."""

from repoguard_eval.grading.enums import ScoreDimension
from repoguard_eval.grading.rubric import (
    EVIDENCE_CRITERIA,
    PATCH_SCOPE_CRITERIA,
    REGRESSION_CRITERIA,
    ROOT_CAUSE_CRITERIA,
    RUBRIC_WEIGHTS,
    TECHNICAL_CORRECTNESS_CRITERIA,
    validate_rubric,
)


def test_rubric_weights_total_100():
    assert sum(RUBRIC_WEIGHTS.values()) == 100


def test_rubric_contains_all_dimensions():
    assert set(RUBRIC_WEIGHTS) == set(ScoreDimension)


def test_each_criterion_group_matches_dimension_weight():
    assert sum(ROOT_CAUSE_CRITERIA.values()) == 20
    assert sum(TECHNICAL_CORRECTNESS_CRITERIA.values()) == 30
    assert sum(EVIDENCE_CRITERIA.values()) == 20
    assert sum(REGRESSION_CRITERIA.values()) == 20
    assert sum(PATCH_SCOPE_CRITERIA.values()) == 10


def test_validate_rubric():
    validate_rubric()