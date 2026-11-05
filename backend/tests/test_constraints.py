"""Unit tests for the reusable constraint validation engine."""

import pytest
from backend.app.evaluation.constraints import ConstraintValidator, ConstraintViolation


def test_validate_binary_variables_valid():
    """Valid binary dict returns zero violations."""
    vals = {"x1": 0, "x2": 1, "x3": 1.0, "x4": 0.0, "x5": True, "x6": False}
    violations = ConstraintValidator.validate_binary_variables(vals)
    assert len(violations) == 0


def test_validate_binary_variables_invalid():
    """Non-binary or non-numeric values return domain and type violations."""
    vals = {"x1": 2, "x2": -1, "x3": 0.5, "x4": "invalid_str"}
    violations = ConstraintValidator.validate_binary_variables(vals)
    assert len(violations) == 4
    assert any(v.constraint_id == "BINARY_DOMAIN_VIOLATION" for v in violations)
    assert any(v.constraint_id == "BINARY_TYPE_VIOLATION" for v in violations)


def test_validate_binary_variables_missing_and_unknown():
    """Checking expected variables catches missing and unexpected variables."""
    expected = ["x1", "x2", "x3"]
    provided = {"x1": 1, "x4": 0}  # x2, x3 missing; x4 unexpected
    violations = ConstraintValidator.validate_binary_variables(provided, expected_variables=expected)
    assert any(v.constraint_id == "MISSING_VARIABLE" and "x2" in v.message for v in violations)
    assert any(v.constraint_id == "MISSING_VARIABLE" and "x3" in v.message for v in violations)
    assert any(v.constraint_id == "UNKNOWN_VARIABLE" and "x4" in v.message for v in violations)


def test_validate_graph_partition_complete():
    """Graph partition assigns every node exactly to 0 or 1."""
    nodes = ["v1", "v2", "v3"]
    violations, norm = ConstraintValidator.validate_graph_partition(nodes, {"v1": 0, "v2": 1, "v3": 0})
    assert len(violations) == 0
    assert norm == {"v1": 0, "v2": 1, "v3": 0}


def test_validate_graph_partition_list_mismatch():
    """Vector length mismatch returns PARTITION_LENGTH_MISMATCH."""
    nodes = ["v1", "v2", "v3"]
    violations, _ = ConstraintValidator.validate_graph_partition(nodes, [0, 1])
    assert len(violations) == 1
    assert violations[0].constraint_id == "PARTITION_LENGTH_MISMATCH"


def test_validate_assignment_constraints_bijection():
    """1-to-1 square assignment passes with no violations."""
    agents = ["A1", "A2"]
    tasks = ["T1", "T2"]
    violations, pairs = ConstraintValidator.validate_assignment_constraints(
        agents, tasks, {"A1": "T2", "A2": "T1"}, is_square=True
    )
    assert len(violations) == 0
    assert len(pairs) == 2


def test_validate_assignment_constraints_collision():
    """Two agents assigned to same task produces TASK_DUPLICATE_ASSIGNMENT."""
    agents = ["A1", "A2"]
    tasks = ["T1", "T2"]
    violations, _ = ConstraintValidator.validate_assignment_constraints(
        agents, tasks, [("A1", "T1"), ("A2", "T1")], is_square=True
    )
    assert any(v.constraint_id == "TASK_DUPLICATE_ASSIGNMENT" for v in violations)


def test_validate_tsp_tour_hamiltonian_cycle():
    """Valid TSP tour produces closed cycle."""
    cities = ["C1", "C2", "C3"]
    violations, closed = ConstraintValidator.validate_tsp_tour(cities, ["C1", "C2", "C3"])
    assert len(violations) == 0
    assert closed == ["C1", "C2", "C3", "C1"]
