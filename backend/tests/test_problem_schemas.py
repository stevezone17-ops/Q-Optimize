"""Unit tests for Problem schemas and mathematical validation."""

import pytest
from pydantic import ValidationError
from backend.app.domain.problems.models import (
    MaxCutInstance,
    AssignmentInstance,
    TSPInstance,
    ProblemCreate,
    ProblemType,
)


def test_valid_max_cut_instance():
    instance = MaxCutInstance(
        nodes=["A", "B", "C"],
        edges=[("A", "B", 1.0), ("B", "C", 2.5)],
    )
    assert len(instance.nodes) == 3
    assert len(instance.edges) == 2


def test_max_cut_self_loop_rejected():
    with pytest.raises(ValidationError, match="Self-loops are not allowed"):
        MaxCutInstance(
            nodes=["A", "B"],
            edges=[("A", "A", 1.0)],
        )


def test_max_cut_non_existent_node_rejected():
    with pytest.raises(ValidationError, match="references non-existent node"):
        MaxCutInstance(
            nodes=["A", "B"],
            edges=[("A", "Z", 1.0)],
        )


def test_max_cut_duplicate_edge_rejected():
    with pytest.raises(ValidationError, match="Duplicate edge detected"):
        MaxCutInstance(
            nodes=["A", "B"],
            edges=[("A", "B", 1.0), ("B", "A", 2.0)],
        )


def test_valid_assignment_instance():
    instance = AssignmentInstance(
        agents=["Agent_1", "Agent_2"],
        tasks=["Task_1", "Task_2"],
        cost_matrix=[[5.0, 9.0], [4.0, 2.0]],
    )
    assert len(instance.agents) == 2
    assert len(instance.tasks) == 2
    assert instance.cost_matrix[0][1] == 9.0


def test_assignment_dimension_mismatch_rejected():
    with pytest.raises(ValidationError, match="does not match agent count"):
        AssignmentInstance(
            agents=["A1", "A2"],
            tasks=["T1", "T2"],
            cost_matrix=[[5.0, 9.0]],  # Only 1 row
        )

    with pytest.raises(ValidationError, match="does not match task count"):
        AssignmentInstance(
            agents=["A1", "A2"],
            tasks=["T1", "T2"],
            cost_matrix=[[5.0], [4.0, 2.0]],  # Row 0 has only 1 column
        )


def test_valid_tsp_instance():
    instance = TSPInstance(
        cities=["City_A", "City_B", "City_C"],
        distance_matrix=[
            [0.0, 10.0, 15.0],
            [10.0, 0.0, 35.0],
            [15.0, 35.0, 0.0],
        ],
    )
    assert len(instance.cities) == 3


def test_tsp_non_zero_diagonal_rejected():
    with pytest.raises(ValidationError, match="must be 0"):
        TSPInstance(
            cities=["City_A", "City_B", "City_C"],
            distance_matrix=[
                [1.0, 10.0, 15.0],
                [10.0, 0.0, 35.0],
                [15.0, 35.0, 0.0],
            ],
        )


def test_tsp_negative_distance_rejected():
    with pytest.raises(ValidationError, match="cannot be negative"):
        TSPInstance(
            cities=["City_A", "City_B", "City_C"],
            distance_matrix=[
                [0.0, -10.0, 15.0],
                [10.0, 0.0, 35.0],
                [15.0, 35.0, 0.0],
            ],
        )


def test_problem_create_parsing():
    prob = ProblemCreate(
        name="Triangle Graph Cut",
        problem_type=ProblemType.MAX_CUT,
        instance={
            "nodes": ["0", "1", "2"],
            "edges": [["0", "1", 1.0], ["1", "2", 1.0], ["2", "0", 1.0]],
        },
    )
    parsed = prob.parse_instance()
    assert isinstance(parsed, MaxCutInstance)
