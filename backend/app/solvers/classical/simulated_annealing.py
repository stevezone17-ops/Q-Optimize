"""Simulated Annealing optimization engine supporting Max-Cut, Assignment, and TSP."""

import time
import math
import random
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

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


class SimulatedAnnealingSolver(IClassicalSolver):
    """
    Configurable Simulated Annealing (SA) metaheuristic.
    Features:
    - Max-Cut: 1-flip neighborhood transitions.
    - Assignment: Transposition (swap) moves preserving 1-to-1 matching validity by construction.
    - TSP: 2-opt edge inversion and vertex swap moves with optional start city pinning.
    - Metropolis acceptance criterion with exponential and linear cooling schedules.
    - Deterministic random seeding and convergence trajectory logging.
    """

    @property
    def solver_id(self) -> str:
        return "simulated_annealing"

    @property
    def name(self) -> str:
        return "Simulated Annealing (SA)"

    @property
    def description(self) -> str:
        return (
            "Stochastic thermodynamic optimization using temperature-controlled "
            "Metropolis acceptance transitions, adaptive cooling schedules, and convergence tracing."
        )

    @property
    def supported_problem_types(self) -> List[ProblemType]:
        return [ProblemType.MAX_CUT, ProblemType.ASSIGNMENT, ProblemType.TSP]

    @property
    def is_implemented(self) -> bool:
        return True

    @property
    def stage_introduced(self) -> str:
        return "Stage 4.4"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "initial_temperature": {"type": "float", "default": 100.0, "description": "Initial system temperature"},
            "final_temperature": {"type": "float", "default": 0.01, "description": "Stopping temperature threshold"},
            "cooling_schedule": {"type": "string", "default": "exponential", "description": "Cooling schedule: 'exponential' or 'linear'"},
            "cooling_rate": {"type": "float", "default": 0.95, "description": "Temperature decay multiplier (for exponential)"},
            "steps_per_temperature": {"type": "integer", "default": 50, "description": "Metropolis proposals per temperature step"},
            "max_iterations": {"type": "integer", "default": 5000, "description": "Maximum total neighborhood evaluations"},
            "seed": {"type": "integer", "default": 42, "description": "Deterministic random seed"},
            "time_limit_seconds": {"type": "float", "default": 60.0, "description": "Maximum execution time in seconds"},
        }

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "initial_temperature": 100.0,
            "final_temperature": 0.01,
            "cooling_schedule": "exponential",
            "cooling_rate": 0.95,
            "steps_per_temperature": 50,
            "max_iterations": 5000,
            "seed": 42,
            "time_limit_seconds": 60.0,
        }

    def solve(
        self,
        problem_type: ProblemType,
        instance: Dict[str, Any],
        config: Optional[SolverConfiguration] = None,
        seed: Optional[int] = 42,
    ) -> SolverResult:
        """Execute Simulated Annealing against canonical problem instance."""
        self.check_problem_support(problem_type)

        # Parse configuration
        c_dict = config.extra_params if config else {}
        t_init = float(c_dict.get("initial_temperature", 100.0))
        t_final = float(c_dict.get("final_temperature", 0.01))
        cooling_schedule = str(c_dict.get("cooling_schedule", "exponential")).lower()
        cooling_rate = float(c_dict.get("cooling_rate", 0.95))
        steps_per_temp = int(c_dict.get("steps_per_temperature", 50))
        max_iterations = int(c_dict.get("max_iterations", 5000))

        time_limit = (
            config.time_limit_seconds
            if config and config.time_limit_seconds
            else float(c_dict.get("time_limit_seconds", 60.0))
        )
        actual_seed = seed if seed is not None else (config.seed if config and config.seed is not None else 42)

        # Validation
        if t_init <= 0:
            raise ValueError(f"initial_temperature must be > 0, got {t_init}")
        if t_final <= 0 or t_final >= t_init:
            raise ValueError(f"final_temperature must be > 0 and < initial_temperature ({t_init}), got {t_final}")
        if cooling_schedule not in ("exponential", "linear"):
            raise ValueError(f"cooling_schedule must be 'exponential' or 'linear', got {cooling_schedule}")
        if cooling_schedule == "exponential" and not (0.0 < cooling_rate < 1.0):
            raise ValueError(f"cooling_rate must be in (0, 1) for exponential cooling, got {cooling_rate}")
        if steps_per_temp < 1:
            raise ValueError(f"steps_per_temperature must be >= 1, got {steps_per_temp}")
        if max_iterations < 1:
            raise ValueError(f"max_iterations must be >= 1, got {max_iterations}")

        rng = random.Random(actual_seed)
        t0 = time.perf_counter()

        # Problem-specific SA execution
        if problem_type == ProblemType.MAX_CUT:
            best_raw, total_evals, final_iter, convergence, reason = self._run_max_cut_sa(
                instance, t_init, t_final, cooling_schedule, cooling_rate, steps_per_temp, max_iterations, time_limit, t0, rng
            )
            candidate = {instance["nodes"][i]: best_raw[i] for i in range(len(instance["nodes"]))}

        elif problem_type == ProblemType.ASSIGNMENT:
            best_raw, total_evals, final_iter, convergence, reason = self._run_assignment_sa(
                instance, t_init, t_final, cooling_schedule, cooling_rate, steps_per_temp, max_iterations, time_limit, t0, rng
            )
            agents = instance.get("agents", [])
            tasks = instance.get("tasks", [])
            candidate = {agents[i]: tasks[best_raw[i]] for i in range(len(agents))}

        elif problem_type == ProblemType.TSP:
            best_raw, total_evals, final_iter, convergence, reason = self._run_tsp_sa(
                instance, t_init, t_final, cooling_schedule, cooling_rate, steps_per_temp, max_iterations, time_limit, t0, rng
            )
            cities = instance.get("cities", [])
            candidate = [cities[idx] for idx in best_raw]

        else:
            raise ValueError(f"Unsupported problem type: {problem_type}")

        runtime_seconds = time.perf_counter() - t0

        # Independent evaluation via Phase 2 evaluation engine
        evaluator = EvaluatorFactory.get_evaluator(problem_type)
        eval_result = evaluator.evaluate(instance, candidate)

        status = SolverStatus.COMPLETED if reason in ("temperature_threshold_reached", "max_iterations_reached") else SolverStatus.TIMED_OUT
        optimality = (
            OptimalityStatus.HEURISTIC_FEASIBLE
            if eval_result.is_feasible
            else OptimalityStatus.HEURISTIC_INFEASIBLE
        )

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
            iterations=final_iter,
            evaluations=total_evals,
            seed=actual_seed,
            optimality_status=optimality,
            termination_reason=reason,
            convergence_history=convergence,
            metadata={
                "initial_temperature": t_init,
                "final_temperature": t_final,
                "cooling_schedule": cooling_schedule,
                "cooling_rate": cooling_rate,
                "steps_per_temperature": steps_per_temp,
                "max_iterations": max_iterations,
                "independent_evaluation_details": eval_result.details,
            },
        )

    # =========================================================================
    # 1. MAX-CUT SA IMPLEMENTATION
    # =========================================================================
    def _run_max_cut_sa(
        self,
        instance: Dict[str, Any],
        t_init: float,
        t_final: float,
        cooling_schedule: str,
        cooling_rate: float,
        steps_per_temp: int,
        max_iterations: int,
        time_limit: float,
        t0: float,
        rng: random.Random,
    ) -> Tuple[List[int], int, int, List[ConvergencePoint], str]:
        nodes = instance.get("nodes", [])
        edges = instance.get("edges", [])
        n = len(nodes)

        if n == 0:
            return [], 0, 0, [], "empty_instance"

        node_to_idx = {node: i for i, node in enumerate(nodes)}
        indexed_edges: List[Tuple[int, int, float]] = []
        for e in edges:
            if isinstance(e, dict):
                u_id = e.get("u")
                v_id = e.get("v")
                w = float(e.get("weight", 1.0))
            elif isinstance(e, (list, tuple)):
                u_id = e[0]
                v_id = e[1]
                w = float(e[2]) if len(e) >= 3 else 1.0
            else:
                continue
            if u_id in node_to_idx and v_id in node_to_idx:
                indexed_edges.append((node_to_idx[u_id], node_to_idx[v_id], w))

        def eval_cut(state: List[int]) -> float:
            cut = 0.0
            for u, v, w in indexed_edges:
                if state[u] != state[v]:
                    cut += w
            return cut

        # Initial solution: random binary partition
        current_state = [rng.randint(0, 1) for _ in range(n)]
        current_cut = eval_cut(current_state)
        eval_count = 1

        best_state = list(current_state)
        best_cut = current_cut

        convergence: List[ConvergencePoint] = [
            ConvergencePoint(
                iteration=0,
                best_objective=best_cut,
                current_objective=current_cut,
                temperature=t_init,
                timestamp_offset=time.perf_counter() - t0,
            )
        ]

        t_curr = t_init
        total_steps = 0
        temp_stage = 0
        reason = "max_iterations_reached"

        # Linear schedule delta
        est_stages = max(1, max_iterations // steps_per_temp)
        delta_t_linear = (t_init - t_final) / est_stages

        while total_steps < max_iterations:
            if time.perf_counter() - t0 > time_limit:
                reason = "time_limit_exceeded"
                break

            if t_curr <= t_final:
                reason = "temperature_threshold_reached"
                break

            # Execute steps at current temperature
            for _ in range(steps_per_temp):
                if total_steps >= max_iterations:
                    break

                # 1-flip neighborhood move
                flip_idx = rng.randint(0, n - 1)
                cand_state = list(current_state)
                cand_state[flip_idx] = 1 - cand_state[flip_idx]

                cand_cut = eval_cut(cand_state)
                eval_count += 1
                total_steps += 1

                # Energy = -Cut (minimization framework)
                delta_cut = cand_cut - current_cut
                delta_energy = -delta_cut

                # Metropolis criterion
                accept = False
                if delta_energy <= 0:  # better or equal cut
                    accept = True
                else:
                    exponent = -delta_energy / max(t_curr, 1e-12)
                    p_accept = math.exp(exponent) if exponent > -700.0 else 0.0
                    if rng.random() < p_accept:
                        accept = True

                if accept:
                    current_state = cand_state
                    current_cut = cand_cut

                    if current_cut > best_cut:
                        best_cut = current_cut
                        best_state = list(current_state)

            # Record convergence checkpoint after temperature step
            convergence.append(
                ConvergencePoint(
                    iteration=total_steps,
                    best_objective=best_cut,
                    current_objective=current_cut,
                    temperature=t_curr,
                    timestamp_offset=time.perf_counter() - t0,
                )
            )

            # Cool temperature
            temp_stage += 1
            if cooling_schedule == "exponential":
                t_curr = max(t_final, t_curr * cooling_rate)
            else:  # linear
                t_curr = max(t_final, t_init - temp_stage * delta_t_linear)

        return best_state, eval_count, total_steps, convergence, reason

    # =========================================================================
    # 2. ASSIGNMENT SA IMPLEMENTATION (Permutation swap moves)
    # =========================================================================
    def _run_assignment_sa(
        self,
        instance: Dict[str, Any],
        t_init: float,
        t_final: float,
        cooling_schedule: str,
        cooling_rate: float,
        steps_per_temp: int,
        max_iterations: int,
        time_limit: float,
        t0: float,
        rng: random.Random,
    ) -> Tuple[List[int], int, int, List[ConvergencePoint], str]:
        agents = instance.get("agents", [])
        tasks = instance.get("tasks", [])
        cost_matrix = instance.get("cost_matrix", [])
        n = len(agents)

        if n == 0 or len(tasks) == 0:
            return [], 0, 0, [], "empty_instance"

        cost_arr = np.array(cost_matrix, dtype=float)

        def eval_cost(perm: List[int]) -> float:
            return sum(cost_arr[i, perm[i]] for i in range(n))

        # Initial solution: random permutation of range(n)
        current_perm = list(range(n))
        rng.shuffle(current_perm)
        current_cost = eval_cost(current_perm)
        eval_count = 1

        best_perm = list(current_perm)
        best_cost = current_cost

        convergence: List[ConvergencePoint] = [
            ConvergencePoint(
                iteration=0,
                best_objective=best_cost,
                current_objective=current_cost,
                temperature=t_init,
                timestamp_offset=time.perf_counter() - t0,
            )
        ]

        t_curr = t_init
        total_steps = 0
        temp_stage = 0
        reason = "max_iterations_reached"

        est_stages = max(1, max_iterations // steps_per_temp)
        delta_t_linear = (t_init - t_final) / est_stages

        while total_steps < max_iterations:
            if time.perf_counter() - t0 > time_limit:
                reason = "time_limit_exceeded"
                break

            if t_curr <= t_final:
                reason = "temperature_threshold_reached"
                break

            for _ in range(steps_per_temp):
                if total_steps >= max_iterations:
                    break

                if n < 2:
                    total_steps += 1
                    continue

                # Swap neighborhood move (transposition between agents i and j)
                i, j = rng.sample(range(n), 2)
                cand_perm = list(current_perm)
                cand_perm[i], cand_perm[j] = cand_perm[j], cand_perm[i]

                cand_cost = eval_cost(cand_perm)
                eval_count += 1
                total_steps += 1

                delta_cost = cand_cost - current_cost

                # Metropolis criterion for minimization
                accept = False
                if delta_cost <= 0:
                    accept = True
                else:
                    exponent = -delta_cost / max(t_curr, 1e-12)
                    p_accept = math.exp(exponent) if exponent > -700.0 else 0.0
                    if rng.random() < p_accept:
                        accept = True

                if accept:
                    current_perm = cand_perm
                    current_cost = cand_cost

                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_perm = list(current_perm)

            convergence.append(
                ConvergencePoint(
                    iteration=total_steps,
                    best_objective=best_cost,
                    current_objective=current_cost,
                    temperature=t_curr,
                    timestamp_offset=time.perf_counter() - t0,
                )
            )

            temp_stage += 1
            if cooling_schedule == "exponential":
                t_curr = max(t_final, t_curr * cooling_rate)
            else:
                t_curr = max(t_final, t_init - temp_stage * delta_t_linear)

        return best_perm, eval_count, total_steps, convergence, reason

    # =========================================================================
    # 3. TSP SA IMPLEMENTATION (2-opt inversion & vertex swap moves)
    # =========================================================================
    def _run_tsp_sa(
        self,
        instance: Dict[str, Any],
        t_init: float,
        t_final: float,
        cooling_schedule: str,
        cooling_rate: float,
        steps_per_temp: int,
        max_iterations: int,
        time_limit: float,
        t0: float,
        rng: random.Random,
    ) -> Tuple[List[int], int, int, List[ConvergencePoint], str]:
        cities = instance.get("cities", [])
        dist_matrix = instance.get("distance_matrix", [])
        start_city = instance.get("start_city", None)
        n = len(cities)

        if n <= 1:
            return list(range(n)), 0, 0, [], "trivial_instance"

        dist_arr = np.array(dist_matrix, dtype=float)
        city_to_idx = {city: i for i, city in enumerate(cities)}

        fixed_first = (start_city in city_to_idx) if start_city else False
        first_idx = city_to_idx[start_city] if fixed_first else 0
        variable_indices = [i for i in range(n) if not fixed_first or i != first_idx]

        def eval_tour(tour: List[int]) -> float:
            return sum(dist_arr[tour[i], tour[(i + 1) % n]] for i in range(n))

        # Initial solution
        shuffled_vars = list(variable_indices)
        rng.shuffle(shuffled_vars)
        current_tour = [first_idx] + shuffled_vars if fixed_first else shuffled_vars
        current_dist = eval_tour(current_tour)
        eval_count = 1

        best_tour = list(current_tour)
        best_dist = current_dist

        convergence: List[ConvergencePoint] = [
            ConvergencePoint(
                iteration=0,
                best_objective=best_dist,
                current_objective=current_dist,
                temperature=t_init,
                timestamp_offset=time.perf_counter() - t0,
            )
        ]

        t_curr = t_init
        total_steps = 0
        temp_stage = 0
        reason = "max_iterations_reached"

        est_stages = max(1, max_iterations // steps_per_temp)
        delta_t_linear = (t_init - t_final) / est_stages

        # Bounds for mutation: if fixed_first, positions 1 to n-1; else 0 to n-1
        start_pos = 1 if fixed_first else 0
        num_mutable = n - start_pos

        while total_steps < max_iterations:
            if time.perf_counter() - t0 > time_limit:
                reason = "time_limit_exceeded"
                break

            if t_curr <= t_final:
                reason = "temperature_threshold_reached"
                break

            for _ in range(steps_per_temp):
                if total_steps >= max_iterations:
                    break

                if num_mutable < 2:
                    total_steps += 1
                    continue

                # Neighborhood move: 80% 2-opt inversion, 20% vertex swap
                cand_tour = list(current_tour)
                i, j = sorted(rng.sample(range(start_pos, n), 2))

                if rng.random() < 0.8:
                    # 2-opt subsegment reversal
                    cand_tour[i : j + 1] = list(reversed(cand_tour[i : j + 1]))
                else:
                    # Vertex swap
                    cand_tour[i], cand_tour[j] = cand_tour[j], cand_tour[i]

                cand_dist = eval_tour(cand_tour)
                eval_count += 1
                total_steps += 1

                delta_dist = cand_dist - current_dist

                # Metropolis criterion for tour minimization
                accept = False
                if delta_dist <= 0:
                    accept = True
                else:
                    exponent = -delta_dist / max(t_curr, 1e-12)
                    p_accept = math.exp(exponent) if exponent > -700.0 else 0.0
                    if rng.random() < p_accept:
                        accept = True

                if accept:
                    current_tour = cand_tour
                    current_dist = cand_dist

                    if current_dist < best_dist:
                        best_dist = current_dist
                        best_tour = list(current_tour)

            convergence.append(
                ConvergencePoint(
                    iteration=total_steps,
                    best_objective=best_dist,
                    current_objective=current_dist,
                    temperature=t_curr,
                    timestamp_offset=time.perf_counter() - t0,
                )
            )

            temp_stage += 1
            if cooling_schedule == "exponential":
                t_curr = max(t_final, t_curr * cooling_rate)
            else:
                t_curr = max(t_final, t_init - temp_stage * delta_t_linear)

        return best_tour, eval_count, total_steps, convergence, reason
