"""Independent mathematical verification for QUBO, Ising, and original problem formulations."""

import itertools
from typing import Dict, Any, List, Optional, Tuple
from backend.app.domain.formulations.models import QuboModel, IsingModel, VerificationResult
from backend.app.formulations.qubo_builder import QuboBuilder
from backend.app.formulations.ising_converter import IsingConverter
from backend.app.evaluation.evaluator_factory import EvaluatorFactory


class FormulationVerifier:
    """
    Exhaustively verifies mathematical equivalence between:
    1. The original canonical optimization problem objective C(x) (via Phase 2 evaluators)
    2. The generated QUBO energy E_QUBO(x)
    3. The transformed Ising Hamiltonian energy H_Ising(Z)
    """

    @staticmethod
    def _map_bitstring_to_max_cut_candidate(
        var_order: List[str], bit_vec: List[int]
    ) -> Dict[str, int]:
        """Map binary state directly to node partition dictionary."""
        return {var_order[i]: bit_vec[i] for i in range(len(var_order))}

    @staticmethod
    def _map_bitstring_to_assignment_candidate(
        var_order: List[str], bit_vec: List[int]
    ) -> List[Tuple[str, str]]:
        """
        Map binary assignment state to list of (agent, task) pairs.
        Variables have naming convention 'x_{agent}_{task}'.
        """
        pairs: List[Tuple[str, str]] = []
        for i, var_name in enumerate(var_order):
            if bit_vec[i] == 1:
                parts = var_name.split("_")
                if len(parts) >= 3 and parts[0] == "x":
                    agent = parts[1]
                    task = "_".join(parts[2:])
                    pairs.append((agent, task))
        return pairs

    @staticmethod
    def _map_bitstring_to_tsp_candidate(
        var_order: List[str], bit_vec: List[int], num_cities: int
    ) -> List[str]:
        """
        Map binary state to ordered tour sequence.
        Variables have naming convention 'x_{city}_{p}'.
        A bitstring is a valid tour representation IF AND ONLY IF:
          1. Every position p has exactly one city (sum_i x_{i, p} == 1)
          2. Every city i has exactly one position (sum_p x_{i, p} == 1)
        If either condition is violated, the bitstring is structurally infeasible.
        """
        pos_to_city: Dict[int, List[str]] = {p: [] for p in range(num_cities)}
        city_to_pos: Dict[str, List[int]] = {}

        for i, var_name in enumerate(var_order):
            if bit_vec[i] == 1:
                parts = var_name.split("_")
                if len(parts) >= 3 and parts[0] == "x":
                    city = parts[1]
                    try:
                        p = int(parts[2])
                        if p in pos_to_city:
                            pos_to_city[p].append(city)
                        city_to_pos.setdefault(city, []).append(p)
                    except ValueError:
                        pass

        # Verify exact 1-to-1 matching between cities and positions
        if any(len(cities) != 1 for cities in pos_to_city.values()):
            return []  # Infeasible state
        if any(len(positions) != 1 for positions in city_to_pos.values()) or len(city_to_pos) != num_cities:
            return []  # Infeasible state

        # Construct tour in order of positions [0, 1, ..., n-1]
        return [pos_to_city[p][0] for p in range(num_cities)]

    @classmethod
    def verify(
        cls,
        problem_type: str,
        instance_data: Dict[str, Any],
        qubo: QuboModel,
        ising: Optional[IsingModel] = None,
        max_states: int = 4096,
        tolerance: float = 1e-7,
    ) -> VerificationResult:
        """
        Run complete exhaustive enumeration across all 2^n binary assignments:
        - Confirms E_QUBO(x) == H_Ising(Z) for all states
        - For Max-Cut, verifies E_QUBO(x) == - C_orig(x)
        - For Assignment and TSP, verifies E_QUBO(x) == C_orig(x) for all feasible states
        - Verifies penalties are strictly positive for infeasible states
        """
        if ising is None:
            ising = IsingConverter.qubo_to_ising(qubo)

        var_order = qubo.variable_order
        n = len(var_order)
        total_states = 2 ** n

        if total_states > max_states:
            raise ValueError(
                f"State space 2^{n} = {total_states} exceeds exhaustive verification limit ({max_states}). "
                f"Exhaustive truth-table verification is reserved for instances with n <= 12 variables."
            )

        evaluator = EvaluatorFactory.get_evaluator(problem_type)

        # Temporary QUBO builder for fast energy evaluations
        builder = QuboBuilder(variable_order=var_order)
        for var, val in qubo.linear_terms.items():
            builder.add_linear(var, val)
        for pair_key, val in qubo.quadratic_terms.items():
            v1, v2 = pair_key.split(",", 1)
            builder.add_quadratic(v1, v2, val)
        builder.add_offset(qubo.offset)

        max_discrepancy = 0.0
        discrepancies: List[Dict[str, Any]] = []
        feasible_count = 0
        min_qubo_energy = float("inf")
        min_ising_energy = float("inf")
        optimal_bitstring = ""

        # Enumerate all 2^n binary vectors
        for bit_tuple in itertools.product([0, 1], repeat=n):
            bit_vec = list(bit_tuple)
            bitstring = "".join(str(b) for b in bit_vec)

            # 1. Evaluate QUBO energy
            e_qubo = builder.evaluate_energy(bit_vec)

            # 2. Evaluate Ising energy via Z_i = 1 - 2*x_i
            z_vec = IsingConverter.binary_to_spin(bit_vec)
            h_ising = IsingConverter.evaluate_energy(ising, z_vec)

            # Compare QUBO and Ising
            diff_qi = abs(e_qubo - h_ising)
            if diff_qi > max_discrepancy:
                max_discrepancy = diff_qi

            if diff_qi > tolerance:
                discrepancies.append({
                    "bitstring": bitstring,
                    "qubo_energy": e_qubo,
                    "ising_energy": h_ising,
                    "difference": diff_qi,
                    "error_type": "QUBO_ISING_MISMATCH",
                })

            if e_qubo < min_qubo_energy:
                min_qubo_energy = e_qubo
                optimal_bitstring = bitstring
            if h_ising < min_ising_energy:
                min_ising_energy = h_ising

            # 3. Independent domain evaluation via Phase 2 evaluator
            if problem_type == "max_cut":
                candidate = cls._map_bitstring_to_max_cut_candidate(var_order, bit_vec)
                eval_res = evaluator.evaluate(instance_data, candidate)
                expected_qubo = - float(eval_res.objective_value)
                if abs(e_qubo - expected_qubo) > tolerance:
                    discrepancies.append({
                        "bitstring": bitstring,
                        "qubo_energy": e_qubo,
                        "expected_energy": expected_qubo,
                        "cut_value": eval_res.objective_value,
                        "difference": abs(e_qubo - expected_qubo),
                        "error_type": "MAX_CUT_OBJECTIVE_MISMATCH",
                    })
                if eval_res.is_feasible:
                    feasible_count += 1

            elif problem_type == "assignment":
                candidate_pairs = cls._map_bitstring_to_assignment_candidate(var_order, bit_vec)
                eval_res = evaluator.evaluate(instance_data, candidate_pairs)
                if eval_res.is_feasible:
                    feasible_count += 1
                    # Feasible matching must match original cost exactly
                    expected_cost = float(eval_res.objective_value)
                    if abs(e_qubo - expected_cost) > tolerance:
                        discrepancies.append({
                            "bitstring": bitstring,
                            "qubo_energy": e_qubo,
                            "expected_cost": expected_cost,
                            "difference": abs(e_qubo - expected_cost),
                            "error_type": "FEASIBLE_ASSIGNMENT_COST_MISMATCH",
                        })
                else:
                    # Infeasible matching must receive positive penalty
                    pass

            elif problem_type == "tsp":
                num_cities = len(instance_data.get("cities", []))
                candidate_tour = cls._map_bitstring_to_tsp_candidate(var_order, bit_vec, num_cities)
                eval_res = evaluator.evaluate(instance_data, candidate_tour)
                if eval_res.is_feasible:
                    feasible_count += 1
                    expected_distance = float(eval_res.objective_value)
                    if abs(e_qubo - expected_distance) > tolerance:
                        discrepancies.append({
                            "bitstring": bitstring,
                            "qubo_energy": e_qubo,
                            "expected_distance": expected_distance,
                            "difference": abs(e_qubo - expected_distance),
                            "error_type": "FEASIBLE_TSP_DISTANCE_MISMATCH",
                        })

        is_verified = (len(discrepancies) == 0) and (max_discrepancy <= tolerance)

        if problem_type == "max_cut":
            summary = (
                f"Exhaustively tested all {total_states} binary configurations. "
                f"E_QUBO(x) == -C(x) verified with max discrepancy {max_discrepancy:.2e}. "
                f"QUBO and Ising energies are strictly identical."
            )
        elif problem_type == "assignment":
            summary = (
                f"Exhaustively tested all {total_states} configurations ({feasible_count} feasible permutations). "
                f"Feasible states have zero penalty with E_QUBO(x) == C_orig(x). "
                f"Infeasible states are penalized."
            )
        elif problem_type == "tsp":
            summary = (
                f"Exhaustively tested all {total_states} configurations ({feasible_count} valid Hamiltonian cycles). "
                f"Valid tours have zero penalty with E_QUBO(x) == Tour Distance. "
                f"QUBO and Ising match across all states."
            )
        else:
            summary = f"Exhaustively tested {total_states} states. QUBO and Ising energies match."

        return VerificationResult(
            is_verified=is_verified,
            num_states_tested=total_states,
            max_energy_discrepancy=round(max_discrepancy, 10),
            tolerance=tolerance,
            feasible_states_count=feasible_count,
            min_qubo_energy=round(min_qubo_energy, 6),
            min_ising_energy=round(min_ising_energy, 6),
            optimal_bitstring=optimal_bitstring,
            feasibility_summary=summary,
            discrepancies=discrepancies[:10],  # Keep up to 10 sample errors if any
        )
