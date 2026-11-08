"""Experiment reporting and research analysis."""

from repoguard_eval.reporting.aggregator import ExperimentAggregator
from repoguard_eval.reporting.artifacts import ReportArtifactWriter
from repoguard_eval.reporting.integration import (
    build_task_reports,
    generate_experiment_report,
)
from repoguard_eval.reporting.raw_outputs import RawOutputStore
from repoguard_eval.reporting.schemas import (
    ExperimentReportMetadata,
    TaskReportResult,
    AggregateReport,
)

__all__ = [
    "ExperimentReportMetadata",
    "TaskReportResult",
    "AggregateReport",
    "ExperimentAggregator",
    "ReportArtifactWriter",
    "RawOutputStore",
    "build_task_reports",
    "generate_experiment_report",
]