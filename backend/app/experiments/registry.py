"""In-memory + MongoDB registry for experiments."""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.app.experiments.models import Experiment, ExperimentStatus
from backend.app.experiments.experiment_exceptions import (
    ExperimentNotFoundError,
    ExperimentAlreadyExistsError,
)
from backend.app.db.mongodb import db_manager

COLLECTION = "experiments"


class ExperimentRegistry:
    """Thread-safe (via GIL) in-memory + persistent storage for experiments."""

    _store: Dict[str, Experiment] = {}

    # ------------------------------------------------------------------ #
    # Write operations
    # ------------------------------------------------------------------ #
    def save(self, experiment: Experiment) -> None:
        self._store[experiment.experiment_id] = experiment
        db_manager.memory_insert(
            COLLECTION, experiment.experiment_id, experiment.model_dump(mode="json")
        )

    def update(self, experiment: Experiment) -> None:
        if experiment.experiment_id not in self._store:
            raise ExperimentNotFoundError(experiment.experiment_id)
        self._store[experiment.experiment_id] = experiment
        db_manager.memory_insert(
            COLLECTION, experiment.experiment_id, experiment.model_dump(mode="json")
        )

    def delete(self, experiment_id: str) -> bool:
        if experiment_id in self._store:
            del self._store[experiment_id]
            db_manager.memory_delete(COLLECTION, experiment_id)
            return True
        return False

    # ------------------------------------------------------------------ #
    # Read operations
    # ------------------------------------------------------------------ #
    def get(self, experiment_id: str) -> Experiment:
        if experiment_id not in self._store:
            raise ExperimentNotFoundError(experiment_id)
        return self._store[experiment_id]

    def get_or_none(self, experiment_id: str) -> Optional[Experiment]:
        return self._store.get(experiment_id)

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[ExperimentStatus] = None,
        problem_type_filter: Optional[str] = None,
    ) -> List[Experiment]:
        experiments = list(self._store.values())
        if status_filter:
            experiments = [e for e in experiments if e.status == status_filter]
        if problem_type_filter:
            experiments = [
                e
                for e in experiments
                if e.configuration.problem_type == problem_type_filter
            ]
        # Sort newest first by metadata.created_at
        experiments.sort(key=lambda e: e.metadata.created_at, reverse=True)
        start = (page - 1) * page_size
        return experiments[start : start + page_size]

    def total_count(
        self,
        status_filter: Optional[ExperimentStatus] = None,
        problem_type_filter: Optional[str] = None,
    ) -> int:
        experiments = list(self._store.values())
        if status_filter:
            experiments = [e for e in experiments if e.status == status_filter]
        if problem_type_filter:
            experiments = [
                e
                for e in experiments
                if e.configuration.problem_type == problem_type_filter
            ]
        return len(experiments)

    def exists(self, experiment_id: str) -> bool:
        return experiment_id in self._store


experiment_registry = ExperimentRegistry()
