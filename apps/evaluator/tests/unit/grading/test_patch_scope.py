from pathlib import Path
from types import SimpleNamespace

import pytest

from repoguard_eval.execution.patch_applier import PatchApplicationResult
from repoguard_eval.execution.patches import PatchFile, ValidatedPatch
from repoguard_eval.grading.enums import ScoreDimension
from repoguard_eval.grading.patch_scope import (
    PatchScopeAssessor,
    PatchScopeReference,
)


def make_patch(*paths):
    return ValidatedPatch(
        content="patch",
        files=tuple(
            PatchFile(old_path=path, new_path=path)
            for path in paths
        ),
        total_bytes=5,
    )


def make_application(*paths):
    return PatchApplicationResult(
        repository_path=Path("repository"),
        changed_files=tuple(paths),
        snapshot=SimpleNamespace(),
    )


@pytest.fixture
def assessor():
    return PatchScopeAssessor()


def test_perfect_patch_scope_score(assessor):
    reference = PatchScopeReference(
        expected_files=("src/main.py", "tests/test_main.py")
    )
    patch = make_patch("src/main.py", "tests/test_main.py")
    application = make_application("src/main.py", "tests/test_main.py")

    result = assessor.assess(reference, patch, application)

    assert result.dimension == ScoreDimension.PATCH_SCOPE
    assert result.score == 10
    assert result.maximum_score == 10


def test_relevant_changes_are_scored_proportionally(assessor):
    reference = PatchScopeReference(
        expected_files=("src/main.py", "tests/test_main.py")
    )
    patch = make_patch("src/main.py")
    application = make_application("src/main.py")

    result = assessor.assess(reference, patch, application)

    assert result.criteria[0].awarded_points == 2


def test_unrelated_changes_lose_scope_points(assessor):
    reference = PatchScopeReference(
        expected_files=("src/main.py",)
    )
    patch = make_patch("src/main.py", "README.md")
    application = make_application("src/main.py", "README.md")

    result = assessor.assess(reference, patch, application)

    assert result.criteria[1].awarded_points == 0


def test_forbidden_changes_lose_scope_points(assessor):
    reference = PatchScopeReference(
        expected_files=("src/main.py",),
        forbidden_files=("config/secrets.py",),
    )
    patch = make_patch("src/main.py", "config/secrets.py")
    application = make_application("src/main.py", "config/secrets.py")

    result = assessor.assess(reference, patch, application)

    assert result.criteria[1].awarded_points == 0


@pytest.mark.parametrize(
    "path",
    (
        "../outside.py",
        "/etc/passwd",
        "src/../outside.py",
        r"src\outside.py",
        "",
    ),
)
def test_unsafe_patch_paths_lose_safety_points(assessor, path):
    reference = PatchScopeReference(expected_files=(path,))
    patch = make_patch(path)
    application = make_application(path)

    result = assessor.assess(reference, patch, application)

    assert result.criteria[2].awarded_points == 0


def test_target_and_changed_file_mismatch_loses_integrity_points(assessor):
    reference = PatchScopeReference(expected_files=("src/main.py",))
    patch = make_patch("src/main.py")
    application = make_application("src/other.py")

    result = assessor.assess(reference, patch, application)

    assert result.criteria[3].awarded_points == 0


def test_evidence_references_are_preserved(assessor):
    reference = PatchScopeReference(expected_files=("src/main.py",))
    evidence = ("patch:src/main.py",)

    result = assessor.assess(
        reference,
        make_patch("src/main.py"),
        make_application("src/main.py"),
        evidence_refs=evidence,
    )

    assert all(
        tuple(item.evidence_refs) == evidence
        for item in result.criteria
    )


def test_criterion_weights_total_ten(assessor):
    assert sum(assessor.WEIGHTS.values()) == 10