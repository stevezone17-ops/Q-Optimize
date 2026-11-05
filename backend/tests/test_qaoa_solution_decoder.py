"""Unit tests for Stage 5.6: QAOA Bitstring Decoding and Independent Solution Evaluation."""

import pytest

from backend.app.domain.problems.models import ProblemType
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.formulations.assignment_qubo import AssignmentQuboGenerator
from backend.app.formulations.tsp_qubo import TSPQuboGenerator
from backend.app.solvers.quantum.solution_decoder import QAOASolutionDecoder
from backend.app.solvers.quantum.models import QuantumSamplingResult, CircuitMetadata


def test_bitstring_little_endian_qubit_ordering_correctness():
    """
    CRITICAL BIT-ORDER TEST:
    Verify that Qiskit's little-endian bitstring convention is mapped correctly to variables.
    In Qiskit, bitstring[0] is qubit n-1 and bitstring[n-1] is qubit 0.
    """
    problem_data = {
        "nodes": ["A", "B", "C"],
        "edges": [["A", "B", 1.0], ["B", "C", 2.0], ["A", "C", 3.0]]
    }
    qubo = MaxCutQuboGenerator.generate(problem_data)
    decoder = QAOASolutionDecoder(ProblemType.MAX_CUT, problem_data, qubo)

    # Qubit 0 = A, Qubit 1 = B, Qubit 2 = C
    # Bitstring "100" in Qiskit means:
    #   Qubit 2 (C) = 1
    #   Qubit 1 (B) = 0
    #   Qubit 0 (A) = 0
    assign_100 = decoder.bitstring_to_variable_assignment("100")
    assert assign_100["A"] == 0
    assert assign_100["B"] == 0
    assert assign_100["C"] == 1

    # Bitstring "001" in Qiskit means:
    #   Qubit 2 (C) = 0
    #   Qubit 1 (B) = 0
    #   Qubit 0 (A) = 1
    assign_001 = decoder.bitstring_to_variable_assignment("001")
    assert assign_001["A"] == 1
    assert assign_001["B"] == 0
    assert assign_001["C"] == 0


def test_max_cut_decoding_and_energy_consistency():
    """Verify Max-Cut decoding, independent evaluation, and QUBO/Ising energy equivalence."""
    problem_data = {
        "nodes": ["A", "B"],
        "edges": [["A", "B", 5.0]]
    }
    qubo = MaxCutQuboGenerator.generate(problem_data)
    decoder = QAOASolutionDecoder(ProblemType.MAX_CUT, problem_data, qubo)

    # Bitstring "01" (q1=B=0, q0=A=1) -> Cut edge (A, B) with weight 5.0
    sample = decoder.evaluate_sample(bitstring="01", frequency_count=500, total_shots=1000)
    assert sample.is_feasible is True
    assert sample.candidate_solution == {"A": 1, "B": 0}
    assert sample.objective_value == 5.0
    # For Max-Cut, E_QUBO(x) == - Cut(x)
    assert sample.qubo_energy == -5.0
    assert abs(sample.qubo_energy - sample.ising_energy) < 1e-6


def test_assignment_decoding_and_feasibility():
    """Verify Assignment problem decoding distinguishes feasible and infeasible samples."""
    assign_data = {
        "agents": ["A", "B"],
        "tasks": ["T1", "T2"],
        "cost_matrix": [
            [2.0, 5.0],
            [1.0, 4.0]
        ]
    }
    qubo = AssignmentQuboGenerator.generate(assign_data, penalty_coefficients={"A": 10.0, "B": 10.0})
    decoder = QAOASolutionDecoder(ProblemType.ASSIGNMENT, assign_data, qubo)

    # Variables in order: x_A_T1, x_A_T2, x_B_T1, x_B_T2 (indices 0, 1, 2, 3)
    # Feasible solution: A->T1 (idx 0), B->T2 (idx 3)
    # Binary vector: x0=1, x1=0, x2=0, x3=1
    # In Qiskit little-endian: bitstring is x3 x2 x1 x0 = "1001"
    sample_feas = decoder.evaluate_sample("1001", frequency_count=600, total_shots=1000)
    assert sample_feas.is_feasible is True
    assert ("A", "T1") in sample_feas.candidate_solution
    assert ("B", "T2") in sample_feas.candidate_solution
    # Cost: A->T1 (2.0) + B->T2 (4.0) = 6.0
    assert sample_feas.objective_value == 6.0
    assert len(sample_feas.constraint_violations) == 0

    # Infeasible solution: both assigned to T1 (x_A_T1=1, x_B_T1=1, x_A_T2=0, x_B_T2=0)
    # Binary: x0=1, x1=0, x2=1, x3=0 -> Qiskit bitstring "0101"
    sample_infeas = decoder.evaluate_sample("0101", frequency_count=400, total_shots=1000)
    assert sample_infeas.is_feasible is False
    assert len(sample_infeas.constraint_violations) > 0


def test_tsp_decoding_and_feasibility():
    """Verify TSP tour decoding correctly builds closed cycles and checks constraints."""
    tsp_data = {
        "cities": ["C0", "C1", "C2"],
        "distance_matrix": [
            [0.0, 10.0, 20.0],
            [10.0, 0.0, 15.0],
            [20.0, 15.0, 0.0]
        ],
        "start_city": "C0"
    }
    qubo = TSPQuboGenerator.generate(tsp_data, penalty_coefficients={"A": 50.0, "B": 50.0, "C": 50.0})
    decoder = QAOASolutionDecoder(ProblemType.TSP, tsp_data, qubo)

    # Variables: 9 vars (x_C0_0, x_C0_1, x_C0_2, x_C1_0, x_C1_1, x_C1_2, x_C2_0, x_C2_1, x_C2_2)
    # Valid tour: C0 at step 0 (x_C0_0=1), C1 at step 1 (x_C1_1=1), C2 at step 2 (x_C2_2=1)
    # Indices: 0, 4, 8 are 1. All others 0.
    n = 9
    x_vec = [0] * n
    x_vec[0] = 1
    x_vec[4] = 1
    x_vec[8] = 1
    # Qiskit little-endian bitstring:
    bitstring = "".join(str(x_vec[n - 1 - k]) for k in range(n))

    sample = decoder.evaluate_sample(bitstring, frequency_count=700, total_shots=1000)
    assert sample.is_feasible is True
    # Tour should be ["C0", "C1", "C2", "C0"]
    assert sample.candidate_solution == ["C0", "C1", "C2", "C0"]
    # Distance: C0->C1 (10) + C1->C2 (15) + C2->C0 (20) = 45.0
    assert sample.objective_value == 45.0


def test_best_solution_selected_by_objective_not_frequency():
    """
    CRITICAL SCIENTIFIC TEST:
    Verify that best feasible candidate is chosen by true optimization objective,
    NOT by measurement frequency alone.
    """
    problem_data = {
        "nodes": ["A", "B", "C"],
        "edges": [["A", "B", 10.0], ["B", "C", 1.0], ["A", "C", 1.0]]
    }
    qubo = MaxCutQuboGenerator.generate(problem_data)
    decoder = QAOASolutionDecoder(ProblemType.MAX_CUT, problem_data, qubo)

    # Node indices: A=0, B=1, C=2
    # Candidate 1: Partition A vs {B, C} -> Cut = 10 + 1 = 11.0 (Optimal cut!)
    # x_A=1, x_B=0, x_C=0 -> Qiskit string "001"
    # Suppose "001" was measured with low count: 150 shots
    # Candidate 2: Partition {A, B} vs C -> Cut = 1 + 1 = 2.0 (Suboptimal cut!)
    # x_A=1, x_B=1, x_C=0 -> Qiskit string "011"
    # Suppose "011" was measured with high count: 850 shots
    sampling_res = QuantumSamplingResult(
        counts={"011": 850, "001": 150},
        probabilities={"011": 0.85, "001": 0.15},
        shots=1000,
        unique_bitstrings=2,
        most_frequent_bitstring="011",
        most_frequent_count=850,
        most_frequent_probability=0.85,
        circuit_metadata=CircuitMetadata(
            num_qubits=3, num_clbits=3, p_depth=1, total_gates=5,
            two_qubit_gates=3, circuit_depth=4, parameter_count=2, has_measurements=True
        ),
        simulation_mode="ideal_shots",
        execution_time_seconds=0.05
    )

    summary = decoder.decode_and_evaluate_sampling_result(sampling_res)

    assert summary.most_frequent_solution.bitstring == "011"
    assert summary.most_frequent_solution.objective_value == 2.0

    # Best feasible solution must be "001" with objective 11.0!
    assert summary.best_feasible_solution is not None
    assert summary.best_feasible_solution.bitstring == "001"
    assert summary.best_feasible_solution.objective_value == 11.0
