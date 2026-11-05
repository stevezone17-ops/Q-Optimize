"""Genetic Algorithm optimization engine supporting Max-Cut, Assignment, and TSP."""

import time
import random
from typing import Dict, Any, List, Optional, Tuple, Union
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


class GeneticAlgorithmSolver(IClassicalSolver):
    """
    Configurable Genetic Algorithm (GA) metaheuristic.
    Features:
    - Max-Cut: Binary chromosome representation with uniform crossover and bit-flip mutation.
    - Assignment: Permutation representation preserving 1-to-1 matching validity by construction.
    - TSP: Permutation chromosomes with Order Crossover (OX), inversion mutation, and optional start pinning.
    - Tournament/Roulette selection, elitism preservation, deterministic seeding, and convergence logging.
    """

    @property
    def solver_id(self) -> str:
        return "genetic_algorithm"

    @property
    def name(self) -> str:
        return "Genetic Algorithm (GA)"

    @property
    def description(self) -> str:
        return (
            "Evolutionary metaheuristic utilizing problem-specific chromosome representations, "
            "order-preserving crossover, adaptive mutation, elitism, and convergence tracking."
        )

    @property
    def supported_problem_types(self) -> List[ProblemType]:
        return [ProblemType.MAX_CUT, ProblemType.ASSIGNMENT, ProblemType.TSP]

    @property
    def is_implemented(self) -> bool:
        return True

    @property
    def stage_introduced(self) -> str:
        return "Stage 4.3"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "population_size": {"type": "integer", "default": 100, "description": "Population size (10-1000)"},
            "generations": {"type": "integer", "default": 200, "description": "Maximum number of generations"},
            "mutation_rate": {"type": "float", "default": 0.05, "description": "Mutation probability per gene/individual"},
            "crossover_rate": {"type": "float", "default": 0.8, "description": "Probability of recombination"},
            "selection_method": {"type": "string", "default": "tournament", "description": "Selection operator: 'tournament' or 'roulette'"},
            "tournament_size": {"type": "integer", "default": 3, "description": "Tournament selection candidates"},
            "elitism_count": {"type": "integer", "default": 2, "description": "Number of elite individuals preserved"},
            "seed": {"type": "integer", "default": 42, "description": "Deterministic random seed"},
            "time_limit_seconds": {"type": "float", "default": 60.0, "description": "Maximum execution time in seconds"},
        }

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "population_size": 100,
            "generations": 200,
            "mutation_rate": 0.05,
            "crossover_rate": 0.8,
            "selection_method": "tournament",
            "tournament_size": 3,
            "elitism_count": 2,
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
        """Execute Genetic Algorithm against canonical problem instance."""
        self.check_problem_support(problem_type)

        # Parse configuration
        c_dict = config.extra_params if config else {}
        pop_size = int(c_dict.get("population_size", 100))
        generations = int(c_dict.get("generations", 200))
        p_mut = float(c_dict.get("mutation_rate", 0.05))
        p_cross = float(c_dict.get("crossover_rate", 0.8))
        selection_method = str(c_dict.get("selection_method", "tournament")).lower()
        tourn_size = int(c_dict.get("tournament_size", 3))
        elitism = int(c_dict.get("elitism_count", 2))
        time_limit = config.time_limit_seconds if config and config.time_limit_seconds else 60.0

        actual_seed = seed if seed is not None else 42
        rng = random.Random(actual_seed)
        np_rng = np.random.default_rng(actual_seed)

        t0 = time.perf_counter()

        # Run problem-specific GA
        if problem_type == ProblemType.MAX_CUT:
            best_raw, total_evals, final_gen, convergence, reason = self._run_max_cut_ga(
                instance, pop_size, generations, p_mut, p_cross, selection_method, tourn_size, elitism, time_limit, t0, rng
            )
            candidate = {instance["nodes"][i]: best_raw[i] for i in range(len(instance["nodes"]))}

        elif problem_type == ProblemType.ASSIGNMENT:
            best_raw, total_evals, final_gen, convergence, reason = self._run_assignment_ga(
                instance, pop_size, generations, p_mut, p_cross, selection_method, tourn_size, elitism, time_limit, t0, rng
            )
            agents = instance.get("agents", [])
            tasks = instance.get("tasks", [])
            candidate = {agents[i]: tasks[best_raw[i]] for i in range(len(agents))}

        elif problem_type == ProblemType.TSP:
            best_raw, total_evals, final_gen, convergence, reason = self._run_tsp_ga(
                instance, pop_size, generations, p_mut, p_cross, selection_method, tourn_size, elitism, time_limit, t0, rng
            )
            cities = instance.get("cities", [])
            candidate = [cities[idx] for idx in best_raw]
        else:
            raise ValueError(f"Unsupported problem type: {problem_type}")

        runtime_seconds = time.perf_counter() - t0

        # Independent evaluation via Phase 2 evaluation engine
        evaluator = EvaluatorFactory.get_evaluator(problem_type)
        eval_result = evaluator.evaluate(instance, candidate)

        status = SolverStatus.COMPLETED if reason == "max_generations_reached" else SolverStatus.TIMED_OUT
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
            iterations=final_gen,
            evaluations=total_evals,
            seed=actual_seed,
            optimality_status=optimality,
            termination_reason=reason,
            convergence_history=convergence,
            metadata={
                "population_size": pop_size,
                "generations_completed": final_gen,
                "mutation_rate": p_mut,
                "crossover_rate": p_cross,
                "selection_method": selection_method,
                "elitism_count": elitism,
                "independent_evaluation_details": eval_result.details,
            },
        )

    # =========================================================================
    # 1. MAX-CUT GA IMPLEMENTATION
    # =========================================================================
    def _run_max_cut_ga(
        self,
        instance: Dict[str, Any],
        pop_size: int,
        generations: int,
        p_mut: float,
        p_cross: float,
        selection_method: str,
        tourn_size: int,
        elitism: int,
        time_limit: float,
        t0: float,
        rng: random.Random,
    ) -> Tuple[List[int], int, int, List[ConvergencePoint], str]:
        nodes = instance.get("nodes", [])
        edges = instance.get("edges", [])
        n = len(nodes)

        if n == 0:
            return [], 0, 0, [], "empty_instance"

        node_idx = {node: i for i, node in enumerate(nodes)}
        edge_data = [(node_idx[e[0]], node_idx[e[1]], float(e[2]) if len(e) >= 3 else 1.0) for e in edges if e[0] in node_idx and e[1] in node_idx]

        def eval_cut(chrom: List[int]) -> float:
            c = 0.0
            for u, v, w in edge_data:
                if chrom[u] != chrom[v]:
                    c += w
            return c

        # Initialize binary population
        population: List[List[int]] = [[rng.randint(0, 1) for _ in range(n)] for _ in range(pop_size)]
        fitnesses: List[float] = [eval_cut(ind) for ind in population]
        eval_count = pop_size

        best_idx = int(np.argmax(fitnesses))
        best_chrom = list(population[best_idx])
        best_obj = fitnesses[best_idx]

        convergence: List[ConvergencePoint] = [
            ConvergencePoint(
                iteration=0,
                best_objective=best_obj,
                mean_fitness=float(np.mean(fitnesses)),
                timestamp_offset=time.perf_counter() - t0,
            )
        ]

        reason = "max_generations_reached"
        final_gen = 0

        for gen in range(1, generations + 1):
            final_gen = gen
            if (time.perf_counter() - t0) >= time_limit:
                reason = "time_limit_exceeded"
                break

            # Selection
            def select_one() -> List[int]:
                if selection_method == "roulette":
                    min_fit = min(fitnesses)
                    adj_fit = [f - min_fit + 1e-4 for f in fitnesses]
                    tot = sum(adj_fit)
                    r = rng.uniform(0, tot)
                    cur = 0.0
                    for idx, val in enumerate(adj_fit):
                        cur += val
                        if cur >= r:
                            return population[idx]
                    return population[-1]
                else:  # Tournament
                    cand_indices = [rng.randint(0, pop_size - 1) for _ in range(tourn_size)]
                    best_cand = max(cand_indices, key=lambda idx: fitnesses[idx])
                    return population[best_cand]

            # Elitism: sort by fitness descending
            sorted_indices = sorted(range(pop_size), key=lambda i: fitnesses[i], reverse=True)
            new_pop: List[List[int]] = [list(population[sorted_indices[i]]) for i in range(min(elitism, pop_size))]

            # Reproduction
            while len(new_pop) < pop_size:
                p1 = select_one()
                p2 = select_one()

                # Crossover
                if rng.random() < p_cross and n > 1:
                    cx1 = rng.randint(0, n - 2)
                    cx2 = rng.randint(cx1 + 1, n - 1)
                    c1 = p1[:cx1] + p2[cx1:cx2] + p1[cx2:]
                    c2 = p2[:cx1] + p1[cx1:cx2] + p2[cx2:]
                else:
                    c1 = list(p1)
                    c2 = list(p2)

                # Mutation
                for chrom in (c1, c2):
                    for gene_idx in range(n):
                        if rng.random() < p_mut:
                            chrom[gene_idx] = 1 - chrom[gene_idx]

                new_pop.append(c1)
                if len(new_pop) < pop_size:
                    new_pop.append(c2)

            population = new_pop
            fitnesses = [eval_cut(ind) for ind in population]
            eval_count += pop_size

            gen_best_idx = int(np.argmax(fitnesses))
            if fitnesses[gen_best_idx] > best_obj:
                best_obj = fitnesses[gen_best_idx]
                best_chrom = list(population[gen_best_idx])

            # Record convergence periodically and on improvement
            if gen % max(1, generations // 50) == 0 or gen == generations:
                convergence.append(
                    ConvergencePoint(
                        iteration=gen,
                        best_objective=best_obj,
                        mean_fitness=float(np.mean(fitnesses)),
                        timestamp_offset=time.perf_counter() - t0,
                    )
                )

        return best_chrom, eval_count, final_gen, convergence, reason

    # =========================================================================
    # 2. ASSIGNMENT GA IMPLEMENTATION (Permutation representation)
    # =========================================================================
    def _run_assignment_ga(
        self,
        instance: Dict[str, Any],
        pop_size: int,
        generations: int,
        p_mut: float,
        p_cross: float,
        selection_method: str,
        tourn_size: int,
        elitism: int,
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

        def eval_assignment(perm: List[int]) -> float:
            """Total cost of assigning agent i to task perm[i]."""
            return sum(cost_arr[i, perm[i]] for i in range(n))

        # Initialize population with random valid permutations of range(n)
        population: List[List[int]] = []
        base_perm = list(range(n))
        for _ in range(pop_size):
            p = list(base_perm)
            rng.shuffle(p)
            population.append(p)

        costs = [eval_assignment(ind) for ind in population]
        eval_count = pop_size

        # For minimization, fitness = 1.0 / (1.0 + cost - min_cost)
        best_idx = int(np.argmin(costs))
        best_cost = costs[best_idx]
        best_perm = list(population[best_idx])

        convergence: List[ConvergencePoint] = [
            ConvergencePoint(
                iteration=0,
                best_objective=best_cost,
                mean_fitness=float(np.mean(costs)),
                timestamp_offset=time.perf_counter() - t0,
            )
        ]

        reason = "max_generations_reached"
        final_gen = 0

        for gen in range(1, generations + 1):
            final_gen = gen
            if (time.perf_counter() - t0) >= time_limit:
                reason = "time_limit_exceeded"
                break

            # Tournament selection (minimization: lowest cost wins)
            def select_one() -> List[int]:
                cand_indices = [rng.randint(0, pop_size - 1) for _ in range(tourn_size)]
                best_cand = min(cand_indices, key=lambda idx: costs[idx])
                return population[best_cand]

            # Elitism: preserve top individuals with lowest cost
            sorted_indices = sorted(range(pop_size), key=lambda i: costs[i])
            new_pop: List[List[int]] = [list(population[sorted_indices[i]]) for i in range(min(elitism, pop_size))]

            while len(new_pop) < pop_size:
                p1 = select_one()
                p2 = select_one()

                # Order Crossover (OX) for permutations
                if rng.random() < p_cross and n > 2:
                    c1 = self._order_crossover(p1, p2, rng)
                    c2 = self._order_crossover(p2, p1, rng)
                else:
                    c1 = list(p1)
                    c2 = list(p2)

                # Swap Mutation
                for chrom in (c1, c2):
                    if rng.random() < p_mut and n > 1:
                        i1, i2 = rng.sample(range(n), 2)
                        chrom[i1], chrom[i2] = chrom[i2], chrom[i1]

                new_pop.append(c1)
                if len(new_pop) < pop_size:
                    new_pop.append(c2)

            population = new_pop
            costs = [eval_assignment(ind) for ind in population]
            eval_count += pop_size

            gen_best_idx = int(np.argmin(costs))
            if costs[gen_best_idx] < best_cost:
                best_cost = costs[gen_best_idx]
                best_perm = list(population[gen_best_idx])

            if gen % max(1, generations // 50) == 0 or gen == generations:
                convergence.append(
                    ConvergencePoint(
                        iteration=gen,
                        best_objective=best_cost,
                        mean_fitness=float(np.mean(costs)),
                        timestamp_offset=time.perf_counter() - t0,
                    )
                )

        return best_perm, eval_count, final_gen, convergence, reason

    # =========================================================================
    # 3. TSP GA IMPLEMENTATION (Permutation representation + OX)
    # =========================================================================
    def _run_tsp_ga(
        self,
        instance: Dict[str, Any],
        pop_size: int,
        generations: int,
        p_mut: float,
        p_cross: float,
        selection_method: str,
        tourn_size: int,
        elitism: int,
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
        m = len(variable_indices)

        def eval_tour(chrom_vars: List[int]) -> float:
            full = [first_idx] + chrom_vars if fixed_first else chrom_vars
            return sum(dist_arr[full[i], full[(i + 1) % n]] for i in range(n))

        # Initialize population
        population: List[List[int]] = []
        for _ in range(pop_size):
            p = list(variable_indices)
            rng.shuffle(p)
            population.append(p)

        distances = [eval_tour(ind) for ind in population]
        eval_count = pop_size

        best_idx = int(np.argmin(distances))
        best_dist = distances[best_idx]
        best_chrom = list(population[best_idx])

        convergence: List[ConvergencePoint] = [
            ConvergencePoint(
                iteration=0,
                best_objective=best_dist,
                mean_fitness=float(np.mean(distances)),
                timestamp_offset=time.perf_counter() - t0,
            )
        ]

        reason = "max_generations_reached"
        final_gen = 0

        for gen in range(1, generations + 1):
            final_gen = gen
            if (time.perf_counter() - t0) >= time_limit:
                reason = "time_limit_exceeded"
                break

            def select_one() -> List[int]:
                cand_indices = [rng.randint(0, pop_size - 1) for _ in range(tourn_size)]
                best_cand = min(cand_indices, key=lambda idx: distances[idx])
                return population[best_cand]

            sorted_indices = sorted(range(pop_size), key=lambda i: distances[i])
            new_pop: List[List[int]] = [list(population[sorted_indices[i]]) for i in range(min(elitism, pop_size))]

            while len(new_pop) < pop_size:
                p1 = select_one()
                p2 = select_one()

                if rng.random() < p_cross and m > 2:
                    c1 = self._order_crossover(p1, p2, rng)
                    c2 = self._order_crossover(p2, p1, rng)
                else:
                    c1 = list(p1)
                    c2 = list(p2)

                # Inversion (2-opt style) mutation + swap mutation
                for chrom in (c1, c2):
                    if rng.random() < p_mut and m > 2:
                        i1, i2 = sorted(rng.sample(range(m), 2))
                        chrom[i1:i2+1] = reversed(chrom[i1:i2+1])
                    elif rng.random() < p_mut and m > 1:
                        i1, i2 = rng.sample(range(m), 2)
                        chrom[i1], chrom[i2] = chrom[i2], chrom[i1]

                new_pop.append(c1)
                if len(new_pop) < pop_size:
                    new_pop.append(c2)

            population = new_pop
            distances = [eval_tour(ind) for ind in population]
            eval_count += pop_size

            gen_best_idx = int(np.argmin(distances))
            if distances[gen_best_idx] < best_dist:
                best_dist = distances[gen_best_idx]
                best_chrom = list(population[gen_best_idx])

            if gen % max(1, generations // 50) == 0 or gen == generations:
                convergence.append(
                    ConvergencePoint(
                        iteration=gen,
                        best_objective=best_dist,
                        mean_fitness=float(np.mean(distances)),
                        timestamp_offset=time.perf_counter() - t0,
                    )
                )

        full_best_tour = [first_idx] + best_chrom if fixed_first else best_chrom
        return full_best_tour, eval_count, final_gen, convergence, reason

    @staticmethod
    def _order_crossover(p1: List[int], p2: List[int], rng: random.Random) -> List[int]:
        """Order Crossover (OX) preserving permutation validity."""
        n = len(p1)
        if n < 3:
            return list(p1)

        i1, i2 = sorted(rng.sample(range(n), 2))
        child = [-1] * n
        child[i1:i2+1] = p1[i1:i2+1]

        copied_set = set(child[i1:i2+1])
        fill_idx = (i2 + 1) % n
        p2_idx = (i2 + 1) % n

        for _ in range(n):
            candidate = p2[p2_idx]
            if candidate not in copied_set:
                child[fill_idx] = candidate
                fill_idx = (fill_idx + 1) % n
            p2_idx = (p2_idx + 1) % n

        return child

