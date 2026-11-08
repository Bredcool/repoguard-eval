# RepoGuard-Eval Dashboard API

## Overview

The Dashboard API provides read-only HTTP access to persisted experiment and evaluation artifacts.

The API does not:

- Execute repository code or benchmark tasks.
- Invoke AI providers.
- Recalculate official evaluation scores.
- Modify experiment artifacts.
- Require PostgreSQL.

## Requirements

- Python 3.13
- FastAPI
- Uvicorn

## Installation

Run from `apps/evaluator`:

```bash
python -m pip install -e ".[dev,api]"
```

## Configuration

The API uses the existing application configuration.

| Variable | Description |
| --- | --- |
| `RG_EXPERIMENTS_DIR` | Experiment and artifact root |
| `RG_ENVIRONMENT` | Application environment |
| `RG_LOG_LEVEL` | Logging level |

Default artifact directory: `data/experiments`

## Running the API

From `apps/evaluator`:

```bash
python -m uvicorn repoguard_eval.api.app:app --host 127.0.0.1 --port 8000
```

Interactive OpenAPI documentation:

`http://127.0.0.1:8000/docs`

Health check:

`http://127.0.0.1:8000/health`

## API Endpoints

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Returns API health status. |

### Experiments

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/experiments` | Returns paginated experiment summaries. |
| GET | `/experiments/{experiment_id}` | Returns experiment definition, orchestration metadata, and persisted execution result. |
| GET | `/experiments/{experiment_id}/tasks` | Returns paginated task evaluation results. |

`GET /experiments` query parameters:

| Parameter | Description |
| --- | --- |
| `limit` | Results per page, 1–100; default 20. |
| `offset` | Pagination offset; default 0. |
| `status` | Exact status filter. |
| `model` | Exact model filter. |
| `provider` | Exact provider filter. |
| `benchmark` | Exact benchmark filter. |

`GET /experiments/{experiment_id}/tasks` query parameters:

| Parameter | Description |
| --- | --- |
| `limit` | Results per page, 1–100; default 20. |
| `offset` | Pagination offset; default 0. |
| `status` | Task status filter. |

### Reports

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/experiments/{experiment_id}/report` | Returns reporting metadata, persisted aggregate scores, and Markdown report. |
| GET | `/experiments/{experiment_id}/failures` | Returns persisted failure analysis. |

### Models

| Method | Endpoint | Description |
|---|---|---|
| GET | `/models/compare` | Returns persisted aggregate metrics grouped by experiment. |

`GET /models/compare` query parameters:

| Parameter | Description |
| --- | --- |
| `limit` | Results per page, 1–100; default 20. |
| `offset` | Pagination offset; default 0. |
| `benchmark` | Benchmark filter. |

No official scores are recalculated.

### Artifacts

| Method | Endpoint | Description |
|---|---|---|
| GET | `/artifacts/{artifact_id}` | Downloads a persisted artifact. |

Artifact ID format:

```text
{experiment_uuid}/{relative_artifact_path}
```

Example:

```text
/artifacts/{experiment_uuid}/reports/report.md
```

Paths outside the experiment directory are rejected.

## Response and Error Handling

| HTTP Status | Meaning |
| --- | --- |
| 200 | Successful request |
| 403 | Artifact access denied |
| 404 | Experiment or artifact not found |
| 422 | Invalid UUID or query parameters |
| 500 | Artifact read or JSON parsing failure |

## Artifact Layout

```text
data/experiments/
├── {experiment_id}.json
└── {experiment_id}/
    ├── metadata.json
    ├── result.json
    ├── tasks/
    ├── raw/
    ├── results/
    │   ├── task_results.json
    │   └── aggregate.json
    └── reports/
        ├── metadata.json
        ├── report.md
        └── failure_analysis.json
```

## Security

- UUID validation for experiment identifiers.
- Resolved-path containment validation.
- Symlink escape protection.
- Read-only artifact access.
- No repository execution through HTTP.
- No arbitrary filesystem access outside experiment directories.

## Architecture

```text
Dashboard
    |
    v
FastAPI
    |
    v
ArtifactService
    |
    v
Persisted Experiment Artifacts
    |
    +-- metadata.json
    +-- result.json
    +-- task_results.json
    +-- aggregate.json
    +-- report.md
    +-- failure_analysis.json
```

FastAPI is an optional dependency. The CLI and evaluation core remain usable without installing the API extra.
