"""Deterministic feature extraction engine for optimization problem instances."""

import math
from typing import Dict, Any, List, Optional, Set
import numpy as np

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import OptimizationFeatures
from backend.app.ai.interfaces import IFeatureExtractor
from backend.app.ai.exceptions import FeatureExtractionError
from backend.app.ai.config import ai_settings
from backend.app.core.logging import logger


class OptimizationFeatureExtractor(IFeatureExtractor):
    """
    Extracts standardized, deterministic numeric and structural features
    from canonical problem instances and their formulations.
    """

    def extract_features(
        self,
        problem_type: ProblemType,
        instance_data: Dict[str, Any],
        formulation_data: Optional[Dict[str, Any]] = None,
        resource_budget: Optional[Dict[str, Any]] = None,
    ) -> OptimizationFeatures:
        """Extract comprehensive feature vector for a problem instance."""
        try:
            if problem_type == ProblemType.MAX_CUT:
                return self._extract_max_cut_features(instance_data, formulation_data, resource_budget)
            elif problem_type == ProblemType.ASSIGNMENT:
                return self._extract_assignment_features(instance_data, formulation_data, resource_budget)
            elif problem_type == ProblemType.TSP:
                return self._extract_tsp_features(instance_data, formulation_data, resource_budget)
            else:
                raise FeatureExtractionError(f"Unsupported problem type for feature extraction: {problem_type}")
        except Exception as e:
            if isinstance(e, FeatureExtractionError):
                raise
            raise FeatureExtractionError(f"Failed to extract features for {problem_type.value}: {str(e)}") from e

    # -------------------------------------------------------------------------
    # Max-Cut Features
    # -------------------------------------------------------------------------
    def _extract_max_cut_features(
        self,
        instance: Dict[str, Any],
        formulation: Optional[Dict[str, Any]],
        budget: Optional[Dict[str, Any]],
    ) -> OptimizationFeatures:
        nodes: List[Any] = instance.get("nodes", [])
        raw_edges: List[Any] = instance.get("edges", [])

        num_vertices = len(nodes)
        num_edges = len(raw_edges)

        # Adjacency and degree mapping
        adj: Dict[Any, List[Any]] = {n: [] for n in nodes}
        weights: List[float] = []

        for e in raw_edges:
            if len(e) >= 2:
                u, v = e[0], e[1]
                w = float(e[2]) if len(e) > 2 else 1.0
                weights.append(w)
                if u in adj:
                    adj[u].append(v)
                if v in adj:
                    adj[v].append(u)

        degrees = [len(neighbors) for neighbors in adj.values()] or [0]
        min_deg = int(np.min(degrees)) if degrees else 0
        max_deg = int(np.max(degrees)) if degrees else 0
        avg_deg = float(np.mean(degrees)) if degrees else 0.0
        std_deg = float(np.std(degrees)) if degrees else 0.0

        possible_edges = (num_vertices * (num_vertices - 1)) / 2 if num_vertices > 1 else 1.0
        graph_density = float(min(1.0, max(0.0, num_edges / possible_edges))) if possible_edges > 0 else 0.0

        # Connected components via BFS
        num_components = self._count_connected_components(nodes, adj)

        # Coefficient statistics from edge weights
        c_min, c_max, c_mean, c_std, c_range = self._compute_distribution_stats(weights or [1.0])

        # State space log2: 2^n -> n
        search_space_log2 = float(num_vertices)

        # QUBO / Ising characteristics
        qubo_vars = num_vertices
        qubo_quad = num_edges
        max_couplings = (qubo_vars * (qubo_vars - 1)) / 2 if qubo_vars > 1 else 1.0
        qubo_density = float(min(1.0, qubo_quad / max_couplings)) if max_couplings > 0 else 0.0

        b = budget or {}
        return OptimizationFeatures(
            schema_version=ai_settings.FEATURE_SCHEMA_VERSION,
            problem_type=ProblemType.MAX_CUT,
            num_variables=num_vertices,
            num_constraints=0,  # Unconstrained binary quadratic
            constraint_density=0.0,
            estimated_search_space_log2=search_space_log2,
            coeff_min=c_min,
            coeff_max=c_max,
            coeff_mean=c_mean,
            coeff_std=c_std,
            coeff_range=c_range,
            num_vertices=num_vertices,
            num_edges=num_edges,
            graph_density=graph_density,
            min_degree=min_deg,
            max_degree=max_deg,
            avg_degree=avg_deg,
            degree_std=std_deg,
            num_connected_components=num_components,
            qubo_num_binary_vars=qubo_vars,
            qubo_nonzero_linear=num_vertices,
            qubo_nonzero_quadratic=qubo_quad,
            qubo_interaction_density=qubo_density,
            ising_num_spins=num_vertices,
            ising_coupling_density=qubo_density,
            ising_max_coupling=c_max / 4.0 if weights else 0.25,
            required_qubits=num_vertices,
            estimated_circuit_depth_p1=max(1, max_deg),
            max_eval_budget=b.get("max_eval_budget"),
            time_limit_seconds=b.get("time_limit_seconds"),
        )

    # -------------------------------------------------------------------------
    # Assignment Features
    # -------------------------------------------------------------------------
    def _extract_assignment_features(
        self,
        instance: Dict[str, Any],
        formulation: Optional[Dict[str, Any]],
        budget: Optional[Dict[str, Any]],
    ) -> OptimizationFeatures:
        agents: List[Any] = instance.get("agents", [])
        tasks: List[Any] = instance.get("tasks", [])
        cost_matrix = instance.get("cost_matrix", [[]])

        n_agents = len(agents)
        n_tasks = len(tasks)
        is_square = (n_agents == n_tasks)

        # Flatten cost matrix
        flat_costs: List[float] = []
        for row in cost_matrix:
            for val in row:
                flat_costs.append(float(val))

        c_min, c_max, c_mean, c_std, c_range = self._compute_distribution_stats(flat_costs or [0.0])

        num_vars = n_agents * n_tasks
        # 1-to-1 matching constraints: n row constraints + m col constraints
        num_constraints = n_agents + n_tasks
        constraint_density = float(num_constraints / num_vars) if num_vars > 0 else 0.0

        # Search space for square assignment: n! permutations
        search_space_log2 = self._log2_factorial(n_agents)

        # QUBO / Ising terms: n*m binary variables
        qubo_vars = num_vars
        # Penalty quadratic interactions: row pairs (n * m*(m-1)/2) + col pairs (m * n*(n-1)/2)
        row_pairs = n_agents * (n_tasks * (n_tasks - 1) // 2) if n_tasks > 1 else 0
        col_pairs = n_tasks * (n_agents * (n_agents - 1) // 2) if n_agents > 1 else 0
        qubo_quad = row_pairs + col_pairs
        total_possible = (qubo_vars * (qubo_vars - 1)) / 2 if qubo_vars > 1 else 1.0
        qubo_density = float(min(1.0, qubo_quad / total_possible)) if total_possible > 0 else 0.0

        b = budget or {}
        return OptimizationFeatures(
            schema_version=ai_settings.FEATURE_SCHEMA_VERSION,
            problem_type=ProblemType.ASSIGNMENT,
            num_variables=num_vars,
            num_constraints=num_constraints,
            constraint_density=constraint_density,
            estimated_search_space_log2=search_space_log2,
            coeff_min=c_min,
            coeff_max=c_max,
            coeff_mean=c_mean,
            coeff_std=c_std,
            coeff_range=c_range,
            num_agents=n_agents,
            num_tasks=n_tasks,
            is_square_matrix=is_square,
            qubo_num_binary_vars=qubo_vars,
            qubo_nonzero_linear=qubo_vars,
            qubo_nonzero_quadratic=qubo_quad,
            qubo_interaction_density=qubo_density,
            ising_num_spins=qubo_vars,
            ising_coupling_density=qubo_density,
            ising_max_coupling=c_range if c_range > 0 else 1.0,
            required_qubits=qubo_vars,
            estimated_circuit_depth_p1=max(2, n_agents + n_tasks),
            max_eval_budget=b.get("max_eval_budget"),
            time_limit_seconds=b.get("time_limit_seconds"),
        )

    # -------------------------------------------------------------------------
    # TSP Features
    # -------------------------------------------------------------------------
    def _extract_tsp_features(
        self,
        instance: Dict[str, Any],
        formulation: Optional[Dict[str, Any]],
        budget: Optional[Dict[str, Any]],
    ) -> OptimizationFeatures:
        cities: List[Any] = instance.get("cities", [])
        dist_matrix = instance.get("distance_matrix", [[]])

        n_cities = len(cities)
        flat_distances: List[float] = []

        is_symmetric = True
        satisfies_triangle = True

        for i in range(n_cities):
            for j in range(n_cities):
                if i != j and i < len(dist_matrix) and j < len(dist_matrix[i]):
                    d_ij = float(dist_matrix[i][j])
                    flat_distances.append(d_ij)
                    # Check symmetry
                    if j < len(dist_matrix) and i < len(dist_matrix[j]):
                        d_ji = float(dist_matrix[j][i])
                        if abs(d_ij - d_ji) > 1e-6:
                            is_symmetric = False

        # Check triangle inequality for a sample if n_cities <= 20
        if n_cities >= 3:
            for i in range(min(n_cities, 12)):
                for j in range(min(n_cities, 12)):
                    for k in range(min(n_cities, 12)):
                        if i != j and j != k and i != k:
                            d_ik = float(dist_matrix[i][k])
                            d_ij = float(dist_matrix[i][j])
                            d_jk = float(dist_matrix[j][k])
                            if d_ik > (d_ij + d_jk + 1e-6):
                                satisfies_triangle = False
                                break

        c_min, c_max, c_mean, c_std, c_range = self._compute_distribution_stats(flat_distances or [1.0])

        # TSP binary formulation uses n^2 variables (city at step p)
        num_vars = n_cities * n_cities
        # 2n constraints: exactly one city per step, exactly one step per city
        num_constraints = 2 * n_cities
        constraint_density = float(num_constraints / num_vars) if num_vars > 0 else 0.0

        # Search space: (n-1)! / 2 for symmetric, (n-1)! for asymmetric
        search_space_log2 = self._log2_factorial(max(1, n_cities - 1))
        if is_symmetric and search_space_log2 > 1.0:
            search_space_log2 -= 1.0

        qubo_vars = num_vars
        # Interactions: transition edges + penalty mutually-exclusive pairs
        qubo_quad = n_cities * (n_cities - 1) * n_cities
        total_possible = (qubo_vars * (qubo_vars - 1)) / 2 if qubo_vars > 1 else 1.0
        qubo_density = float(min(1.0, qubo_quad / total_possible)) if total_possible > 0 else 0.0

        b = budget or {}
        return OptimizationFeatures(
            schema_version=ai_settings.FEATURE_SCHEMA_VERSION,
            problem_type=ProblemType.TSP,
            num_variables=num_vars,
            num_constraints=num_constraints,
            constraint_density=constraint_density,
            estimated_search_space_log2=search_space_log2,
            coeff_min=c_min,
            coeff_max=c_max,
            coeff_mean=c_mean,
            coeff_std=c_std,
            coeff_range=c_range,
            num_cities=n_cities,
            is_symmetric_distance=is_symmetric,
            satisfies_triangle_inequality=satisfies_triangle,
            qubo_num_binary_vars=qubo_vars,
            qubo_nonzero_linear=qubo_vars,
            qubo_nonzero_quadratic=qubo_quad,
            qubo_interaction_density=qubo_density,
            ising_num_spins=qubo_vars,
            ising_coupling_density=qubo_density,
            ising_max_coupling=c_range if c_range > 0 else 1.0,
            required_qubits=qubo_vars,
            estimated_circuit_depth_p1=max(2, 2 * n_cities),
            max_eval_budget=b.get("max_eval_budget"),
            time_limit_seconds=b.get("time_limit_seconds"),
        )

    # -------------------------------------------------------------------------
    # Helper algorithms
    # -------------------------------------------------------------------------
    @staticmethod
    def _compute_distribution_stats(vals: List[float]):
        """Calculate min, max, mean, std, range with numerical stability."""
        if not vals:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        arr = np.array(vals, dtype=float)
        v_min = float(np.min(arr))
        v_max = float(np.max(arr))
        v_mean = float(np.mean(arr))
        v_std = float(np.std(arr))
        v_range = float(v_max - v_min)
        return v_min, v_max, v_mean, v_std, v_range

    @staticmethod
    def _count_connected_components(nodes: List[Any], adj: Dict[Any, List[Any]]) -> int:
        """Count connected components using BFS."""
        visited: Set[Any] = set()
        count = 0
        for node in nodes:
            if node not in visited:
                count += 1
                queue = [node]
                visited.add(node)
                while queue:
                    curr = queue.pop(0)
                    for neighbor in adj.get(curr, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
        return max(1, count) if nodes else 0

    @staticmethod
    def _log2_factorial(n: int) -> float:
        """Calculate log2(n!) accurately using math.lgamma."""
        if n <= 1:
            return 0.0
        # log2(n!) = ln(Gamma(n + 1)) / ln(2)
        return float(math.lgamma(n + 1) / math.log(2))


# Instantiate and register default extractor
default_feature_extractor = OptimizationFeatureExtractor()
from backend.app.ai.registry import AIServiceRegistry
AIServiceRegistry.register_feature_extractor(default_feature_extractor)
