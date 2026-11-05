"""Quantum circuit execution, measurement sampling, and transpilation engine."""

from typing import Dict, Any, List, Optional
import time
import logging
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from backend.app.solvers.quantum.config import (
    SimulationMode,
    QuantumResourceLimits,
    default_quantum_limits,
)
from backend.app.solvers.quantum.models import (
    QAOAConfiguration,
    CircuitMetadata,
    QuantumSamplingResult,
)
from backend.app.solvers.quantum.backend_manager import QuantumBackendManager
from backend.app.solvers.quantum.execution_context import QuantumExecutionContext
from backend.app.solvers.quantum.exceptions import (
    TranspilationError,
    QubitLimitExceededError,
    ShotLimitExceededError,
)

logger = logging.getLogger(__name__)


class QuantumExecutionEngine:
    """
    Executes compiled QAOA quantum circuits on Qiskit Aer simulators:
      - Enforces resource limits on qubits and shot counts.
      - Handles transpilation and measurement gate insertion.
      - Samples measurement counts and computes empirical bitstring distributions.
      - Records execution time and hardware transparency metadata.
    """

    def __init__(
        self,
        backend_manager: Optional[QuantumBackendManager] = None,
        limits: Optional[QuantumResourceLimits] = None,
    ):
        self.limits = limits or default_quantum_limits
        self.backend_manager = backend_manager or QuantumBackendManager(limits=self.limits)

    def execute_sampling(
        self,
        circuit: QuantumCircuit,
        config: QAOAConfiguration,
        context: Optional[QuantumExecutionContext] = None,
    ) -> QuantumSamplingResult:
        """
        Executes a quantum circuit on the configured Aer simulator target and returns measurement statistics.
        """
        ctx = context or QuantumExecutionContext(time_limit_seconds=config.time_limit_seconds)
        ctx.check_status()

        # 1. Resource limit validation
        self.backend_manager.validate_resource_requirements(
            num_qubits=circuit.num_qubits,
            shots=config.shots,
            simulation_mode=config.simulation_mode,
        )

        # 2. Ensure circuit has measurement operations
        measured_qc = circuit.copy()
        has_meas = any(instr.operation.name == "measure" for instr in measured_qc.data)
        if not has_meas:
            measured_qc.measure_all()

        # 3. Instantiate simulator target
        simulator = self.backend_manager.instantiate_aer_simulator(config)

        # 4. Transpile circuit for Aer target
        ctx.check_status()
        try:
            transpiled_qc = transpile(
                measured_qc,
                simulator,
                seed_transpiler=config.seed or 42,
            )
        except Exception as exc:
            raise TranspilationError(f"Failed to transpile quantum circuit for simulator: {str(exc)}") from exc

        # 5. Execute simulation job
        ctx.check_status()
        t0 = time.perf_counter()
        job = simulator.run(transpiled_qc, shots=config.shots)
        result = job.result()
        execution_duration = time.perf_counter() - t0

        counts: Dict[str, int] = result.get_counts()
        total_shots = sum(counts.values())

        if total_shots == 0:
            raise RuntimeError("Circuit execution completed with 0 total measured shots.")

        # 6. Normalize probabilities
        probabilities: Dict[str, float] = {
            bitstring: count / total_shots
            for bitstring, count in counts.items()
        }

        # 7. Identify most frequent bitstring
        most_freq_bitstring, most_freq_count = max(counts.items(), key=lambda kv: kv[1])
        most_freq_prob = most_freq_count / total_shots

        # 8. Compute circuit metadata
        two_qubit_count = sum(1 for d in circuit.data if len(d.qubits) == 2)
        total_gate_count = sum(1 for d in circuit.data if d.operation.name not in ["barrier", "measure"])

        circuit_metadata = CircuitMetadata(
            num_qubits=circuit.num_qubits,
            num_clbits=measured_qc.num_clbits,
            p_depth=config.p_depth,
            total_gates=total_gate_count,
            two_qubit_gates=two_qubit_count,
            circuit_depth=circuit.depth(),
            parameter_count=len(circuit.parameters),
            has_measurements=True,
            qubit_variable_map={},
        )

        return QuantumSamplingResult(
            counts=counts,
            probabilities=probabilities,
            shots=total_shots,
            unique_bitstrings=len(counts),
            most_frequent_bitstring=most_freq_bitstring,
            most_frequent_count=most_freq_count,
            most_frequent_probability=round(most_freq_prob, 6),
            circuit_metadata=circuit_metadata,
            simulation_mode=config.simulation_mode.value,
            execution_time_seconds=round(execution_duration, 4),
            seed=config.seed,
            is_noisy=config.noise_model_enabled,
            noise_error_rate=config.noise_error_rate if config.noise_model_enabled else None,
        )
