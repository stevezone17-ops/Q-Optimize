"""Adaptive QAOA parameter initialization strategies."""

from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Dict, Any, Union
import numpy as np

from backend.app.solvers.quantum.adaptive.adaptive_config import InitializationStrategyType
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import IncompatibleWarmStartError


class BaseParameterInitializer(ABC):
    """Abstract base class for parameter initialization strategies."""

    @abstractmethod
    def initialize(self, p: int, **kwargs) -> Tuple[List[float], List[float]]:
        """
        Generate initial variational parameter vectors (gamma, beta) for circuit depth p.
        Returns:
            Tuple of (gamma_list, beta_list), each of length p.
        """
        pass

    def _validate_lengths(self, gamma: List[float], beta: List[float], p: int) -> None:
        """Validate that generated vectors match depth p."""
        if len(gamma) != p or len(beta) != p:
            raise ValueError(
                f"Initializer produced invalid dimensions: len(gamma)={len(gamma)}, "
                f"len(beta)={len(beta)}, expected p={p}"
            )


class RandomInitializer(BaseParameterInitializer):
    """Uniformly distributed random parameter initialization."""

    def __init__(
        self,
        seed: Optional[int] = 42,
        gamma_range: Tuple[float, float] = (0.0, 2.0 * np.pi),
        beta_range: Tuple[float, float] = (0.0, np.pi),
    ):
        self.seed = seed
        self.gamma_range = gamma_range
        self.beta_range = beta_range

    def initialize(self, p: int, **kwargs) -> Tuple[List[float], List[float]]:
        if p < 1:
            raise ValueError(f"Circuit depth p must be >= 1, received {p}")
        seed = kwargs.get("seed", self.seed)
        rng = np.random.RandomState(seed)
        gamma = rng.uniform(self.gamma_range[0], self.gamma_range[1], size=p).tolist()
        beta = rng.uniform(self.beta_range[0], self.beta_range[1], size=p).tolist()
        self._validate_lengths(gamma, beta, p)
        return [float(g) for g in gamma], [float(b) for b in beta]


class LinearRampInitializer(BaseParameterInitializer):
    """
    Trotterized adiabatic ramp schedule:
    gamma_l = (l / p) * delta_t
    beta_l = (1 - l / p) * delta_t
    Smoothly transitions from driver mixer Hamiltonian to problem cost Hamiltonian.
    """

    def __init__(self, delta_t: float = 0.75):
        self.delta_t = delta_t

    def initialize(self, p: int, **kwargs) -> Tuple[List[float], List[float]]:
        if p < 1:
            raise ValueError(f"Circuit depth p must be >= 1, received {p}")
        dt = kwargs.get("delta_t", self.delta_t)
        if p == 1:
            # Special case for p=1: symmetric midpoint
            gamma = [0.5 * dt]
            beta = [0.5 * dt]
        else:
            gamma = [float((l / p) * dt) for l in range(1, p + 1)]
            beta = [float((1.0 - (l - 1) / p) * dt) for l in range(1, p + 1)]
        self._validate_lengths(gamma, beta, p)
        return gamma, beta


class FourierInitializer(BaseParameterInitializer):
    """
    Fourier-domain parameterization for QAOA variational angles (Zhou et al., 2020):
    gamma_l = sum_{k=0}^{q-1} u_k * cos((2k + 1) * l * pi / (2 * p))
    beta_l  = sum_{k=0}^{q-1} v_k * sin((2k + 1) * l * pi / (2 * p))
    where l in {1, ..., p} and q is the Fourier order.
    """

    def __init__(self, q_order: int = 2):
        self.q_order = max(1, q_order)

    @staticmethod
    def fourier_to_angles(
        u_coeffs: List[float],
        v_coeffs: List[float],
        p: int
    ) -> Tuple[List[float], List[float]]:
        """
        Evaluate variational angles (gamma, beta) for depth p from Fourier coefficients (u, v).
        """
        if p < 1:
            raise ValueError(f"Depth p must be >= 1, received {p}")
        q_u = len(u_coeffs)
        q_v = len(v_coeffs)
        if q_u == 0 or q_v == 0:
            raise ValueError("Fourier coefficient vectors u and v cannot be empty")

        gamma: List[float] = []
        beta: List[float] = []

        for l in range(1, p + 1):
            g_l = 0.0
            for k in range(q_u):
                angle = ((2 * k + 1) * l * np.pi) / (2.0 * p)
                g_l += u_coeffs[k] * np.cos(angle)
            gamma.append(float(g_l))

            b_l = 0.0
            for k in range(q_v):
                angle = ((2 * k + 1) * l * np.pi) / (2.0 * p)
                b_l += v_coeffs[k] * np.sin(angle)
            beta.append(float(b_l))

        return gamma, beta

    def initialize(self, p: int, **kwargs) -> Tuple[List[float], List[float]]:
        if p < 1:
            raise ValueError(f"Circuit depth p must be >= 1, received {p}")
        q = min(p, kwargs.get("fourier_q_order", self.q_order))
        u = kwargs.get("u_coeffs")
        v = kwargs.get("v_coeffs")

        if u is None or v is None:
            # Default smooth initialization: decaying harmonic coefficients
            u = [float(0.5 / (2 * k + 1)) for k in range(q)]
            v = [float(0.5 / (2 * k + 1)) for k in range(q)]

        return self.fourier_to_angles(u, v, p)


class WarmStartInitializer(BaseParameterInitializer):
    """
    Initializes variational parameters from prior optimization results.
    If depth p matches prior depth, returns exact prior parameters.
    If depth p > prior depth, applies linear interpolation or extension.
    """

    def __init__(
        self,
        prior_gamma: Optional[List[float]] = None,
        prior_beta: Optional[List[float]] = None,
    ):
        self.prior_gamma = prior_gamma
        self.prior_beta = prior_beta

    def initialize(self, p: int, **kwargs) -> Tuple[List[float], List[float]]:
        if p < 1:
            raise ValueError(f"Circuit depth p must be >= 1, received {p}")
        gamma = kwargs.get("prior_gamma", self.prior_gamma)
        beta = kwargs.get("prior_beta", self.prior_beta)

        if gamma is None or beta is None:
            raise IncompatibleWarmStartError(
                "Warm-start initialization requires prior_gamma and prior_beta vectors."
            )
        if len(gamma) != len(beta):
            raise IncompatibleWarmStartError(
                f"Dimension mismatch between prior_gamma ({len(gamma)}) and prior_beta ({len(beta)})"
            )

        p_prior = len(gamma)
        if p_prior == p:
            return [float(g) for g in gamma], [float(b) for b in beta]

        if p > p_prior:
            # Linear interpolation / expansion to higher depth
            x_old = np.linspace(0.0, 1.0, p_prior)
            x_new = np.linspace(0.0, 1.0, p)
            new_gamma = np.interp(x_new, x_old, gamma).tolist()
            new_beta = np.interp(x_new, x_old, beta).tolist()
            return [float(g) for g in new_gamma], [float(b) for b in new_beta]
        else:
            # Truncation to lower depth
            return [float(g) for g in gamma[:p]], [float(b) for b in beta[:p]]


class CustomInitializer(BaseParameterInitializer):
    """Allows user-specified exact parameter vectors with strict dimension validation."""

    def __init__(
        self,
        gamma: Optional[List[float]] = None,
        beta: Optional[List[float]] = None,
    ):
        self.gamma = gamma
        self.beta = beta

    def initialize(self, p: int, **kwargs) -> Tuple[List[float], List[float]]:
        if p < 1:
            raise ValueError(f"Circuit depth p must be >= 1, received {p}")
        gamma = kwargs.get("gamma", self.gamma)
        beta = kwargs.get("beta", self.beta)

        if gamma is None or beta is None:
            raise ValueError("Custom initialization requires explicit gamma and beta vectors.")
        if len(gamma) != p or len(beta) != p:
            raise ValueError(
                f"Custom angles dimension mismatch: len(gamma)={len(gamma)}, "
                f"len(beta)={len(beta)}, expected depth p={p}"
            )
        return [float(g) for g in gamma], [float(b) for b in beta]


class ParameterInitializerFactory:
    """Factory to instantiate the appropriate parameter initializer."""

    @staticmethod
    def get_initializer(
        strategy_type: Union[InitializationStrategyType, str],
        **kwargs
    ) -> BaseParameterInitializer:
        """Create and return a parameter initializer instance."""
        strat = (
            strategy_type.value
            if isinstance(strategy_type, InitializationStrategyType)
            else str(strategy_type).lower()
        )

        if strat == InitializationStrategyType.RANDOM.value:
            return RandomInitializer(
                seed=kwargs.get("seed", 42),
            )
        elif strat == InitializationStrategyType.LINEAR_RAMP.value:
            return LinearRampInitializer(
                delta_t=kwargs.get("delta_t", 0.75),
            )
        elif strat == InitializationStrategyType.FOURIER.value:
            return FourierInitializer(
                q_order=kwargs.get("fourier_q_order", 2),
            )
        elif strat == InitializationStrategyType.WARM_START.value:
            return WarmStartInitializer(
                prior_gamma=kwargs.get("prior_gamma"),
                prior_beta=kwargs.get("prior_beta"),
            )
        elif strat == InitializationStrategyType.CUSTOM.value:
            return CustomInitializer(
                gamma=kwargs.get("gamma"),
                beta=kwargs.get("beta"),
            )
        else:
            raise ValueError(f"Unknown initialization strategy: {strategy_type}")
