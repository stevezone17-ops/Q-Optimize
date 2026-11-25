"""Unit tests for the independent mathematical formulation verification module."""

import pytest
from backend.app.formulations.verification import FormulationVerifier
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.formulations.assignment_qubo import AssignmentQuboGenerator
from backend.app.formulations.tsp_qubo import TSPQuboGenerator


def test_verification_max_cut_complete():
    """Verify 4-node Max-Cut formulation exhaustively across all 16 states."""
    problem = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 1.5],
            ["B", "C", 2.0],
            ["C", "D", 2.5],
            ["D", "A", 3.0],
            ["A", "C", 1.0],
        ],
    }
    qubo = MaxCutQuboGenerator.generate(problem)
    res = FormulationVerifier.verify(
        problem_type="max_cut",
        instance_data=problem,
        qubo=qubo,
    )
    assert res.is_verified is True
    assert res.num_states_tested == 16
    assert res.max_energy_discrepancy < 1e-8
    assert len(res.discrepancies) == 0


def test_verification_unweighted_max_cut_4node_cycle():
    """
    Verify unweighted 4-Node Cycle (C4) Max-Cut benchmark exhaustively:
    - 4 vertices, 4 edges, 16 binary configurations
    - Maximum cut value of 4.0 (QUBO energy -4.0)
    - Optimal assignments 0101 and 1010 under cyclic vertex ordering
    - Exact QUBO and Ising energy equivalence
    """
    from backend.app.formulations.ising_converter import IsingConverter
    from backend.app.formulations.qubo_builder import QuboBuilder

    problem = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 1.0],
            ["B", "C", 1.0],
            ["C", "D", 1.0],
            ["D", "A", 1.0],
        ],
    }
    qubo = MaxCutQuboGenerator.generate(problem)
    ising = IsingConverter.qubo_to_ising(qubo)
    res = FormulationVerifier.verify(
        problem_type="max_cut",
        instance_data=problem,
        qubo=qubo,
        ising=ising,
    )
    assert res.is_verified is True
    assert res.num_states_tested == 16
    assert res.max_energy_discrepancy < 1e-8
    assert abs(res.min_qubo_energy - (-4.0)) < 1e-8

    builder = QuboBuilder(variable_order=qubo.variable_order)
    for var, val in qubo.linear_terms.items():
        builder.add_linear(var, val)
    for pair_key, val in qubo.quadratic_terms.items():
        v1, v2 = pair_key.split(",", 1)
        builder.add_quadratic(v1, v2, val)
    builder.add_offset(qubo.offset)

    optimal_bitstrings = []
    for bits in [(a, b, c, d) for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1)]:
        bit_vec = list(bits)
        e_qubo = builder.evaluate_energy(bit_vec)
        z_vec = IsingConverter.binary_to_spin(bit_vec)
        e_ising = IsingConverter.evaluate_energy(ising, z_vec)
        assert abs(e_qubo - e_ising) < 1e-8
        if abs(e_qubo - (-4.0)) < 1e-8:
            optimal_bitstrings.append("".join(str(x) for x in bits))

    assert set(optimal_bitstrings) == {"0101", "1010"}


def test_verification_assignment_complete():
    """Verify 2x2 Assignment formulation exhaustively across all 16 states."""
    problem = {
        "agents": ["A1", "A2"],
        "tasks": ["T1", "T2"],
        "cost_matrix": [
            [4.0, 7.0],
            [2.0, 5.0],
        ],
    }
    qubo = AssignmentQuboGenerator.generate(problem)
    res = FormulationVerifier.verify(
        problem_type="assignment",
        instance_data=problem,
        qubo=qubo,
    )
    assert res.is_verified is True
    assert res.num_states_tested == 16
    assert res.feasible_states_count == 2  # 2! = 2 feasible matchings
    assert res.max_energy_discrepancy < 1e-8


def test_verification_tsp_complete():
    """Verify 3-city TSP formulation exhaustively across all 2^9 = 512 states."""
    problem = {
        "cities": ["C1", "C2", "C3"],
        "distance_matrix": [
            [0.0, 10.0, 15.0],
            [10.0, 0.0, 20.0],
            [15.0, 20.0, 0.0],
        ],
    }
    qubo = TSPQuboGenerator.generate(problem)
    res = FormulationVerifier.verify(
        problem_type="tsp",
        instance_data=problem,
        qubo=qubo,
    )
    assert res.is_verified is True
    assert res.num_states_tested == 512
    assert res.feasible_states_count == 6  # 3! = 6 cyclic permutations
    assert res.max_energy_discrepancy < 1e-8


def test_verification_state_space_limit():
    """Attempts to verify state spaces exceeding limit must raise ValueError."""
    from backend.app.domain.formulations.models import QuboModel
    large_vars = [f"x_{i}" for i in range(15)]  # 2^15 = 32768 states
    qubo = QuboModel(
        variable_order=large_vars,
        linear_terms={},
        quadratic_terms={},
        offset=0.0,
    )
    with pytest.raises(ValueError, match="exceeds exhaustive verification limit"):
        FormulationVerifier.verify(
            problem_type="max_cut",
            instance_data={"nodes": large_vars, "edges": []},
            qubo=qubo,
            max_states=4096,
        )
