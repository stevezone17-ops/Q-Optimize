"""Max-Cut canonical QUBO formulation generator."""

from typing import Dict, Any, List, Tuple
from backend.app.domain.formulations.models import QuboModel
from backend.app.formulations.qubo_builder import QuboBuilder


class MaxCutQuboGenerator:
    """
    Constructs the canonical minimization QUBO for Max-Cut:
    Original problem:
        max sum_{(i,j) in E} w_{ij} * (x_i + x_j - 2*x_i*x_j)
    Equivalent minimization QUBO:
        min E(x) = - C(x) = sum_{(i,j) in E} w_{ij} * (2*x_i*x_j - x_i - x_j)
    Upper-triangular terms:
        - Linear coefficient on diagonal for vertex v: Q_{vv} = - sum_{u in N(v)} w_{vu}
        - Quadratic interaction between connected vertices (u, v) with u < v: Q_{uv} = 2 * w_{uv}
        - Constant offset: c = 0.0
    Equivalence guarantee:
        E_QUBO(x) == - C(x) for all binary vectors x in {0, 1}^|V|.
    """

    @staticmethod
    def generate(instance_data: Dict[str, Any]) -> QuboModel:
        nodes: List[str] = instance_data.get("nodes", [])
        edges: List[Any] = instance_data.get("edges", [])

        if len(nodes) < 2:
            raise ValueError("Max-Cut requires at least 2 nodes.")

        # Preserve canonical node ordering
        builder = QuboBuilder(variable_order=nodes)

        total_weight = 0.0
        for edge in edges:
            u = str(edge[0]).strip()
            v = str(edge[1]).strip()
            w = float(edge[2]) if len(edge) >= 3 else 1.0
            total_weight += w

            # Linear terms: -w * x_u and -w * x_v
            builder.add_linear(u, -w)
            builder.add_linear(v, -w)

            # Quadratic cross-term: +2w * x_u * x_v
            builder.add_quadratic(u, v, 2.0 * w)

        builder.metadata = {
            "problem_type": "max_cut",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "total_graph_weight": total_weight,
            "objective_conversion": "min E_QUBO(x) == - C(x)",
            "sign_relationship": "C(x) = - E_QUBO(x)",
        }
        builder.assumptions = [
            "Graph is undirected with canonical node indexing.",
            "QUBO formulation minimizes negative cut value: E_QUBO(x) = -C(x).",
            "Isolated vertices (degree 0) have zero linear and quadratic coefficients.",
        ]

        return builder.build_model()
