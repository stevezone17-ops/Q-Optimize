"""Comprehensive mathematical unit tests for Max-Cut Evaluator."""

import pytest
from backend.app.domain.problems.models import MaxCutInstance
from backend.app.evaluation.max_cut_evaluator import MaxCutEvaluator


@pytest.fixture
def evaluator():
    return MaxCutEvaluator()


def test_max_cut_two_node_crossing(evaluator):
    """Two-node graph with weight 7.5. Partitioning nodes cuts the single edge."""
    problem = {
        "nodes": ["A", "B"],
        "edges": [["A", "B", 7.5]],
    }
    # Hand-calculated expected cut: 7.5
    res = evaluator.evaluate(problem, {"A": 0, "B": 1})
    assert res.is_feasible is True
    assert res.objective_value == 7.5
    assert len(res.violations) == 0
    assert len(res.details["crossing_edges"]) == 1
    assert res.details["cut_fraction"] == 1.0


def test_max_cut_two_node_same_partition(evaluator):
    """Two-node graph where both nodes are in the same partition (cut is 0.0)."""
    problem = {
        "nodes": ["A", "B"],
        "edges": [["A", "B", 7.5]],
    }
    # Hand-calculated expected cut: 0.0
    res = evaluator.evaluate(problem, {"A": 0, "B": 0})
    assert res.is_feasible is True
    assert res.objective_value == 0.0
    assert len(res.details["crossing_edges"]) == 0
    assert len(res.details["non_crossing_edges"]) == 1


def test_max_cut_four_node_weighted_hand_calculated(evaluator):
    """
    Weighted 4-node graph:
    Edges: (A,B, 2.0), (B,C, 3.0), (C,D, 4.0), (D,A, 5.0), (A,C, 1.0)
    Partition: S0 = {A, C}, S1 = {B, D}
    Crossing edges:
      (A, B): 2.0
      (B, C): 3.0
      (C, D): 4.0
      (D, A): 5.0
      (A, C): 0.0 (non-crossing)
    Hand-calculated Cut = 2.0 + 3.0 + 4.0 + 5.0 = 14.0
    Total graph weight = 15.0
    """
    problem = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 2.0],
            ["B", "C", 3.0],
            ["C", "D", 4.0],
            ["D", "A", 5.0],
            ["A", "C", 1.0],
        ],
    }
    res = evaluator.evaluate(problem, {"A": 0, "B": 1, "C": 0, "D": 1})
    assert res.is_feasible is True
    assert res.objective_value == 14.0
    assert res.details["total_graph_weight"] == 15.0
    assert res.details["crossing_edge_count"] == 4
    assert res.details["partition_0"] == ["A", "C"]
    assert res.details["partition_1"] == ["B", "D"]


def test_max_cut_disconnected_graph(evaluator):
    """
    Disconnected graph with two components: {A, B} and {C, D}.
    Component 1: (A, B, 3.0)
    Component 2: (C, D, 6.0)
    Partition: A=0, B=1, C=0, D=1
    Both component edges cross their partition boundaries -> Hand-calculated cut = 3.0 + 6.0 = 9.0
    """
    problem = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 3.0],
            ["C", "D", 6.0],
        ],
    }
    res = evaluator.evaluate(problem, {"A": 0, "B": 1, "C": 0, "D": 1})
    assert res.is_feasible is True
    assert res.objective_value == 9.0

    # Only first component crosses
    res_half = evaluator.evaluate(problem, {"A": 0, "B": 1, "C": 0, "D": 0})
    assert res_half.is_feasible is True
    assert res_half.objective_value == 3.0


def test_max_cut_unweighted_edges_default_to_one(evaluator):
    """Unweighted edges [u, v] default to weight 1.0."""
    instance = MaxCutInstance(
        nodes=["A", "B", "C"],
        edges=[["A", "B"], ["B", "C"]],
    )
    res = evaluator.evaluate(instance.model_dump(), {"A": 0, "B": 1, "C": 0})
    assert res.is_feasible is True
    assert res.objective_value == 2.0  # Both edges cross with weight 1.0 each


def test_max_cut_solution_as_list(evaluator):
    """Candidate solution provided as aligned binary vector [0, 1, 0, 1]."""
    problem = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 2.0],
            ["B", "C", 3.0],
            ["C", "D", 4.0],
            ["D", "A", 5.0],
        ],
    }
    res = evaluator.evaluate(problem, [0, 1, 0, 1])
    assert res.is_feasible is True
    assert res.objective_value == 14.0


def test_max_cut_invalid_solution_missing_node(evaluator):
    """Candidate solution omits a vertex -> infeasible with structured violation."""
    problem = {
        "nodes": ["A", "B", "C"],
        "edges": [["A", "B", 1.0], ["B", "C", 1.0]],
    }
    res = evaluator.evaluate(problem, {"A": 0, "B": 1})
    assert res.is_feasible is False
    assert len(res.violations) >= 1
    assert any(v.constraint_id == "MISSING_VARIABLE" for v in res.violations)


def test_max_cut_invalid_solution_non_binary_value(evaluator):
    """Candidate solution assigns invalid non-binary value 2 -> violation."""
    problem = {
        "nodes": ["A", "B"],
        "edges": [["A", "B", 1.0]],
    }
    res = evaluator.evaluate(problem, {"A": 0, "B": 2})
    assert res.is_feasible is False
    assert any(v.constraint_id == "BINARY_DOMAIN_VIOLATION" for v in res.violations)

