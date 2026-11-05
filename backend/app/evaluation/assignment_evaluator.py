"""Independent Linear Assignment objective evaluator and feasibility verifier."""

from typing import Dict, Any, Tuple, List, Union
from backend.app.evaluation.interface import IEvaluator
from backend.app.evaluation.models import EvaluationResult, ObjectiveSense
from backend.app.evaluation.constraints import ConstraintValidator, ConstraintViolation


class AssignmentEvaluator(IEvaluator):
    """
    Evaluates Linear Assignment problem solutions independently:
    Objective:
        min sum_{i=1}^n sum_{j=1}^m c_{ij} * x_{ij}
        where x_{ij} in {0, 1}
    Feasibility:
        sum_{j} x_{ij} <= 1 for all agents i (== 1 for square matching)
        sum_{i} x_{ij} <= 1 for all tasks j (== 1 for square matching)
    """

    def _get_cost_map(
        self, agents: List[str], tasks: List[str], cost_matrix: List[List[float]]
    ) -> Dict[Tuple[str, str], float]:
        cost_map: Dict[Tuple[str, str], float] = {}
        for i, agent in enumerate(agents):
            for j, task in enumerate(tasks):
                if i < len(cost_matrix) and j < len(cost_matrix[i]):
                    cost_map[(agent, task)] = float(cost_matrix[i][j])
        return cost_map

    def check_feasibility(
        self, problem_instance: Dict[str, Any], candidate: Any
    ) -> Tuple[bool, List[ConstraintViolation]]:
        agents = problem_instance.get("agents", [])
        tasks = problem_instance.get("tasks", [])
        is_square = len(agents) == len(tasks)
        violations, _ = ConstraintValidator.validate_assignment_constraints(
            agents, tasks, candidate, is_square=is_square
        )
        return len(violations) == 0, violations

    def evaluate_objective(
        self, problem_instance: Dict[str, Any], candidate: Any
    ) -> float:
        agents = problem_instance.get("agents", [])
        tasks = problem_instance.get("tasks", [])
        cost_matrix = problem_instance.get("cost_matrix", [])
        is_square = len(agents) == len(tasks)

        _, pairs = ConstraintValidator.validate_assignment_constraints(
            agents, tasks, candidate, is_square=is_square
        )
        cost_map = self._get_cost_map(agents, tasks, cost_matrix)

        total_cost = 0.0
        for agent, task in pairs:
            if (agent, task) in cost_map:
                total_cost += cost_map[(agent, task)]

        return total_cost

    def evaluate(
        self, problem_instance: Dict[str, Any], candidate: Any
    ) -> EvaluationResult:
        agents = problem_instance.get("agents", [])
        tasks = problem_instance.get("tasks", [])
        cost_matrix = problem_instance.get("cost_matrix", [])
        is_square = len(agents) == len(tasks)

        violations, pairs = ConstraintValidator.validate_assignment_constraints(
            agents, tasks, candidate, is_square=is_square
        )
        is_feasible = len(violations) == 0
        cost_map = self._get_cost_map(agents, tasks, cost_matrix)

        assignment_details = []
        total_cost = 0.0
        assigned_agents = set()
        assigned_tasks = set()

        for agent, task in pairs:
            assigned_agents.add(agent)
            assigned_tasks.add(task)
            cost = cost_map.get((agent, task), 0.0)
            total_cost += cost
            assignment_details.append({
                "agent": agent,
                "task": task,
                "cost": cost,
            })

        unassigned_agents = [a for a in agents if a not in assigned_agents]
        unassigned_tasks = [t for t in tasks if t not in assigned_tasks]

        details = {
            "assignments": assignment_details,
            "total_cost": total_cost,
            "assigned_count": len(pairs),
            "unassigned_agents": unassigned_agents,
            "unassigned_tasks": unassigned_tasks,
            "is_square": is_square,
            "average_cost": (total_cost / len(pairs)) if pairs else 0.0,
        }

        return EvaluationResult(
            problem_type="assignment",
            objective_sense=ObjectiveSense.MINIMIZE,
            objective_value=total_cost,
            is_feasible=is_feasible,
            violations=violations,
            details=details,
        )
