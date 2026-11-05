"""Travelling Salesperson Problem (TSP) position-based canonical QUBO formulation generator."""

from typing import Dict, Any, List, Optional
from backend.app.domain.formulations.models import QuboModel
from backend.app.formulations.qubo_builder import QuboBuilder
from backend.app.formulations.penalties import PenaltyManager


class TSPQuboGenerator:
    """
    Constructs the position-based canonical minimization QUBO for the Travelling Salesperson Problem:
    Decision variables:
        x_{i, p} in {0, 1} where i is a city and p in {0, ..., n-1} is its tour visit position.
    Objective:
        min sum_{p=0}^{n-1} sum_{i != j} D_{ij} * x_{i, p} * x_{j, (p+1) mod n}
    Constraints:
        1. City constraint: Each city i must occupy exactly one position p:
           P_city = A * sum_i (sum_p x_{i, p} - 1)^2
        2. Position constraint: Each position p must contain exactly one city i:
           P_pos  = B * sum_p (sum_i x_{i, p} - 1)^2
        3. Starting city (optional):
           P_start = S * (x_{start, 0} - 1)^2 = -S * x_{start, 0} + S
    Total QUBO:
        Linear terms:
            Q_{(i,p), (i,p)} = - A - B   (plus -S if city i == start_city and p == 0)
        Quadratic terms:
            - Same city, different positions: Q_{(i,p), (i,q)} = 2 * A  (for p < q)
            - Same position, different cities: Q_{(i,p), (j,p)} = 2 * B  (for i < j)
            - Consecutive tour legs: Q_{(i,p), (j, (p+1)%n)} += D_{ij}
        Offset:
            c = n * A + n * B  (plus S if start_city specified)
    Feasibility guarantee:
        Any valid Hamiltonian cycle has P_city == 0 and P_pos == 0.
        E_QUBO(x) == Tour Distance for all valid tours.
    """

    @staticmethod
    def generate(
        instance_data: Dict[str, Any],
        penalty_coefficients: Optional[Dict[str, float]] = None,
    ) -> QuboModel:
        cities: List[str] = instance_data.get("cities", [])
        distance_matrix: List[List[float]] = instance_data.get("distance_matrix", [])
        start_city: Optional[str] = instance_data.get("start_city", None)

        n = len(cities)
        if n < 3:
            raise ValueError(f"TSP requires at least 3 cities for a closed Hamiltonian cycle, got {n}.")

        # Resolve penalties
        penalties, warnings = PenaltyManager.resolve_penalties(
            problem_type="tsp",
            instance_data=instance_data,
            user_penalties=penalty_coefficients,
        )
        penalty_a = penalties.get("A", 10.0)
        penalty_b = penalties.get("B", 10.0)
        penalty_s = penalties.get("S", max(penalty_a, penalty_b)) if start_city else 0.0

        # Canonical variable ordering: x_{city}_{p}
        variable_order: List[str] = []
        for city in cities:
            for p in range(n):
                variable_order.append(f"x_{city}_{p}")

        builder = QuboBuilder(variable_order=variable_order)

        # 1. Linear terms: -A - B for every x_{i, p}
        for city in cities:
            for p in range(n):
                var_name = f"x_{city}_{p}"
                linear_val = - penalty_a - penalty_b
                if start_city and city == start_city and p == 0:
                    linear_val -= penalty_s
                builder.add_linear(var_name, linear_val)

        # 2. City constraint quadratic terms: +2A * x_{i, p} * x_{i, q} for p < q
        for city in cities:
            for p in range(n):
                for q in range(p + 1, n):
                    var_p = f"x_{city}_{p}"
                    var_q = f"x_{city}_{q}"
                    builder.add_quadratic(var_p, var_q, 2.0 * penalty_a)

        # 3. Position constraint quadratic terms: +2B * x_{i, p} * x_{j, p} for i < j
        for p in range(n):
            for i in range(n):
                for j in range(i + 1, n):
                    var_i = f"x_{cities[i]}_{p}"
                    var_j = f"x_{cities[j]}_{p}"
                    builder.add_quadratic(var_i, var_j, 2.0 * penalty_b)

        # 4. Objective distance quadratic terms: D_{ij} * x_{i, p} * x_{j, (p+1) % n}
        for p in range(n):
            next_p = (p + 1) % n
            for i in range(n):
                for j in range(n):
                    if i != j:
                        dist_ij = float(distance_matrix[i][j])
                        if dist_ij != 0.0:
                            var_from = f"x_{cities[i]}_{p}"
                            var_to = f"x_{cities[j]}_{next_p}"
                            builder.add_quadratic(var_from, var_to, dist_ij)

        # 5. Constant offset: n * (A + B) (+ S if starting city enforced)
        total_offset = n * (penalty_a + penalty_b) + penalty_s
        builder.add_offset(total_offset)

        builder.penalties = {"A": penalty_a, "B": penalty_b}
        if start_city:
            builder.penalties["S"] = penalty_s

        builder.assumptions = [
            f"Position-based binary encoding with {n*n} variables ({n} cities x {n} positions).",
            f"City penalty A = {penalty_a} enforces each city is visited exactly once.",
            f"Position penalty B = {penalty_b} enforces each step contains exactly one city.",
            f"Cyclic transition connects position {n-1} back to position 0.",
            "Valid tours have zero penalty: E_QUBO(x) == Tour Distance.",
        ]
        if start_city:
            builder.assumptions.append(f"Starting city penalty S = {penalty_s} enforces tour starts at '{start_city}'.")

        builder.metadata = {
            "problem_type": "tsp",
            "num_cities": n,
            "num_positions": n,
            "total_variables": n * n,
            "start_city": start_city,
            "penalty_warnings": warnings,
            "offset": total_offset,
        }

        return builder.build_model()
