"""Typed exceptions for the experiments subsystem."""


class ExperimentError(Exception):
    """Base exception for all experiment-related errors."""


class ExperimentNotFoundError(ExperimentError):
    """Raised when a requested experiment does not exist."""

    def __init__(self, experiment_id: str) -> None:
        super().__init__(f"Experiment '{experiment_id}' not found.")
        self.experiment_id = experiment_id


class ExperimentAlreadyExistsError(ExperimentError):
    """Raised when trying to create an experiment with a duplicate ID."""

    def __init__(self, experiment_id: str) -> None:
        super().__init__(f"Experiment '{experiment_id}' already exists.")
        self.experiment_id = experiment_id


class InvalidExperimentStatusTransitionError(ExperimentError):
    """Raised when an invalid lifecycle transition is attempted."""

    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Cannot transition experiment from '{current}' to '{target}'.")
        self.current = current
        self.target = target


class ExperimentValidationError(ExperimentError):
    """Raised when experiment configuration fails validation."""


class ExperimentExecutionError(ExperimentError):
    """Raised when an error occurs during experiment execution."""


class ExperimentCancelledError(ExperimentError):
    """Raised when an experiment is cancelled during execution."""


class DatasetNotFoundError(ExperimentError):
    """Raised when a benchmark dataset is not found."""

    def __init__(self, dataset_id: str) -> None:
        super().__init__(f"Dataset '{dataset_id}' not found.")
        self.dataset_id = dataset_id
