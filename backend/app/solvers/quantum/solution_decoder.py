"""Decoding quantum measurement bitstrings into canonical optimization solutions with independent verification."""

from typing import Dict, Any, List, Tuple, Optional, Union
import logging

from backend.app.domain.problems.models import ProblemType
from backend.app.domain.formulations.models import QuboModel
from backend.app.evaluation.max_cut_evaluator import MaxCutEvaluator
from backend.app.evaluation.assignment_evaluator import AssignmentEvaluator
from backend.app.evaluation.tsp_evaluator import TSPEvaluator
from backend.app.evaluation.constraints import ConstraintValidator
from backend.app.formulations.qubo_builder import QuboBuilder
from backend.app.formulations.ising_converter import IsingConverter
from backend.app.solvers.quantum.hamiltonians import QAOACostHamiltonian
from backend.app.solvers.quantum.models import (
    QuantumSamplingResult,
    DecodedSample,
    QAOADecodingSummary,
)

logger = logging.getLogger(__name__)


class QAOASolutionDecoder:
    """
    Dedicated decoding and evaluation layer:
      1. Translates little-endian Qiskit bitstrings to problem variable assignments.
      2. Reconstructs domain-specific problem solutions (partitions, assignment pairs, tours).
      3. Validates constraints with Phase 2 ConstraintValidator.
      4. Evaluates solution truth via Phase 2 independent objective evaluators.
      5. Evaluates QUBO and Ising energies for mathematical cross-verification.
      6. Selects best feasible solutions using true problem direction (maximization vs minimization).
    """

    def __init__(
        self,
        problem_type: Union[ProblemType, str],
        problem_instance: Dict[str, Any],
        qubo_model: QuboModel,
        cost_hamiltonian: Optional[QAOACostHamiltonian] = None,
    ):
        if isinstance(problem_type, ProblemType):
            self.problem_type = problem_type.value
        else:
            self.problem_type = str(problem_type).lower()

        self.problem_instance = problem_instance
        self.qubo_model = qubo_model
        self.cost_hamiltonian = cost_hamiltonian or QAOACostHamiltonian.from_qubo(qubo_model)
        self.num_variables = len(qubo_model.variable_order)

        # Instantiate appropriate Phase 2 independent evaluator
        if self.problem_type in ["max_cut", "maxcut"]:
            self.evaluator = MaxCutEvaluator()
            self.is_maximization = True
        elif self.problem_type in ["assignment", "linear_assignment"]:
            self.evaluator = AssignmentEvaluator()
            self.is_maximization = False
        elif self.problem_type in ["tsp", "traveling_salesperson"]:
            self.evaluator = TSPEvaluator()
            self.is_maximization = False
        else:
            raise ValueError(f"Unsupported problem type for QAOA decoding: '{problem_type}'")

        # Cache evaluation builder for fast QUBO energy computation
        self._eval_builder = QuboBuilder(qubo_model.variable_order)
        for v, val in qubo_model.linear_terms.items():
            self._eval_builder.add_linear(v, val)
        for pair, val in qubo_model.quadratic_terms.items():
            v1, v2 = pair.split(",")
            self._eval_builder.add_quadratic(v1, v2, val)
        self._eval_builder.add_offset(qubo_model.offset)

    def bitstring_to_variable_assignment(self, bitstring: str) -> Dict[str, int]:
        """
        Converts a Qiskit little-endian measurement bitstring into a named variable assignment dict.
        
        Qiskit bitstring convention:
          bitstring[0] corresponds to qubit (num_qubits - 1).
          bitstring[num_qubits - 1 - q] corresponds to qubit q.
        """
        clean_bits = bitstring.strip().replace(" ", "")
        n = self.num_variables
        if len(clean_bits) != n:
            raise ValueError(
                f"Bitstring length ({len(clean_bits)}) does not match variable count ({n})."
            )

        var_assignment: Dict[str, int] = {}
        for var_name in self.qubo_model.variable_order:
            q_idx = self.cost_hamiltonian.var_to_qubit.get(var_name, None)
            if q_idx is None:
                q_idx = self.cost_hamiltonian.spin_to_qubit.get(f"Z_{var_name}", 0)
            
            # Map bitstring position to qubit index
            bit_val = int(clean_bits[n - 1 - q_idx])
            var_assignment[var_name] = bit_val

        return var_assignment

    def decode_candidate(self, var_assignment: Dict[str, int]) -> Any:
        """Transforms a binary variable assignment into domain-specific solution format."""
        if self.problem_type in ["max_cut", "maxcut"]:
            nodes = self.problem_instance.get("nodes", [])
            return {node: var_assignment.get(node, 0) for node in nodes}

        elif self.problem_type in ["assignment", "linear_assignment"]:
            agents = self.problem_instance.get("agents", [])
            tasks = self.problem_instance.get("tasks", [])
            pairs: List[Tuple[str, str]] = []
            for agent in agents:
                for task in tasks:
                    var_name = f"x_{agent}_{task}"
                    if var_assignment.get(var_name, 0) == 1:
                        pairs.append((agent, task))
            return pairs

        elif self.problem_type in ["tsp", "traveling_salesperson"]:
            cities = self.problem_instance.get("cities", [])
            n_cities = len(cities)
            steps: Dict[int, List[str]] = {}
            for city in cities:
                for p in range(n_cities):
                    var_name = f"x_{city}_{p}"
                    if var_assignment.get(var_name, 0) == 1:
                        steps.setdefault(p, []).append(city)

            # Reconstruct ordered sequence
            tour: List[Optional[str]] = []
            is_valid_structure = True
            for p in range(n_cities):
                visited_at_step = steps.get(p, [])
                if len(visited_at_step) == 1:
                    tour.append(visited_at_step[0])
                else:
                    is_valid_structure = False
                    tour.append(visited_at_step[0] if visited_at_step else None)

            # If properly structured and has valid start, close cycle
            if is_valid_structure and None not in tour and len(tour) == n_cities:
                tour.append(tour[0])
            return tour

        return var_assignment

    def evaluate_sample(
        self,
        bitstring: str,
        frequency_count: int,
        total_shots: int,
    ) -> DecodedSample:
        """Decodes, validates, and independently evaluates a single unique quantum measurement outcome."""
        var_assignment = self.bitstring_to_variable_assignment(bitstring)
        candidate = self.decode_candidate(var_assignment)
        prob = frequency_count / total_shots if total_shots > 0 else 0.0

        # Independent feasibility check
        is_feasible, violations = self.evaluator.check_feasibility(self.problem_instance, candidate)
        violation_messages = [v.message for v in violations]

        # Independent objective evaluation
        obj_value = 0.0
        try:
            obj_value = float(self.evaluator.evaluate_objective(self.problem_instance, candidate))
        except Exception as exc:
            violation_messages.append(f"Objective evaluation error: {str(exc)}")
            is_feasible = False

        # Energy cross-verification
        x_vec = [var_assignment[v] for v in self.qubo_model.variable_order]
        qubo_energy = float(self._eval_builder.evaluate_energy(x_vec))
        
        spins = IsingConverter.binary_to_spin(x_vec)
        ising_energy = float(self.cost_hamiltonian.evaluate_spins_energy(spins))

        return DecodedSample(
            bitstring=bitstring,
            frequency_count=frequency_count,
            probability=round(prob, 6),
            candidate_solution=candidate,
            is_feasible=is_feasible,
            objective_value=round(obj_value, 6),
            constraint_violations=violation_messages,
            qubo_energy=round(qubo_energy, 6),
            ising_energy=round(ising_energy, 6),
            is_repaired=False,
            raw_candidate_solution=candidate,
        )

    def decode_and_evaluate_sampling_result(
        self,
        sampling_result: QuantumSamplingResult,
    ) -> QAOADecodingSummary:
        """Decodes and independently evaluates all unique measured bitstrings from a sampling run."""
        total_shots = sampling_result.shots
        all_samples: List[DecodedSample] = []
        feasible_samples: List[DecodedSample] = []
        infeasible_samples: List[DecodedSample] = []
        feasible_shot_count = 0

        for bitstring, count in sampling_result.counts.items():
            sample = self.evaluate_sample(bitstring, count, total_shots)
            all_samples.append(sample)
            if sample.is_feasible:
                feasible_samples.append(sample)
                feasible_shot_count += count
            else:
                infeasible_samples.append(sample)

        # Most frequently measured sample
        most_freq_sample = next(
            (s for s in all_samples if s.bitstring == sampling_result.most_frequent_bitstring),
            all_samples[0] if all_samples else None
        )

        # Select best feasible sample using TRUE optimization sense
        best_feasible = None
        if feasible_samples:
            if self.is_maximization:
                # Maximize objective (e.g. Max-Cut)
                best_feasible = max(feasible_samples, key=lambda s: s.objective_value)
            else:
                # Minimize objective (e.g. Assignment, TSP)
                best_feasible = min(feasible_samples, key=lambda s: s.objective_value)

        # Select best infeasible sample (for diagnostics)
        best_infeasible = None
        if infeasible_samples:
            if self.is_maximization:
                best_infeasible = max(infeasible_samples, key=lambda s: s.objective_value)
            else:
                best_infeasible = min(infeasible_samples, key=lambda s: s.objective_value)

        # Sort all samples by probability descending
        all_samples.sort(key=lambda s: s.frequency_count, reverse=True)

        feasible_rate = (feasible_shot_count / total_shots) if total_shots > 0 else 0.0

        return QAOADecodingSummary(
            total_samples=total_shots,
            unique_samples=len(all_samples),
            feasible_samples=feasible_shot_count,
            infeasible_samples=total_shots - feasible_shot_count,
            feasible_rate=round(feasible_rate, 4),
            best_feasible_solution=best_feasible,
            best_infeasible_solution=best_infeasible,
            most_frequent_solution=most_freq_sample,
            all_decoded_samples=all_samples,
        )
