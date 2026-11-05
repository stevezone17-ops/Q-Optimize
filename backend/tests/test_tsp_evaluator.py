"""Comprehensive mathematical unit tests for Travelling Salesperson Problem (TSP) Evaluator."""

import pytest
from backend.app.domain.problems.models import TSPInstance
from backend.app.evaluation.tsp_evaluator import TSPEvaluator


@pytest.fixture
def evaluator():
    return TSPEvaluator()


def test_tsp_three_city_tour(evaluator):
    """
    3-City Triangle:
      Paris -> London: 344.0, London -> Berlin: 933.0, Berlin -> Paris: 878.0
    Tour: Paris -> London -> Berlin -> Paris
    Hand-calculated Distance: 344.0 + 933.0 + 878.0 = 2155.0
    """
    problem = {
        "cities": ["Paris", "London", "Berlin"],
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
    }
    # Open tour specification (implicitly closed)
    res = evaluator.evaluate(problem, ["Paris", "London", "Berlin"])
    assert res.is_feasible is True
    assert res.objective_value == 2155.0
    assert len(res.violations) == 0
    assert len(res.details["legs"]) == 3
    assert res.details["is_symmetric"] is True


def test_tsp_explicitly_closed_tour(evaluator):
    """Explicitly closed tour [Paris, London, Berlin, Paris] produces exact same distance."""
    problem = {
        "cities": ["Paris", "London", "Berlin"],
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
    }
    res = evaluator.evaluate(problem, ["Paris", "London", "Berlin", "Paris"])
    assert res.is_feasible is True
    assert res.objective_value == 2155.0


def test_tsp_four_city_tour_by_indices(evaluator):
    """
    4-City circuit:
    Cities: [C0, C1, C2, C3]
    Distances:
      C0-C1: 10, C1-C2: 15, C2-C3: 35, C3-C0: 30
    Tour: [0, 1, 2, 3] -> Hand-calculated distance = 10 + 15 + 35 + 30 = 90.0
    """
    problem = {
        "cities": ["C0", "C1", "C2", "C3"],
        "distance_matrix": [
            [0.0, 10.0, 20.0, 30.0],
            [10.0, 0.0, 15.0, 25.0],
            [20.0, 15.0, 0.0, 35.0],
            [30.0, 25.0, 35.0, 0.0],
        ],
    }
    res = evaluator.evaluate(problem, [0, 1, 2, 3])
    assert res.is_feasible is True
    assert res.objective_value == 90.0
    assert res.details["num_cities"] == 4


def test_tsp_asymmetric_distance_matrix(evaluator):
    """
    Asymmetric distance matrix:
    Cities: [X, Y, Z]
    D[X, Y] = 5,  D[Y, X] = 12
    D[Y, Z] = 8,  D[Z, Y] = 14
    D[Z, X] = 20, D[X, Z] = 3

    Forward tour [X, Y, Z, X]:
      X->Y (5) + Y->Z (8) + Z->X (20) = 33.0
    Reverse tour [X, Z, Y, X]:
      X->Z (3) + Z->Y (14) + Y->X (12) = 29.0
    """
    problem = {
        "cities": ["X", "Y", "Z"],
        "distance_matrix": [
            [0.0, 5.0, 3.0],
            [12.0, 0.0, 8.0],
            [20.0, 14.0, 0.0],
        ],
    }
    res_fwd = evaluator.evaluate(problem, ["X", "Y", "Z"])
    assert res_fwd.is_feasible is True
    assert res_fwd.objective_value == 33.0
    assert res_fwd.details["is_symmetric"] is False

    res_rev = evaluator.evaluate(problem, ["X", "Z", "Y"])
    assert res_rev.is_feasible is True
    assert res_rev.objective_value == 29.0


def test_tsp_start_city_constraint(evaluator):
    """When start_city is configured, starting at a different city raises START_CITY_MISMATCH."""
    problem = {
        "cities": ["Paris", "London", "Berlin"],
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
        "start_city": "Paris",
    }
    # Tour starts at London instead of Paris
    res = evaluator.evaluate(problem, ["London", "Berlin", "Paris"])
    assert res.is_feasible is False
    assert any(v.constraint_id == "START_CITY_MISMATCH" for v in res.violations)


def test_tsp_invalid_city_identifier(evaluator):
    """Tour referencing unknown city fails city validity constraint."""
    problem = {
        "cities": ["Paris", "London", "Berlin"],
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
    }
    res = evaluator.evaluate(problem, ["Paris", "Tokyo", "Berlin"])
    assert res.is_feasible is False
    assert any(v.constraint_id == "UNKNOWN_CITY" for v in res.violations)


def test_tsp_duplicate_city_visit_fails(evaluator):
    """Revisiting a city before completing tour cycle fails single visit constraint."""
    problem = {
        "cities": ["Paris", "London", "Berlin"],
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
    }
    # London visited twice
    res = evaluator.evaluate(problem, ["Paris", "London", "London"])
    assert res.is_feasible is False
    assert any(v.constraint_id == "DUPLICATE_CITY_VISIT" for v in res.violations)
    assert any(v.constraint_id == "OMITTED_CITIES" for v in res.violations)


def test_tsp_missing_city_tour_fails(evaluator):
    """Incomplete tour omitting cities fails length constraint."""
    problem = {
        "cities": ["Paris", "London", "Berlin"],
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
    }
    res = evaluator.evaluate(problem, ["Paris", "London"])
    assert res.is_feasible is False
    assert any(v.constraint_id == "TOUR_LENGTH_MISMATCH" for v in res.violations)

