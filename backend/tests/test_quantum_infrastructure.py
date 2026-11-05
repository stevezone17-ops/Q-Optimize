"""Unit tests for Stage 5.1: Quantum Computing Infrastructure and Qiskit Integration."""

import pytest
import qiskit
import qiskit_aer
from qiskit_aer import AerSimulator
from pydantic import ValidationError

from backend.app.solvers.quantum.config import (
    SimulationMode,
    QuantumBackendType,
    ClassicalOptimizerType,
    ParameterInitializationStrategy,
    QuantumResourceLimits,
)
from backend.app.solvers.quantum.models import (
    QuantumBackendInfo,
    QAOAConfiguration,
    CircuitMetadata,
    QuantumExecutionStatus,
)
from backend.app.solvers.quantum.exceptions import (
    BackendNotAvailableError,
    QubitLimitExceededError,
    ShotLimitExceededError,
    CancellationError,
    ExecutionTimeoutError,
)
from backend.app.solvers.quantum.backend_manager import QuantumBackendManager
from backend.app.solvers.quantum.quantum_registry import QuantumSolverRegistry
from backend.app.solvers.quantum.execution_context import QuantumExecutionContext


def test_qiskit_and_aer_installed():
    """Verify that modern Qiskit and Qiskit Aer are present and report versions."""
    assert hasattr(qiskit, "__version__")
    assert hasattr(qiskit_aer, "__version__")
    manager = QuantumBackendManager()
    assert manager.qiskit_version == qiskit.__version__
    assert manager.aer_version == qiskit_aer.__version__


def test_backend_manager_discovery_and_transparency():
    """Verify backend manager lists expected backends with complete hardware transparency disclaimers."""
    manager = QuantumBackendManager()
    backends = manager.list_available_backends()
    assert len(backends) >= 3
    
    backend_ids = [b.backend_id for b in backends]
    assert "aer_simulator" in backend_ids
    assert "aer_statevector" in backend_ids
    assert "local_statevector" in backend_ids

    aer_sim = manager.get_backend_info("aer_simulator")
    assert aer_sim.is_simulator is True
    assert aer_sim.is_hardware is False
    assert "classical quantum circuit simulation" in aer_sim.hardware_transparency_note
    assert "No physical quantum hardware speedup is claimed" in aer_sim.hardware_transparency_note
    assert aer_sim.max_qubits == 24


def test_backend_manager_unknown_backend_fails():
    """Verify requesting an unknown backend raises BackendNotAvailableError."""
    manager = QuantumBackendManager()
    with pytest.raises(BackendNotAvailableError, match="not recognized"):
        manager.get_backend_info("non_existent_qpu")


def test_qaoa_configuration_validation():
    """Verify Pydantic validation rules on QAOAConfiguration."""
    # Valid default config
    cfg = QAOAConfiguration()
    assert cfg.p_depth == 1
    assert cfg.shots == 1024
    assert cfg.optimizer == ClassicalOptimizerType.COBYLA
    assert cfg.simulation_mode == SimulationMode.IDEAL_SHOTS

    # Invalid p_depth (< 1 or > 10)
    with pytest.raises(ValidationError):
        QAOAConfiguration(p_depth=0)
    with pytest.raises(ValidationError):
        QAOAConfiguration(p_depth=15)

    # Invalid shots (< 10 or > 50000)
    with pytest.raises(ValidationError):
        QAOAConfiguration(shots=5)
    with pytest.raises(ValidationError):
        QAOAConfiguration(shots=100000)


def test_resource_limit_checks():
    """Verify that resource limits protect against unconstrained quantum simulation."""
    manager = QuantumBackendManager(limits=QuantumResourceLimits(
        max_qubits=24,
        max_statevector_qubits=16,
        max_shots=10000,
        min_shots=10
    ))

    # Acceptable dimensions
    manager.validate_resource_requirements(num_qubits=8, shots=1024, simulation_mode=SimulationMode.IDEAL_SHOTS)
    manager.validate_resource_requirements(num_qubits=12, shots=1024, simulation_mode=SimulationMode.STATEVECTOR_EXACT)

    # Exceeding shot-based qubit limit (e.g. 25 qubits)
    with pytest.raises(QubitLimitExceededError, match="exceeds the platform limit"):
        manager.validate_resource_requirements(num_qubits=25, shots=1000, simulation_mode=SimulationMode.IDEAL_SHOTS)

    # Exceeding statevector qubit limit (e.g. 17 qubits)
    with pytest.raises(QubitLimitExceededError, match="exceeds statevector limit"):
        manager.validate_resource_requirements(num_qubits=17, shots=1000, simulation_mode=SimulationMode.STATEVECTOR_EXACT)

    # Exceeding shots
    with pytest.raises(ShotLimitExceededError, match="exceeds maximum"):
        manager.validate_resource_requirements(num_qubits=4, shots=20000)

    # Subceeding shots
    with pytest.raises(ShotLimitExceededError, match="below the minimum"):
        manager.validate_resource_requirements(num_qubits=4, shots=4)


def test_aer_simulator_instantiation():
    """Verify that AerSimulator can be cleanly instantiated with configuration."""
    manager = QuantumBackendManager()
    cfg = QAOAConfiguration(
        backend_name="aer_simulator",
        seed=12345,
        simulation_mode=SimulationMode.IDEAL_SHOTS,
    )
    sim = manager.instantiate_aer_simulator(cfg)
    assert isinstance(sim, AerSimulator)

    # Statevector exact simulator
    cfg_sv = QAOAConfiguration(
        backend_name="aer_simulator",
        seed=999,
        simulation_mode=SimulationMode.STATEVECTOR_EXACT,
    )
    sim_sv = manager.instantiate_aer_simulator(cfg_sv)
    assert isinstance(sim_sv, AerSimulator)


def test_quantum_execution_context_cancellation_and_timeout():
    """Verify QuantumExecutionContext detects cancellation tokens and timeouts."""
    # Cancellation test
    ctx = QuantumExecutionContext(time_limit_seconds=10.0)
    ctx.check_status()
    assert ctx.eval_count == 0
    ctx.record_evaluation()
    assert ctx.eval_count == 1

    ctx.cancel()
    with pytest.raises(CancellationError, match="cancelled by user request"):
        ctx.check_status()

    # Timeout test
    ctx_timed = QuantumExecutionContext(time_limit_seconds=0.001)
    import time
    time.sleep(0.01)
    with pytest.raises(ExecutionTimeoutError, match="timed out"):
        ctx_timed.check_status()


def test_quantum_solver_registry():
    """Verify QuantumSolverRegistry singleton tracks backends and solvers."""
    registry = QuantumSolverRegistry.get_instance()
    assert registry is QuantumSolverRegistry.get_instance()

    backends = registry.list_backends()
    assert len(backends) >= 3

    # Register dummy solver
    class DummyQAOASolver:
        pass

    registry.register_solver("qaoa_v1", DummyQAOASolver)
    assert "qaoa_v1" in registry.list_solvers()
    assert registry.get_solver("qaoa_v1") is DummyQAOASolver

    with pytest.raises(KeyError, match="not found"):
        registry.get_solver("non_existent_solver")
