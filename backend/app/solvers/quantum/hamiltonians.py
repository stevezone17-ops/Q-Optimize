"""Cost and Mixer Hamiltonian representations for QAOA quantum circuits."""

from typing import Dict, Any, List, Tuple, Union, Optional
import math
import numpy as np
from qiskit.circuit import QuantumCircuit, Parameter, ParameterExpression
from qiskit.quantum_info import SparsePauliOp

from backend.app.domain.formulations.models import IsingModel, QuboModel
from backend.app.formulations.ising_converter import IsingConverter
from backend.app.solvers.quantum.exceptions import CircuitConstructionError


class QAOACostHamiltonian:
    """
    Cost Hamiltonian H_C = C + sum_i h_i Z_i + sum_{i < j} J_ij Z_i Z_j derived from Phase 3 Ising models.
    
    Provides:
      1. Unitary circuit evolution U_C(gamma) = exp(-i * gamma * H_C) using single-qubit RZ and two-qubit RZZ gates.
      2. Exact state and bitstring energy evaluations matching Phase 3 QUBO and Ising definitions.
      3. SparsePauliOp conversion for exact quantum statevector expectation calculations.
    """

    def __init__(self, ising: IsingModel):
        self.ising = ising
        self.num_qubits = len(ising.variable_order)
        self.spin_order = list(ising.variable_order)
        
        # Mapping between qubit index and spin name (e.g. 0 -> "Z_x0")
        self.qubit_to_spin: Dict[int, str] = {i: s for i, s in enumerate(self.spin_order)}
        self.spin_to_qubit: Dict[str, int] = {s: i for i, s in enumerate(self.spin_order)}
        
        # Problem variable to qubit index mapping (e.g. "x0" -> 0)
        self.var_to_qubit: Dict[str, int] = {}
        for var_name, spin_name in ising.spin_mapping.items():
            if spin_name in self.spin_to_qubit:
                self.var_to_qubit[var_name] = self.spin_to_qubit[spin_name]

        # Extract linear terms h_i
        self.linear_terms: List[Tuple[int, float]] = []
        for spin_name, h_val in ising.local_fields.items():
            if spin_name in self.spin_to_qubit:
                q_idx = self.spin_to_qubit[spin_name]
                if abs(h_val) > 1e-12:
                    self.linear_terms.append((q_idx, float(h_val)))

        # Extract quadratic coupling terms J_ij (i < j)
        self.coupling_terms: List[Tuple[int, int, float]] = []
        for pair_key, j_val in ising.couplings.items():
            if "," in pair_key:
                s1, s2 = pair_key.split(",", 1)
                if s1 in self.spin_to_qubit and s2 in self.spin_to_qubit:
                    q1 = self.spin_to_qubit[s1]
                    q2 = self.spin_to_qubit[s2]
                    idx_min, idx_max = min(q1, q2), max(q1, q2)
                    if abs(j_val) > 1e-12:
                        self.coupling_terms.append((idx_min, idx_max, float(j_val)))

        # Constant offset C
        self.offset: float = float(ising.offset)

    @classmethod
    def from_qubo(cls, qubo: QuboModel) -> "QAOACostHamiltonian":
        """Construct a QAOACostHamiltonian directly from a canonical QUBO model."""
        ising = IsingConverter.qubo_to_ising(qubo)
        return cls(ising)

    def apply_cost_unitary(
        self,
        qc: QuantumCircuit,
        gamma: Union[float, Parameter, ParameterExpression]
    ) -> None:
        """
        Applies U_C(gamma) = exp(-i * gamma * H_C) to the quantum circuit.
        
        Angle derivations:
          - Single-qubit Z rotation: Qiskit rz(phi) applies exp(-i * phi/2 * Z).
            To apply exp(-i * gamma * h_i * Z_i), we set phi = 2 * gamma * h_i.
          - Pairwise ZZ rotation: Qiskit rzz(theta) applies exp(-i * theta/2 * Z_i * Z_j).
            To apply exp(-i * gamma * J_ij * Z_i * Z_j), we set theta = 2 * gamma * J_ij.
          - The constant offset C contributes a global phase exp(-i * gamma * C) and is
            omitted from circuit gates while preserved in reported energy calculations.
        """
        if qc.num_qubits < self.num_qubits:
            raise CircuitConstructionError(
                f"Circuit has {qc.num_qubits} qubits but Cost Hamiltonian requires {self.num_qubits}."
            )

        # 1. Single-qubit Z rotations for linear terms
        for q_idx, h_val in self.linear_terms:
            rz_angle = 2.0 * gamma * h_val
            qc.rz(rz_angle, q_idx)

        # 2. Two-qubit ZZ interactions for coupling terms
        for q_i, q_j, j_val in self.coupling_terms:
            rzz_angle = 2.0 * gamma * j_val
            qc.rzz(rzz_angle, q_i, q_j)

    def evaluate_spins_energy(self, spins: List[int]) -> float:
        """
        Evaluates exact energy H_C(Z) = C + sum_i h_i Z_i + sum_{i < j} J_ij Z_i Z_j
        for spin vector Z where Z_i in {-1, +1}.
        """
        if len(spins) != self.num_qubits:
            raise ValueError(f"Expected {self.num_qubits} spins, got {len(spins)}")

        energy = self.offset
        for q_idx, h_val in self.linear_terms:
            energy += h_val * spins[q_idx]

        for q_i, q_j, j_val in self.coupling_terms:
            energy += j_val * spins[q_i] * spins[q_j]

        return energy

    def evaluate_binary_energy(self, x_vec: List[int]) -> float:
        """
        Evaluates Hamiltonian energy for binary variables x in {0, 1}^n
        using the Phase 3 mapping x_i = (1 - Z_i)/2 <=> Z_i = 1 - 2*x_i.
        """
        spins = [1 - 2 * int(xi) for xi in x_vec]
        return self.evaluate_spins_energy(spins)

    def evaluate_bitstring_energy(self, bitstring: str, little_endian: bool = True) -> float:
        """
        Evaluates Hamiltonian energy for a measurement bitstring.
        
        By default (little_endian=True, matching Qiskit's counts format),
        bitstring[0] corresponds to qubit n-1 and bitstring[-1] corresponds to qubit 0.
        """
        clean_bits = bitstring.strip().replace(" ", "")
        if len(clean_bits) != self.num_qubits:
            raise ValueError(
                f"Bitstring length ({len(clean_bits)}) does not match qubit count ({self.num_qubits})"
            )

        if little_endian:
            # Qiskit format: rightmost bit is qubit 0
            x_vec = [int(clean_bits[self.num_qubits - 1 - i]) for i in range(self.num_qubits)]
        else:
            # Left-to-right format: leftmost bit is qubit 0
            x_vec = [int(clean_bits[i]) for i in range(self.num_qubits)]

        return self.evaluate_binary_energy(x_vec)

    def to_sparse_pauli_op(self) -> SparsePauliOp:
        """
        Constructs a Qiskit SparsePauliOp representing H_C for statevector expectation computation.
        
        Note on Qiskit Pauli indexing:
          In SparsePauliOp strings, qubit 0 is the rightmost character (index n - 1 - qubit).
        """
        pauli_list: List[Tuple[str, float]] = []

        # 1. Identity term with constant offset C
        if abs(self.offset) > 1e-12:
            pauli_list.append(("I" * self.num_qubits, self.offset))

        # 2. Linear Pauli-Z terms
        for q_idx, h_val in self.linear_terms:
            chars = ["I"] * self.num_qubits
            chars[self.num_qubits - 1 - q_idx] = "Z"
            pauli_list.append(("".join(chars), h_val))

        # 3. Quadratic Pauli-ZZ terms
        for q_i, q_j, j_val in self.coupling_terms:
            chars = ["I"] * self.num_qubits
            chars[self.num_qubits - 1 - q_i] = "Z"
            chars[self.num_qubits - 1 - q_j] = "Z"
            pauli_list.append(("".join(chars), j_val))

        if not pauli_list:
            return SparsePauliOp.from_list([("I" * self.num_qubits, 0.0)])

        return SparsePauliOp.from_list(pauli_list)

    def get_metadata(self) -> Dict[str, Any]:
        """Summary metadata of the cost Hamiltonian."""
        return {
            "num_qubits": self.num_qubits,
            "num_linear_terms": len(self.linear_terms),
            "num_coupling_terms": len(self.coupling_terms),
            "offset": round(self.offset, 6),
            "qubit_variable_map": self.qubit_to_spin,
        }


class QAOAMixerHamiltonian:
    """
    Standard transverse-field mixer Hamiltonian H_M = sum_{i=0}^{n-1} X_i.
    
    Provides:
      1. Unitary circuit evolution U_M(beta) = exp(-i * beta * H_M) using single-qubit RX gates.
      2. SparsePauliOp conversion for expectation calculations.
    """

    def __init__(self, num_qubits: int):
        if num_qubits < 1:
            raise ValueError(f"Number of qubits must be at least 1, got {num_qubits}")
        self.num_qubits = num_qubits

    def apply_mixer_unitary(
        self,
        qc: QuantumCircuit,
        beta: Union[float, Parameter, ParameterExpression]
    ) -> None:
        """
        Applies U_M(beta) = exp(-i * beta * sum_i X_i) to the quantum circuit.
        
        Angle derivation:
          Qiskit rx(theta) applies exp(-i * theta/2 * X).
          To apply exp(-i * beta * X_i), we set theta = 2 * beta.
        """
        if qc.num_qubits < self.num_qubits:
            raise CircuitConstructionError(
                f"Circuit has {qc.num_qubits} qubits but Mixer Hamiltonian requires {self.num_qubits}."
            )

        rx_angle = 2.0 * beta
        for q_idx in range(self.num_qubits):
            qc.rx(rx_angle, q_idx)

    def to_sparse_pauli_op(self) -> SparsePauliOp:
        """Constructs a Qiskit SparsePauliOp representing H_M = sum_i X_i."""
        pauli_list: List[Tuple[str, float]] = []
        for q_idx in range(self.num_qubits):
            chars = ["I"] * self.num_qubits
            chars[self.num_qubits - 1 - q_idx] = "X"
            pauli_list.append(("".join(chars), 1.0))

        return SparsePauliOp.from_list(pauli_list)

    def get_metadata(self) -> Dict[str, Any]:
        """Summary metadata of the mixer Hamiltonian."""
        return {
            "num_qubits": self.num_qubits,
            "type": "transverse_field_x",
            "terms": self.num_qubits,
        }
