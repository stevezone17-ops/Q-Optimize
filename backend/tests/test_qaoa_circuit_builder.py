"""Unit tests for Stage 5.3: Parameterized QAOA Circuit Builder."""

import pytest
import numpy as np
from qiskit import QuantumCircuit

from backend.app.formulations.qubo_builder import QuboBuilder
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.formulations.assignment_qubo import AssignmentQuboGenerator
from backend.app.formulations.tsp_qubo import TSPQuboGenerator
from backend.app.solvers.quantum.hamiltonians import QAOACostHamiltonian, QAOAMixerHamiltonian
from backend.app.solvers.quantum.circuit_builder import QAOACircuitBuilder
from backend.app.solvers.quantum.exceptions import CircuitConstructionError, QubitLimitExceededError
from backend.app.solvers.quantum.config import QuantumResourceLimits


def test_qaoa_circuit_builder_basic_p1():
    """Verify parameterized circuit construction for p=1 depth."""
    builder = QuboBuilder(["x0", "x1"])
    builder.add_linear("x0", 1.0)
    builder.add_quadratic("x0", "x1", 2.0)
    qubo_model = builder.build_model()
    cost_ham = QAOACostHamiltonian.from_qubo(qubo_model)

    circuit_builder = QAOACircuitBuilder(cost_ham, p_depth=1)
    qc = circuit_builder.build_circuit(include_measurements=False)

    assert qc.num_qubits == 2
    assert qc.num_clbits == 0
    assert len(qc.parameters) == 2  # gamma[0], beta[0]
    
    # Check Hadamard initialization
    h_gates = [d for d in qc.data if d.operation.name == "h"]
    assert len(h_gates) == 2


def test_qaoa_circuit_builder_higher_depth_p3():
    """Verify parameterized circuit scaling for p=3 depth."""
    builder = QuboBuilder(["x0", "x1", "x2"])
    builder.add_quadratic("x0", "x1", 1.0)
    builder.add_quadratic("x1", "x2", 1.0)
    qubo_model = builder.build_model()
    cost_ham = QAOACostHamiltonian.from_qubo(qubo_model)

    circuit_builder = QAOACircuitBuilder(cost_ham, p_depth=3)
    qc = circuit_builder.build_circuit(include_measurements=True)

    assert qc.num_qubits == 3
    assert qc.num_clbits == 3
    assert len(qc.parameters) == 6  # 3 gammas + 3 betas

    meta = circuit_builder.extract_circuit_metadata(qc)
    assert meta.num_qubits == 3
    assert meta.num_clbits == 3
    assert meta.p_depth == 3
    assert meta.has_measurements is True
    assert meta.two_qubit_gates == 3 * 2  # 2 couplings per layer * 3 layers = 6


def test_parameter_binding():
    """Verify binding numerical angles into circuit assigns all parameters."""
    builder = QuboBuilder(["x0", "x1"])
    builder.add_quadratic("x0", "x1", 2.0)
    cost_ham = QAOACostHamiltonian.from_qubo(builder.build_model())

    circuit_builder = QAOACircuitBuilder(cost_ham, p_depth=2)
    param_qc = circuit_builder.build_circuit()
    assert len(param_qc.parameters) == 4

    # Bind with valid angles
    bound_qc = circuit_builder.bind_parameters(
        param_qc,
        gamma_vals=[0.25, 0.5],
        beta_vals=[0.1, 0.2]
    )
    assert len(bound_qc.parameters) == 0

    # Invalid angle lengths raise ValueError
    with pytest.raises(ValueError, match="Expected 2 gamma values"):
        circuit_builder.bind_parameters(param_qc, [0.1], [0.1, 0.2])
    with pytest.raises(ValueError, match="Expected 2 beta values"):
        circuit_builder.bind_parameters(param_qc, [0.1, 0.2], [0.1])


def test_circuit_builder_across_problem_families():
    """Verify circuit generation across Max-Cut, Assignment, and TSP."""
    # 1. Max-Cut (4 nodes, 4 qubits)
    maxcut_data = {
        "nodes": ["0", "1", "2", "3"],
        "edges": [["0", "1", 1.0], ["1", "2", 1.0], ["2", "3", 1.0], ["3", "0", 1.0]]
    }
    maxcut_ham = QAOACostHamiltonian.from_qubo(MaxCutQuboGenerator.generate(maxcut_data))
    maxcut_cb = QAOACircuitBuilder(maxcut_ham, p_depth=2)
    qc_maxcut = maxcut_cb.build_circuit()
    assert qc_maxcut.num_qubits == 4
    assert len(qc_maxcut.parameters) == 4

    # 2. Assignment (2x2, 4 qubits)
    assign_data = {
        "agents": ["A", "B"],
        "tasks": ["T1", "T2"],
        "cost_matrix": [[1.0, 3.0], [2.0, 4.0]]
    }
    assign_ham = QAOACostHamiltonian.from_qubo(
        AssignmentQuboGenerator.generate(assign_data, penalty_coefficients={"A": 10.0, "B": 10.0})
    )
    assign_cb = QAOACircuitBuilder(assign_ham, p_depth=1)
    qc_assign = assign_cb.build_circuit()
    assert qc_assign.num_qubits == 4

    # 3. TSP (3 cities, 9 qubits)
    tsp_data = {
        "cities": ["A", "B", "C"],
        "distance_matrix": [[0, 1, 2], [1, 0, 3], [2, 3, 0]],
        "start_city": "A"
    }
    tsp_ham = QAOACostHamiltonian.from_qubo(
        TSPQuboGenerator.generate(tsp_data, penalty_coefficients={"A": 20.0, "B": 20.0, "C": 20.0})
    )
    tsp_cb = QAOACircuitBuilder(tsp_ham, p_depth=1)
    qc_tsp = tsp_cb.build_circuit()
    assert qc_tsp.num_qubits == 9


def test_circuit_builder_resource_limits():
    """Verify that resource limit boundaries protect against runaway quantum circuits."""
    limits = QuantumResourceLimits(max_qubits=4, max_p_depth=3)
    
    # Exceeding qubits
    builder_large = QuboBuilder(["x0", "x1", "x2", "x3", "x4"])
    cost_ham_large = QAOACostHamiltonian.from_qubo(builder_large.build_model())
    with pytest.raises(QubitLimitExceededError, match="exceeding the platform limit"):
        QAOACircuitBuilder(cost_ham_large, limits=limits)

    # Exceeding p depth
    builder_small = QuboBuilder(["x0", "x1"])
    cost_ham_small = QAOACostHamiltonian.from_qubo(builder_small.build_model())
    with pytest.raises(CircuitConstructionError, match="QAOA depth p must be between"):
        QAOACircuitBuilder(cost_ham_small, p_depth=5, limits=limits)


def test_ascii_diagram_rendering():
    """Verify ASCII diagram text generation."""
    builder = QuboBuilder(["x0", "x1"])
    cost_ham = QAOACostHamiltonian.from_qubo(builder.build_model())
    cb = QAOACircuitBuilder(cost_ham, p_depth=1)
    qc = cb.build_circuit()
    ascii_art = cb.render_ascii_diagram(qc)
    assert "q_0" in ascii_art
    assert "q_1" in ascii_art
    assert "H" in ascii_art
