"""Read-only FastAPI application for experiment dashboards."""

from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from repoguard_eval.api.dependencies import get_artifact_service
from repoguard_eval.api.exceptions import (
    ArtifactAccessError,
    ArtifactNotFoundError,
    ArtifactReadError,
    ExperimentNotFoundError,
)
from repoguard_eval.api.schemas import (
    ErrorResponse,
    ExperimentDetailResponse,
    ExperimentListResponse,
    FailureResponse,
    HealthResponse,
    ModelComparisonResponse,
    ReportResponse,
    TaskListResponse,
)
from repoguard_eval.api.services.artifacts import ArtifactService


def create_app(
    artifact_dir: Path | None = None,
) -> FastAPI:
    """Create an API application with an optional artifact root override."""

    application = FastAPI(
        title="RepoGuard-Eval Dashboard API",
        description=(
            "Read-only API for persisted experiment and evaluation artifacts."
        ),
        version="0.1.0",
    )

    if artifact_dir is not None:
        service = ArtifactService(artifact_dir)
        application.dependency_overrides[get_artifact_service] = (
            lambda: service
        )

    @application.exception_handler(ExperimentNotFoundError)
    async def experiment_not_found_handler(request, exc):
        return _error_response(404, "experiment_not_found", str(exc))

    @application.exception_handler(ArtifactNotFoundError)
    async def artifact_not_found_handler(request, exc):
        return _error_response(404, "artifact_not_found", str(exc))

    @application.exception_handler(ArtifactAccessError)
    async def artifact_access_handler(request, exc):
        return _error_response(403, "artifact_access_denied", str(exc))

    @application.exception_handler(ArtifactReadError)
    async def artifact_read_handler(request, exc):
        return _error_response(500, "artifact_read_error", str(exc))

    @application.get(
        "/health",
        response_model=HealthResponse,
        tags=["System"],
    )
    async def health():
        return HealthResponse()

    @application.get(
        "/experiments",
        response_model=ExperimentListResponse,
        tags=["Experiments"],
    )
    async def list_experiments(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        status: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        benchmark: str | None = None,
        service: ArtifactService = Depends(get_artifact_service),
    ):
        result = service.list_experiments(
            limit=limit,
            offset=offset,
            status=status,
            model=model,
            provider=provider,
            benchmark=benchmark,
        )

        return {
            "items": result["items"],
            "pagination": {
                "total": result["total"],
                "limit": limit,
                "offset": offset,
            },
        }

    @application.get(
        "/experiments/{experiment_id}",
        response_model=ExperimentDetailResponse,
        tags=["Experiments"],
    )
    async def get_experiment(
        experiment_id: UUID,
        service: ArtifactService = Depends(get_artifact_service),
    ):
        return service.get_experiment(experiment_id)

    @application.get(
        "/experiments/{experiment_id}/tasks",
        response_model=TaskListResponse,
        tags=["Experiments"],
    )
    async def get_tasks(
        experiment_id: UUID,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        status: str | None = None,
        service: ArtifactService = Depends(get_artifact_service),
    ):
        result = service.list_tasks(
            experiment_id,
            limit=limit,
            offset=offset,
            status=status,
        )

        return {
            "experiment_id": str(experiment_id),
            "items": result["items"],
            "pagination": {
                "total": result["total"],
                "limit": limit,
                "offset": offset,
            },
        }

    @application.get(
        "/experiments/{experiment_id}/report",
        response_model=ReportResponse,
        tags=["Reports"],
    )
    async def get_report(
        experiment_id: UUID,
        service: ArtifactService = Depends(get_artifact_service),
    ):
        return service.get_report(experiment_id)

    @application.get(
        "/experiments/{experiment_id}/failures",
        response_model=FailureResponse,
        tags=["Reports"],
    )
    async def get_failures(
        experiment_id: UUID,
        service: ArtifactService = Depends(get_artifact_service),
    ):
        return service.get_failures(experiment_id)

    @application.get(
        "/models/compare",
        response_model=ModelComparisonResponse,
        tags=["Models"],
    )
    async def compare_models(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        benchmark: str | None = None,
        service: ArtifactService = Depends(get_artifact_service),
    ):
        result = service.compare_models(
            limit=limit,
            offset=offset,
            benchmark=benchmark,
        )

        return {
            "items": result["items"],
            "pagination": {
                "total": result["total"],
                "limit": limit,
                "offset": offset,
            },
        }

    @application.get(
        "/artifacts/{artifact_id:path}",
        tags=["Artifacts"],
        responses={
            403: {"model": ErrorResponse},
            404: {"model": ErrorResponse},
        },
    )
    async def get_artifact(
        artifact_id: str,
        service: ArtifactService = Depends(get_artifact_service),
    ):
        path = service.read_artifact(artifact_id)

        return FileResponse(
            path=path,
            filename=path.name,
        )

    return application


def _error_response(
    status_code: int,
    error: str,
    detail: str,
):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "detail": detail,
        },
    )


app = create_app()