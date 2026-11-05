"""Unit tests for Stage 5.4: Classical Parameter Optimization for QAOA."""

import pytest
import math
import numpy as np

from backend.app.formulations.qubo_builder import QuboBuilder
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.solvers.quantum.hamiltonians import QAOACostHamiltonian
from backend.app.solvers.quantum.circuit_builder import QAOACircuitBuilder
from backend.app.solvers.quantum.optimizer import QAOAOptimizer
from backend.app.solvers.quantum.config import (
    SimulationMode,
    ClassicalOptimizerType,
    ParameterInitializationStrategy,
)
from backend.app.solvers.quantum.models import QAOAConfiguration
from backend.app.solvers.quantum.execution_context import QuantumExecutionContext


def test_parameter_initialization_strategies():
    """Verify different parameter initialization strategies produce expected structures."""
    builder = QuboBuilder(["x0", "x1"])
    cost_ham = QAOACostHamiltonian.from_qubo(builder.build_model())
    cb = QAOACircuitBuilder(cost_ham, p_depth=2)

    # 1. ZEROS
    cfg_zeros = QAOAConfiguration(p_depth=2, init_strategy=ParameterInitializationStrategy.ZEROS)
    opt_zeros = QAOAOptimizer(cb, cfg_zeros)
    g, b = opt_zeros.get_initial_parameters()
    assert g == [0.0, 0.0]
    assert b == [0.0, 0.0]

    # 2. LINEAR_RAMP
    cfg_ramp = QAOAConfiguration(p_depth=2, init_strategy=ParameterInitializationStrategy.LINEAR_RAMP)
    opt_ramp = QAOAOptimizer(cb, cfg_ramp)
    g_ramp, b_ramp = opt_ramp.get_initial_parameters()
    assert len(g_ramp) == 2 and len(b_ramp) == 2
    assert g_ramp[0] < g_ramp[1]  # Gamma increases
    assert b_ramp[0] > b_ramp[1]  # Beta decreases

    # 3. CUSTOM
    cfg_custom = QAOAConfiguration(
        p_depth=2,
        init_strategy=ParameterInitializationStrategy.CUSTOM,
        initial_gamma=[0.33, 0.66],
        initial_beta=[0.11, 0.22]
    )
    opt_custom = QAOAOptimizer(cb, cfg_custom)
    g_c, b_c = opt_custom.get_initial_parameters()
    assert g_c == [0.33, 0.66]
    assert b_c == [0.11, 0.22]

    # 4. RANDOM reproducibility
    cfg_rand1 = QAOAConfiguration(p_depth=2, seed=12345, init_strategy=ParameterInitializationStrategy.RANDOM)
    cfg_rand2 = QAOAConfiguration(p_depth=2, seed=12345, init_strategy=ParameterInitializationStrategy.RANDOM)
    g1, b1 = QAOAOptimizer(cb, cfg_rand1).get_initial_parameters()
    g2, b2 = QAOAOptimizer(cb, cfg_rand2).get_initial_parameters()
    assert g1 == g2
    assert b1 == b2


def test_statevector_and_shot_expectation_evaluation():
    """Verify statevector exact expectation and shot-based sampling expectation."""
    # 2-node graph with weight 4.0
    problem_data = {
        "nodes": ["0", "1"],
        "edges": [["0", "1", 4.0]]
    }
    cost_ham = QAOACostHamiltonian.from_qubo(MaxCutQuboGenerator.generate(problem_data))
    cb = QAOACircuitBuilder(cost_ham, p_depth=1)

    # Statevector exact mode
    cfg_sv = QAOAConfiguration(
        p_depth=1,
        simulation_mode=SimulationMode.STATEVECTOR_EXACT
    )
    opt_sv = QAOAOptimizer(cb, cfg_sv)
    # At gamma=0, beta=0, circuit is purely uniform superposition |+>
    # Average energy of 2-node cut:
    # cuts are: 00: 0, 01: 4, 10: 4, 11: 0 -> QUBO energies: 0, -4, -4, 0. Mean = -2.0
    energy_sv_0 = opt_sv.evaluate_expectation([0.0], [0.0])
    assert abs(energy_sv_0 - (-2.0)) < 1e-6

    # Shot-based mode with 5000 shots
    cfg_shots = QAOAConfiguration(
        p_depth=1,
        shots=5000,
        seed=42,
        simulation_mode=SimulationMode.IDEAL_SHOTS
    )
    opt_shots = QAOAOptimizer(cb, cfg_shots)
    energy_shots_0 = opt_shots.evaluate_expectation([0.0], [0.0])
    # Should be close to -2.0 within statistical sampling noise
    assert abs(energy_shots_0 - (-2.0)) < 0.2


def test_qaoa_optimization_loop_cobyla():
    """Verify variational parameter optimization with COBYLA reduces expected energy."""
    problem_data = {
        "nodes": ["0", "1", "2"],
        "edges": [["0", "1", 2.0], ["1", "2", 3.0], ["0", "2", 1.0]]
    }
    cost_ham = QAOACostHamiltonian.from_qubo(MaxCutQuboGenerator.generate(problem_data))
    cb = QAOACircuitBuilder(cost_ham, p_depth=1)

    cfg = QAOAConfiguration(
        p_depth=1,
        simulation_mode=SimulationMode.STATEVECTOR_EXACT,
        optimizer=ClassicalOptimizerType.COBYLA,
        max_iterations=30,
        seed=101,
        init_strategy=ParameterInitializationStrategy.LINEAR_RAMP,
    )
    optimizer = QAOAOptimizer(cb, cfg)
    result = optimizer.optimize()

    assert result.optimizer_name == "COBYLA"
    assert len(result.optimal_gamma) == 1
    assert len(result.optimal_beta) == 1
    assert result.total_evaluations > 0
    # Energy should be reduced or maintained
    assert result.best_expected_energy <= result.initial_expected_energy

    # Verify convergence history monotonicity of best_expected_energy
    best_so_far = float("inf")
    for pt in result.convergence_history:
        assert pt.best_expected_energy <= best_so_far
        best_so_far = pt.best_expected_energy


def test_optimizer_cancellation_preserves_best_angles():
    """Verify cooperative cancellation stops optimization and returns best parameters found."""
    builder = QuboBuilder(["x0", "x1"])
    cost_ham = QAOACostHamiltonian.from_qubo(builder.build_model())
    cb = QAOACircuitBuilder(cost_ham, p_depth=1)

    ctx = QuantumExecutionContext(time_limit_seconds=10.0)
    ctx.cancel()  # Cancel immediately

    cfg = QAOAConfiguration(p_depth=1, max_iterations=50)
    optimizer = QAOAOptimizer(cb, cfg, context=ctx)
    result = optimizer.optimize()

    assert "cancelled" in result.termination_reason.lower()
    assert len(result.optimal_gamma) == 1
    assert len(result.optimal_beta) == 1
