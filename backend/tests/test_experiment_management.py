"""Tests for Stage 8.1 — Experiment Management Architecture."""

import pytest
from datetime import datetime, timezone

from backend.app.experiments.models import (
    ExperimentAlgorithm,
    ExperimentStatus,
    ExperimentResourceBudget,
)
from backend.app.experiments.schemas import (
    ExperimentCreateRequest,
    ExperimentUpdateRequest,
)
from backend.app.experiments.experiment_manager import ExperimentManager
from backend.app.experiments.experiment_metadata import compute_config_hash, capture_metadata
from backend.app.experiments.experiment_status import (
    validate_transition,
    can_transition,
    is_terminal,
)
from backend.app.experiments.experiment_exceptions import (
    ExperimentNotFoundError,
    InvalidExperimentStatusTransitionError,
)
from backend.app.experiments.registry import ExperimentRegistry


def _make_manager() -> ExperimentManager:
    """Return a fresh ExperimentManager backed by a fresh registry."""
    mgr = ExperimentManager()
    mgr_registry = ExperimentRegistry()
    # Monkey-patch to use isolated registry
    import backend.app.experiments.experiment_manager as em_mod
    original_registry = em_mod.experiment_registry
    em_mod.experiment_registry = mgr_registry

    # Patch the status module to use the same registry
    import backend.app.experiments.experiment_status as es_mod  # noqa: F401

    return mgr, mgr_registry, em_mod, original_registry


def _make_create_request(
    name: str = "Test Experiment",
    problem_type: str = "max_cut",
    algorithms: list = None,
    num_trials: int = 1,
) -> ExperimentCreateRequest:
    return ExperimentCreateRequest(
        name=name,
        problem_type=problem_type,
        problem_instance={"num_nodes": 4, "edge_list": [[0, 1], [1, 2], [2, 3]]},
        algorithms=algorithms or [ExperimentAlgorithm.SIMULATED_ANNEALING],
        num_trials=num_trials,
    )


class TestExperimentCreation:
    def test_create_experiment_returns_experiment_with_id(self):
        mgr = ExperimentManager()
        req = _make_create_request()
        exp = mgr.create_experiment(req)
        assert exp.experiment_id
        assert exp.name == "Test Experiment"
        assert exp.status == ExperimentStatus.DRAFT

    def test_create_experiment_stores_configuration(self):
        mgr = ExperimentManager()
        req = _make_create_request(problem_type="assignment")
        exp = mgr.create_experiment(req)
        assert exp.configuration.problem_type == "assignment"

    def test_create_experiment_captures_metadata(self):
        mgr = ExperimentManager()
        req = _make_create_request()
        exp = mgr.create_experiment(req)
        assert exp.metadata.created_at is not None
        assert exp.metadata.reproducibility_hash != ""

    def test_create_experiment_invalid_problem_type_raises(self):
        import pydantic
        try:
            ExperimentCreateRequest(
                name="bad",
                problem_type="invalid_type",
                problem_instance={},
                algorithms=[ExperimentAlgorithm.SIMULATED_ANNEALING],
            )
            # If creation succeeded, test via manager
            mgr = ExperimentManager()
            with pytest.raises((pydantic.ValidationError, ValueError, Exception)):
                mgr.create_experiment(
                    ExperimentCreateRequest(
                        name="bad",
                        problem_type="invalid_type",
                        problem_instance={},
                        algorithms=[ExperimentAlgorithm.SIMULATED_ANNEALING],
                    )
                )
        except (pydantic.ValidationError, ValueError):
            pass  # expected — validation raised at construction time

    def test_retrieve_created_experiment(self):
        mgr = ExperimentManager()
        req = _make_create_request(name="Retrieve Me")
        exp = mgr.create_experiment(req)
        retrieved = mgr.get_experiment(exp.experiment_id)
        assert retrieved.experiment_id == exp.experiment_id
        assert retrieved.name == "Retrieve Me"

    def test_get_nonexistent_experiment_raises(self):
        mgr = ExperimentManager()
        with pytest.raises(ExperimentNotFoundError):
            mgr.get_experiment("nonexistent-id-9999")


class TestExperimentLifecycle:
    def test_valid_transition_draft_to_validating(self):
        assert can_transition(ExperimentStatus.DRAFT, ExperimentStatus.VALIDATING)

    def test_invalid_transition_completed_to_running(self):
        assert not can_transition(ExperimentStatus.COMPLETED, ExperimentStatus.RUNNING)

    def test_validate_transition_raises_on_invalid(self):
        with pytest.raises(InvalidExperimentStatusTransitionError):
            validate_transition(ExperimentStatus.COMPLETED, ExperimentStatus.RUNNING)

    def test_terminal_states(self):
        assert is_terminal(ExperimentStatus.COMPLETED)
        assert is_terminal(ExperimentStatus.FAILED)
        assert is_terminal(ExperimentStatus.CANCELLED)
        assert not is_terminal(ExperimentStatus.RUNNING)

    def test_cancel_draft_experiment(self):
        mgr = ExperimentManager()
        req = _make_create_request()
        exp = mgr.create_experiment(req)
        cancelled = mgr.cancel_experiment(exp.experiment_id)
        assert cancelled.status == ExperimentStatus.CANCELLED


class TestExperimentMetadata:
    def test_reproducibility_hash_is_stable(self):
        mgr = ExperimentManager()
        req = _make_create_request()
        exp1 = mgr.create_experiment(req)
        exp2 = mgr.create_experiment(req)
        # Same config → same hash
        assert exp1.metadata.reproducibility_hash == exp2.metadata.reproducibility_hash

    def test_different_config_different_hash(self):
        mgr = ExperimentManager()
        req1 = _make_create_request(problem_type="max_cut")
        req2 = _make_create_request(problem_type="assignment")
        exp1 = mgr.create_experiment(req1)
        exp2 = mgr.create_experiment(req2)
        assert exp1.metadata.reproducibility_hash != exp2.metadata.reproducibility_hash

    def test_metadata_has_python_version(self):
        mgr = ExperimentManager()
        req = _make_create_request()
        exp = mgr.create_experiment(req)
        assert exp.metadata.python_version != ""


class TestExperimentListing:
    def test_list_experiments_returns_created(self):
        mgr = ExperimentManager()
        req = _make_create_request(name="Listed Experiment")
        exp = mgr.create_experiment(req)
        result = mgr.list_experiments(page=1, page_size=100)
        ids = [e.experiment_id for e in result.experiments]
        assert exp.experiment_id in ids

    def test_list_experiments_pagination(self):
        mgr = ExperimentManager()
        for i in range(5):
            mgr.create_experiment(_make_create_request(name=f"Experiment {i}"))
        page1 = mgr.list_experiments(page=1, page_size=3)
        assert len(page1.experiments) <= 3

    def test_delete_experiment(self):
        mgr = ExperimentManager()
        req = _make_create_request()
        exp = mgr.create_experiment(req)
        result = mgr.delete_experiment(exp.experiment_id)
        assert result is True
        with pytest.raises(ExperimentNotFoundError):
            mgr.get_experiment(exp.experiment_id)


class TestPartialCompletion:
    def test_partially_completed_transition_allowed_from_running(self):
        assert can_transition(
            ExperimentStatus.RUNNING, ExperimentStatus.PARTIALLY_COMPLETED
        )
