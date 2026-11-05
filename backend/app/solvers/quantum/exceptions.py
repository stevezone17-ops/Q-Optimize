"""Domain exceptions for quantum optimization algorithms and Qiskit execution."""


class QuantumSolverError(Exception):
    """Base exception for all quantum solver errors."""
    pass


class BackendNotAvailableError(QuantumSolverError):
    """Raised when a requested quantum backend or simulator is not available."""
    pass


class UnsupportedSimulationMethodError(QuantumSolverError):
    """Raised when a requested simulation method is not supported by the backend."""
    pass


class QuantumResourceLimitExceeded(QuantumSolverError):
    """Base exception when a quantum configuration exceeds platform resource limits."""
    pass


class QubitLimitExceededError(QuantumResourceLimitExceeded):
    """Raised when the required number of qubits exceeds platform limits."""
    pass


class ShotLimitExceededError(QuantumResourceLimitExceeded):
    """Raised when the requested number of measurement shots exceeds platform limits."""
    pass


class CircuitConstructionError(QuantumSolverError):
    """Raised when parameterized circuit generation or unitary evolution fails."""
    pass


class TranspilationError(QuantumSolverError):
    """Raised when quantum circuit transpilation fails."""
    pass


class ExecutionTimeoutError(QuantumSolverError):
    """Raised when quantum execution exceeds the configured wall-clock time limit."""
    pass


class CancellationError(QuantumSolverError):
    """Raised when a quantum execution is cooperatively cancelled by user request."""
    pass
