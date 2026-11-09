"""Unit tests for Stage 7.5: Solver Recommendation Evaluation and Explainability."""

import pytest
import numpy as np

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import (
    OptimizationFeatures,
    RankedSolverAlternative,
    TrainingSample,
    RecommendationSource,
)
from backend.app.ai.recommender import MLSolverRecommenderModel
from backend.app.ai.evaluation import SolverRecommendationEvaluator
from backend.app.ai.explainability import ExplainabilityEngine
from backend.app.ai.dataset_builder import ExperimentDatasetBuilder
from backend.app.ai.training_pipeline import ModelTrainingPipeline


def test_solver_recommendation_evaluator_metrics():
    """Verify evaluator accurately calculates classification and regret metrics."""
    samples, _ = ExperimentDatasetBuilder.create_sample_test_dataset()
    X, y, groups = ModelTrainingPipeline.prepare_data_matrices(samples)

    # Train model on first 15, evaluate on remaining 5
    model = MLSolverRecommenderModel(model_id="eval_test_rf")
    model.train(
        X=X[:15].tolist(),
        y=y[:15].tolist(),
        feature_names=ModelTrainingPipeline.FEATURE_NAMES,
        target_classes=ModelTrainingPipeline.TARGET_CLASSES,
    )

    evaluator = SolverRecommendationEvaluator()
    res = evaluator.evaluate_samples(model, samples[15:])

    assert res.sample_count == len(samples[15:])
    assert 0.0 <= res.accuracy <= 1.0
    assert 0.0 <= res.macro_f1 <= 1.0
    assert 0.0 <= res.top_2_accuracy <= 1.0
    assert res.recommendation_coverage == 1.0
    assert res.mean_runtime_regret_ms >= 0.0
    assert res.mean_objective_regret_percent >= 0.0
    assert isinstance(res.confusion_matrix, dict)


def test_explainability_engine_textual_rationale():
    """Verify explanation generation identifies top features and uncertainty."""
    features = OptimizationFeatures(
        problem_type=ProblemType.MAX_CUT,
        num_variables=12,
        num_vertices=12,
        graph_density=0.75,
        estimated_search_space_log2=12.0,
    )

    alts = [
        RankedSolverAlternative(solver_name="exact", score=0.55, rank=1, reason="fast"),
        RankedSolverAlternative(solver_name="adaptive_qaoa", score=0.48, rank=2, reason="good"),
    ]

    importances = {"graph_density": 0.45, "num_variables": 0.35, "coeff_mean": 0.10}

    explanation = ExplainabilityEngine.generate_recommendation_explanation(
        features=features,
        recommended_solver="exact",
        ranked_alternatives=alts,
        feature_importances=importances,
    )

    assert "exact" in explanation.lower()
    assert "graph_density" in explanation
    # Delta score is 0.55 - 0.48 = 0.07 < 0.10, so uncertainty note should be triggered
    assert "Prediction is competitive" in explanation


def test_confidence_calibration_brier_score():
    """Verify Brier score calibration assessment."""
    # Well-calibrated probabilities
    probs_good = [0.9, 0.8, 0.1, 0.2]
    outcomes_good = [1, 1, 0, 0]
    brier_good, is_calib_good = ExplainabilityEngine.check_confidence_calibration(probs_good, outcomes_good)
    assert brier_good < 0.10
    assert is_calib_good is True

    # Poorly-calibrated overconfident probabilities
    probs_bad = [0.95, 0.95, 0.05, 0.05]
    outcomes_bad = [0, 0, 1, 1]  # Complete inversion
    brier_bad, is_calib_bad = ExplainabilityEngine.check_confidence_calibration(probs_bad, outcomes_bad)
    assert brier_bad > 0.80
    assert is_calib_bad is False


def test_out_of_distribution_detection():
    """Verify OOD detection flags instances with extreme dimensionality or coefficient values."""
    # Standard normal instance -> In-Distribution
    normal_features = OptimizationFeatures(
        problem_type=ProblemType.MAX_CUT,
        num_variables=8,
        num_vertices=8,
        graph_density=0.5,
        estimated_search_space_log2=8.0,
        coeff_min=1.0,
        coeff_max=10.0,
        coeff_mean=5.0,
        coeff_std=2.0,
        coeff_range=9.0,
    )
    is_ood_norm, max_z_norm, _ = ExplainabilityEngine.detect_out_of_distribution(normal_features)
    assert is_ood_norm is False
    assert max_z_norm < 3.5

    # Extreme instance (e.g. 500 variables, search space 500) -> Out-of-Distribution
    extreme_features = OptimizationFeatures(
        problem_type=ProblemType.MAX_CUT,
        num_variables=500,
        num_vertices=500,
        graph_density=0.9,
        estimated_search_space_log2=500.0,
        coeff_min=1000.0,
        coeff_max=50000.0,
        coeff_mean=25000.0,
        coeff_std=12000.0,
        coeff_range=49000.0,
    )
    is_ood_ext, max_z_ext, divergent = ExplainabilityEngine.detect_out_of_distribution(extreme_features)
    assert is_ood_ext is True
    assert max_z_ext > 3.5
    assert len(divergent) >= 1

