"""Unit and mathematical verification tests for Travelling Salesperson Problem (TSP) QUBO generation."""

import itertools
import pytest
from backend.app.formulations.tsp_qubo import TSPQuboGenerator
from backend.app.evaluation.tsp_evaluator import TSPEvaluator
from backend.app.formulations.qubo_builder import QuboBuilder


def test_tsp_qubo_three_city_triangle_cyclic_transition():
    """
    3-City Triangle:
      Paris -> London: 344.0
      London -> Berlin: 933.0
      Berlin -> Paris: 878.0
    Tour path: Paris (pos 0), London (pos 1), Berlin (pos 2), returns to Paris (pos 0)
    Cyclic transition: Berlin at pos 2 -> Paris at pos 0 incurs distance 878.0.
    Hand-calculated distance = 344.0 + 933.0 + 878.0 = 2155.0.
    """
    problem = {
        "cities": ["Paris", "London", "Berlin"],
        "distance_matrix": [
            [0.0, 344.0, 878.0],
            [344.0, 0.0, 933.0],
            [878.0, 933.0, 0.0],
        ],
    }
    qubo = TSPQuboGenerator.generate(problem)
    assert qubo.metadata["num_cities"] == 3
    assert qubo.metadata["total_variables"] == 9

    # Reconstruct builder for energy evaluation
    builder = QuboBuilder(variable_order=qubo.variable_order)
    for v, val in qubo.linear_terms.items():
        builder.add_linear(v, val)
    for pair, val in qubo.quadratic_terms.items():
        v1, v2 = pair.split(",")
        builder.add_quadratic(v1, v2, val)
    builder.add_offset(qubo.offset)

    # Tour 1: Paris(0), London(1), Berlin(2)
    # Binary state:
    # Paris_0=1, Paris_1=0, Paris_2=0
    # London_0=0, London_1=1, London_2=0
    # Berlin_0=0, Berlin_1=0, Berlin_2=1
    state_dict = {
        "x_Paris_0": 1, "x_Paris_1": 0, "x_Paris_2": 0,
        "x_London_0": 0, "x_London_1": 1, "x_London_2": 0,
        "x_Berlin_0": 0, "x_Berlin_1": 0, "x_Berlin_2": 1,
    }
    energy = builder.evaluate_energy(state_dict)
    assert abs(energy - 2155.0) < 1e-9

    # Independent check against Phase 2 evaluator
    evaluator = TSPEvaluator()
    dist_orig = evaluator.evaluate_objective(problem, ["Paris", "London", "Berlin"])
    assert abs(energy - dist_orig) < 1e-9


def test_tsp_qubo_asymmetric_matrix_preservation():
    """
    Asymmetric 3-city TSP:
      D[X, Y] = 5.0, D[Y, X] = 12.0
      D[Y, Z] = 8.0, D[Z, Y] = 14.0
      D[Z, X] = 20.0, D[X, Z] = 3.0
    Forward tour [X(0), Y(1), Z(2)]: distance = 5 + 8 + 20 = 33.0
    Reverse tour [X(0), Z(1), Y(2)]: distance = 3 + 14 + 12 = 29.0
    """
    problem = {
        "cities": ["X", "Y", "Z"],
        "distance_matrix": [
            [0.0, 5.0, 3.0],
            [12.0, 0.0, 8.0],
            [20.0, 14.0, 0.0],
        ],
    }
    qubo = TSPQuboGenerator.generate(problem)

    builder = QuboBuilder(variable_order=qubo.variable_order)
    for v, val in qubo.linear_terms.items():
        builder.add_linear(v, val)
    for pair, val in qubo.quadratic_terms.items():
        v1, v2 = pair.split(",")
        builder.add_quadratic(v1, v2, val)
    builder.add_offset(qubo.offset)

    # Forward
    fwd_state = {
        "x_X_0": 1, "x_X_1": 0, "x_X_2": 0,
        "x_Y_0": 0, "x_Y_1": 1, "x_Y_2": 0,
        "x_Z_0": 0, "x_Z_1": 0, "x_Z_2": 1,
    }
    assert abs(builder.evaluate_energy(fwd_state) - 33.0) < 1e-9

    # Reverse
    rev_state = {
        "x_X_0": 1, "x_X_1": 0, "x_X_2": 0,
        "x_Z_0": 0, "x_Z_1": 1, "x_Z_2": 0,
        "x_Y_0": 0, "x_Y_1": 0, "x_Y_2": 1,
    }
    assert abs(builder.evaluate_energy(rev_state) - 29.0) < 1e-9


def test_tsp_qubo_start_city_penalty():
    """When start_city is configured, tours not starting at start_city incur penalty S."""
    problem = {
        "cities": ["Paris", "London", "Berlin"],
        "distance_matrix": [
            [0.0, 10.0, 20.0],
            [10.0, 0.0, 15.0],
            [20.0, 15.0, 0.0],
        ],
        "start_city": "Paris",
    }
    penalty_s = 50.0
    qubo = TSPQuboGenerator.generate(problem, penalty_coefficients={"A": 30.0, "B": 30.0, "S": penalty_s})

    builder = QuboBuilder(variable_order=qubo.variable_order)
    for v, val in qubo.linear_terms.items():
        builder.add_linear(v, val)
    for pair, val in qubo.quadratic_terms.items():
        v1, v2 = pair.split(",")
        builder.add_quadratic(v1, v2, val)
    builder.add_offset(qubo.offset)

    # Valid tour starting at Paris: [Paris(0), London(1), Berlin(2)] -> Distance = 10 + 15 + 20 = 45.0
    valid_state = {
        "x_Paris_0": 1, "x_Paris_1": 0, "x_Paris_2": 0,
        "x_London_0": 0, "x_London_1": 1, "x_London_2": 0,
        "x_Berlin_0": 0, "x_Berlin_1": 0, "x_Berlin_2": 1,
    }
    assert abs(builder.evaluate_energy(valid_state) - 45.0) < 1e-9

    # Same tour cycle shifted: starts at London [London(0), Berlin(1), Paris(2)]
    # Incurs +penalty_s because Paris is at pos 2 not pos 0
    shifted_state = {
        "x_London_0": 1, "x_London_1": 0, "x_London_2": 0,
        "x_Berlin_0": 0, "x_Berlin_1": 1, "x_Berlin_2": 0,
        "x_Paris_0": 0, "x_Paris_1": 0, "x_Paris_2": 1,
    }
    shifted_energy = builder.evaluate_energy(shifted_state)
    assert abs(shifted_energy - (45.0 + penalty_s)) < 1e-9
