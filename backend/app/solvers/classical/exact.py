"""Exact classical optimization solver supporting Max-Cut, Assignment, and TSP."""

import time
import itertools
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import scipy.optimize

from backend.app.domain.problems.models import ProblemType
from backend.app.solvers.classical.base import IClassicalSolver
from backend.app.solvers.classical.models import (
    SolverConfiguration,
    SolverResult,
    SolverStatus,
    OptimalityStatus,
    ConvergencePoint,
)
from backend.app.evaluation.evaluator_factory import EvaluatorFactory


class ExactSolver(IClassicalSolver):
    """
    Exact classical optimization solver.
    Provides mathematically guaranteed global optima for small instances:
    - Max-Cut: Exhaustive binary partition enumeration with reflection symmetry exploitation.
    - Assignment: Hungarian algorithm (Kuhn-Munkres) via SciPy.
    - TSP: Full permutation enumeration of Hamiltonian cycles with starting vertex pinning.
    """

    MAX_MAX_CUT_VARIABLES = 18
    MAX_TSP_CITIES = 10
    MAX_ASSIGNMENT_DIMENSION = 100

    @property
    def solver_id(self) -> str:
        return "exact"

    @property
    def name(self) -> str:
        return "Exact Classical Solver"

    @property
    def description(self) -> str:
        return (
            "Deterministic global optimization via exhaustive enumeration and Hungarian matching. "
            "Guarantees proven global optimum within practical instance size limits."
        )

    @property
    def supported_problem_types(self) -> List[ProblemType]:
        return [ProblemType.MAX_CUT, ProblemType.ASSIGNMENT, ProblemType.TSP]

    @property
    def is_implemented(self) -> bool:
        return True

    @property
    def stage_introduced(self) -> str:
        return "Stage 4.2"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "time_limit_seconds": {
                "type": "float",
                "default": 60.0,
                "description": "Maximum execution time in seconds",
            },
            "max_variables": {
                "type": "integer",
                "default": 18,
                "description": "Safety threshold for exhaustive enumeration search space",
            },
        }

    def solve(
        self,
        problem_type: ProblemType,
        instance: Dict[str, Any],
        config: Optional[SolverConfiguration] = None,
        seed: Optional[int] = 42,
    ) -> SolverResult:
        """Solve an optimization problem instance to exact global optimality."""
        self.check_problem_support(problem_type)

        time_limit = config.time_limit_seconds if config and config.time_limit_seconds else 60.0
        max_vars = int(config.extra_params.get("max_variables", self.MAX_MAX_CUT_VARIABLES)) if config else self.MAX_MAX_CUT_VARIABLES

        t0 = time.perf_counter()

        # Dispatch problem-specific exact search
        if problem_type == ProblemType.MAX_CUT:
            candidate, evaluations, iterations, completed, reason = self._solve_max_cut(instance, time_limit, max_vars)
        elif problem_type == ProblemType.ASSIGNMENT:
            candidate, evaluations, iterations, completed, reason = self._solve_assignment(instance, time_limit)
        elif problem_type == ProblemType.TSP:
            candidate, evaluations, iterations, completed, reason = self._solve_tsp(instance, time_limit)
        else:
            raise ValueError(f"Unsupported problem type: {problem_type}")

        runtime_seconds = time.perf_counter() - t0

        # Independent evaluation using Phase 2 evaluation engine
        evaluator = EvaluatorFactory.get_evaluator(problem_type)
        eval_result = evaluator.evaluate(instance, candidate)

        optimality = (
            OptimalityStatus.PROVEN_OPTIMAL
            if (completed and eval_result.is_feasible)
            else (OptimalityStatus.HEURISTIC_FEASIBLE if eval_result.is_feasible else OptimalityStatus.HEURISTIC_INFEASIBLE)
        )

        status = SolverStatus.COMPLETED if completed else SolverStatus.TIMED_OUT

        convergence = [
            ConvergencePoint(
                iteration=iterations,
                best_objective=eval_result.objective_value,
                current_objective=eval_result.objective_value,
                timestamp_offset=runtime_seconds,
            )
        ]

        return SolverResult(
            solver_id=self.solver_id,
            solver_name=self.name,
            problem_type=problem_type,
            status=status,
            candidate_solution=candidate,
            objective_value=eval_result.objective_value,
            is_feasible=eval_result.is_feasible,
            constraint_violations=[v.message for v in eval_result.violations],
            runtime_seconds=runtime_seconds,
            iterations=iterations,
            evaluations=evaluations,
            seed=seed,
            optimality_status=optimality,
            termination_reason=reason,
            convergence_history=convergence,
            metadata={
                "method": "exact_exhaustive" if problem_type != ProblemType.ASSIGNMENT else "hungarian_algorithm",
                "completed_search_space": completed,
                "evaluations_performed": evaluations,
                "independent_evaluation_details": eval_result.details,
            },
        )

    def _solve_max_cut(
        self, instance: Dict[str, Any], time_limit: float, max_vars: int
    ) -> Tuple[Dict[str, int], int, int, bool, str]:
        """Exhaustively evaluate all 2^(n-1) binary partitions fixing vertex 0 = 0."""
        nodes: List[str] = instance.get("nodes", [])
        edges: List[Any] = instance.get("edges", [])
        n = len(nodes)

        if n == 0:
            return {}, 0, 0, True, "empty_instance"

        if n > max_vars:
            raise ValueError(
                f"Max-Cut instance with {n} vertices exceeds exact solver safety limit of {max_vars}. "
                "Exhaustive 2^n enumeration would exceed practical compute bounds."
            )

        # Parse weighted adjacency list
        node_index = {node: idx for idx, node in enumerate(nodes)}
        edge_tuples: List[Tuple[int, int, float]] = []
        for e in edges:
            u, v = e[0], e[1]
            w = float(e[2]) if len(e) >= 3 else 1.0
            if u in node_index and v in node_index:
                edge_tuples.append((node_index[u], node_index[v], w))

        best_cut = -1.0
        best_partition_bits = [0] * n
        evaluations = 0
        t_start = time.perf_counter()
        completed = True
        reason = "proven_global_optimum"

        # By partition symmetry (0 <-> 1 complement), we fix node 0 to partition 0
        # and enumerate all 2^(n-1) combinations for nodes 1..n-1
        remaining_count = n - 1
        num_combinations = 1 << remaining_count

        for mask in range(num_combinations):
            evaluations += 1

            # Check time limit every 8192 iterations
            if (evaluations & 0x1FFF) == 0:
                if (time.perf_counter() - t_start) >= time_limit:
                    completed = False
                    reason = "time_limit_exceeded"
                    break

            # Build bit assignment: node 0 is 0; node i is bit (mask >> (i-1)) & 1
            current_cut = 0.0
            for u_idx, v_idx, w in edge_tuples:
                b_u = 0 if u_idx == 0 else ((mask >> (u_idx - 1)) & 1)
                b_v = 0 if v_idx == 0 else ((mask >> (v_idx - 1)) & 1)
                if b_u != b_v:
                    current_cut += w

            if current_cut > best_cut:
                best_cut = current_cut
                best_partition_bits = [0] + [((mask >> j) & 1) for j in range(remaining_count)]

        best_assignment = {nodes[i]: best_partition_bits[i] for i in range(n)}
        return best_assignment, evaluations, evaluations, completed, reason

    def _solve_assignment(
        self, instance: Dict[str, Any], time_limit: float
    ) -> Tuple[List[List[str]], int, int, bool, str]:
        """Solve Linear Assignment problem exactly using Hungarian algorithm."""
        agents: List[str] = instance.get("agents", [])
        tasks: List[str] = instance.get("tasks", [])
        cost_matrix = instance.get("cost_matrix", [])

        n_agents = len(agents)
        n_tasks = len(tasks)

        if n_agents == 0 or n_tasks == 0:
            return [], 0, 0, True, "empty_instance"

        if n_agents > self.MAX_ASSIGNMENT_DIMENSION or n_tasks > self.MAX_ASSIGNMENT_DIMENSION:
            raise ValueError(
                f"Assignment instance ({n_agents}x{n_tasks}) exceeds exact solver dimension limit of {self.MAX_ASSIGNMENT_DIMENSION}."
            )

        cost_array = np.array(cost_matrix, dtype=float)
        row_ind, col_ind = scipy.optimize.linear_sum_assignment(cost_array)

        candidate_dict = {agents[r]: tasks[c] for r, c in zip(row_ind, col_ind)}
        evaluations = 1
        iterations = len(agents)

        return candidate_dict, evaluations, iterations, True, "proven_global_optimum"

    def _solve_tsp(
        self, instance: Dict[str, Any], time_limit: float
    ) -> Tuple[List[str], int, int, bool, str]:
        """Solve Travelling Salesperson Problem exactly by exhaustive permutation enumeration."""
        cities: List[str] = instance.get("cities", [])
        dist_matrix = instance.get("distance_matrix", [])
        start_city: Optional[str] = instance.get("start_city", None)
        n = len(cities)

        if n == 0:
            return [], 0, 0, True, "empty_instance"

        if n == 1:
            return [cities[0]], 1, 1, True, "proven_global_optimum"

        if n > self.MAX_TSP_CITIES:
            raise ValueError(
                f"TSP instance with {n} cities exceeds exact solver limit of {self.MAX_TSP_CITIES}. "
                "Exhaustive n! enumeration would exceed practical compute bounds."
            )

        city_to_idx = {city: i for i, city in enumerate(cities)}
        dist_arr = np.array(dist_matrix, dtype=float)

        # Fix the starting city (either explicitly given or cities[0] due to cyclic loop invariance)
        fixed_first_city = start_city if (start_city and start_city in city_to_idx) else cities[0]
        first_idx = city_to_idx[fixed_first_city]
        other_indices = [i for i in range(n) if i != first_idx]

        best_dist = float("inf")
        best_tour_indices: List[int] = []
        evaluations = 0
        t_start = time.perf_counter()
        completed = True
        reason = "proven_global_optimum"

        for perm in itertools.permutations(other_indices):
            evaluations += 1

            if (evaluations & 0x1FFF) == 0:
                if (time.perf_counter() - t_start) >= time_limit:
                    completed = False
                    reason = "time_limit_exceeded"
                    break

            full_tour = [first_idx] + list(perm)
            # Compute total distance along cyclic tour
            total_d = sum(dist_arr[full_tour[i], full_tour[(i + 1) % n]] for i in range(n))

            if total_d < best_dist:
                best_dist = total_d
                best_tour_indices = full_tour

        best_tour_cities = [cities[idx] for idx in best_tour_indices]
        return best_tour_cities, evaluations, evaluations, completed, reason
