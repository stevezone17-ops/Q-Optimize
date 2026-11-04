"""Independent evaluation interface specification."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List


class IEvaluator(ABC):
    """
    Independent evaluator ensuring candidate solutions are validated
    without trusting solver self-reporting.
    Scheduled for complete implementation across problem types in Phase 2.
    """

    @abstractmethod
    def evaluate_objective(self, problem_instance: Dict[str, Any], candidate: Any) -> float:
        raise NotImplementedError("Independent objective evaluation is scheduled for Phase 2.")

    @abstractmethod
    def check_feasibility(self, problem_instance: Dict[str, Any], candidate: Any) -> Tuple[bool, List[str]]:
        raise NotImplementedError("Independent feasibility validation is scheduled for Phase 2.")
