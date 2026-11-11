"""Tests for Stage 8.5 — Advanced Algorithm Comparison and Research Analytics."""

import pytest
from backend.app.experiments.analytics import (
    AlgorithmComparisonEngine,
    AlgorithmPerformanceSummary,
    RuntimeDecomposition,
    ScalabilityDataPoint,
)
from backend.app.experiments.models import (
    Experiment,
    ExperimentAlgorithm,
    ExperimentConfiguration,
    ExperimentResult,
    ExperimentStatus,
)
from backend.app.experiments.registry import experiment_registry


class TestAlgorithmComparisonEngine:
    def setup_method(self):
        self.engine = AlgorithmComparisonEngine()

    def test_analyze_results_basic(self):
        results = [
            ExperimentResult(
                algorithm="simulated_annealing",
                trial_index=0,
                objective_value=12.0,
                runtime_seconds=0.05,
                is_feasible=True,
                num_evaluations=100,
                status="completed",
                convergence_history=[5.0, 8.0, 12.0],
            ),
            ExperimentResult(
                algorithm="simulated_annealing",
                trial_index=1,
                objective_value=14.0,
                runtime_seconds=0.07,
                is_feasible=True,
                num_evaluations=120,
                status="completed",
                convergence_history=[6.0, 10.0, 14.0],
            ),
            ExperimentResult(
                algorithm="exact",
                trial_index=0,
                objective_value=15.0,
                runtime_seconds=0.01,
                is_feasible=True,
                num_evaluations=16,
                status="completed",
            ),
        ]
        resp = self.engine.analyze_results(
            results=results,
            problem_type="max_cut",
            problem_instance={"num_nodes": 4},
            optimal_value=15.0,
            objective_direction="max",
        )
        assert len(resp.algorithm_summaries) == 2
        sa_sum = next(s for s in resp.algorithm_summaries if s.algorithm == "simulated_annealing")
        assert sa_sum.best_objective == 14.0
        assert sa_sum.mean_objective == 13.0
        assert sa_sum.feasibility_rate == 1.0

        # Check convergence profile
        assert "simulated_annealing" in resp.convergence_profiles
        assert len(resp.convergence_profiles["simulated_annealing"]) == 3

    def test_runtime_decomposition_custom_metrics(self):
        results = [
            ExperimentResult(
                algorithm="qaoa",
                trial_index=0,
                objective_value=10.0,
                runtime_seconds=1.0,
                is_feasible=True,
                num_evaluations=50,
                status="completed",
                algorithm_metrics={
                    "circuit_construction_time": 0.1,
                    "transpilation_time": 0.2,
                    "optimization_time": 0.5,
                    "execution_time": 0.15,
                    "decoding_time": 0.05,
                },
            )
        ]
        resp = self.engine.analyze_results(
            results=results,
            problem_type="max_cut",
            problem_instance={"num_nodes": 4},
        )
        decomp = resp.runtime_breakdowns["qaoa"]
        assert decomp.circuit_construction_seconds == 0.1
        assert decomp.transpilation_seconds == 0.2
        assert decomp.parameter_optimization_seconds == 0.5
        assert decomp.quantum_execution_seconds == 0.15
        assert decomp.solution_decoding_seconds == 0.05

    def test_analyze_experiment_from_registry(self):
        exp = Experiment(
            experiment_id="test-exp-analytics-1",
            name="Analytics Test Experiment",
            configuration=ExperimentConfiguration(
                problem_type="max_cut",
                problem_instance={"num_nodes": 4},
                algorithms=[ExperimentAlgorithm.SIMULATED_ANNEALING],
                num_trials=1,
            ),
            status=ExperimentStatus.COMPLETED,
            results=[
                ExperimentResult(
                    algorithm="simulated_annealing",
                    trial_index=0,
                    objective_value=8.0,
                    runtime_seconds=0.02,
                    is_feasible=True,
                    num_evaluations=50,
                    status="completed",
                )
            ],
        )
        experiment_registry.save(exp)

        resp = self.engine.analyze_experiment("test-exp-analytics-1")
        assert resp.experiment_id == "test-exp-analytics-1"
        assert len(resp.algorithm_summaries) == 1
        assert resp.algorithm_summaries[0].best_objective == 8.0

    def test_compute_scalability_series(self):
        exp1 = Experiment(
            experiment_id="exp-scale-4",
            name="Size 4",
            configuration=ExperimentConfiguration(
                problem_type="max_cut",
                problem_instance={"num_nodes": 4},
                algorithms=[ExperimentAlgorithm.SIMULATED_ANNEALING],
            ),
            results=[
                ExperimentResult(
                    algorithm="simulated_annealing",
                    trial_index=0,
                    objective_value=6.0,
                    runtime_seconds=0.01,
                    is_feasible=True,
                    status="completed",
                )
            ],
        )
        exp2 = Experiment(
            experiment_id="exp-scale-8",
            name="Size 8",
            configuration=ExperimentConfiguration(
                problem_type="max_cut",
                problem_instance={"num_nodes": 8},
                algorithms=[ExperimentAlgorithm.SIMULATED_ANNEALING],
            ),
            results=[
                ExperimentResult(
                    algorithm="simulated_annealing",
                    trial_index=0,
                    objective_value=14.0,
                    runtime_seconds=0.05,
                    is_feasible=True,
                    status="completed",
                )
            ],
        )
        series = self.engine.compute_scalability_series([exp1, exp2])
        assert len(series) == 2
        assert series[0].problem_size == 4
        assert series[1].problem_size == 8
        assert series[1].mean_runtime_seconds > series[0].mean_runtime_seconds
