"""Unit and mathematical verification tests for Max-Cut QUBO generation."""

import itertools
import pytest
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.evaluation.max_cut_evaluator import MaxCutEvaluator


def test_max_cut_qubo_two_node_hand_calculated():
    """
    Two-node graph: nodes A, B, edge (A, B, 5.0)
    Objective: max 5.0 * (x_A + x_B - 2 x_A x_B)
    Minimization QUBO: min -5.0 x_A - 5.0 x_B + 10.0 x_A x_B
    Hand-calculated Q:
      Q_AA = -5.0
      Q_BB = -5.0
      Q_AB = 10.0
      offset = 0.0
    """
    problem = {
        "nodes": ["A", "B"],
        "edges": [["A", "B", 5.0]],
    }
    qubo = MaxCutQuboGenerator.generate(problem)
    assert qubo.variable_order == ["A", "B"]
    assert qubo.linear_terms["A"] == -5.0
    assert qubo.linear_terms["B"] == -5.0
    assert qubo.quadratic_terms["A,B"] == 10.0
    assert qubo.offset == 0.0

    evaluator = MaxCutEvaluator()
    for x_a in [0, 1]:
        for x_b in [0, 1]:
            cand = {"A": x_a, "B": x_b}
            cut_val = evaluator.evaluate_objective(problem, cand)

            # Manual QUBO evaluation: -5*x_a - 5*x_b + 10*x_a*x_b
            e_qubo = -5.0 * x_a - 5.0 * x_b + 10.0 * x_a * x_b
            assert e_qubo == - cut_val


def test_max_cut_qubo_three_node_triangle_exhaustive():
    """
    3-node triangle with weights:
      (A, B, 1.0), (B, C, 2.0), (A, C, 3.0)
    Hand-calculated degrees:
      deg_w(A) = 1 + 3 = 4.0  -> Q_AA = -4.0
      deg_w(B) = 1 + 2 = 3.0  -> Q_BB = -3.0
      deg_w(C) = 2 + 3 = 5.0  -> Q_CC = -5.0
    Couplings:
      Q_AB = 2.0
      Q_AC = 6.0
      Q_BC = 4.0
    """
    problem = {
        "nodes": ["A", "B", "C"],
        "edges": [
            ["A", "B", 1.0],
            ["B", "C", 2.0],
            ["A", "C", 3.0],
        ],
    }
    qubo = MaxCutQuboGenerator.generate(problem)
    assert qubo.linear_terms["A"] == -4.0
    assert qubo.linear_terms["B"] == -3.0
    assert qubo.linear_terms["C"] == -5.0
    assert qubo.quadratic_terms["A,B"] == 2.0
    assert qubo.quadratic_terms["A,C"] == 6.0
    assert qubo.quadratic_terms["B,C"] == 4.0

    # Exhaustive verification against independent Phase 2 evaluator
    evaluator = MaxCutEvaluator()
    for bits in itertools.product([0, 1], repeat=3):
        cand = {"A": bits[0], "B": bits[1], "C": bits[2]}
        cut_val = evaluator.evaluate_objective(problem, cand)
        e_qubo = (
            qubo.linear_terms["A"] * bits[0]
            + qubo.linear_terms["B"] * bits[1]
            + qubo.linear_terms["C"] * bits[2]
            + qubo.quadratic_terms["A,B"] * bits[0] * bits[1]
            + qubo.quadratic_terms["A,C"] * bits[0] * bits[2]
            + qubo.quadratic_terms["B,C"] * bits[1] * bits[2]
        )
        assert abs(e_qubo - (-cut_val)) < 1e-9


def test_max_cut_qubo_disconnected_and_isolated_vertex():
    """
    Graph with an isolated vertex:
    Nodes: A, B, C, D (D is isolated)
    Edges: (A, B, 2.0), (B, C, 4.0)
    Vertex D has zero degree -> Q_DD should be 0.0, no cross-terms with D.
    """
    problem = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 2.0],
            ["B", "C", 4.0],
        ],
    }
    qubo = MaxCutQuboGenerator.generate(problem)
    assert "D" not in qubo.linear_terms  # zero coefficient filtered
    assert not any("D" in key for key in qubo.quadratic_terms.keys())

    evaluator = MaxCutEvaluator()
    for bits in itertools.product([0, 1], repeat=4):
        cand = {"A": bits[0], "B": bits[1], "C": bits[2], "D": bits[3]}
        cut_val = evaluator.evaluate_objective(problem, cand)

        # QUBO energy
        e_qubo = (
            qubo.linear_terms.get("A", 0.0) * bits[0]
            + qubo.linear_terms.get("B", 0.0) * bits[1]
            + qubo.linear_terms.get("C", 0.0) * bits[2]
            + qubo.quadratic_terms.get("A,B", 0.0) * bits[0] * bits[1]
            + qubo.quadratic_terms.get("B,C", 0.0) * bits[1] * bits[2]
        )
        assert abs(e_qubo - (-cut_val)) < 1e-9
