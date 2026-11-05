"""Independent Max-Cut objective evaluator and feasibility verifier."""

import math
from typing import Dict, Any, Tuple, List, Union
from backend.app.evaluation.interface import IEvaluator
from backend.app.evaluation.models import EvaluationResult, ObjectiveSense
from backend.app.evaluation.constraints import ConstraintValidator, ConstraintViolation


class MaxCutEvaluator(IEvaluator):
    """
    Evaluates Max-Cut problem solutions independently:
    Objective:
        max sum_{(i,j) in E} w_{ij} * (x_i + x_j - 2*x_i*x_j)
        where x_i in {0, 1}
    Feasibility:
        Every vertex v in V must be assigned to exactly one partition {0, 1}.
    """

    def check_feasibility(
        self, problem_instance: Dict[str, Any], candidate: Any
    ) -> Tuple[bool, List[ConstraintViolation]]:
        nodes = problem_instance.get("nodes", [])
        violations, _ = ConstraintValidator.validate_graph_partition(nodes, candidate)
        is_feasible = len(violations) == 0
        return is_feasible, violations

    def evaluate_objective(
        self, problem_instance: Dict[str, Any], candidate: Any
    ) -> float:
        nodes = problem_instance.get("nodes", [])
        edges = problem_instance.get("edges", [])
        _, normalized = ConstraintValidator.validate_graph_partition(nodes, candidate)

        cut_value = 0.0
        for edge in edges:
            u, v = edge[0], edge[1]
            w = float(edge[2]) if len(edge) >= 3 else 1.0

            x_u = normalized.get(u, None)
            x_v = normalized.get(v, None)

            if x_u is not None and x_v is not None:
                # w_{ij} * (x_i + x_j - 2*x_i*x_j) evaluates to w_{ij} iff x_i != x_j
                if x_u != x_v:
                    cut_value += w

        return cut_value

    def evaluate(
        self, problem_instance: Dict[str, Any], candidate: Any
    ) -> EvaluationResult:
        nodes = problem_instance.get("nodes", [])
        edges = problem_instance.get("edges", [])

        violations, normalized = ConstraintValidator.validate_graph_partition(nodes, candidate)
        is_feasible = len(violations) == 0

        crossing_edges = []
        non_crossing_edges = []
        total_edge_weight = 0.0
        cut_value = 0.0

        for edge in edges:
            u, v = edge[0], edge[1]
            w = float(edge[2]) if len(edge) >= 3 else 1.0
            total_edge_weight += w

            x_u = normalized.get(u, None)
            x_v = normalized.get(v, None)

            edge_data = {"u": u, "v": v, "weight": w}

            if x_u is not None and x_v is not None:
                if x_u != x_v:
                    cut_value += w
                    crossing_edges.append(edge_data)
                else:
                    non_crossing_edges.append(edge_data)

        # Build partition sets
        partition_s0 = [n for n, p in normalized.items() if p == 0]
        partition_s1 = [n for n, p in normalized.items() if p == 1]

        cut_ratio = (cut_value / total_edge_weight) if total_edge_weight > 0 else 0.0

        details = {
            "partition_0": sorted(partition_s0),
            "partition_1": sorted(partition_s1),
            "crossing_edges": crossing_edges,
            "non_crossing_edges": non_crossing_edges,
            "crossing_edge_count": len(crossing_edges),
            "total_edge_count": len(edges),
            "total_graph_weight": total_edge_weight,
            "cut_fraction": round(cut_ratio, 4),
        }

        return EvaluationResult(
            problem_type="max_cut",
            objective_sense=ObjectiveSense.MAXIMIZE,
            objective_value=cut_value,
            is_feasible=is_feasible,
            violations=violations,
            details=details,
        )

