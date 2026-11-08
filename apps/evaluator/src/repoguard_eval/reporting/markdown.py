"""Markdown report generation."""

from repoguard_eval.reporting.schemas import (
    AggregateReport,
    ExperimentReportMetadata,
)


def render_experiment_report(
    metadata: ExperimentReportMetadata,
    aggregate: AggregateReport,
) -> str:
    if metadata.experiment_id != aggregate.experiment_id:
        raise ValueError("Metadata and aggregate experiment IDs differ.")

    def percentage(rate):
        if rate.rate is None:
            return "N/A"
        return f"{rate.rate * 100:.2f}% ({rate.numerator}/{rate.denominator})"

    def metric(value):
        return "N/A" if value is None else f"{value:.4f}"

    lines = [
        f"# Experiment Report: {metadata.benchmark_name}",
        "",
        "## Experiment Metadata",
        "",
        f"- Experiment ID: `{metadata.experiment_id}`",
        f"- Benchmark version: `{metadata.benchmark_version}`",
        f"- Model: `{metadata.model}`",
        f"- Provider: `{metadata.provider or 'N/A'}`",
        f"- Generated at: `{metadata.generated_at.isoformat()}`",
        f"- Started at: `{metadata.started_at.isoformat() if metadata.started_at else 'N/A'}`",
        f"- Completed at: `{metadata.completed_at.isoformat() if metadata.completed_at else 'N/A'}`",
        f"- Duration: `{metric(metadata.duration_seconds)}` seconds",
        "",
        "## Experiment Summary",
        "",
        f"- Total tasks: **{aggregate.total_tasks}**",
        f"- Completed tasks: **{aggregate.completed_tasks}**",
        f"- Failed tasks: **{aggregate.failed_tasks}**",
        f"- Average score: **{metric(aggregate.score.average)}**",
        f"- Median score: **{metric(aggregate.score.median)}**",
        f"- Functional pass rate: **{percentage(aggregate.functional_pass_rate)}**",
        f"- Build success rate: **{percentage(aggregate.build_success_rate)}**",
        f"- Regression pass rate: **{percentage(aggregate.regression_pass_rate)}**",
        f"- Total duration: **{metric(aggregate.total_duration_seconds)} seconds**",
        f"- Total cost: **{metric(aggregate.total_cost_usd)} USD**",
        f"- Total tokens: **{aggregate.total_tokens if aggregate.total_tokens is not None else 'N/A'}**",
        "",
        "## Task Results",
        "",
        "| Task ID | Status | Score | Model | Duration (s) | Cost (USD) |",
        "|---|---|---:|---|---:|---:|",
    ]

    for result in aggregate.task_results:
        score = (
            metric(result.evaluation.total_score)
            if result.evaluation is not None
            else "N/A"
        )

        lines.append(
            f"| {result.task_id} "
            f"| {result.status} "
            f"| {score} "
            f"| {result.model or 'N/A'} "
            f"| {metric(result.duration_seconds)} "
            f"| {metric(result.cost_usd)} |"
        )

    lines.extend([
        "",
        "## Failure Analysis",
        "",
    ])

    if aggregate.failure_breakdown:
        lines.extend(
            f"- {item.category}: {item.count}"
            for item in aggregate.failure_breakdown
        )
    else:
        lines.append("No failure classifications were recorded.")

    lines.extend([
        "",
        "## Language Breakdown",
        "",
    ])

    if aggregate.language_breakdown:
        lines.extend(
            f"- {item.category}: {item.count}"
            for item in aggregate.language_breakdown
        )
    else:
        lines.append("Language metadata was not available.")

    lines.extend([
        "",
        "## Model Breakdown",
        "",
    ])

    if aggregate.model_breakdown:
        lines.extend(
            f"- {item.category}: {item.count}"
            for item in aggregate.model_breakdown
        )
    else:
        lines.append("Model metadata was not available.")

    lines.extend([
        "",
        "## Reproducibility",
        "",
        f"- Experiment ID: `{metadata.experiment_id}`",
        f"- Benchmark: `{metadata.benchmark_name}`",
        f"- Benchmark version: `{metadata.benchmark_version}`",
        f"- Task IDs: {', '.join(metadata.task_ids)}",
        f"- Configuration: `{metadata.configuration}`",
        "",
        "Metrics are calculated only from recorded experiment artifacts. "
        "Unavailable measurements are reported as N/A.",
        "",
    ])

    return "\n".join(lines)