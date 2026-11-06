"""Unit tests for Stage 7.4: ML-Based Intelligent Solver Recommendation."""

import os
import tempfile
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import OptimizationFeatures, RecommendationSource
from backend.app.ai.recommender import (
    MLSolverRecommenderModel,
    RuleBasedSolverRecommender,
    IntelligentSolverRecommender,
)
from backend.app.ai.dataset_builder import ExperimentDatasetBuilder
from backend.app.ai.training_pipeline import ModelTrainingPipeline
from backend.app.ai.registry import MLModelRegistry
from backend.app.ai.exceptions import ModelNotTrainedError


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_ml_recommender_model_lifecycle():
    """Verify training, prediction, probabilities, and serialization of MLSolverRecommenderModel."""
    model = MLSolverRecommenderModel(model_id="test_rf", algorithm_name="random_forest")

    # Predict before train raises error
    with pytest.raises(ModelNotTrainedError):
        model.predict([1.0] * 18)

    # Train on sample test dataset
    samples, _ = ExperimentDatasetBuilder.create_sample_test_dataset()
    X, y, groups = ModelTrainingPipeline.prepare_data_matrices(samples)

    meta = model.train(
        X=X.tolist(),
        y=y.tolist(),
        feature_names=ModelTrainingPipeline.FEATURE_NAMES,
        target_classes=ModelTrainingPipeline.TARGET_CLASSES,
    )
    assert meta.is_trained is True

    # Test prediction
    pred = model.predict(X[0].tolist())
    assert isinstance(pred, str)
    assert pred in ModelTrainingPipeline.TARGET_CLASSES

    # Test probabilities
    probs = model.predict_proba(X[0].tolist())
    assert isinstance(probs, dict)
    assert sum(probs.values()) == pytest.approx(1.0, rel=1e-3)

    # Test feature importances
    importances = model.get_feature_importances()
    assert isinstance(importances, dict)
    assert len(importances) == 18

    # Test serialization and deserialization
    with tempfile.TemporaryDirectory() as tmp_dir:
        art_path = os.path.join(tmp_dir, "test_model.pkl")
        model.save(art_path)
        assert os.path.exists(art_path)

        loaded_model = MLSolverRecommenderModel(model_id="loaded_rf")
        loaded_model.load(art_path)
        assert loaded_model.predict(X[0].tolist()) == pred


def test_rule_based_recommender_heuristics():
    """Verify expert rule-based recommendations across problem families and sizes."""
    # 1. Small Max-Cut (n=6) -> Exact
    f_small_mc = OptimizationFeatures(
        problem_type=ProblemType.MAX_CUT,
        num_variables=6,
        num_vertices=6,
        estimated_search_space_log2=6.0,
    )
    rec_small_mc = RuleBasedSolverRecommender.recommend(ProblemType.MAX_CUT, f_small_mc)
    assert rec_small_mc.recommended_solver == "exact"
    assert rec_small_mc.recommendation_source == RecommendationSource.RULE_BASED

    # 2. Large Max-Cut (n=25) -> Simulated Annealing
    f_large_mc = OptimizationFeatures(
        problem_type=ProblemType.MAX_CUT,
        num_variables=25,
        num_vertices=25,
        estimated_search_space_log2=25.0,
    )
    rec_large_mc = RuleBasedSolverRecommender.recommend(ProblemType.MAX_CUT, f_large_mc)
    assert rec_large_mc.recommended_solver == "simulated_annealing"

    # 3. Assignment (n=4) -> Exact (Hungarian polynomial time)
    f_assign = OptimizationFeatures(
        problem_type=ProblemType.ASSIGNMENT,
        num_variables=16,
        num_agents=4,
        num_tasks=4,
        estimated_search_space_log2=4.58,
    )
    rec_assign = RuleBasedSolverRecommender.recommend(ProblemType.ASSIGNMENT, f_assign)
    assert rec_assign.recommended_solver == "exact"

    # 4. TSP small (n=4) -> Exact
    f_small_tsp = OptimizationFeatures(
        problem_type=ProblemType.TSP,
        num_variables=16,
        num_cities=4,
        estimated_search_space_log2=1.58,
    )
    rec_small_tsp = RuleBasedSolverRecommender.recommend(ProblemType.TSP, f_small_tsp)
    assert rec_small_tsp.recommended_solver == "exact"

    # 5. TSP large (n=14) -> Simulated Annealing
    f_large_tsp = OptimizationFeatures(
        problem_type=ProblemType.TSP,
        num_variables=196,
        num_cities=14,
        estimated_search_space_log2=35.0,
    )
    rec_large_tsp = RuleBasedSolverRecommender.recommend(ProblemType.TSP, f_large_tsp)
    assert rec_large_tsp.recommended_solver == "simulated_annealing"


@pytest.mark.asyncio
async def test_intelligent_recommender_safety_filtering():
    """Verify safety filtering disables Exact solver on large instances."""
    recommender = IntelligentSolverRecommender()

    # Max-Cut with 24 vertices
    inst_large = {
        "nodes": [f"V{i}" for i in range(24)],
        "edges": [[f"V{i}", f"V{(i+1)%24}", 1.0] for i in range(24)],
    }

    rec = await recommender.recommend_solver(ProblemType.MAX_CUT, inst_large)
    # Recommended solver must not be exact
    assert rec.recommended_solver != "exact"

    # Check ranked alternatives: exact must be marked as not compatible
    exact_alt = next((a for a in rec.ranked_alternatives if a.solver_name == "exact"), None)
    if exact_alt:
        assert exact_alt.is_compatible is False
        assert "exceed safety limit" in exact_alt.reason


def test_api_recommend_endpoint(client: TestClient):
    """Verify REST POST /api/v1/ai/recommend endpoint."""
    payload = {
        "problem_type": "max_cut",
        "instance": {
            "nodes": ["A", "B", "C", "D"],
            "edges": [["A", "B", 1.0], ["B", "C", 2.0], ["C", "D", 1.5], ["D", "A", 2.5]],
        },
    }

    resp = client.post("/api/v1/ai/recommend", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["problem_type"] == "max_cut"
    assert "recommended_solver" in data
    assert "ranked_alternatives" in data
    assert len(data["ranked_alternatives"]) >= 2
    assert "explanation" in data


def test_api_train_and_list_models_endpoints(client: TestClient):
    """Verify REST POST /api/v1/ai/train and GET /api/v1/ai/models."""
    train_payload = {
        "algorithm_name": "random_forest",
        "model_version": "v1.0.0-test",
        "use_sample_test_data": True,
    }

    train_resp = client.post("/api/v1/ai/train", json=train_payload)
    assert train_resp.status_code == 200
    train_data = train_resp.json()

    assert train_data["success"] is True
    assert train_data["model_metadata"]["is_trained"] is True
    assert train_data["model_metadata"]["model_version"] == "v1.0.0-test"

    list_resp = client.get("/api/v1/ai/models")
    assert list_resp.status_code == 200
    models = list_resp.json()
    assert any(m["model_version"] == "v1.0.0-test" for m in models)
