"""Comprehensive mathematical unit tests for Assignment Evaluator."""

import pytest
from backend.app.domain.problems.models import AssignmentInstance
from backend.app.evaluation.assignment_evaluator import AssignmentEvaluator


@pytest.fixture
def evaluator():
    return AssignmentEvaluator()


def test_standard_3x3_assignment_optimal(evaluator):
    """
    Standard 3x3 assignment cost matrix:
      Alice:   [9.0, 2.0, 7.0]
      Bob:     [6.0, 4.0, 3.0]
      Charlie: [5.0, 8.0, 1.0]

    Candidate 1 (Optimal Matching):
      Alice -> Task_2 (2.0)
      Bob -> Task_1 (6.0)
      Charlie -> Task_3 (1.0)
    Hand-calculated Cost = 2.0 + 6.0 + 1.0 = 9.0
    """
    problem = {
        "agents": ["Alice", "Bob", "Charlie"],
        "tasks": ["Task_1", "Task_2", "Task_3"],
        "cost_matrix": [
            [9.0, 2.0, 7.0],
            [6.0, 4.0, 3.0],
            [5.0, 8.0, 1.0],
        ],
    }
    candidate = {
        "Alice": "Task_2",
        "Bob": "Task_1",
        "Charlie": "Task_3",
    }
    res = evaluator.evaluate(problem, candidate)
    assert res.is_feasible is True
    assert res.objective_value == 9.0
    assert len(res.violations) == 0
    assert res.details["assigned_count"] == 3
    assert len(res.details["unassigned_agents"]) == 0
    assert len(res.details["unassigned_tasks"]) == 0


def test_standard_3x3_assignment_suboptimal(evaluator):
    """
    Same 3x3 problem with suboptimal assignment:
      Alice -> Task_1 (9.0)
      Bob -> Task_2 (4.0)
      Charlie -> Task_3 (1.0)
    Hand-calculated Cost = 9.0 + 4.0 + 1.0 = 14.0
    """
    problem = {
        "agents": ["Alice", "Bob", "Charlie"],
        "tasks": ["Task_1", "Task_2", "Task_3"],
        "cost_matrix": [
            [9.0, 2.0, 7.0],
            [6.0, 4.0, 3.0],
            [5.0, 8.0, 1.0],
        ],
    }
    candidate = {
        "Alice": "Task_1",
        "Bob": "Task_2",
        "Charlie": "Task_3",
    }
    res = evaluator.evaluate(problem, candidate)
    assert res.is_feasible is True
    assert res.objective_value == 14.0


def test_assignment_via_binary_matrix(evaluator):
    """Candidate solution provided as binary permutation matrix."""
    problem = {
        "agents": ["Alice", "Bob", "Charlie"],
        "tasks": ["Task_1", "Task_2", "Task_3"],
        "cost_matrix": [
            [9.0, 2.0, 7.0],
            [6.0, 4.0, 3.0],
            [5.0, 8.0, 1.0],
        ],
    }
    # Alice->Task_2 (col 1), Bob->Task_1 (col 0), Charlie->Task_3 (col 2)
    binary_matrix = [
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
    ]
    res = evaluator.evaluate(problem, binary_matrix)
    assert res.is_feasible is True
    assert res.objective_value == 9.0


def test_rectangular_assignment_feasibility(evaluator):
    """
    Rectangular instance (2 agents, 3 tasks):
      Agent_1 -> Task_2 (20.0)
      Agent_2 -> Task_3 (60.0)
    Hand-calculated Cost = 80.0
    """
    problem = {
        "agents": ["Agent_1", "Agent_2"],
        "tasks": ["Task_1", "Task_2", "Task_3"],
        "cost_matrix": [
            [10.0, 20.0, 30.0],
            [40.0, 50.0, 60.0],
        ],
    }
    candidate = {"Agent_1": "Task_2", "Agent_2": "Task_3"}
    res = evaluator.evaluate(problem, candidate)
    assert res.is_feasible is True
    assert res.objective_value == 80.0
    assert len(res.details["unassigned_tasks"]) == 1
    assert res.details["unassigned_tasks"][0] == "Task_1"


def test_assignment_duplicate_agent_assignment_fails(evaluator):
    """Agent assigned multiple tasks fails agent single task constraint."""
    problem = {
        "agents": ["Alice", "Bob"],
        "tasks": ["Task_1", "Task_2"],
        "cost_matrix": [[1.0, 2.0], [3.0, 4.0]],
    }
    # Alice assigned both Task_1 and Task_2
    candidate = [("Alice", "Task_1"), ("Alice", "Task_2")]
    res = evaluator.evaluate(problem, candidate)
    assert res.is_feasible is False
    assert any(v.constraint_id == "AGENT_DUPLICATE_ASSIGNMENT" for v in res.violations)


def test_assignment_duplicate_task_assignment_fails(evaluator):
    """Task assigned to multiple agents fails task single agent constraint."""
    problem = {
        "agents": ["Alice", "Bob"],
        "tasks": ["Task_1", "Task_2"],
        "cost_matrix": [[1.0, 2.0], [3.0, 4.0]],
    }
    # Both Alice and Bob assigned to Task_1
    candidate = [("Alice", "Task_1"), ("Bob", "Task_1")]
    res = evaluator.evaluate(problem, candidate)
    assert res.is_feasible is False
    assert any(v.constraint_id == "TASK_DUPLICATE_ASSIGNMENT" for v in res.violations)


def test_assignment_missing_agent_in_square_fails(evaluator):
    """In square matching, leaving an agent unassigned fails complete matching constraint."""
    problem = {
        "agents": ["Alice", "Bob"],
        "tasks": ["Task_1", "Task_2"],
        "cost_matrix": [[1.0, 2.0], [3.0, 4.0]],
    }
    candidate = {"Alice": "Task_1"}  # Bob is missing
    res = evaluator.evaluate(problem, candidate)
    assert res.is_feasible is False
    assert any(v.constraint_id == "UNASSIGNED_AGENT" for v in res.violations)
    assert any(v.constraint_id == "UNASSIGNED_TASK" for v in res.violations)


def test_assignment_invalid_matrix_cost():
    """AssignmentInstance rejects NaN or non-finite cost values."""
    with pytest.raises(ValueError):
        AssignmentInstance(
            agents=["Alice"],
            tasks=["Task_1"],
            cost_matrix=[[float("nan")]],
        )

