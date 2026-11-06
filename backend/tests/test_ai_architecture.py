"""Unit tests for Stage 7.1: AI and Machine Learning Architecture and Data Foundation."""

import pytest
from datetime import datetime, timezone

from backend.app.domain.problems.models import ProblemType
from backend.app.db.mongodb import db_manager
from backend.app.ai.models import (
    AIRequest,
    AIResponse,
    OptimizationFeatures,
    SolverRecommendation,
    RankedSolverAlternative,
    ModelMetadata,
    TrainingDatasetMetadata,
    ModelEvaluationResult,
    ExperimentRecord,
    RecommendationSource,
    SolverCandidate,
)
from backend.app.ai.interfaces import IMLRecommenderModel, IFeatureExtractor
from backend.app.ai.registry import MLModelRegistry, AIServiceRegistry
from backend.app.ai.data_access import ExperimentDataAccess
from backend.app.ai.exceptions import ModelNotFoundError, DataQualityError


class DummyModel(IMLRecommenderModel):
    """Mock implementation for registry testing."""
    def __init__(self, model_id: str, is_trained: bool = False):
        self._id = model_id
        self._is_trained = is_trained

    @property
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id=self._id,
            model_version="v1.0.0",
            algorithm_name="DummyClassifier",
            is_trained=self._is_trained,
            is_active=False,
        )

    def train(self, X, y, feature_names, target_classes):
        self._is_trained = True
        return self.metadata

    def predict(self, feature_vector):
        return "exact"

    def predict_proba(self, feature_vector):
        return {"exact": 1.0}

    def get_feature_importances(self):
        return {"feat_0": 1.0}

    def save(self, filepath):
        pass

    def load(self, filepath):
        pass


def test_ai_request_response_envelopes():
    """Verify generic AI request and response envelopes."""
    req = AIRequest(operation="recommend_solver", parameters={"problem_type": "max_cut"})
    assert req.operation == "recommend_solver"
    assert req.parameters["problem_type"] == "max_cut"

    res = AIResponse(operation="recommend_solver", success=True, data={"recommended_solver": "exact"})
    assert res.success is True
    assert res.data["recommended_solver"] == "exact"
    assert isinstance(res.timestamp, datetime)


def test_optimization_features_model():
    """Verify OptimizationFeatures serialization and feature vector generation."""
    features = OptimizationFeatures(
        schema_version="v1.0.0",
        problem_type=ProblemType.MAX_CUT,
        num_variables=8,
        num_constraints=0,
        constraint_density=0.0,
        estimated_search_space_log2=8.0,
        coeff_min=1.0,
        coeff_max=5.0,
        coeff_mean=2.5,
        coeff_std=1.2,
        coeff_range=4.0,
        num_vertices=8,
        num_edges=12,
        graph_density=0.428,
        min_degree=2,
        max_degree=4,
        avg_degree=3.0,
        degree_std=0.7,
        qubo_num_binary_vars=8,
        qubo_interaction_density=0.428,
        ising_num_spins=8,
        ising_coupling_density=0.428,
        required_qubits=8,
    )
    assert features.num_variables == 8
    assert features.graph_density == pytest.approx(0.428, rel=1e-2)

    vec = features.to_feature_vector()
    assert isinstance(vec, list)
    assert len(vec) == 18
    assert vec[0] == 8.0  # num_variables
    assert vec[3] == 8.0  # search space log2


def test_solver_recommendation_model():
    """Verify SolverRecommendation model with ranked alternatives."""
    rec = SolverRecommendation(
        problem_type=ProblemType.MAX_CUT,
        recommended_solver="exact",
        confidence_score=0.95,
        is_confidence_calibrated=True,
        recommendation_source=RecommendationSource.RULE_BASED,
        ranked_alternatives=[
            RankedSolverAlternative(
                solver_name="simulated_annealing",
                score=0.82,
                rank=2,
                is_compatible=True,
                reason="Good heuristic for moderate size graphs",
            )
        ],
        explanation="Instance has 8 vertices, which is well within ExactSolver safe limit (n <= 18).",
        key_features_summary={"num_variables": 8, "graph_density": 0.428},
    )
    assert rec.recommended_solver == "exact"
    assert rec.confidence_score == 0.95
    assert len(rec.ranked_alternatives) == 1
    assert rec.ranked_alternatives[0].solver_name == "simulated_annealing"


def test_ml_model_registry():
    """Verify MLModelRegistry registration, retrieval, and active model toggling."""
    MLModelRegistry.clear()

    model1 = DummyModel("model_rf_1")
    meta1 = model1.metadata
    MLModelRegistry.register_model("model_rf_1", model1, meta1, set_active=True)

    assert MLModelRegistry.get_model("model_rf_1") is model1
    assert MLModelRegistry.get_metadata("model_rf_1").model_id == "model_rf_1"
    assert MLModelRegistry.is_active_model_trained() is False

    # Register second model and switch active
    model2 = DummyModel("model_gb_2", is_trained=True)
    meta2 = model2.metadata
    MLModelRegistry.register_model("model_gb_2", model2, meta2, set_active=True)

    assert MLModelRegistry.get_model() is model2
    assert MLModelRegistry.is_active_model_trained() is True

    # Switching to unknown model raises ModelNotFoundError
    with pytest.raises(ModelNotFoundError):
        MLModelRegistry.set_active_model("non_existent_model")

    models = MLModelRegistry.list_models()
    assert len(models) == 2


@pytest.mark.asyncio
async def test_experiment_data_access_merging_and_dedup():
    """Verify ExperimentDataAccess retrieves, validates, and deduplicates records."""
    try:
        # Seed mock memory store with classical executions
        db_manager.memory_insert("executions", "test_exec_1", {
            "execution_id": "test_exec_1",
            "solver_id": "exact",
            "solver_name": "exact",
            "problem_type": "max_cut",
            "status": "COMPLETED",
            "config": {"random_seed": 42},
            "result": {
                "solver_id": "exact",
                "solver_name": "exact",
                "problem_type": "max_cut",
                "candidate_solution": [0, 1],
                "termination_reason": "OPTIMAL",
                "is_feasible": True,
                "objective_value": 14.0,
                "runtime_seconds": 0.005,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        # Failed run should be excluded when filter_failed is True
        db_manager.memory_insert("executions", "test_exec_failed", {
            "execution_id": "test_exec_failed",
            "solver_id": "exact",
            "solver_name": "exact",
            "problem_type": "max_cut",
            "status": "FAILED",
            "config": {},
            "result": {
                "solver_id": "exact",
                "solver_name": "exact",
                "problem_type": "max_cut",
                "candidate_solution": [],
                "termination_reason": "FAILED",
                "is_feasible": False,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        records = await ExperimentDataAccess.fetch_all_experiments(
            include_classical=True,
            include_qaoa=False,
            include_adaptive=False,
            include_benchmarks=False,
            filter_failed=True,
        )

        assert any(r.record_id == "test_exec_1" for r in records)
        assert not any(r.record_id == "test_exec_failed" for r in records)

        # Test deduplication: merging identical trial does not duplicate
        seen = set()
        target = []
        ExperimentDataAccess._merge_records(target, records, seen, filter_failed=True)
        assert len(target) == len(records)
        # Merging again
        ExperimentDataAccess._merge_records(target, records, seen, filter_failed=True)
        assert len(target) == len(records)  # Count unchanged due to dedup key
    finally:
        # Clean up memory store so other test suites are not affected
        db_manager.memory_delete("executions", "test_exec_1")
        db_manager.memory_delete("executions", "test_exec_failed")
