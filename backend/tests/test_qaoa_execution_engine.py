"""Unit tests for Stage 5.5: QAOA Quantum Circuit Execution and Measurement Engine."""

import pytest
import math
from qiskit import QuantumCircuit

from backend.app.solvers.quantum.circuit_builder import QAOACircuitBuilder
from backend.app.solvers.quantum.hamiltonians import QAOACostHamiltonian
from backend.app.formulations.qubo_builder import QuboBuilder
from backend.app.solvers.quantum.models import QAOAConfiguration
from backend.app.solvers.quantum.execution_engine import QuantumExecutionEngine
from backend.app.solvers.quantum.exceptions import QubitLimitExceededError, ShotLimitExceededError
from backend.app.solvers.quantum.config import QuantumResourceLimits


def test_basic_circuit_execution_and_sampling():
    """Verify circuit execution returns counts, normalized probabilities, and execution metadata."""
    # Build 2-qubit Bell circuit
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    engine = QuantumExecutionEngine()
    cfg = QAOAConfiguration(shots=2000, seed=42)
    result = engine.execute_sampling(qc, cfg)

    assert result.shots == 2000
    assert sum(result.counts.values()) == 2000
    assert abs(sum(result.probabilities.values()) - 1.0) < 1e-6
    # Bell state should mainly measure '00' and '11'
    assert "00" in result.counts
    assert "11" in result.counts
    assert result.counts["00"] + result.counts["11"] == 2000
    assert result.execution_time_seconds >= 0.0
    assert "Qiskit Aer simulation" in result.hardware_transparency_note


def test_automatic_measurement_layer_insertion():
    """Verify that an unmeasured circuit has measurements added automatically."""
    qc = QuantumCircuit(2)
    qc.x(0)  # State |01> (q0=1, q1=0)

    engine = QuantumExecutionEngine()
    cfg = QAOAConfiguration(shots=500, seed=123)
    result = engine.execute_sampling(qc, cfg)

    # In Qiskit, q0=1, q1=0 is bitstring '01'
    assert result.most_frequent_bitstring == "01"
    assert result.most_frequent_count == 500
    assert result.most_frequent_probability == 1.0
    assert result.circuit_metadata.has_measurements is True


def test_sampling_seed_reproducibility():
    """Verify identical seeds produce identical measurement outcomes on Aer."""
    qc = QuantumCircuit(2)
    qc.h([0, 1])

    engine = QuantumExecutionEngine()
    cfg1 = QAOAConfiguration(shots=1000, seed=777)
    cfg2 = QAOAConfiguration(shots=1000, seed=777)

    res1 = engine.execute_sampling(qc, cfg1)
    res2 = engine.execute_sampling(qc, cfg2)

    assert res1.counts == res2.counts


def test_optional_noise_model_execution():
    """Verify optional depolarizing noise simulation runs and flags noisy execution."""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    engine = QuantumExecutionEngine()
    cfg_noisy = QAOAConfiguration(
        shots=1000,
        seed=42,
        noise_model_enabled=True,
        noise_error_rate=0.01,
    )
    result = engine.execute_sampling(qc, cfg_noisy)

    assert result.is_noisy is True
    assert result.noise_error_rate == 0.01
    assert result.shots == 1000
    # In presence of depolarizing noise, bitstrings other than '00' and '11' can appear
    assert len(result.counts) >= 2


def test_resource_limits_rejection():
    """Verify exceeding resource limits is intercepted before simulation."""
    limits = QuantumResourceLimits(max_qubits=2, max_shots=500)
    engine = QuantumExecutionEngine(limits=limits)

    # 3 qubits exceeds max 2
    qc_3q = QuantumCircuit(3)
    with pytest.raises(QubitLimitExceededError):
        engine.execute_sampling(qc_3q, QAOAConfiguration(shots=100))

    # 1000 shots exceeds max 500
    qc_2q = QuantumCircuit(2)
    with pytest.raises(ShotLimitExceededError):
        engine.execute_sampling(qc_2q, QAOAConfiguration(shots=1000))
