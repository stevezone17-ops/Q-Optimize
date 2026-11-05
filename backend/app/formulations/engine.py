"""Master formulation engine implementing IFormulationEngine."""

from typing import Dict, Any, Optional
from backend.app.domain.formulations.models import QuboModel, IsingModel
from backend.app.formulations.interface import IFormulationEngine
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.formulations.assignment_qubo import AssignmentQuboGenerator
from backend.app.formulations.tsp_qubo import TSPQuboGenerator
from backend.app.formulations.ising_converter import IsingConverter


class FormulationEngine(IFormulationEngine):
    """Core engine converting canonical problems into verified QUBO and Ising formulations."""

    def generate_qubo(
        self,
        problem_type: str,
        problem_instance: Dict[str, Any],
        penalty_coefficients: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> QuboModel:
        if hasattr(problem_type, "value"):
            p_type = str(problem_type.value).lower().strip()
        else:
            p_type = str(problem_type).split(".")[-1].lower().strip()

        if p_type == "max_cut":
            return MaxCutQuboGenerator.generate(problem_instance)
        elif p_type == "assignment":
            return AssignmentQuboGenerator.generate(problem_instance, penalty_coefficients=penalty_coefficients)
        elif p_type == "tsp":
            return TSPQuboGenerator.generate(problem_instance, penalty_coefficients=penalty_coefficients)
        else:
            raise ValueError(
                f"Unsupported problem type for QUBO generation: '{problem_type}'. "
                f"Supported types: ['max_cut', 'assignment', 'tsp']"
            )

    def qubo_to_ising(self, qubo: QuboModel) -> IsingModel:
        return IsingConverter.qubo_to_ising(qubo)
