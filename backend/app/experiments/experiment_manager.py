"""CRUD operations and lifecycle management for experiments."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.experiments.models import (
    Experiment,
    ExperimentConfiguration,
    ExperimentMetadata,
    ExperimentRun,
    ExperimentStatus,
)
from backend.app.experiments.schemas import (
    ExperimentCreateRequest,
    ExperimentUpdateRequest,
    ExperimentSummaryResponse,
    ExperimentDetailResponse,
    ExperimentListResponse,
)
from backend.app.experiments.registry import experiment_registry
from backend.app.experiments.experiment_metadata import capture_metadata
from backend.app.experiments.experiment_status import validate_transition, is_terminal
from backend.app.experiments.experiment_exceptions import (
    ExperimentNotFoundError,
    ExperimentValidationError,
    InvalidExperimentStatusTransitionError,
)
from backend.app.experiments.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from backend.app.core.logging import logger


class ExperimentManager:
    """Provides CRUD and lifecycle management for experiments."""

    # ------------------------------------------------------------------ #
    # Creation
    # ------------------------------------------------------------------ #
    def create_experiment(self, request: ExperimentCreateRequest) -> Experiment:
        """Create a new experiment in DRAFT state."""
        experiment_id = str(uuid.uuid4())
        configuration = ExperimentConfiguration(
            algorithms=request.algorithms,
            problem_type=request.problem_type,
            problem_instance=request.problem_instance,
            num_trials=request.num_trials,
            seeds=request.seeds,
            resource_budget=request.resource_budget,
            algorithm_configs=request.algorithm_configs,
            description=request.description,
            tags=request.tags,
        )
        metadata = capture_metadata(configuration)
        experiment = Experiment(
            experiment_id=experiment_id,
            name=request.name,
            configuration=configuration,
            status=ExperimentStatus.DRAFT,
            metadata=metadata,
        )
        experiment_registry.save(experiment)
        logger.info(f"Created experiment '{experiment_id}' name='{request.name}'")
        return experiment

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #
    def get_experiment(self, experiment_id: str) -> Experiment:
        return experiment_registry.get(experiment_id)

    def list_experiments(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        status_filter: Optional[ExperimentStatus] = None,
        problem_type_filter: Optional[str] = None,
    ) -> ExperimentListResponse:
        page_size = min(page_size, MAX_PAGE_SIZE)
        experiments = experiment_registry.list_all(
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            problem_type_filter=problem_type_filter,
        )
        total = experiment_registry.total_count(
            status_filter=status_filter,
            problem_type_filter=problem_type_filter,
        )
        summaries = [self._to_summary(e) for e in experiments]
        return ExperimentListResponse(
            experiments=summaries, total=total, page=page, page_size=page_size
        )

    # ------------------------------------------------------------------ #
    # Update
    # ------------------------------------------------------------------ #
    def update_experiment(
        self, experiment_id: str, request: ExperimentUpdateRequest
    ) -> Experiment:
        experiment = experiment_registry.get(experiment_id)
        if request.name is not None:
            experiment.name = request.name
        if request.description is not None:
            experiment.configuration.description = request.description
        if request.tags is not None:
            experiment.configuration.tags = request.tags
        experiment.metadata.updated_at = datetime.now(timezone.utc)
        experiment_registry.update(experiment)
        return experiment

    # ------------------------------------------------------------------ #
    # Status transitions
    # ------------------------------------------------------------------ #
    def transition_status(
        self,
        experiment_id: str,
        target: ExperimentStatus,
        error_message: Optional[str] = None,
    ) -> Experiment:
        experiment = experiment_registry.get(experiment_id)
        validate_transition(experiment.status, target)
        experiment.status = target
        now = datetime.now(timezone.utc)
        experiment.metadata.updated_at = now
        if target == ExperimentStatus.RUNNING and experiment.metadata.started_at is None:
            experiment.metadata.started_at = now
        if is_terminal(target) or target == ExperimentStatus.PARTIALLY_COMPLETED:
            experiment.metadata.completed_at = now
        if error_message is not None:
            experiment.error_message = error_message
        experiment_registry.update(experiment)
        logger.info(
            f"Experiment '{experiment_id}' transitioned to '{target.value}'"
        )
        return experiment

    def cancel_experiment(self, experiment_id: str) -> Experiment:
        experiment = experiment_registry.get(experiment_id)
        if is_terminal(experiment.status):
            return experiment  # already done
        try:
            return self.transition_status(
                experiment_id, ExperimentStatus.CANCELLED, "Cancelled by user."
            )
        except InvalidExperimentStatusTransitionError:
            return experiment

    # ------------------------------------------------------------------ #
    # Delete
    # ------------------------------------------------------------------ #
    def delete_experiment(self, experiment_id: str) -> bool:
        experiment_registry.get(experiment_id)  # raises if not found
        return experiment_registry.delete(experiment_id)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def to_detail_response(self, experiment: Experiment) -> ExperimentDetailResponse:
        return ExperimentDetailResponse(
            experiment_id=experiment.experiment_id,
            name=experiment.name,
            status=experiment.status,
            configuration=experiment.configuration,
            metadata=experiment.metadata,
            runs=experiment.runs,
            results=experiment.results,
            progress=experiment.progress,
            error_message=experiment.error_message,
        )

    @staticmethod
    def _to_summary(experiment: Experiment) -> ExperimentSummaryResponse:
        return ExperimentSummaryResponse(
            experiment_id=experiment.experiment_id,
            name=experiment.name,
            status=experiment.status,
            problem_type=experiment.configuration.problem_type,
            algorithms=[a.value for a in experiment.configuration.algorithms],
            num_trials=experiment.configuration.num_trials,
            progress=experiment.progress,
            created_at=experiment.metadata.created_at.isoformat(),
            completed_at=(
                experiment.metadata.completed_at.isoformat()
                if experiment.metadata.completed_at
                else None
            ),
        )


experiment_manager = ExperimentManager()
