"""Linear Assignment Problem canonical QUBO formulation generator."""

from typing import Dict, Any, List, Optional
from backend.app.domain.formulations.models import QuboModel
from backend.app.formulations.qubo_builder import QuboBuilder
from backend.app.formulations.penalties import PenaltyManager


class AssignmentQuboGenerator:
    """
    Constructs the canonical minimization QUBO for the Linear Assignment Problem:
    Objective:
        min sum_{i=1}^n sum_{j=1}^m c_{ij} * x_{ij}
    Equality constraints for square matching (n == m):
        Agent constraint: sum_{j=1}^n x_{ij} = 1  for all agents i
        Task constraint:  sum_{i=1}^n x_{ij} = 1  for all tasks j
    Penalty expansions:
        P_row = A * sum_i (sum_j x_{ij} - 1)^2
              = A * [ - sum_{ij} x_{ij} + 2 * sum_{i, j < k} x_{ij} x_{ik} + n ]
        P_col = B * sum_j (sum_i x_{ij} - 1)^2
              = B * [ - sum_{ij} x_{ij} + 2 * sum_{j, i < k} x_{ij} x_{kj} + n ]
    Total QUBO:
        E(x) = sum_{ij} (c_{ij} - A - B) * x_{ij}
             + sum_{i, j < k} 2*A * x_{ij} x_{ik}
             + sum_{j, i < k} 2*B * x_{ij} x_{kj}
             + n * (A + B)
    Feasibility guarantee:
        For any feasible 1-to-1 matching, P_row = 0 and P_col = 0, so E(x) == C_orig(x).
        For any infeasible assignment, penalties > 0 raise the energy.
    """

    @staticmethod
    def generate(
        instance_data: Dict[str, Any],
        penalty_coefficients: Optional[Dict[str, float]] = None,
    ) -> QuboModel:
        agents: List[str] = instance_data.get("agents", [])
        tasks: List[str] = instance_data.get("tasks", [])
        cost_matrix: List[List[float]] = instance_data.get("cost_matrix", [])

        num_agents = len(agents)
        num_tasks = len(tasks)

        if num_agents < 1 or num_tasks < 1:
            raise ValueError("Assignment problem requires at least 1 agent and 1 task.")

        # Reject rectangular instances with clear, unambiguous message
        if num_agents != num_tasks:
            raise ValueError(
                f"Standard 1-to-1 matching equality constraints require square dimensions. "
                f"Received rectangular instance with {num_agents} agents and {num_tasks} tasks. "
                f"Rectangular matching with unequal cardinality requires explicit slack variables."
            )

        n = num_agents

        # Resolve penalties
        penalties, warnings = PenaltyManager.resolve_penalties(
            problem_type="assignment",
            instance_data=instance_data,
            user_penalties=penalty_coefficients,
        )
        penalty_a = penalties.get("A", 10.0)
        penalty_b = penalties.get("B", 10.0)

        # Canonical variable ordering: x_{agent}_{task}
        variable_order: List[str] = []
        for agent in agents:
            for task in tasks:
                variable_order.append(f"x_{agent}_{task}")

        builder = QuboBuilder(variable_order=variable_order)

        # 1. Linear objective costs and constraint diagonal contributions: c_{ij} - A - B
        for i, agent in enumerate(agents):
            for j, task in enumerate(tasks):
                var_name = f"x_{agent}_{task}"
                cost_ij = float(cost_matrix[i][j])
                builder.add_linear(var_name, cost_ij - penalty_a - penalty_b)

        # 2. Row constraint penalties: +2A * x_{i,j} * x_{i,k} for j < k
        for i, agent in enumerate(agents):
            for j in range(num_tasks):
                for k in range(j + 1, num_tasks):
                    var_j = f"x_{agent}_{tasks[j]}"
                    var_k = f"x_{agent}_{tasks[k]}"
                    builder.add_quadratic(var_j, var_k, 2.0 * penalty_a)

        # 3. Column constraint penalties: +2B * x_{i,j} * x_{k,j} for i < k
        for j, task in enumerate(tasks):
            for i in range(num_agents):
                for k in range(i + 1, num_agents):
                    var_i = f"x_{agents[i]}_{task}"
                    var_k = f"x_{agents[k]}_{task}"
                    builder.add_quadratic(var_i, var_k, 2.0 * penalty_b)

        # 4. Constant offset: n * (A + B)
        builder.add_offset(n * (penalty_a + penalty_b))

        builder.penalties = {"A": penalty_a, "B": penalty_b}
        builder.assumptions = [
            f"Square {n}x{n} assignment problem with bijective 1-to-1 matching.",
            f"Row penalty A = {penalty_a} enforces each agent receives exactly 1 task.",
            f"Column penalty B = {penalty_b} enforces each task is assigned to exactly 1 agent.",
            "Feasible states have zero penalty: E_QUBO(x) == C_orig(x).",
        ]
        builder.metadata = {
            "problem_type": "assignment",
            "num_agents": num_agents,
            "num_tasks": num_tasks,
            "is_square": True,
            "penalty_warnings": warnings,
            "offset": n * (penalty_a + penalty_b),
        }

        return builder.build_model()
