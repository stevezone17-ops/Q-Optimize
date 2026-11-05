"""Classical parameter optimization for QAOA variational angle discovery."""

from typing import Dict, Any, List, Tuple, Optional
import time
import math
import numpy as np
import scipy.optimize as opt
from qiskit.quantum_info import Statevector

from backend.app.solvers.quantum.circuit_builder import QAOACircuitBuilder
from backend.app.solvers.quantum.models import (
    QAOAConfiguration,
    QAOAOptimizationResult,
    QuantumConvergencePoint,
)
from backend.app.solvers.quantum.config import (
    SimulationMode,
    ClassicalOptimizerType,
    ParameterInitializationStrategy,
)
from backend.app.solvers.quantum.backend_manager import QuantumBackendManager
from backend.app.solvers.quantum.execution_context import QuantumExecutionContext
from backend.app.solvers.quantum.exceptions import (
    QuantumSolverError,
    ExecutionTimeoutError,
    CancellationError,
)


class QAOAOptimizer:
    """
    Classical parameter optimizer minimizing the expected Cost Hamiltonian energy:
      min_{gamma, beta} E(gamma, beta) = <psi(gamma, beta)| H_C |psi(gamma, beta)>
    """

    def __init__(
        self,
        circuit_builder: QAOACircuitBuilder,
        config: QAOAConfiguration,
        backend_manager: Optional[QuantumBackendManager] = None,
        context: Optional[QuantumExecutionContext] = None,
    ):
        self.circuit_builder = circuit_builder
        self.config = config
        self.backend_manager = backend_manager or QuantumBackendManager()
        self.context = context or QuantumExecutionContext(time_limit_seconds=config.time_limit_seconds)
        
        self.p_depth = circuit_builder.p_depth
        self.cost_ham = circuit_builder.cost_hamiltonian
        self.sparse_pauli_op = self.cost_ham.to_sparse_pauli_op()

        # Cache unmeasured circuit for fast statevector evaluations
        self._unmeasured_circuit = self.circuit_builder.build_circuit(include_measurements=False)
        # Measured circuit for shot-based sampling
        self._measured_circuit = self.circuit_builder.build_circuit(include_measurements=True)

        # Simulator instance for shot-based evaluations
        self._aer_simulator = None
        if self.config.simulation_mode != SimulationMode.STATEVECTOR_EXACT:
            self._aer_simulator = self.backend_manager.instantiate_aer_simulator(self.config)

        # Optimization state
        self._convergence_history: List[QuantumConvergencePoint] = []
        self._best_energy: float = float("inf")
        self._best_gamma: List[float] = []
        self._best_beta: List[float] = []
        self._eval_count: int = 0
        self._iteration_count: int = 0

    def get_initial_parameters(self) -> Tuple[List[float], List[float]]:
        """Determine initial gamma and beta parameters based on configured strategy."""
        p = self.p_depth
        strategy = self.config.init_strategy

        if strategy == ParameterInitializationStrategy.CUSTOM:
            if self.config.initial_gamma and self.config.initial_beta:
                if len(self.config.initial_gamma) == p and len(self.config.initial_beta) == p:
                    return list(self.config.initial_gamma), list(self.config.initial_beta)

        if strategy == ParameterInitializationStrategy.ZEROS:
            return [0.0] * p, [0.0] * p

        if strategy == ParameterInitializationStrategy.LINEAR_RAMP:
            # Linear ramp heuristic: gamma increases from 0 to pi/2, beta decreases from pi/4 to 0
            gamma = [((k + 1) / p) * (math.pi / 2.0) for k in range(p)]
            beta = [(1.0 - (k / p)) * (math.pi / 4.0) for k in range(p)]
            return gamma, beta

        # Default: RANDOM initialization
        seed = self.config.seed or 42
        rng = np.random.default_rng(seed)
        # Standard intervals: gamma in [0, pi], beta in [0, pi/2]
        gamma = list(rng.uniform(0.0, math.pi, size=p))
        beta = list(rng.uniform(0.0, math.pi / 2.0, size=p))
        return gamma, beta

    def evaluate_expectation(self, gamma: List[float], beta: List[float]) -> float:
        """
        Computes the expected energy <psi(gamma, beta)| H_C |psi(gamma, beta)>
        using exact statevector expectation or shot-based empirical sampling.
        """
        self.context.check_status()
        self._eval_count += 1
        self.context.record_evaluation()

        if self.config.simulation_mode == SimulationMode.STATEVECTOR_EXACT:
            # Exact statevector expectation without statistical shot noise
            bound_circuit = self.circuit_builder.bind_parameters(
                self._unmeasured_circuit, gamma, beta
            )
            sv = Statevector.from_instruction(bound_circuit)
            expected_energy = float(sv.expectation_value(self.sparse_pauli_op).real)
        else:
            # Shot-based sampling expectation
            bound_circuit = self.circuit_builder.bind_parameters(
                self._measured_circuit, gamma, beta
            )
            result = self._aer_simulator.run(bound_circuit, shots=self.config.shots).result()
            counts = result.get_counts()
            
            # Weighted average over measured bitstrings
            total_shots = sum(counts.values())
            weighted_energy = 0.0
            for bitstring, count in counts.items():
                e_val = self.cost_ham.evaluate_bitstring_energy(bitstring, little_endian=True)
                weighted_energy += (count / total_shots) * e_val
            expected_energy = float(weighted_energy)

        # Track best found parameters
        if expected_energy < self._best_energy:
            self._best_energy = expected_energy
            self._best_gamma = list(gamma)
            self._best_beta = list(beta)

        # Record convergence trace
        point = QuantumConvergencePoint(
            iteration=self._eval_count,
            expected_energy=round(expected_energy, 6),
            best_expected_energy=round(self._best_energy, 6),
            gamma=[round(g, 6) for g in gamma],
            beta=[round(b, 6) for b in beta],
            eval_count=self._eval_count,
            timestamp_offset=round(self.context.elapsed_seconds, 4),
        )
        self._convergence_history.append(point)

        return expected_energy

    def optimize(self) -> QAOAOptimizationResult:
        """Runs the classical optimization loop to minimize expected QAOA energy."""
        init_gamma, init_beta = self.get_initial_parameters()
        x0 = np.array(init_gamma + init_beta, dtype=float)
        p = self.p_depth

        initial_energy = 0.0
        termination_reason = "Optimization completed successfully."
        try:
            # Initial baseline evaluation
            initial_energy = self.evaluate_expectation(init_gamma, init_beta)

            def objective(x: np.ndarray) -> float:
                gamma = list(x[:p])
                beta = list(x[p:])
                return self.evaluate_expectation(gamma, beta)

            optimizer_method = self.config.optimizer.value
            options: Dict[str, Any] = {
                "maxiter": self.config.max_iterations,
            }
            if self.config.optimizer_tol is not None:
                if optimizer_method in ["COBYLA"]:
                    options["tol"] = self.config.optimizer_tol
                elif optimizer_method in ["SLSQP", "Nelder-Mead"]:
                    options["xatol"] = self.config.optimizer_tol
                    options["fatol"] = self.config.optimizer_tol

            # Parameter bounds: gamma in [-2pi, 2pi], beta in [-pi, pi]
            bounds = [(-2.0 * math.pi, 2.0 * math.pi)] * p + [(-math.pi, math.pi)] * p

            if optimizer_method == "COBYLA":
                # COBYLA handles non-linear constraints; bounds can be represented as constraints or unconstrained
                res = opt.minimize(
                    objective,
                    x0,
                    method="COBYLA",
                    options=options,
                )
            elif optimizer_method in ["SLSQP", "L-BFGS-B"]:
                res = opt.minimize(
                    objective,
                    x0,
                    method=optimizer_method,
                    bounds=bounds,
                    options=options,
                )
            else:
                # Nelder-Mead
                res = opt.minimize(
                    objective,
                    x0,
                    method="Nelder-Mead",
                    bounds=bounds,
                    options=options,
                )
            
            termination_reason = str(getattr(res, "message", "Optimizer terminated normally."))
            self._iteration_count = int(getattr(res, "nit", self._eval_count))
        except (ExecutionTimeoutError, CancellationError) as exc:
            termination_reason = str(exc)
        except Exception as exc:
            termination_reason = f"Optimizer exception: {str(exc)}"

        return QAOAOptimizationResult(
            optimal_gamma=self._best_gamma or init_gamma,
            optimal_beta=self._best_beta or init_beta,
            best_expected_energy=round(self._best_energy, 6),
            initial_expected_energy=round(initial_energy, 6),
            total_evaluations=self._eval_count,
            iterations=self._iteration_count or self._eval_count,
            convergence_history=self._convergence_history,
            termination_reason=termination_reason,
            evaluation_mode=self.config.simulation_mode.value,
            optimizer_name=self.config.optimizer.value,
        )
