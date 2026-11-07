
import pytest

from repoguard_eval.context.schemas import RepositoryContext, RepositoryFile
from repoguard_eval.grading.enums import ExecutionStatus, ScoreDimension
from repoguard_eval.grading.evidence import EvidenceAnchor, EvidenceAssessor
from repoguard_eval.grading.schemas import ExecutionCheckEvidence


@pytest.fixture
def assessor():
    return EvidenceAssessor()


@pytest.fixture
def repository():
    content = "\n".join([
        "def get_page(items, page, limit):",
        "    offset = (page - 1) * limit",
        "    return items[offset:offset + limit]",
        "",
        "def unrelated_function():",
        "    return True",
    ])

    return RepositoryContext(
        files=(
            RepositoryFile(
                path="src/service/pagination.py",
                content=content,
                size_bytes=len(content.encode()),
            ),
        ),
    )


@pytest.fixture
def anchors():
    return [
        EvidenceAnchor(
            path="src/service/pagination.py",
            start_line=1,
            end_line=3,
            keywords=["pagination", "offset", "page"],
        )
    ]


def test_perfect_evidence_score(assessor, repository, anchors):
    result = assessor.assess(
        repository=repository,
        evidence_refs=["src/service/pagination.py:1-3"],
        anchors=anchors,
        claims=["pagination offset page calculation"],
        reproduction_checks=[
            ExecutionCheckEvidence(
                name="reproduction",
                status=ExecutionStatus.PASSED,
                command="pytest",
                exit_code=0,
            )
        ],
    )

    assert result.dimension == ScoreDimension.EVIDENCE
    assert result.score == 20
    assert result.maximum_score == 20


def test_valid_reference_has_provenance(assessor, repository, anchors):
    result = assessor.assess(
        repository=repository,
        evidence_refs=["src/service/pagination.py:2"],
        anchors=anchors,
    )

    criterion = next(
        item for item in result.criteria
        if item.criterion_id == "evidence_provenance"
    )

    assert criterion.awarded_points == 6


def test_fabricated_path_has_no_provenance(assessor, repository, anchors):
    result = assessor.assess(
        repository=repository,
        evidence_refs=["src/missing.py:10"],
        anchors=anchors,
    )

    criterion = next(
        item for item in result.criteria
        if item.criterion_id == "evidence_provenance"
    )

    assert criterion.awarded_points == 0


def test_out_of_range_line_has_no_provenance(assessor, repository, anchors):
    result = assessor.assess(
        repository=repository,
        evidence_refs=["src/service/pagination.py:100"],
        anchors=anchors,
    )

    criterion = next(
        item for item in result.criteria
        if item.criterion_id == "evidence_provenance"
    )

    assert criterion.awarded_points == 0


def test_unrelated_evidence_has_no_relevance(assessor, repository, anchors):
    result = assessor.assess(
        repository=repository,
        evidence_refs=["src/service/pagination.py:5-6"],
        anchors=anchors,
    )

    criterion = next(
        item for item in result.criteria
        if item.criterion_id == "relevant_evidence"
    )

    assert criterion.awarded_points == 0


def test_claim_without_code_support_scores_zero(assessor, repository, anchors):
    result = assessor.assess(
        repository=repository,
        evidence_refs=["src/service/pagination.py:5-6"],
        anchors=anchors,
        claims=["database transaction rollback failure"],
    )

    criterion = next(
        item for item in result.criteria
        if item.criterion_id == "claim_traceability"
    )

    assert criterion.awarded_points == 0


def test_reproducibility_requires_passed_checks(assessor, repository, anchors):
    result = assessor.assess(
        repository=repository,
        evidence_refs=["src/service/pagination.py:2"],
        anchors=anchors,
        reproduction_checks=[
            ExecutionCheckEvidence(
                name="reproduction",
                status=ExecutionStatus.FAILED,
                command="pytest",
                exit_code=1,
            )
        ],
    )

    criterion = next(
        item for item in result.criteria
        if item.criterion_id == "reproducibility"
    )

    assert criterion.awarded_points == 0


def test_empty_evidence_scores_zero(assessor, repository, anchors):
    result = assessor.assess(
        repository=repository,
        evidence_refs=[],
        anchors=anchors,
    )

    assert result.score == 0


def test_evidence_references_are_preserved(assessor, repository, anchors):
    references = ["src/service/pagination.py:2"]

    result = assessor.assess(
        repository=repository,
        evidence_refs=references,
        anchors=anchors,
    )

    assert all(
        list(item.evidence_refs) == references
        for item in result.criteria
    )


def test_evidence_criteria_weights_total_twenty():
    assert sum(EvidenceAssessor.WEIGHTS.values()) == 20


def test_invalid_anchor_range_is_rejected():
    with pytest.raises(ValueError):
        EvidenceAnchor(
            path="src/main.py",
            start_line=10,
            end_line=5,
        )
