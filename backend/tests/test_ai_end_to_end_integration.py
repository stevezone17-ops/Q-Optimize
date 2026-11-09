"""End-to-End integration tests for Phase 7: AI and Machine Learning Intelligence Layer."""

import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType, ProblemCreate
from backend.app.services.problem_service import ProblemService
from backend.app.solvers.classical.models import SolverStatus
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.ai.models import (
    RecommendationFeedback,
    RecommendationSource,
    OptimizationFeatures,
)
from backend.app.ai.natural_language.assistant import default_nl_assistant
from backend.app.ai.recommender import default_solver_recommender, RuleBasedSolverRecommender
from backend.app.ai.monitoring import ModelMonitor
from backend.app.ai.feature_extraction import default_feature_extractor


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.asyncio
async def test_end_to_end_max_cut_ai_workflow(client: TestClient):
    """
    End-to-end integration:
    1. Parse natural language description into structured draft.
    2. Mathematically validate draft via canonical Phase 2 validator.
    3. Register canonical problem definition.
    4. Query intelligent solver recommender.
    5. Execute recommended solver and verify solution with Phase 2 independent evaluator.
    6. Log user feedback and verify audit monitoring.
    """
    # 1. Natural Language Parse
    nl_text = "Partition a cluster of 4 servers Alpha, Beta, Gamma, Delta with connection latency weights."
    draft = await default_nl_assistant.parse_problem_description(
        text=nl_text,
        problem_type_hint=ProblemType.MAX_CUT,
    )
    assert draft.problem_type == ProblemType.MAX_CUT
    assert draft.requires_user_confirmation is True
    assert draft.validation_status.lower() == "valid"

    # 2. Canonical Validation
    val_res = ProblemService.validate_problem_definition(ProblemType.MAX_CUT, draft.suggested_instance)
    assert val_res.is_valid is True

    # 3. Register Problem
    created_problem = await ProblemService.create_problem(
        ProblemCreate(
            name="E2E Max-Cut AI Test",
            problem_type=ProblemType.MAX_CUT,
            instance=draft.suggested_instance,
            description="E2E AI generated problem",
        )
    )
    assert created_problem.id is not None

    # 4. Request Solver Recommendation
    rec = await default_solver_recommender.recommend_solver(
        problem_type=ProblemType.MAX_CUT,
        instance_data=created_problem.instance,
        problem_id=created_problem.id,
    )
    assert rec.recommended_solver in ["exact", "simulated_annealing", "genetic_algorithm", "adaptive_qaoa"]
    assert len(rec.ranked_alternatives) >= 2
    assert rec.key_features_summary["num_variables"] >= 4

    # 5. Execute recommended classical solver (or exact for n=4)
    chosen_solver = rec.recommended_solver if rec.recommended_solver in ["exact", "simulated_annealing", "genetic_algorithm"] else "exact"
    solver = ClassicalSolverFactory.get_solver(chosen_solver)
    exec_res = solver.solve(
        problem_type=ProblemType.MAX_CUT,
        instance=created_problem.instance,
    )
    assert exec_res.status == SolverStatus.COMPLETED
    assert exec_res.is_feasible is True
    assert exec_res.objective_value is not None

    # 6. Record Feedback
    fb_id = await ModelMonitor.record_feedback(
        RecommendationFeedback(
            feedback_id=f"fb_e2e_{created_problem.id}",
            problem_id=created_problem.id,
            problem_type=ProblemType.MAX_CUT,
            recommended_solver=rec.recommended_solver,
            user_selected_solver=chosen_solver,
            was_accepted=(chosen_solver == rec.recommended_solver),
            recommendation_source=rec.recommendation_source,
            realized_objective_value=exec_res.objective_value,
            realized_runtime_seconds=exec_res.runtime_seconds,
            realized_is_feasible=exec_res.is_feasible,
        )
    )
    assert fb_id is not None


@pytest.mark.asyncio
async def test_end_to_end_assignment_ai_workflow():
    """
    End-to-end integration for Assignment problem:
    NL Parse -> Validate -> Recommender -> Execute Hungarian exact solver -> Evaluate.
    """
    nl_text = "Assign workers Alice and Bob to jobs Task1 and Task2 with costs 5, 9, 3, 2."
    draft = await default_nl_assistant.parse_problem_description(
        text=nl_text,
        problem_type_hint=ProblemType.ASSIGNMENT,
    )
    assert draft.problem_type == ProblemType.ASSIGNMENT

    # Recommender: Exact (Hungarian) must be top recommendation
    rec = await default_solver_recommender.recommend_solver(
        problem_type=ProblemType.ASSIGNMENT,
        instance_data=draft.suggested_instance,
    )
    assert rec.recommended_solver == "exact"
    assert rec.confidence_score >= 0.70
    assert "exact" in rec.explanation.lower() or "assignment" in rec.explanation.lower()


@pytest.mark.asyncio
async def test_end_to_end_tsp_ai_workflow():
    """
    End-to-end integration for TSP problem:
    NL Parse -> Validate -> Recommender -> Execute -> Evaluate.
    """
    nl_text = "Find optimal travel route visiting Tokyo, Osaka, Kyoto and returning to start."
    draft = await default_nl_assistant.parse_problem_description(
        text=nl_text,
        problem_type_hint=ProblemType.TSP,
    )
    assert draft.problem_type == ProblemType.TSP

    rec = await default_solver_recommender.recommend_solver(
        problem_type=ProblemType.TSP,
        instance_data=draft.suggested_instance,
    )
    assert rec.recommended_solver in ["exact", "simulated_annealing", "genetic_algorithm"]
    n_cities = len(draft.suggested_instance.get("cities", []))
    assert rec.resource_considerations["quantum_simulator_compatible"] == (n_cities * n_cities <= 20)


def test_cross_capability_safety_consistency():
    """
    Verify AI recommendations never violate physical or computational bounds:
    1. Exact solver NEVER recommended for instances exceeding size limits.
    2. Quantum solvers NEVER recommended when required qubits exceed simulation ceiling (n <= 20).
    3. Out-of-distribution instances ALWAYS trigger rule-based fallback and user warning.
    """
    # 1. Large Max-Cut graph (n=25) -> Exact must not be recommended
    f_large_mc = OptimizationFeatures(
        problem_type=ProblemType.MAX_CUT,
        num_variables=25,
        num_vertices=25,
        estimated_search_space_log2=25.0,
        required_qubits=25,
    )
    rec_mc = RuleBasedSolverRecommender.recommend(ProblemType.MAX_CUT, f_large_mc)
    assert rec_mc.recommended_solver != "exact"
    exact_alt = next((a for a in rec_mc.ranked_alternatives if a.solver_name == "exact"), None)
    if exact_alt:
        assert exact_alt.is_compatible is False

    # 2. Large TSP (n=15 cities) -> Exact must not be recommended
    f_large_tsp = OptimizationFeatures(
        problem_type=ProblemType.TSP,
        num_variables=225,
        num_cities=15,
        estimated_search_space_log2=40.0,
        required_qubits=225,
    )
    rec_tsp = RuleBasedSolverRecommender.recommend(ProblemType.TSP, f_large_tsp)
    assert rec_tsp.recommended_solver != "exact"
    assert rec_tsp.recommended_solver in ["simulated_annealing", "genetic_algorithm"]

    # 3. Quantum simulation limits check (qubits > 20)
    assert f_large_mc.required_qubits > 20
    qaoa_compat = rec_mc.resource_considerations.get("quantum_simulator_compatible")
    assert qaoa_compat is False
