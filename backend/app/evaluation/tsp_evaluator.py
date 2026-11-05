"""Independent Travelling Salesperson Problem (TSP) objective evaluator and feasibility verifier."""

from typing import Dict, Any, Tuple, List, Union, Optional
from backend.app.evaluation.interface import IEvaluator
from backend.app.evaluation.models import EvaluationResult, ObjectiveSense
from backend.app.evaluation.constraints import ConstraintValidator, ConstraintViolation


class TSPEvaluator(IEvaluator):
    """
    Evaluates Travelling Salesperson Problem (TSP) solutions independently:
    Objective:
        min sum_{k=0}^{N-1} D[tour[k], tour[k+1]]
        with tour[N] = tour[0] (closed Hamiltonian cycle)
    Feasibility:
        - Every city must be visited exactly once before returning to start.
        - Tour must return to start to form a closed cycle.
        - No unknown cities or sub-tours.
        - If start_city is configured, tour must begin with that city.
    """

    def _get_distance_map(
        self, cities: List[str], distance_matrix: List[List[float]]
    ) -> Dict[Tuple[str, str], float]:
        dist_map: Dict[Tuple[str, str], float] = {}
        for i, c_from in enumerate(cities):
            for j, c_to in enumerate(cities):
                if i < len(distance_matrix) and j < len(distance_matrix[i]):
                    dist_map[(c_from, c_to)] = float(distance_matrix[i][j])
        return dist_map

    def check_feasibility(
        self, problem_instance: Dict[str, Any], candidate: Any
    ) -> Tuple[bool, List[ConstraintViolation]]:
        cities = problem_instance.get("cities", [])
        start_city = problem_instance.get("start_city", None)
        violations, _ = ConstraintValidator.validate_tsp_tour(
            cities, candidate, start_city=start_city
        )
        return len(violations) == 0, violations

    def evaluate_objective(
        self, problem_instance: Dict[str, Any], candidate: Any
    ) -> float:
        cities = problem_instance.get("cities", [])
        distance_matrix = problem_instance.get("distance_matrix", [])
        start_city = problem_instance.get("start_city", None)

        _, closed_tour = ConstraintValidator.validate_tsp_tour(
            cities, candidate, start_city=start_city
        )
        if len(closed_tour) < 2:
            return 0.0

        dist_map = self._get_distance_map(cities, distance_matrix)
        total_dist = 0.0
        for i in range(len(closed_tour) - 1):
            c_from = closed_tour[i]
            c_to = closed_tour[i + 1]
            total_dist += dist_map.get((c_from, c_to), 0.0)

        return total_dist

    def evaluate(
        self, problem_instance: Dict[str, Any], candidate: Any
    ) -> EvaluationResult:
        cities = problem_instance.get("cities", [])
        distance_matrix = problem_instance.get("distance_matrix", [])
        start_city = problem_instance.get("start_city", None)

        violations, closed_tour = ConstraintValidator.validate_tsp_tour(
            cities, candidate, start_city=start_city
        )
        is_feasible = len(violations) == 0

        dist_map = self._get_distance_map(cities, distance_matrix)
        legs = []
        total_distance = 0.0

        if len(closed_tour) >= 2:
            for i in range(len(closed_tour) - 1):
                c_from = closed_tour[i]
                c_to = closed_tour[i + 1]
                leg_dist = dist_map.get((c_from, c_to), 0.0)
                total_distance += leg_dist
                legs.append({
                    "from": c_from,
                    "to": c_to,
                    "distance": leg_dist,
                    "leg_index": i + 1,
                })

        # Check matrix symmetry
        n = len(cities)
        is_symmetric = True
        for i in range(n):
            for j in range(i + 1, n):
                if i < len(distance_matrix) and j < len(distance_matrix[i]):
                    if distance_matrix[i][j] != distance_matrix[j][i]:
                        is_symmetric = False
                        break
            if not is_symmetric:
                break

        details = {
            "tour": closed_tour,
            "legs": legs,
            "total_distance": total_distance,
            "num_cities": len(cities),
            "is_symmetric": is_symmetric,
            "start_city": closed_tour[0] if closed_tour else start_city,
            "average_leg_distance": (total_distance / len(legs)) if legs else 0.0,
        }

        return EvaluationResult(
            problem_type="tsp",
            objective_sense=ObjectiveSense.MINIMIZE,
            objective_value=total_distance,
            is_feasible=is_feasible,
            violations=violations,
            details=details,
        )

