"""Quantum backend manager discovering, configuring, and validating simulation targets."""

from typing import Dict, List, Optional, Any
import logging
import qiskit
import qiskit_aer
from qiskit_aer import AerSimulator

from backend.app.solvers.quantum.config import (
    SimulationMode,
    QuantumBackendType,
    QuantumResourceLimits,
    default_quantum_limits,
)
from backend.app.solvers.quantum.models import QuantumBackendInfo, QAOAConfiguration
from backend.app.solvers.quantum.exceptions import (
    BackendNotAvailableError,
    UnsupportedSimulationMethodError,
    QubitLimitExceededError,
    ShotLimitExceededError,
)

logger = logging.getLogger(__name__)


class QuantumBackendManager:
    """Discovers, validates, and provisions quantum simulation backends via Qiskit and Qiskit Aer."""

    def __init__(self, limits: Optional[QuantumResourceLimits] = None):
        self.limits = limits or default_quantum_limits
        self._qiskit_version = getattr(qiskit, "__version__", "unknown")
        self._aer_version = getattr(qiskit_aer, "__version__", "unknown")

    @property
    def qiskit_version(self) -> str:
        return self._qiskit_version

    @property
    def aer_version(self) -> str:
        return self._aer_version

    def list_available_backends(self) -> List[QuantumBackendInfo]:
        """Discover and describe all available quantum execution backends."""
        return [
            QuantumBackendInfo(
                backend_id="aer_simulator",
                name="Qiskit Aer Multi-Shot Simulator",
                backend_type=QuantumBackendType.AER_SIMULATOR,
                is_simulator=True,
                is_hardware=False,
                max_qubits=self.limits.max_qubits,
                supported_methods=["automatic", "statevector", "matrix_product_state", "extended_stabilizer"],
                is_available=True,
                qiskit_version=self._qiskit_version,
                aer_version=self._aer_version,
            ),
            QuantumBackendInfo(
                backend_id="aer_statevector",
                name="Qiskit Aer Exact Statevector Simulator",
                backend_type=QuantumBackendType.AER_STATEVECTOR,
                is_simulator=True,
                is_hardware=False,
                max_qubits=self.limits.max_statevector_qubits,
                supported_methods=["statevector"],
                is_available=True,
                qiskit_version=self._qiskit_version,
                aer_version=self._aer_version,
            ),
            QuantumBackendInfo(
                backend_id="local_statevector",
                name="Qiskit QuantumInfo Local Statevector",
                backend_type=QuantumBackendType.LOCAL_STATEVECTOR,
                is_simulator=True,
                is_hardware=False,
                max_qubits=self.limits.max_statevector_qubits,
                supported_methods=["statevector_exact"],
                is_available=True,
                qiskit_version=self._qiskit_version,
                aer_version=self._aer_version,
            ),
        ]

    def get_backend_info(self, backend_id: str) -> QuantumBackendInfo:
        """Retrieve metadata for a specific backend ID."""
        for backend in self.list_available_backends():
            if backend.backend_id == backend_id:
                return backend
        raise BackendNotAvailableError(
            f"Quantum backend '{backend_id}' is not recognized or installed. "
            f"Available backends: {[b.backend_id for b in self.list_available_backends()]}"
        )

    def validate_resource_requirements(
        self,
        num_qubits: int,
        shots: int,
        simulation_mode: SimulationMode = SimulationMode.IDEAL_SHOTS,
    ) -> None:
        """Validate that requested circuit dimensions do not exceed platform limits."""
        if simulation_mode == SimulationMode.STATEVECTOR_EXACT:
            if num_qubits > self.limits.max_statevector_qubits:
                raise QubitLimitExceededError(
                    f"Requested {num_qubits} qubits exceeds statevector limit of "
                    f"{self.limits.max_statevector_qubits}. Use 'ideal_shots' mode for larger problems."
                )
        else:
            if num_qubits > self.limits.max_qubits:
                raise QubitLimitExceededError(
                    f"Requested {num_qubits} qubits exceeds the platform limit of "
                    f"{self.limits.max_qubits} qubits."
                )

        if shots > self.limits.max_shots:
            raise ShotLimitExceededError(
                f"Requested {shots} shots exceeds maximum allowable limit of {self.limits.max_shots}."
            )
        if shots < self.limits.min_shots:
            raise ShotLimitExceededError(
                f"Requested {shots} shots is below the minimum required limit of {self.limits.min_shots}."
            )

    def instantiate_aer_simulator(
        self,
        config: QAOAConfiguration,
    ) -> AerSimulator:
        """Create and configure an AerSimulator instance based on QAOAConfiguration."""
        if config.backend_name not in ["aer_simulator", "aer_statevector"]:
            raise BackendNotAvailableError(f"Cannot instantiate AerSimulator for backend '{config.backend_name}'.")

        kwargs: Dict[str, Any] = {}
        if config.seed is not None:
            kwargs["seed_simulator"] = config.seed

        if config.simulation_mode == SimulationMode.STATEVECTOR_EXACT:
            kwargs["method"] = "statevector"
        else:
            kwargs["method"] = "automatic"

        # Optional noise model
        if config.noise_model_enabled:
            try:
                from qiskit_aer.noise import NoiseModel, depolarizing_error
                noise_model = NoiseModel()
                error_1q = depolarizing_error(config.noise_error_rate, 1)
                error_2q = depolarizing_error(config.noise_error_rate * 2, 2)
                noise_model.add_all_qubit_quantum_error(error_1q, ["rx", "rz", "h"])
                noise_model.add_all_qubit_quantum_error(error_2q, ["cx", "rzz"])
                kwargs["noise_model"] = noise_model
                logger.info("Configured Aer depolarizing noise model with rate %.4f", config.noise_error_rate)
            except Exception as e:
                logger.warning("Failed to configure Aer noise model: %s. Proceeding with ideal simulation.", e)

        return AerSimulator(**kwargs)
