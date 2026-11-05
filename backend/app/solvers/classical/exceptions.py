"""Exceptions for classical optimization solvers."""


class ClassicalSolverError(Exception):
    """Base exception for all classical solver errors."""
    pass


class SolverNotFoundError(ClassicalSolverError):
    """Raised when a requested solver ID is not registered."""
    pass


class SolverNotImplementedError(ClassicalSolverError):
    """Raised when a requested solver is registered but not yet implemented."""
    pass


class SolverConfigurationError(ClassicalSolverError):
    """Raised when solver configuration parameters fail validation."""
    pass


class SolverTimeoutError(ClassicalSolverError):
    """Raised when solver execution exceeds the allocated time limit."""
    pass


class UnsupportedProblemTypeError(ClassicalSolverError):
    """Raised when a solver does not support the requested problem type."""
    pass

