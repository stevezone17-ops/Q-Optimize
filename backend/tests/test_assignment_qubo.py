"""Unit and mathematical verification tests for Linear Assignment QUBO generation."""

import itertools
import pytest
from backend.app.formulations.assignment_qubo import AssignmentQuboGenerator
from backend.app.evaluation.assignment_evaluator import AssignmentEvaluator


def test_assignment_qubo_2x2_hand_calculated():
    """
    2x2 Assignment problem:
      Agents: [A, B], Tasks: [T1, T2]
      Costs:
        A: [3.0, 8.0]
        B: [6.0, 2.0]
      Penalties: A = 10.0, B = 10.0
      Offset: n * (A + B) = 2 * 20.0 = 40.0
    Hand-calculated linear:
      x_A_T1: 3.0 - 20.0 = -17.0
      x_A_T2: 8.0 - 20.0 = -12.0
      x_B_T1: 6.0 - 20.0 = -14.0
      x_B_T2: 2.0 - 20.0 = -18.0
    Hand-calculated quadratic:
      x_A_T1, x_A_T2 (same agent A): 2 * 10 = 20.0
      x_B_T1, x_B_T2 (same agent B): 2 * 10 = 20.0
      x_A_T1, x_B_T1 (same task T1): 2 * 10 = 20.0
      x_A_T2, x_B_T2 (same task T2): 2 * 10 = 20.0
    """
    problem = {
        "agents": ["A", "B"],
        "tasks": ["T1", "T2"],
        "cost_matrix": [
            [3.0, 8.0],
            [6.0, 2.0],
        ],
    }
    qubo = AssignmentQuboGenerator.generate(problem, penalty_coefficients={"A": 10.0, "B": 10.0})

    assert qubo.offset == 40.0
    assert qubo.linear_terms["x_A_T1"] == -17.0
    assert qubo.linear_terms["x_A_T2"] == -12.0
    assert qubo.linear_terms["x_B_T1"] == -14.0
    assert qubo.linear_terms["x_B_T2"] == -18.0

    assert qubo.quadratic_terms["x_A_T1,x_A_T2"] == 20.0
    assert qubo.quadratic_terms["x_B_T1,x_B_T2"] == 20.0
    assert qubo.quadratic_terms["x_A_T1,x_B_T1"] == 20.0
    assert qubo.quadratic_terms["x_A_T2,x_B_T2"] == 20.0

    # Test Feasible 1: A->T1, B->T2 (cost = 3 + 2 = 5.0)
    # Binary vector: [1, 0, 0, 1]
    from backend.app.formulations.qubo_builder import QuboBuilder
    builder = QuboBuilder(variable_order=qubo.variable_order)
    for v, val in qubo.linear_terms.items():
        builder.add_linear(v, val)
    for pair, val in qubo.quadratic_terms.items():
        v1, v2 = pair.split(",")
        builder.add_quadratic(v1, v2, val)
    builder.add_offset(qubo.offset)

    assert builder.evaluate_energy([1, 0, 0, 1]) == 5.0

    # Test Feasible 2: A->T2, B->T1 (cost = 8 + 6 = 14.0)
    # Binary vector: [0, 1, 1, 0]
    assert builder.evaluate_energy([0, 1, 1, 0]) == 14.0

    # Test Infeasible 1: All zeros -> energy = offset = 40.0
    assert builder.evaluate_energy([0, 0, 0, 0]) == 40.0

    # Test Infeasible 2: Duplicate on T1 (both A and B on T1)
    # Vector [1, 0, 1, 0] -> -17 - 14 + 20 + 40 = 29.0 > 14.0
    assert builder.evaluate_energy([1, 0, 1, 0]) == 29.0


def test_assignment_qubo_3x3_feasible_preservation():
    """
    3x3 Assignment:
    Verify that all 3! = 6 feasible permutations match their Phase 2 objective cost exactly.
    """
    problem = {
        "agents": ["A1", "A2", "A3"],
        "tasks": ["T1", "T2", "T3"],
        "cost_matrix": [
            [9.0, 2.0, 7.0],
            [6.0, 4.0, 3.0],
            [5.0, 8.0, 1.0],
        ],
    }
    qubo = AssignmentQuboGenerator.generate(problem)

    from backend.app.formulations.qubo_builder import QuboBuilder
    builder = QuboBuilder(variable_order=qubo.variable_order)
    for v, val in qubo.linear_terms.items():
        builder.add_linear(v, val)
    for pair, val in qubo.quadratic_terms.items():
        v1, v2 = pair.split(",")
        builder.add_quadratic(v1, v2, val)
    builder.add_offset(qubo.offset)

    evaluator = AssignmentEvaluator()

    # All 6 permutations of tasks [0, 1, 2]
    import itertools
    for perm in itertools.permutations([0, 1, 2]):
        cand_dict = {
            f"A{i+1}": f"T{perm[i]+1}" for i in range(3)
        }
        original_cost = evaluator.evaluate_objective(problem, cand_dict)

        # Build binary vector for qubo
        bit_vec = [0] * 9
        for i in range(3):
            task_idx = perm[i]
            bit_idx = i * 3 + task_idx
            bit_vec[bit_idx] = 1

        qubo_energy = builder.evaluate_energy(bit_vec)
        assert abs(qubo_energy - original_cost) < 1e-9


def test_assignment_qubo_rejects_rectangular_instances():
    """Rectangular assignment instances must be rejected with clear error."""
    problem = {
        "agents": ["A1", "A2"],
        "tasks": ["T1", "T2", "T3"],
        "cost_matrix": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
    }
    with pytest.raises(ValueError, match="square dimensions"):
        AssignmentQuboGenerator.generate(problem)
