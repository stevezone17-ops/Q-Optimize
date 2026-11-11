"""Status transition validation for experiment lifecycle management."""

from backend.app.experiments.models import ExperimentStatus
from backend.app.experiments.config import EXPERIMENT_STATUS_TRANSITIONS
from backend.app.experiments.experiment_exceptions import InvalidExperimentStatusTransitionError


def validate_transition(current: ExperimentStatus, target: ExperimentStatus) -> None:
    """Raise InvalidExperimentStatusTransitionError if the transition is not allowed."""
    allowed = EXPERIMENT_STATUS_TRANSITIONS.get(current.value, set())
    if target.value not in allowed:
        raise InvalidExperimentStatusTransitionError(current.value, target.value)


def can_transition(current: ExperimentStatus, target: ExperimentStatus) -> bool:
    """Return True if the status transition is valid."""
    allowed = EXPERIMENT_STATUS_TRANSITIONS.get(current.value, set())
    return target.value in allowed


def is_terminal(status: ExperimentStatus) -> bool:
    """Return True if the status is a terminal (non-actionable) state."""
    return status in {
        ExperimentStatus.COMPLETED,
        ExperimentStatus.FAILED,
        ExperimentStatus.CANCELLED,
    }
