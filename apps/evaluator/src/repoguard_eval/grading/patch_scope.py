from pathlib import PurePosixPath

from repoguard_eval.execution.patch_applier import PatchApplicationResult
from repoguard_eval.execution.patches import ValidatedPatch
from repoguard_eval.grading.schemas import (
    CriterionScore,
    DimensionScore,
    GradingModel,
    ScoreDimension,
)


class PatchScopeReference(GradingModel):
    """Benchmark expectations for patch scope."""

    expected_files: tuple[str, ...] = ()
    forbidden_files: tuple[str, ...] = ()


class PatchScopeAssessor:
    """Assess relevance, scope, safety, and integrity of an applied patch."""

    WEIGHTS = {
        "relevant_changes": 4,
        "no_unrelated_changes": 2,
        "safety": 3,
        "patch_integrity": 1,
    }

    def assess(
        self,
        reference: PatchScopeReference,
        patch: ValidatedPatch,
        application: PatchApplicationResult,
        evidence_refs: tuple[str, ...] = (),
    ) -> DimensionScore:
        if not isinstance(reference, PatchScopeReference):
            raise TypeError("reference must be a PatchScopeReference.")

        if not isinstance(patch, ValidatedPatch):
            raise TypeError("patch must be a ValidatedPatch.")

        if not isinstance(application, PatchApplicationResult):
            raise TypeError("application must be a PatchApplicationResult.")

        expected = set(reference.expected_files)
        forbidden = set(reference.forbidden_files)

        targets = {
            path
            for item in patch.files
            for path in (item.old_path, item.new_path)
            if path is not None
        }

        changed = set(application.changed_files)

        relevant = targets & expected
        unexpected = changed - expected
        forbidden_changes = changed & forbidden

        relevant_score = (
            self.WEIGHTS["relevant_changes"] * len(relevant) / len(expected)
            if expected
            else 0.0
        )

        unrelated_score = (
            float(self.WEIGHTS["no_unrelated_changes"])
            if not unexpected and not forbidden_changes
            else 0.0
        )

        safe_targets = all(self._is_safe_path(path) for path in targets)
        safe_changes = all(self._is_safe_path(path) for path in changed)

        safety_score = (
            float(self.WEIGHTS["safety"])
            if safe_targets and safe_changes
            else 0.0
        )

        integrity_score = (
            float(self.WEIGHTS["patch_integrity"])
            if targets == changed
            else 0.0
        )

        criteria = (
            CriterionScore(
                criterion_id="relevant_changes",
                awarded_points=relevant_score,
                maximum_points=self.WEIGHTS["relevant_changes"],
                rationale=(
                    f"{len(relevant)} of {len(expected)} expected files "
                    "were targeted by the patch."
                ),
                evidence_refs=evidence_refs,
            ),
            CriterionScore(
                criterion_id="no_unrelated_changes",
                awarded_points=unrelated_score,
                maximum_points=self.WEIGHTS["no_unrelated_changes"],
                rationale=(
                    "No unrelated files were changed."
                    if unrelated_score
                    else f"Unexpected changes detected: {sorted(unexpected | forbidden_changes)}."
                ),
                evidence_refs=evidence_refs,
            ),
            CriterionScore(
                criterion_id="safety",
                awarded_points=safety_score,
                maximum_points=self.WEIGHTS["safety"],
                rationale=(
                    "All patch targets and changed paths are safe."
                    if safety_score
                    else "Unsafe patch target or changed path detected."
                ),
                evidence_refs=evidence_refs,
            ),
            CriterionScore(
                criterion_id="patch_integrity",
                awarded_points=integrity_score,
                maximum_points=self.WEIGHTS["patch_integrity"],
                rationale=(
                    "Applied changes match declared patch targets."
                    if integrity_score
                    else (
                        f"Target/change mismatch. "
                        f"Missing: {sorted(targets - changed)}; "
                        f"unexpected: {sorted(changed - targets)}."
                    )
                ),
                evidence_refs=evidence_refs,
            ),
        )

        return DimensionScore(
            dimension=ScoreDimension.PATCH_SCOPE,
            score=sum(item.awarded_points for item in criteria),
            maximum_score=sum(self.WEIGHTS.values()),
            criteria=criteria,
        )

    @staticmethod
    def _is_safe_path(path: str) -> bool:
        if not isinstance(path, str) or not path:
            return False

        if "\\" in path or "\x00" in path:
            return False

        parsed = PurePosixPath(path)

        if parsed.is_absolute():
            return False

        if any(part in {"", ".", ".."} for part in path.split("/")):
            return False

        return True