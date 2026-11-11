"""Experiment management REST endpoints — Phase 8."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status as http_status

from backend.app.experiments.schemas import (
    ExperimentCreateRequest,
    ExperimentUpdateRequest,
    ExperimentDetailResponse,
    ExperimentListResponse,
    ExperimentStatusResponse,
    ExperimentSummaryResponse,
)
from backend.app.experiments.models import ExperimentStatus
from backend.app.experiments.experiment_manager import experiment_manager
from backend.app.experiments.experiment_scheduler import schedule_experiment
from backend.app.experiments.experiment_exceptions import (
    ExperimentNotFoundError,
    ExperimentValidationError,
    InvalidExperimentStatusTransitionError,
)

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.post("", response_model=ExperimentDetailResponse, status_code=201)
async def create_experiment(request: ExperimentCreateRequest) -> ExperimentDetailResponse:
    """Create a new experiment in DRAFT state."""
    try:
        experiment = experiment_manager.create_experiment(request)
        return experiment_manager.to_detail_response(experiment)
    except ExperimentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[ExperimentStatus] = Query(default=None),
    problem_type: Optional[str] = Query(default=None),
) -> ExperimentListResponse:
    """List experiments with pagination and filtering."""
    return experiment_manager.list_experiments(
        page=page,
        page_size=page_size,
        status_filter=status,
        problem_type_filter=problem_type,
    )


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(experiment_id: str) -> ExperimentDetailResponse:
    """Retrieve full experiment details by ID."""
    try:
        experiment = experiment_manager.get_experiment(experiment_id)
        return experiment_manager.to_detail_response(experiment)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.put("/{experiment_id}", response_model=ExperimentDetailResponse)
async def update_experiment(
    experiment_id: str, request: ExperimentUpdateRequest
) -> ExperimentDetailResponse:
    """Update experiment name, description, or tags."""
    try:
        experiment = experiment_manager.update_experiment(experiment_id, request)
        return experiment_manager.to_detail_response(experiment)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{experiment_id}", status_code=204)
async def delete_experiment(experiment_id: str) -> None:
    """Delete an experiment."""
    try:
        experiment_manager.delete_experiment(experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{experiment_id}/submit", response_model=ExperimentStatusResponse)
async def submit_experiment(experiment_id: str) -> ExperimentStatusResponse:
    """Submit an experiment for execution (DRAFT → QUEUED → RUNNING)."""
    try:
        experiment = experiment_manager.get_experiment(experiment_id)
        experiment = await schedule_experiment(experiment)
        return ExperimentStatusResponse(
            experiment_id=experiment_id,
            status=experiment.status,
            progress=experiment.progress,
            message="Experiment submitted for execution.",
        )
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except InvalidExperimentStatusTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/{experiment_id}/cancel", response_model=ExperimentStatusResponse)
async def cancel_experiment(experiment_id: str) -> ExperimentStatusResponse:
    """Request cancellation of a running or queued experiment."""
    try:
        experiment = experiment_manager.cancel_experiment(experiment_id)
        return ExperimentStatusResponse(
            experiment_id=experiment_id,
            status=experiment.status,
            progress=experiment.progress,
            message="Cancellation requested.",
        )
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{experiment_id}/status", response_model=ExperimentStatusResponse)
async def get_experiment_status(experiment_id: str) -> ExperimentStatusResponse:
    """Get the current status and progress of an experiment."""
    try:
        experiment = experiment_manager.get_experiment(experiment_id)
        return ExperimentStatusResponse(
            experiment_id=experiment_id,
            status=experiment.status,
            progress=experiment.progress,
        )
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
