"""Unit tests for Stage 5.2: Cost Hamiltonian and Mixer Hamiltonian Construction."""

import pytest
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector, SparsePauliOp

from backend.app.domain.problems.models import ProblemType
from backend.app.domain.formulations.models import QuboModel
from backend.app.formulations.qubo_builder import QuboBuilder
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.formulations.assignment_qubo import AssignmentQuboGenerator
from backend.app.formulations.tsp_qubo import TSPQuboGenerator
from backend.app.formulations.ising_converter import IsingConverter
from backend.app.solvers.quantum.hamiltonians import QAOACostHamiltonian, QAOAMixerHamiltonian
from backend.app.solvers.quantum.exceptions import CircuitConstructionError


def test_cost_hamiltonian_construction_from_ising():
    """Verify QAOACostHamiltonian correctly parses linear fields, couplings, and offset."""
    # Build a small manual QUBO: 2 variables x0, x1
    # E(x) = 2.0*x0 - 3.0*x1 + 4.0*x0*x1 + 1.5
    builder = QuboBuilder(variable_order=["x0", "x1"])
    builder.add_linear("x0", 2.0)
    builder.add_linear("x1", -3.0)
    builder.add_quadratic("x0", "x1", 4.0)
    builder.add_offset(1.5)
    qubo_model = builder.build_model()

    cost_ham = QAOACostHamiltonian.from_qubo(qubo_model)
    assert cost_ham.num_qubits == 2
    assert cost_ham.qubit_to_spin[0] == "Z_x0"
    assert cost_ham.qubit_to_spin[1] == "Z_x1"
    assert len(cost_ham.coupling_terms) == 1
    # J_01 should be 4.0 / 4 = 1.0
    assert cost_ham.coupling_terms[0] == (0, 1, 1.0)
    assert abs(cost_ham.offset) > 0.0


def test_cost_unitary_gate_application():
    """Verify apply_cost_unitary appends correct Rz and Rzz gates with 2*gamma factor."""
    builder = QuboBuilder(variable_order=["x0", "x1"])
    builder.add_linear("x0", 1.0)
    builder.add_quadratic("x0", "x1", 2.0)
    qubo_model = builder.build_model()

    cost_ham = QAOACostHamiltonian.from_qubo(qubo_model)
    
    # 1. With numerical gamma = 0.5
    qc = QuantumCircuit(2)
    cost_ham.apply_cost_unitary(qc, gamma=0.5)
    # Check gate types
    ops = [instruction.operation.name for instruction in qc.data]
    assert "rz" in ops
    assert "rzz" in ops

    # 2. With symbolic Parameter
    gamma = Parameter("gamma")
    qc_sym = QuantumCircuit(2)
    cost_ham.apply_cost_unitary(qc_sym, gamma=gamma)
    assert len(qc_sym.parameters) == 1
    assert gamma in qc_sym.parameters


def test_mixer_hamiltonian_and_gates():
    """Verify QAOAMixerHamiltonian creates Rx(2*beta) gates across all qubits."""
    mixer = QAOAMixerHamiltonian(num_qubits=3)
    assert mixer.num_qubits == 3

    beta = Parameter("beta")
    qc = QuantumCircuit(3)
    mixer.apply_mixer_unitary(qc, beta=beta)
    
    assert len(qc.data) == 3
    for instruction in qc.data:
        assert instruction.operation.name == "rx"

    # Check SparsePauliOp
    pauli_op = mixer.to_sparse_pauli_op()
    assert isinstance(pauli_op, SparsePauliOp)
    assert pauli_op.num_qubits == 3


def test_circuit_qubit_dimension_mismatch_raises():
    """Verify attempting to apply Hamiltonians to a smaller circuit raises CircuitConstructionError."""
    builder = QuboBuilder(variable_order=["x0", "x1", "x2"])
    cost_ham = QAOACostHamiltonian.from_qubo(builder.build_model())
    qc_small = QuantumCircuit(2)
    with pytest.raises(CircuitConstructionError, match="requires 3"):
        cost_ham.apply_cost_unitary(qc_small, gamma=0.1)

    mixer = QAOAMixerHamiltonian(num_qubits=3)
    with pytest.raises(CircuitConstructionError, match="requires 3"):
        mixer.apply_mixer_unitary(qc_small, beta=0.1)


def test_exact_energy_equivalence_across_all_basis_states():
    """
    Exhaustively verify across all 2^n basis states that:
      E_QUBO(x) == H_Ising(Z) == CostHamiltonian.evaluate_binary_energy(x) == Statevector expectation.
    """
    # 3-node triangle Max-Cut graph
    problem_data = {
        "nodes": ["0", "1", "2"],
        "edges": [["0", "1", 1.0], ["1", "2", 2.0], ["0", "2", 3.0]]
    }
    qubo_model = MaxCutQuboGenerator.generate(problem_data)
    cost_ham = QAOACostHamiltonian.from_qubo(qubo_model)
    ising_model = cost_ham.ising
    sparse_op = cost_ham.to_sparse_pauli_op()

    n = 3
    # Build evaluation builder for QUBO energy
    eval_builder = QuboBuilder(qubo_model.variable_order)
    for v, val in qubo_model.linear_terms.items():
        eval_builder.add_linear(v, val)
    for pair, val in qubo_model.quadratic_terms.items():
        v1, v2 = pair.split(",")
        eval_builder.add_quadratic(v1, v2, val)
    eval_builder.add_offset(qubo_model.offset)

    for i in range(2**n):
        # x_vec in binary (e.g. [0, 1, 1])
        x_vec = [(i >> (n - 1 - k)) & 1 for k in range(n)]
        
        # 1. QUBO energy
        qubo_energy = eval_builder.evaluate_energy(x_vec)

        # 2. Ising energy from IsingConverter
        spins = IsingConverter.binary_to_spin(x_vec)
        ising_energy = IsingConverter.evaluate_energy(ising_model, spins)

        # 3. Cost Hamiltonian binary energy
        cost_ham_energy = cost_ham.evaluate_binary_energy(x_vec)

        # 4. Bitstring evaluation (little-endian matching Qiskit)
        bitstring = "".join(str(x_vec[n - 1 - k]) for k in range(n))
        bitstring_energy = cost_ham.evaluate_bitstring_energy(bitstring, little_endian=True)

        # 5. Statevector expectation
        qc = QuantumCircuit(n)
        for q, bit in enumerate(x_vec):
            if bit == 1:
                qc.x(q)
        sv = Statevector.from_instruction(qc)
        quantum_expected_energy = float(sv.expectation_value(sparse_op).real)

        # Assert all representations are mathematically identical to 1e-9 tolerance
        assert abs(qubo_energy - ising_energy) < 1e-9
        assert abs(ising_energy - cost_ham_energy) < 1e-9
        assert abs(cost_ham_energy - bitstring_energy) < 1e-9
        assert abs(cost_ham_energy - quantum_expected_energy) < 1e-9


def test_assignment_and_tsp_cost_hamiltonians():
    """Verify Cost Hamiltonian generation for Assignment and TSP problems."""
    # Small 2x2 Assignment Problem (4 binary variables)
    assign_data = {
        "agents": ["A", "B"],
        "tasks": ["T1", "T2"],
        "cost_matrix": [
            [4.0, 2.0],
            [1.0, 5.0]
        ]
    }
    assign_qubo = AssignmentQuboGenerator.generate(assign_data, penalty_coefficients={"A": 10.0, "B": 10.0})
    assign_ham = QAOACostHamiltonian.from_qubo(assign_qubo)
    assert assign_ham.num_qubits == 4
    assert len(assign_ham.coupling_terms) > 0

    # 3-city TSP (9 position-based binary variables)
    tsp_data = {
        "cities": ["C0", "C1", "C2"],
        "distance_matrix": [
            [0.0, 10.0, 15.0],
            [10.0, 0.0, 20.0],
            [15.0, 20.0, 0.0]
        ],
        "start_city": "C0"
    }
    tsp_qubo = TSPQuboGenerator.generate(tsp_data, penalty_coefficients={"A": 50.0, "B": 50.0, "C": 50.0})
    tsp_ham = QAOACostHamiltonian.from_qubo(tsp_qubo)
    assert tsp_ham.num_qubits == 9
    assert len(tsp_ham.coupling_terms) > 0
    assert tsp_ham.offset > 0.0
