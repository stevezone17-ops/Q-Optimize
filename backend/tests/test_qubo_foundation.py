"""Unit tests for the canonical QUBO mathematical foundation and QuboBuilder."""

import pytest
from backend.app.formulations.qubo_builder import QuboBuilder


def test_qubo_builder_variable_indexing():
    """Verify variable ordering and index lookups."""
    builder = QuboBuilder(variable_order=["v0", "v1", "v2"])
    assert builder.num_variables == 3
    assert builder.get_variable_index("v0") == 0
    assert builder.get_variable_index("v1") == 1
    assert builder.get_variable_index("v2") == 2

    with pytest.raises(KeyError):
        builder.get_variable_index("unknown")


def test_qubo_builder_rejects_empty_or_duplicate_variables():
    """Empty list or duplicate variable names must be rejected."""
    with pytest.raises(ValueError):
        QuboBuilder(variable_order=[])

    with pytest.raises(ValueError):
        QuboBuilder(variable_order=["a", "b", "a"])


def test_qubo_builder_upper_triangular_routing():
    """
    Adding quadratic term with reversed order (v2, v0) must route
    to the canonical upper-triangular pair (v0, v2).
    """
    builder = QuboBuilder(variable_order=["v0", "v1", "v2"])
    builder.add_quadratic("v2", "v0", 5.0)

    # Calling it again adds to the existing interaction without duplicate keys
    builder.add_quadratic("v0", "v2", 3.0)

    lin, quad = builder.to_dict_coefficients()
    assert len(lin) == 0
    assert "v0,v2" in quad
    assert quad["v0,v2"] == 8.0
    assert "v2,v0" not in quad


def test_qubo_builder_linear_and_diagonal():
    """Adding quadratic with same variable routes to linear diagonal term (x^2 = x)."""
    builder = QuboBuilder(variable_order=["x0", "x1"])
    builder.add_linear("x0", 2.0)
    builder.add_quadratic("x0", "x0", 3.0)  # x0^2 == x0

    lin, _ = builder.to_dict_coefficients()
    assert lin["x0"] == 5.0


def test_qubo_builder_penalty_square_expansion():
    """
    Test penalty term expansion: P = multiplier * (x0 + x1 - 1)^2
    Expansion: (x0 + x1 - 1)^2 = - x0 - x1 + 2 x0 x1 + 1
    For multiplier = 10.0:
      linear x0: -10.0
      linear x1: -10.0
      quadratic (x0, x1): +20.0
      offset: +10.0
    """
    builder = QuboBuilder(variable_order=["x0", "x1"])
    builder.add_penalty_square(
        linear_terms={"x0": 1.0, "x1": 1.0},
        constant=-1.0,
        multiplier=10.0,
    )

    lin, quad = builder.to_dict_coefficients()
    assert lin["x0"] == -10.0
    assert lin["x1"] == -10.0
    assert quad["x0,x1"] == 20.0
    assert builder._offset == 10.0

    # Feasible: exactly one is 1
    assert builder.evaluate_energy([1, 0]) == 0.0
    assert builder.evaluate_energy([0, 1]) == 0.0

    # Infeasible: both 0 -> (0 - 1)^2 * 10 = 10.0
    assert builder.evaluate_energy([0, 0]) == 10.0

    # Infeasible: both 1 -> (2 - 1)^2 * 10 = 10.0
    assert builder.evaluate_energy([1, 1]) == 10.0


def test_qubo_builder_dense_and_symmetric_equivalence():
    """
    Verify that energy evaluated with the upper-triangular matrix
    equals energy evaluated with the symmetric matrix representation:
        x^T Q_upper x == x^T Q_sym x
    """
    builder = QuboBuilder(variable_order=["x0", "x1", "x2"])
    builder.add_linear("x0", 1.5)
    builder.add_linear("x1", -2.0)
    builder.add_quadratic("x0", "x1", 4.0)
    builder.add_quadratic("x1", "x2", -6.0)
    builder.add_offset(3.5)

    q_upper = builder.to_dense_upper_triangular_matrix()
    q_sym = builder.to_dense_symmetric_matrix()

    # Diagonal should match
    assert q_upper[0][0] == q_sym[0][0] == 1.5
    assert q_upper[1][1] == q_sym[1][1] == -2.0

    # Off-diagonal: upper has 4.0, sym has 2.0 and 2.0
    assert q_upper[0][1] == 4.0
    assert q_upper[1][0] == 0.0
    assert q_sym[0][1] == 2.0
    assert q_sym[1][0] == 2.0

    # Test on arbitrary binary vector x = [1, 1, 0]
    # Energy = 1.5(1) - 2.0(1) + 4.0(1*1) + 3.5 = 7.0
    energy_builder = builder.evaluate_energy([1, 1, 0])
    assert energy_builder == 7.0

    # Calculate x^T Q_sym x + offset
    x = [1, 1, 0]
    sym_energy = builder._offset
    for i in range(3):
        for j in range(3):
            sym_energy += x[i] * q_sym[i][j] * x[j]

    assert abs(energy_builder - sym_energy) < 1e-9


def test_qubo_builder_rejects_non_finite_coefficients():
    """Rejects NaN and infinity values."""
    builder = QuboBuilder(variable_order=["x0", "x1"])
    with pytest.raises(ValueError):
        builder.add_linear("x0", float("nan"))
    with pytest.raises(ValueError):
        builder.add_quadratic("x0", "x1", float("inf"))
    with pytest.raises(ValueError):
        builder.add_offset(float("-inf"))
