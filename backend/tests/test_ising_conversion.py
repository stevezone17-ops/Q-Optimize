"""Unit and mathematical equivalence tests for QUBO-to-Ising conversion."""

import itertools
import pytest
from backend.app.domain.formulations.models import QuboModel
from backend.app.formulations.ising_converter import IsingConverter
from backend.app.formulations.qubo_builder import QuboBuilder


def test_ising_single_variable_hand_calculated():
    """
    Single variable QUBO:
      E(x) = a * x + c  with x in {0, 1}
    With x = (1 - Z) / 2:
      E(Z) = a * (1 - Z)/2 + c = (c + a/2) - (a/2) * Z
    Ising parameters:
      C = c + a / 2
      h = - a / 2
    """
    qubo = QuboModel(
        variable_order=["x0"],
        linear_terms={"x0": 6.0},
        quadratic_terms={},
        offset=2.0,
    )
    ising = IsingConverter.qubo_to_ising(qubo)

    assert ising.offset == 2.0 + 3.0 == 5.0
    assert ising.local_fields["Z_x0"] == - 3.0
    assert len(ising.couplings) == 0

    # Test state x = 0 -> Z = +1: E(0) = 2.0; H(+1) = 5.0 - 3.0(1) = 2.0
    assert IsingConverter.evaluate_energy(ising, [1]) == 2.0

    # Test state x = 1 -> Z = -1: E(1) = 2 + 6 = 8.0; H(-1) = 5.0 - 3.0(-1) = 8.0
    assert IsingConverter.evaluate_energy(ising, [-1]) == 8.0


def test_ising_two_variable_hand_calculated():
    """
    Two-variable QUBO:
      E(x) = a1*x1 + a2*x2 + b12*x1*x2 + c
    For a1 = 4.0, a2 = -2.0, b12 = 8.0, c = 1.0:
      C = c + (a1 + a2)/2 + b12/4
        = 1.0 + (4.0 - 2.0)/2 + 8.0/4 = 1.0 + 1.0 + 2.0 = 4.0
      h1 = - a1/2 - b12/4 = - 2.0 - 2.0 = - 4.0
      h2 = - a2/2 - b12/4 = - (-1.0) - 2.0 = - 1.0
      J12 = b12/4 = 8.0/4 = 2.0
    """
    qubo = QuboModel(
        variable_order=["x1", "x2"],
        linear_terms={"x1": 4.0, "x2": -2.0},
        quadratic_terms={"x1,x2": 8.0},
        offset=1.0,
    )
    ising = IsingConverter.qubo_to_ising(qubo)

    assert ising.offset == 4.0
    assert ising.local_fields["Z_x1"] == - 4.0
    assert ising.local_fields["Z_x2"] == - 1.0
    assert ising.couplings["Z_x1,Z_x2"] == 2.0

    # Test all 4 states
    builder = QuboBuilder(variable_order=["x1", "x2"])
    builder.add_linear("x1", 4.0)
    builder.add_linear("x2", -2.0)
    builder.add_quadratic("x1", "x2", 8.0)
    builder.add_offset(1.0)

    for b1 in [0, 1]:
        for b2 in [0, 1]:
            x_vec = [b1, b2]
            z_vec = IsingConverter.binary_to_spin(x_vec)

            e_qubo = builder.evaluate_energy(x_vec)
            h_ising = IsingConverter.evaluate_energy(ising, z_vec)

            assert abs(e_qubo - h_ising) < 1e-9


def test_ising_conversion_multi_variable_exhaustive():
    """Exhaustive energy equivalence across all 2^5 = 32 states for 5 variables."""
    builder = QuboBuilder(variable_order=["x0", "x1", "x2", "x3", "x4"])
    builder.add_linear("x0", 3.0)
    builder.add_linear("x1", -1.5)
    builder.add_linear("x3", 2.2)
    builder.add_quadratic("x0", "x1", 4.0)
    builder.add_quadratic("x1", "x2", -5.0)
    builder.add_quadratic("x2", "x3", 1.8)
    builder.add_quadratic("x0", "x4", 3.4)
    builder.add_offset(7.1)

    qubo = builder.build_model()
    ising = IsingConverter.qubo_to_ising(qubo)

    for bits in itertools.product([0, 1], repeat=5):
        x_vec = list(bits)
        z_vec = IsingConverter.binary_to_spin(x_vec)

        e_qubo = builder.evaluate_energy(x_vec)
        h_ising = IsingConverter.evaluate_energy(ising, z_vec)

        assert abs(e_qubo - h_ising) < 1e-8


def test_ising_spin_binary_conversions():
    """Verify bidirectional mappings: x <-> Z."""
    x = [0, 1, 1, 0]
    z = IsingConverter.binary_to_spin(x)
    assert z == [1, -1, -1, 1]

    x_back = IsingConverter.spin_to_binary(z)
    assert x_back == x
