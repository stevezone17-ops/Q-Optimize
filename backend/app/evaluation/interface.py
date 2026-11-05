"""Independent evaluation interface specification for Q-Optimize."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List
from backend.app.evaluation.models import EvaluationResult
from backend.app.evaluation.constraints import ConstraintViolation


class IEvaluator(ABC):
    """
    Independent evaluator ensuring candidate solutions are validated
    mathematically without trusting solver self-reporting.
    """

    @abstractmethod
    def evaluate(self, problem_instance: Dict[str, Any], candidate: Any) -> EvaluationResult:
        """
        Perform complete, independent evaluation of candidate solution.
        Calculates exact objective value and tests all problem constraints.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate_objective(self, problem_instance: Dict[str, Any], candidate: Any) -> float:
        """Calculate pure objective value."""
        raise NotImplementedError

    @abstractmethod
    def check_feasibility(self, problem_instance: Dict[str, Any], candidate: Any) -> Tuple[bool, List[ConstraintViolation]]:
        """Validate candidate feasibility and return any violations."""
        raise NotImplementedError
