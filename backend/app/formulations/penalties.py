"""Reusable penalty coefficient management and sufficiency analysis."""

import math
from typing import Dict, Any, Tuple, List, Optional
from pydantic import BaseModel, Field


class PenaltyRecommendation(BaseModel):
    """Recommended penalty values with mathematical justification."""
    recommended_penalties: Dict[str, float] = Field(..., description="Calculated default penalty coefficients")
    minimum_safe_bounds: Dict[str, float] = Field(..., description="Estimated minimum safe penalty thresholds")
    justification: str = Field(..., description="Mathematical derivation and justification")
    warnings: List[str] = Field(default_factory=list, description="Warnings regarding penalty parameter regimes")


class PenaltyManager:
    """Manages penalty coefficients, validation, and sufficiency bounds."""

    @staticmethod
    def validate_penalties(penalties: Dict[str, float]) -> Dict[str, float]:
        """Validate that all penalty coefficients are strictly positive and finite."""
        validated: Dict[str, float] = {}
        for name, val in penalties.items():
            try:
                v = float(val)
            except (ValueError, TypeError):
                raise ValueError(f"Penalty coefficient '{name}' must be numeric, got {val}")
            if not math.isfinite(v):
                raise ValueError(f"Penalty coefficient '{name}' must be finite, got {v}")
            if v <= 0.0:
                raise ValueError(f"Penalty coefficient '{name}' must be strictly positive (> 0), got {v}")
            validated[name] = v
        return validated

    @staticmethod
    def get_assignment_penalty_bounds(
        cost_matrix: List[List[float]],
        num_agents: int,
        num_tasks: int,
    ) -> PenaltyRecommendation:
        """
        Derive recommended penalty bounds for square Linear Assignment:
            min sum_{ij} c_{ij} x_{ij} + A * P_row + B * P_col
        Sufficiency derivation:
            Let Delta_C = max(c_{ij}) - min(c_{ij}).
            Any constraint violation in a row or column incurs a penalty of at least A or B.
            For a single agent/task violation to never be advantageous over the worst-case
            feasible matching, we recommend:
                A = B >= max(10.0, 1.5 * n * (Delta_C + 1.0))
        """
        flat_costs = [float(cell) for row in cost_matrix for cell in row]
        if not flat_costs:
            flat_costs = [1.0]

        min_c = min(flat_costs)
        max_c = max(flat_costs)
        delta_c = max(0.0, max_c - min_c)
        n = max(num_agents, num_tasks)

        # Minimum bound where penalties begin to compete with individual cell costs
        min_bound = max(1.0, max(abs(min_c), abs(max_c)))
        # Recommended robust penalty bound
        recommended = max(10.0, round(1.5 * n * (delta_c + 1.0), 2))

        return PenaltyRecommendation(
            recommended_penalties={"A": recommended, "B": recommended},
            minimum_safe_bounds={"A": min_bound, "B": min_bound},
            justification=(
                f"For {n}x{n} assignment with cost spread Delta_C = {delta_c:.2f}, "
                f"A = B = {recommended:.2f} ensures constraint penalties dominate potential cost deltas."
            ),
            warnings=[],
        )

    @staticmethod
    def get_tsp_penalty_bounds(
        distance_matrix: List[List[float]],
        num_cities: int,
    ) -> PenaltyRecommendation:
        """
        Derive recommended penalty bounds for TSP position formulation:
            min D_tour + A * P_city + B * P_position
        Sufficiency derivation:
            Let D_max = max(D_{ij}).
            If an invalid tour omits a city or duplicates a position, it might save at most
            n * D_max in travel distance.
            To guarantee every infeasible state is penalized above the feasible optimal tour:
                A = B >= max(10.0, 1.5 * n * D_max)
        """
        flat_dists = [
            float(distance_matrix[i][j])
            for i in range(len(distance_matrix))
            for j in range(len(distance_matrix[i]))
            if i != j
        ]
        d_max = max(flat_dists) if flat_dists else 10.0
        n = num_cities

        min_bound = max(1.0, d_max)
        recommended = max(10.0, round(1.5 * n * d_max, 2))

        return PenaltyRecommendation(
            recommended_penalties={"A": recommended, "B": recommended},
            minimum_safe_bounds={"A": min_bound, "B": min_bound},
            justification=(
                f"For {n}-city TSP with max inter-city distance D_max = {d_max:.2f}, "
                f"A = B = {recommended:.2f} guarantees invalid tours (omitted/duplicate cities) "
                f"incur penalties exceeding any shortcut distance reduction."
            ),
            warnings=[],
        )

    @staticmethod
    def resolve_penalties(
        problem_type: str,
        instance_data: Dict[str, Any],
        user_penalties: Optional[Dict[str, float]] = None,
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Resolve penalty coefficients:
        Uses user-specified values if provided and valid, otherwise calculates
        mathematically justified recommendations.
        Emits warnings if user values fall below minimum safe bounds.
        """
        warnings: List[str] = []

        if problem_type == "assignment":
            cost_matrix = instance_data.get("cost_matrix", [])
            agents = instance_data.get("agents", [])
            tasks = instance_data.get("tasks", [])
            rec = PenaltyManager.get_assignment_penalty_bounds(cost_matrix, len(agents), len(tasks))
        elif problem_type == "tsp":
            distance_matrix = instance_data.get("distance_matrix", [])
            cities = instance_data.get("cities", [])
            rec = PenaltyManager.get_tsp_penalty_bounds(distance_matrix, len(cities))
        else:
            # Max-Cut has no equality constraint penalties
            return {}, []

        if user_penalties:
            validated_user = PenaltyManager.validate_penalties(user_penalties)
            final_penalties = dict(rec.recommended_penalties)
            for k, val in validated_user.items():
                final_penalties[k] = val
                min_safe = rec.minimum_safe_bounds.get(k, 1.0)
                if val < min_safe:
                    warnings.append(
                        f"User-specified penalty '{k}'={val} is below the estimated minimum safe bound ({min_safe}). "
                        f"Infeasible solutions with constraint violations may be preferred by the solver."
                    )
            return final_penalties, warnings

        return rec.recommended_penalties, warnings
