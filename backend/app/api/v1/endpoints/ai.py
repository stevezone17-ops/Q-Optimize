"""REST API endpoints for AI and Machine Learning Intelligence Layer."""

from typing import Dict, Any, List, Optional
import numpy as np
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import (
    SolverRecommendation,
    ModelMetadata,
    OptimizationFeatures,
    ProblemDraftProposal,
)
from backend.app.ai.natural_language.assistant import default_nl_assistant
from backend.app.ai.recommender import default_solver_recommender
from backend.app.ai.registry import MLModelRegistry
from backend.app.ai.data_access import ExperimentDataAccess
from backend.app.ai.dataset_builder import ExperimentDatasetBuilder
from backend.app.ai.training_pipeline import ModelTrainingPipeline
from backend.app.ai.feature_extraction import default_feature_extractor
from backend.app.services.problem_service import ProblemService
from backend.app.core.logging import logger

router = APIRouter(prefix="/ai", tags=["AI & Machine Learning"])


class SolverRecommendationRequest(BaseModel):
    """Request payload for solver recommendation."""
    problem_id: Optional[str] = Field(default=None, description="Optional stored problem ID")
    problem_type: Optional[ProblemType] = Field(default=None, description="Problem type if ad-hoc")
    instance: Optional[Dict[str, Any]] = Field(default=None, description="Instance data if ad-hoc")
    user_constraints: Optional[Dict[str, Any]] = Field(default=None, description="Resource or time limits")


class ModelTrainRequest(BaseModel):
    """Request payload to train a new solver recommendation model."""
    algorithm_name: str = Field(default="random_forest", description="random_forest, gradient_boosting, extra_trees, decision_tree")
    model_version: str = Field(default="v1.0.0", description="Semantic model version string")
    use_sample_test_data: bool = Field(default=False, description="For testing: use isolated synthetic test dataset")


class ModelTrainResponse(BaseModel):
    """Response returned upon training a model."""
    success: bool
    model_metadata: ModelMetadata
    evaluation_metrics: Dict[str, Any]
    training_sample_count: int
    notes: str


@router.post("/recommend", response_model=SolverRecommendation)
async def recommend_solver(req: SolverRecommendationRequest) -> SolverRecommendation:
    """
    Produce an intelligent, data-driven solver recommendation with ranked alternatives,
    confidence metrics, and plain-English explanations.
    """
    prob_type = req.problem_type
    instance_data = req.instance or {}

    # If problem_id provided, fetch canonical problem definition
    if req.problem_id and not (prob_type and instance_data):
        problem = await ProblemService.get_problem(req.problem_id)
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Problem '{req.problem_id}' was not found.",
            )
        prob_type = problem.problem_type
        instance_data = problem.instance

    if not prob_type or not instance_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a valid 'problem_id' or both 'problem_type' and 'instance' must be provided.",
        )

    try:
        recommendation = await default_solver_recommender.recommend_solver(
            problem_type=prob_type,
            instance_data=instance_data,
            problem_id=req.problem_id,
            user_constraints=req.user_constraints,
        )
        return recommendation
    except Exception as e:
        logger.error(f"Error generating solver recommendation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}",
        )


@router.get("/models", response_model=List[ModelMetadata])
async def list_models() -> List[ModelMetadata]:
    """List all registered recommendation models, versions, and deployment statuses."""
    return MLModelRegistry.list_models()


@router.post("/train", response_model=ModelTrainResponse)
async def train_recommendation_model(req: ModelTrainRequest) -> ModelTrainResponse:
    """
    Train a candidate solver recommendation model from historical experiment data.
    """
    try:
        if req.use_sample_test_data:
            samples, ds_meta = ExperimentDatasetBuilder.create_sample_test_dataset()
        else:
            records = await ExperimentDataAccess.fetch_all_experiments()
            if not records:
                # Under real operational conditions without records, report transparently
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No historical experiment records available to train a production model.",
                )
            samples, ds_meta = ExperimentDatasetBuilder.build_dataset(records)

        X, y, groups = ModelTrainingPipeline.prepare_data_matrices(samples)
        X_train, X_test, y_train, y_test = ModelTrainingPipeline.split_group_aware(X, y, groups)

        from backend.app.ai.recommender import MLSolverRecommenderModel
        model_id = f"recommender_{req.algorithm_name}_{req.model_version}"
        model = MLSolverRecommenderModel(
            model_id=model_id,
            model_version=req.model_version,
            algorithm_name=req.algorithm_name,
        )

        model.train(
            X=X_train.tolist(),
            y=y_train.tolist(),
            feature_names=ModelTrainingPipeline.FEATURE_NAMES,
            target_classes=ModelTrainingPipeline.TARGET_CLASSES,
        )

        y_pred = [model.predict(x) for x in X_test]
        metrics = ModelTrainingPipeline.compute_evaluation_metrics(y_test, np.array(y_pred))

        # Register model as active
        meta = model.metadata
        meta.accuracy = metrics.get("accuracy")
        meta.macro_f1 = metrics.get("macro_f1")
        meta.training_sample_count = len(X_train)
        MLModelRegistry.register_model(model_id, model, meta, set_active=True)

        return ModelTrainResponse(
            success=True,
            model_metadata=meta,
            evaluation_metrics=metrics,
            training_sample_count=len(X_train),
            notes="Trained and activated candidate recommendation model successfully.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model training pipeline error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(e)}",
        )


class NLParseRequest(BaseModel):
    """Request payload to parse natural language description into problem draft."""
    text: str = Field(..., min_length=5, max_length=4000, description="Natural language problem description")
    problem_type_hint: Optional[ProblemType] = Field(default=None, description="Optional problem type hint")
    provider_name: Optional[str] = Field(default=None, description="Optional provider override (gemini, deterministic_fallback, mock_llm)")


class NLValidateDraftRequest(BaseModel):
    """Request payload to re-validate an edited problem draft instance."""
    problem_type: ProblemType
    instance: Dict[str, Any]


@router.post("/assistant/parse", response_model=ProblemDraftProposal)
async def parse_natural_language_draft(req: NLParseRequest) -> ProblemDraftProposal:
    """
    Parse natural language description into an editable, reviewable problem proposal draft.
    Does NOT bypass Phase 2 mathematical validation.
    """
    try:
        draft = await default_nl_assistant.parse_problem_description(
            text=req.text,
            problem_type_hint=req.problem_type_hint,
            provider_name=req.provider_name,
        )
        return draft
    except Exception as e:
        logger.error(f"Natural language parsing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse problem description: {str(e)}",
        )


@router.post("/assistant/validate-draft")
async def validate_draft_instance(req: NLValidateDraftRequest) -> Dict[str, Any]:
    """
    Re-validate an edited problem instance draft against canonical Phase 2 domain validators.
    """
    try:
        res = ProblemService.validate_problem_definition(req.problem_type, req.instance)
        return {
            "is_valid": res.is_valid,
            "status": res.status.value,
            "issues": res.issues,
            "num_variables": len(res.variables),
            "num_constraints": len(res.constraints),
            "metadata": res.metadata,
        }
    except Exception as e:
        logger.error(f"Draft validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Draft validation failed: {str(e)}",
        )
