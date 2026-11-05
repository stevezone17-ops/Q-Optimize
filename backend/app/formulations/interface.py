"""Formulation engine interface specification for QUBO and Ising models."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.app.domain.formulations.models import QuboModel, IsingModel, FormulationResponse


class IFormulationEngine(ABC):
    """Interface for converting canonical optimization problems to QUBO and Ising formulations."""

    @abstractmethod
    def generate_qubo(
        self,
        problem_type: str,
        problem_instance: Dict[str, Any],
        penalty_coefficients: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> QuboModel:
        """Construct canonical quadratic unconstrained binary optimization model."""
        raise NotImplementedError

    @abstractmethod
    def qubo_to_ising(self, qubo: QuboModel) -> IsingModel:
        """Convert QUBO 0/1 binary variables to Ising -1/+1 spins with energy equivalence."""
        raise NotImplementedError
