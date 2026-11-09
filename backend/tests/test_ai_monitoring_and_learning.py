"""Unit and integration tests for Stage 7.9: Model Monitoring, Feedback, and Continuous Learning."""

import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import (
    RecommendationFeedback,
    RecommendationSource,
    OptimizationFeatures,
)
from backend.app.ai.monitoring import ModelMonitor, FEEDBACK_COLLECTION, AUDIT_COLLECTION
from backend.app.ai.continuous_learning import ContinuousLearningPipeline
from backend.app.ai.registry import MLModelRegistry
from backend.app.ai.recommender import MLSolverRecommenderModel
from backend.app.db.mongodb import db_manager


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.asyncio
async def test_record_feedback_and_compute_metrics():
    """Verify feedback recording, audit logging, and aggregate monitoring metrics computation."""
    # Ensure memory store is clean for feedback
    db_manager._memory_store.pop(FEEDBACK_COLLECTION, None)
    db_manager._memory_store.pop(AUDIT_COLLECTION, None)

    # 1. Log two recommendation audits
    from backend.app.ai.models import SolverRecommendation
    rec1 = SolverRecommendation(
        problem_id="prob_test_1",
        problem_type=ProblemType.MAX_CUT,
        recommended_solver="exact",
        confidence_score=0.95,
        is_confidence_calibrated=True,
        recommendation_source=RecommendationSource.RULE_BASED,
        ranked_alternatives=[],
        explanation="Test explanation",
        key_features_summary={"num_variables": 4, "estimated_search_space_log2": 4.0},
    )
    rec2 = SolverRecommendation(
        problem_id="prob_test_2",
        problem_type=ProblemType.MAX_CUT,
        recommended_solver="simulated_annealing",
        confidence_score=0.85,
        is_confidence_calibrated=True,
        recommendation_source=RecommendationSource.ML_MODEL,
        ranked_alternatives=[],
        explanation="Test explanation 2",
        key_features_summary={"num_variables": 20, "estimated_search_space_log2": 20.0},
    )
    await ModelMonitor.log_recommendation(rec1)
    await ModelMonitor.log_recommendation(rec2)

    # 2. Record 2 feedback items: 1 accepted & feasible, 1 overridden & feasible
    fb1 = RecommendationFeedback(
        feedback_id="fb_1",
        problem_id="prob_test_1",
        problem_type=ProblemType.MAX_CUT,
        recommended_solver="exact",
        user_selected_solver="exact",
        was_accepted=True,
        recommendation_source=RecommendationSource.RULE_BASED,
        realized_is_feasible=True,
        realized_runtime_seconds=0.01,
    )
    fb2 = RecommendationFeedback(
        feedback_id="fb_2",
        problem_id="prob_test_2",
        problem_type=ProblemType.MAX_CUT,
        recommended_solver="simulated_annealing",
        user_selected_solver="genetic_algorithm",
        was_accepted=False,
        recommendation_source=RecommendationSource.ML_MODEL,
        realized_is_feasible=True,
        realized_runtime_seconds=0.25,
    )

    await ModelMonitor.record_feedback(fb1)
    await ModelMonitor.record_feedback(fb2)

    # 3. Compute metrics
    metrics = await ModelMonitor.compute_monitoring_metrics()
    assert metrics.total_recommendations >= 2
    assert metrics.total_feedback_count >= 2
    assert metrics.acceptance_rate == pytest.approx(0.5, rel=1e-2)
    assert metrics.realized_feasibility_rate == pytest.approx(1.0, rel=1e-2)
    assert "exact" in metrics.prediction_distribution
    assert "simulated_annealing" in metrics.prediction_distribution
    assert metrics.average_confidence > 0.8


def test_detect_feature_drift():
    """Verify KS-statistic data drift detection on normal vs shifted distributions."""
    # 1. Normal recommendations aligned with baseline
    normal_recs = [
        {"key_features_summary": {"num_variables": v, "estimated_search_space_log2": v}}
        for v in [4, 6, 8, 10, 12, 14, 16]
    ]
    drift_norm, details_norm = ModelMonitor.detect_data_drift(normal_recs)
    assert drift_norm is False

    # 2. Heavily shifted distribution (e.g. huge instances v=200..300)
    shifted_recs = [
        {"key_features_summary": {"num_variables": v, "estimated_search_space_log2": v * 1.5}}
        for v in [150, 180, 200, 240, 280, 320]
    ]
    drift_shift, details_shift = ModelMonitor.detect_data_drift(shifted_recs)
    assert drift_shift is True
    assert details_shift["num_variables"]["drift_flag"] is True
    assert details_shift["num_variables"]["p_value"] < 0.05


@pytest.mark.asyncio
async def test_continuous_retraining_promotion():
    """Verify continuous retraining pipeline evaluates and promotes candidate model."""
    res = await ContinuousLearningPipeline.evaluate_and_retrain(
        algorithm_name="random_forest",
        candidate_version="v2.0.0-retrain-test",
        use_sample_test_data=True,
        force_promote=True,
    )

    assert res.promoted is True
    assert res.candidate_model_version == "v2.0.0-retrain-test"
    assert res.training_sample_count > 0
    assert "accuracy" in res.candidate_metrics

    # Verify model is now active in registry
    active = MLModelRegistry.get_model()
    assert active is not None
    assert active.metadata.model_version == "v2.0.0-retrain-test"


@pytest.mark.asyncio
async def test_continuous_retraining_insufficient_data():
    """Verify continuous retraining gracefully rejects when live records are below threshold."""
    # Without test data and without sufficient historical DB records, it rejects
    res = await ContinuousLearningPipeline.evaluate_and_retrain(
        use_sample_test_data=False,
    )
    assert res.promoted is False
    assert "Insufficient" in res.promotion_reason


def test_rollback_workflow():
    """Verify rolling back to an earlier registered model version."""
    # Register two models
    m1 = MLSolverRecommenderModel(model_id="rollback_m1", model_version="v1.0.0-rb")
    m2 = MLSolverRecommenderModel(model_id="rollback_m2", model_version="v1.1.0-rb")
    MLModelRegistry.register_model(m1.metadata.model_id, m1, m1.metadata, set_active=False)
    MLModelRegistry.register_model(m2.metadata.model_id, m2, m2.metadata, set_active=True)

    assert MLModelRegistry.get_model().metadata.model_version == "v1.1.0-rb"

    # Roll back to v1.0.0-rb
    rb_res = ContinuousLearningPipeline.rollback("v1.0.0-rb")
    assert rb_res.success is True
    assert rb_res.active_model_version == "v1.0.0-rb"
    assert MLModelRegistry.get_model().metadata.model_version == "v1.0.0-rb"

    # Roll back to unknown version
    fail_res = ContinuousLearningPipeline.rollback("v9.9.9-unknown")
    assert fail_res.success is False


def test_api_monitoring_and_learning_endpoints(client: TestClient):
    """Verify REST /api/v1/ai feedback, monitoring, retrain, and rollback endpoints."""
    # 1. POST /feedback
    fb_payload = {
        "feedback_id": "api_fb_1",
        "problem_type": "max_cut",
        "recommended_solver": "simulated_annealing",
        "user_selected_solver": "simulated_annealing",
        "was_accepted": True,
        "recommendation_source": "ml_model",
        "realized_is_feasible": True,
        "realized_runtime_seconds": 0.05,
    }
    fb_resp = client.post("/api/v1/ai/feedback", json=fb_payload)
    assert fb_resp.status_code == 200
    assert fb_resp.json()["success"] is True

    # 2. GET /monitoring
    mon_resp = client.get("/api/v1/ai/monitoring")
    assert mon_resp.status_code == 200
    mon_data = mon_resp.json()
    assert "acceptance_rate" in mon_data
    assert "prediction_distribution" in mon_data
    assert "feature_drift_detected" in mon_data

    # 3. POST /retrain
    retrain_payload = {
        "algorithm_name": "random_forest",
        "candidate_version": "v2.5.0-api",
        "use_sample_test_data": True,
        "force_promote": True,
    }
    retrain_resp = client.post("/api/v1/ai/retrain", json=retrain_payload)
    assert retrain_resp.status_code == 200
    assert retrain_resp.json()["promoted"] is True
    assert retrain_resp.json()["candidate_model_version"] == "v2.5.0-api"

    # 4. POST /rollback
    rb_payload = {"target_model_version": "v2.5.0-api"}
    rb_resp = client.post("/api/v1/ai/rollback", json=rb_payload)
    assert rb_resp.status_code == 200
    assert rb_resp.json()["success"] is True
    assert rb_resp.json()["active_model_version"] == "v2.5.0-api"
