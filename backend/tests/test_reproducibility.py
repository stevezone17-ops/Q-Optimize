"""Tests for Stage 8.9 — Experiment Reproducibility, Research Validation, and Reliability."""

import pytest
from backend.app.experiments.models import (
    Experiment,
    ExperimentAlgorithm,
    ExperimentConfiguration,
    ExperimentResult,
    ExperimentStatus,
)
from backend.app.experiments.registry import experiment_registry
from backend.app.experiments.reproducibility import reproducibility_manager
from backend.app.experiments.validators import benchmark_validator


@pytest.fixture
def executed_experiment():
    instance = {
        "nodes": ["0", "1", "2", "3"],
        "edges": [["0", "1", 1.0], ["1", "2", 1.0], ["2", "3", 1.0]],
        "num_nodes": 4,
        "edge_list": [[0, 1], [1, 2], [2, 3]],
    }
    exp = Experiment(
        experiment_id="exp-repro-test-1",
        name="Reproducibility Test Benchmark",
        configuration=ExperimentConfiguration(
            problem_type="max_cut",
            problem_instance=instance,
            algorithms=[ExperimentAlgorithm.EXACT],
            num_trials=1,
            seeds=[42],
        ),
        status=ExperimentStatus.COMPLETED,
        results=[
            ExperimentResult(
                algorithm="exact",
                trial_index=0,
                seed=42,
                objective_value=3.0,
                runtime_seconds=0.005,
                is_feasible=True,
                num_evaluations=8,
                status="completed",
            )
        ],
    )
    experiment_registry.save(exp)
    return exp


class TestReproducibilityAndValidation:
    def test_replay_experiment_reproduces_exact_optimum(self, executed_experiment):
        replayed = reproducibility_manager.replay_experiment(
            executed_experiment.experiment_id, preserve_seeds=True
        )
        assert replayed.experiment_id != executed_experiment.experiment_id
        assert replayed.status == ExperimentStatus.COMPLETED
        assert len(replayed.results) == 1
        assert replayed.results[0].objective_value == 3.0

        comparison = reproducibility_manager.verify_reproducibility(
            executed_experiment.experiment_id, replayed.experiment_id
        )
        assert comparison.is_exact_match is True
        assert comparison.relative_difference_pct == 0.0

    def test_validator_detects_clean_experiment(self, executed_experiment):
        report = benchmark_validator.validate_experiment(executed_experiment)
        assert report.is_valid is True
        assert report.num_issues == 0
        assert len(report.outliers_detected) == 0

    def test_validator_detects_missing_trials(self):
        exp = Experiment(
            experiment_id="exp-missing-trials",
            name="Missing Trials Benchmark",
            configuration=ExperimentConfiguration(
                problem_type="max_cut",
                problem_instance={"num_nodes": 4, "edge_list": [[0, 1]]},
                algorithms=[ExperimentAlgorithm.EXACT, ExperimentAlgorithm.SIMULATED_ANNEALING],
                num_trials=2,
            ),
            status=ExperimentStatus.COMPLETED,
            results=[
                ExperimentResult(
                    algorithm="exact",
                    trial_index=0,
                    objective_value=1.0,
                    runtime_seconds=0.01,
                    is_feasible=True,
                    status="completed",
                )
            ],  # Only 1 of 4 expected
        )
        report = benchmark_validator.validate_experiment(exp)
        codes = [i.code for i in report.issues]
        assert "MISSING_TRIALS" in codes

    def test_validator_flags_statistical_outlier(self):
        # 4 trials with normal values (10, 10, 10) and one extreme outlier (100)
        exp = Experiment(
            experiment_id="exp-outlier-test",
            name="Outlier Benchmark",
            configuration=ExperimentConfiguration(
                problem_type="max_cut",
                problem_instance={"num_nodes": 4, "edge_list": [[0, 1]]},
                algorithms=[ExperimentAlgorithm.SIMULATED_ANNEALING],
                num_trials=5,
            ),
            status=ExperimentStatus.COMPLETED,
            results=[
                ExperimentResult(algorithm="simulated_annealing", trial_index=0, objective_value=10.0, status="completed", is_feasible=True),
                ExperimentResult(algorithm="simulated_annealing", trial_index=1, objective_value=10.5, status="completed", is_feasible=True),
                ExperimentResult(algorithm="simulated_annealing", trial_index=2, objective_value=9.5, status="completed", is_feasible=True),
                ExperimentResult(algorithm="simulated_annealing", trial_index=3, objective_value=10.0, status="completed", is_feasible=True),
                ExperimentResult(algorithm="simulated_annealing", trial_index=4, objective_value=100.0, status="completed", is_feasible=True),
            ],
        )
        report = benchmark_validator.validate_experiment(exp)
        assert len(report.outliers_detected) >= 1
        assert report.outliers_detected[0]["value"] == 100.0

    def test_validator_detects_duplicate_trials(self):
        exp = Experiment(
            experiment_id="exp-duplicate-trials",
            name="Duplicate Trials",
            configuration=ExperimentConfiguration(
                problem_type="max_cut",
                problem_instance={"num_nodes": 4, "edge_list": [[0, 1]]},
                algorithms=[ExperimentAlgorithm.EXACT],
                num_trials=1,
            ),
            status=ExperimentStatus.COMPLETED,
            results=[
                ExperimentResult(algorithm="exact", trial_index=0, objective_value=1.0, status="completed", is_feasible=True),
                ExperimentResult(algorithm="exact", trial_index=0, objective_value=1.0, status="completed", is_feasible=True),
            ],
        )
        report = benchmark_validator.validate_experiment(exp)
        assert report.is_valid is False
        codes = [i.code for i in report.issues]
        assert "DUPLICATE_TRIAL" in codes
