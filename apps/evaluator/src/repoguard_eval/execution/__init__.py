"""Execution infrastructure package."""

from repoguard_eval.execution.docker_process import (
    DockerCommandResult,
    DockerProcessManager,
)
from repoguard_eval.execution.docker_runtime import (
    DockerResourceLimits,
    DockerRuntime,
    DockerRuntimeManager,
)
from repoguard_eval.execution.docker_transfer import DockerVolumeTransfer
from repoguard_eval.execution.fixtures import FixtureManager
from repoguard_eval.execution.patch_applier import (
    PatchApplier,
    PatchApplicationResult,
)
from repoguard_eval.execution.patches import (
    Patch,
    PatchFile,
    ValidatedPatch,
)
from repoguard_eval.execution.patch_validator import PatchValidator
from repoguard_eval.execution.snapshots import (
    RepositorySnapshot,
    SnapshotEntry,
    SnapshotManager,
)
from repoguard_eval.execution.workspace import (
    Workspace,
    WorkspaceManager,
)
from repoguard_eval.execution.command_runner import (
    ContainerCommandResult,
    ContainerCommandRunner,
)
from repoguard_eval.execution.evaluator import ExecutionEvaluator
from repoguard_eval.execution.stage_evaluators import (
    BuildEvaluator,
    FunctionalTestEvaluator,
    HiddenTestEvaluator,
    RegressionTestEvaluator,
)
from repoguard_eval.execution.language_validators import (
    CppValidator,
    GoValidator,
    LanguageValidationConfig,
    LanguageValidator,
    PythonValidator,
)

__all__ = [
    "DockerCommandResult",
    "DockerProcessManager",
    "DockerResourceLimits",
    "DockerRuntime",
    "DockerRuntimeManager",
    "DockerVolumeTransfer",
    "FixtureManager",
    "Patch",
    "PatchApplier",
    "PatchApplicationResult",
    "PatchFile",
    "PatchValidator",
    "RepositorySnapshot",
    "SnapshotEntry",
    "SnapshotManager",
    "ValidatedPatch",
    "Workspace",
    "WorkspaceManager",
    "ContainerCommandResult",
    "ContainerCommandRunner",
    "ExecutionEvaluator",
    "BuildEvaluator",
    "FunctionalTestEvaluator",
    "HiddenTestEvaluator",
    "RegressionTestEvaluator",
    "CppValidator",
    "GoValidator",
    "LanguageValidationConfig",
    "LanguageValidator",
    "PythonValidator",
]