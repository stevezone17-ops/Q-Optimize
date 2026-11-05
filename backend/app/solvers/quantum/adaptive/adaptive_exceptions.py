"""Domain exceptions for adaptive QAOA research and dynamic parameter strategies."""

from backend.app.solvers.quantum.exceptions import QuantumSolverError


class AdaptiveQAOAError(QuantumSolverError):
    """Base exception for all adaptive QAOA errors."""
    pass


class AdaptiveStrategyNotFoundError(AdaptiveQAOAError):
    """Raised when an unknown adaptive strategy identifier is requested."""
    pass


class IncompatibleWarmStartError(AdaptiveQAOAError):
    """Raised when warm-start parameter vector or source problem is incompatible with target Hamiltonian."""
    pass


class DepthLimitExceededError(AdaptiveQAOAError):
    """Raised when dynamic layer expansion exceeds maximum configured depth limit."""
    pass


class AdaptiveConvergenceError(AdaptiveQAOAError):
    """Raised when adaptive parameter search fails to converge within safety bounds."""
    pass


class AdaptiveOptimizerError(AdaptiveQAOAError):
    """Raised when classical optimizer controller fails or transitions invalidly."""
    pass


class IncompatibleTransferError(AdaptiveQAOAError):
    """Raised when parameter transfer dimensions or topologies do not match."""
    pass
