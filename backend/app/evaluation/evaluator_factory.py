"""Factory for obtaining independent objective evaluators by problem type."""

from typing import Union
from backend.app.domain.problems.models import ProblemType
from backend.app.evaluation.interface import IEvaluator
from backend.app.evaluation.max_cut_evaluator import MaxCutEvaluator
from backend.app.evaluation.assignment_evaluator import AssignmentEvaluator
from backend.app.evaluation.tsp_evaluator import TSPEvaluator


class EvaluatorFactory:
    """Registry and factory for problem evaluators."""

    _evaluators = {
        ProblemType.MAX_CUT: MaxCutEvaluator(),
        ProblemType.ASSIGNMENT: AssignmentEvaluator(),
        ProblemType.TSP: TSPEvaluator(),
    }

    @classmethod
    def get_evaluator(cls, problem_type: Union[ProblemType, str]) -> IEvaluator:
        """Resolve the appropriate independent evaluator for the given problem type."""
        # Convert string to enum if necessary
        pt: ProblemType
        if isinstance(problem_type, str):
            try:
                pt = ProblemType(problem_type.lower())
            except ValueError:
                raise ValueError(
                    f"Unsupported problem type for evaluation: '{problem_type}'. Supported: {[p.value for p in ProblemType]}"
                )
        else:
            pt = problem_type

        evaluator = cls._evaluators.get(pt)
        if not evaluator:
            raise ValueError(f"No evaluator registered for problem type '{pt.value}'.")
        return evaluator
