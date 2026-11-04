"""Formulation interface specification for QUBO and Ising models (Phase 3)."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from backend.app.domain.formulations.models import FormulationResponse


class IFormulationEngine(ABC):
    """
    Interface for converting canonical problems to QUBO and Ising formulations.
    Scheduled for full implementation in Phase 3.
    """

    @abstractmethod
    def generate_qubo(self, problem_instance: Dict[str, Any], **kwargs: Any) -> FormulationResponse:
        """Construct quadratic unconstrained binary optimization matrix."""
        raise NotImplementedError("Formulation engine is scheduled for Phase 3.")

    @abstractmethod
    def qubo_to_ising(self, qubo_formulation: FormulationResponse) -> FormulationResponse:
        """Convert QUBO 0/1 binary variables to Ising -1/+1 spins with energy equivalence verification."""
        raise NotImplementedError("QUBO to Ising conversion is scheduled for Phase 3.")
