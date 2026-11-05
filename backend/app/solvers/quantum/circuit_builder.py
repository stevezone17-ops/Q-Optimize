"""Parameterized QAOA quantum circuit builder and inspector."""

from typing import Dict, Any, List, Optional, Union
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector

from backend.app.solvers.quantum.hamiltonians import QAOACostHamiltonian, QAOAMixerHamiltonian
from backend.app.solvers.quantum.models import CircuitMetadata
from backend.app.solvers.quantum.exceptions import CircuitConstructionError, QubitLimitExceededError
from backend.app.solvers.quantum.config import default_quantum_limits, QuantumResourceLimits


class QAOACircuitBuilder:
    """
    Constructs parameterized QAOA quantum circuits:
      |psi(gamma, beta)> = U_M(beta_p) U_C(gamma_p) ... U_M(beta_1) U_C(gamma_1) |+>^{otimes n}
    
    Features:
      - Clean layer-by-layer alternating evolution (Cost unitary -> Mixer unitary).
      - ParameterVector management for variational parameters (gamma, beta).
      - Circuit parameter binding with validation.
      - Structural metadata extraction (qubits, clbits, gates, depth, 2Q gates).
      - Measurement mapping (qubit i -> clbit i).
    """

    def __init__(
        self,
        cost_hamiltonian: QAOACostHamiltonian,
        mixer_hamiltonian: Optional[QAOAMixerHamiltonian] = None,
        p_depth: int = 1,
        limits: Optional[QuantumResourceLimits] = None,
    ):
        self.limits = limits or default_quantum_limits
        self.cost_hamiltonian = cost_hamiltonian
        self.num_qubits = cost_hamiltonian.num_qubits

        # Validate resource limits
        if self.num_qubits > self.limits.max_qubits:
            raise QubitLimitExceededError(
                f"Cost Hamiltonian requires {self.num_qubits} qubits, exceeding the platform limit of {self.limits.max_qubits}."
            )
        if p_depth < 1 or p_depth > self.limits.max_p_depth:
            raise CircuitConstructionError(
                f"QAOA depth p must be between 1 and {self.limits.max_p_depth}, got {p_depth}."
            )

        self.p_depth = p_depth
        self.mixer_hamiltonian = mixer_hamiltonian or QAOAMixerHamiltonian(self.num_qubits)

        if self.mixer_hamiltonian.num_qubits != self.num_qubits:
            raise CircuitConstructionError(
                f"Mixer Hamiltonian qubits ({self.mixer_hamiltonian.num_qubits}) does not match "
                f"Cost Hamiltonian qubits ({self.num_qubits})."
            )

        # Symbolic parameters for variational optimization
        self.gamma = ParameterVector("gamma", self.p_depth)
        self.beta = ParameterVector("beta", self.p_depth)

    def build_circuit(
        self,
        include_measurements: bool = False,
        initial_superposition: bool = True,
    ) -> QuantumCircuit:
        """
        Builds the parameterized QAOA quantum circuit.
        
        Args:
            include_measurements: If True, adds classical register and measures all qubits.
            initial_superposition: If True, applies Hadamard gates to all qubits at step 0.
        """
        qc = QuantumCircuit(self.num_qubits, name=f"QAOA_p{self.p_depth}_n{self.num_qubits}")

        # 1. Initial State Preparation: Uniform Superposition |+>^{otimes n}
        if initial_superposition:
            for q in range(self.num_qubits):
                qc.h(q)

        # 2. Alternating QAOA Layers
        for k in range(self.p_depth):
            # Cost Hamiltonian unitary: U_C(gamma_k)
            self.cost_hamiltonian.apply_cost_unitary(qc, self.gamma[k])
            # Mixer Hamiltonian unitary: U_M(beta_k)
            self.mixer_hamiltonian.apply_mixer_unitary(qc, self.beta[k])

        # 3. Optional Measurement Layer
        if include_measurements:
            qc.measure_all()

        return qc

    def bind_parameters(
        self,
        circuit: QuantumCircuit,
        gamma_vals: Union[List[float], np.ndarray],
        beta_vals: Union[List[float], np.ndarray],
    ) -> QuantumCircuit:
        """
        Binds numerical angles into a parameterized circuit.
        
        Args:
            circuit: Parameterized QAOA QuantumCircuit.
            gamma_vals: Numerical gamma angles (length must equal p_depth).
            beta_vals: Numerical beta angles (length must equal p_depth).
        """
        if len(gamma_vals) != self.p_depth:
            raise ValueError(f"Expected {self.p_depth} gamma values, got {len(gamma_vals)}.")
        if len(beta_vals) != self.p_depth:
            raise ValueError(f"Expected {self.p_depth} beta values, got {len(beta_vals)}.")

        param_dict: Dict[Any, float] = {}
        for k in range(self.p_depth):
            param_dict[self.gamma[k]] = float(gamma_vals[k])
            param_dict[self.beta[k]] = float(beta_vals[k])

        return circuit.assign_parameters(param_dict)

    def build_and_bind(
        self,
        gamma_vals: Union[List[float], np.ndarray],
        beta_vals: Union[List[float], np.ndarray],
        include_measurements: bool = False,
    ) -> QuantumCircuit:
        """Constructs and immediately binds parameters in a single step."""
        param_circuit = self.build_circuit(include_measurements=include_measurements)
        return self.bind_parameters(param_circuit, gamma_vals, beta_vals)

    def extract_circuit_metadata(self, circuit: QuantumCircuit) -> CircuitMetadata:
        """Computes structural gate statistics and metadata for a QAOA circuit."""
        two_qubit_count = 0
        total_gate_count = 0
        has_meas = False

        for instruction in circuit.data:
            op_name = instruction.operation.name
            if op_name == "measure":
                has_meas = True
            elif op_name != "barrier":
                total_gate_count += 1
                if len(instruction.qubits) == 2:
                    two_qubit_count += 1

        return CircuitMetadata(
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            p_depth=self.p_depth,
            total_gates=total_gate_count,
            two_qubit_gates=two_qubit_count,
            circuit_depth=circuit.depth(),
            parameter_count=len(circuit.parameters),
            has_measurements=has_meas,
            qubit_variable_map=self.cost_hamiltonian.qubit_to_spin,
        )

    def render_ascii_diagram(self, circuit: QuantumCircuit) -> str:
        """Renders an ASCII text diagram of the circuit."""
        return str(circuit.draw(output="text"))
