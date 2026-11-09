"""Unit tests for Stage 7.3: Experiment Dataset Construction and Training Pipeline."""

import pytest
import numpy as np

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import ExperimentRecord
from backend.app.ai.dataset_builder import SolverSelectionPolicy, ExperimentDatasetBuilder
from backend.app.ai.training_pipeline import ModelTrainingPipeline
from backend.app.ai.exceptions import InsufficientDataError, DataQualityError


def test_solver_selection_policy_maximization():
    """Verify policy prefers highest feasible objective for Max-Cut."""
    runs = [
        ExperimentRecord(
            record_id="r1",
            provenance_collection="executions",
            problem_type=ProblemType.MAX_CUT,
            solver_name="simulated_annealing",
            status="COMPLETED",
            is_feasible=True,
            objective_value=12.0,
            runtime_seconds=0.05,
        ),
        ExperimentRecord(
            record_id="r2",
            provenance_collection="executions",
            problem_type=ProblemType.MAX_CUT,
            solver_name="genetic_algorithm",
            status="COMPLETED",
            is_feasible=True,
            objective_value=14.0,  # Best objective
            runtime_seconds=0.10,
        ),
        ExperimentRecord(
            record_id="r3",
            provenance_collection="executions",
            problem_type=ProblemType.MAX_CUT,
            solver_name="standard_qaoa",
            status="COMPLETED",
            is_feasible=False,  # Infeasible
            objective_value=18.0,
            runtime_seconds=0.08,
        ),
    ]

    best = SolverSelectionPolicy.select_best_solver(ProblemType.MAX_CUT, runs)
    assert best == "genetic_algorithm"


def test_solver_selection_policy_minimization():
    """Verify policy prefers lowest feasible objective for Assignment/TSP."""
    runs = [
        ExperimentRecord(
            record_id="r1",
            provenance_collection="executions",
            problem_type=ProblemType.TSP,
            solver_name="simulated_annealing",
            status="COMPLETED",
            is_feasible=True,
            objective_value=42.0,  # Best route length
            runtime_seconds=0.04,
        ),
        ExperimentRecord(
            record_id="r2",
            provenance_collection="executions",
            problem_type=ProblemType.TSP,
            solver_name="genetic_algorithm",
            status="COMPLETED",
            is_feasible=True,
            objective_value=55.0,
            runtime_seconds=0.08,
        ),
    ]

    best = SolverSelectionPolicy.select_best_solver(ProblemType.TSP, runs)
    assert best == "simulated_annealing"


def test_solver_selection_policy_exact_preference_and_tiebreak():
    """Verify Exact solver is preferred when within top tier, and runtime tie-breaker."""
    runs = [
        ExperimentRecord(
            record_id="r1",
            provenance_collection="executions",
            problem_type=ProblemType.MAX_CUT,
            solver_name="exact",
            status="COMPLETED",
            is_feasible=True,
            objective_value=10.0,
            runtime_seconds=0.002,
        ),
        ExperimentRecord(
            record_id="r2",
            provenance_collection="executions",
            problem_type=ProblemType.MAX_CUT,
            solver_name="simulated_annealing",
            status="COMPLETED",
            is_feasible=True,
            objective_value=10.0,
            runtime_seconds=0.015,
        ),
    ]

    best = SolverSelectionPolicy.select_best_solver(ProblemType.MAX_CUT, runs)
    assert best == "exact"


def test_experiment_dataset_builder_aggregation():
    """Verify ExperimentDatasetBuilder groups multiple solver runs by instance."""
    inst_data = {"nodes": ["A", "B", "C"], "edges": [["A", "B", 1.0], ["B", "C", 2.0]]}
    records = [
        ExperimentRecord(
            record_id="run_1",
            provenance_collection="executions",
            problem_id="prob_alpha",
            problem_type=ProblemType.MAX_CUT,
            instance_data=inst_data,
            solver_name="exact",
            status="COMPLETED",
            is_feasible=True,
            objective_value=3.0,
            runtime_seconds=0.001,
        ),
        ExperimentRecord(
            record_id="run_2",
            provenance_collection="executions",
            problem_id="prob_alpha",  # Same instance
            problem_type=ProblemType.MAX_CUT,
            instance_data=inst_data,
            solver_name="genetic_algorithm",
            status="COMPLETED",
            is_feasible=True,
            objective_value=3.0,
            runtime_seconds=0.02,
        ),
    ]

    samples, meta = ExperimentDatasetBuilder.build_dataset(records, dataset_version="v1.0.0")

    assert len(samples) == 1
    assert samples[0].best_solver_label == "exact"
    assert "exact" in samples[0].solver_evaluations
    assert "genetic_algorithm" in samples[0].solver_evaluations
    assert meta.total_samples == 1
    assert meta.class_distribution == {"exact": 1}


def test_sample_test_dataset_generation():
    """Verify sample test dataset generator produces valid, isolated test data."""
    samples, meta = ExperimentDatasetBuilder.create_sample_test_dataset()

    assert len(samples) == 20
    assert meta.total_samples == 20
    assert meta.provenance_summary == "ISOLATED_TEST_DATASET_FOR_UNIT_TESTS_ONLY"
    assert len(meta.class_distribution) >= 3


def test_group_aware_train_test_split():
    """Verify group-aware splitting guarantees zero instance leakage between train and test."""
    samples, _ = ExperimentDatasetBuilder.create_sample_test_dataset()

    X, y, groups = ModelTrainingPipeline.prepare_data_matrices(samples)

    X_train, X_test, y_train, y_test = ModelTrainingPipeline.split_group_aware(
        X, y, groups, test_size=0.3, random_state=42
    )

    assert len(X_train) + len(X_test) == len(samples)
    assert len(y_train) + len(y_test) == len(samples)


def test_insufficient_training_data_raises():
    """Verify InsufficientDataError is raised when sample size is below safety limit."""
    small_samples, _ = ExperimentDatasetBuilder.create_sample_test_dataset()
    small_samples = small_samples[:5]  # Only 5 samples, below threshold 15

    with pytest.raises(InsufficientDataError):
        ModelTrainingPipeline.prepare_data_matrices(small_samples)


def test_compute_evaluation_metrics():
    """Verify classification metrics and confusion matrix calculations."""
    y_true = np.array(["exact", "genetic_algorithm", "exact", "simulated_annealing"])
    y_pred = np.array(["exact", "genetic_algorithm", "simulated_annealing", "simulated_annealing"])

    metrics = ModelTrainingPipeline.compute_evaluation_metrics(y_true, y_pred)

    assert metrics["accuracy"] == 0.75  # 3 of 4 correct
    assert "confusion_matrix" in metrics
    assert metrics["confusion_matrix"]["exact"]["exact"] == 1
    assert metrics["confusion_matrix"]["exact"]["simulated_annealing"] == 1

