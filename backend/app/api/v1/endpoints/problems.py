"""Problem definition, types, validation, and evaluation endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from backend.app.domain.problems.models import (
    ProblemType,
    ProblemCreate,
    ProblemResponse,
    ProblemDraftRequest,
    ProblemDraftResponse,
    ProblemValidationResponse,
    ProblemTypeInfo,
)
from backend.app.evaluation.models import EvaluationRequest, EvaluationResult
from backend.app.services.problem_service import ProblemService

router = APIRouter(prefix="/problems", tags=["Problems"])


class DirectValidateRequest(BaseModel):
    problem_type: ProblemType
    instance: Dict[str, Any]


class DirectEvaluateRequest(BaseModel):
    problem_type: ProblemType
    instance: Dict[str, Any]
    candidate: Any


@router.get("/types", response_model=List[ProblemTypeInfo])
async def list_problem_types() -> List[ProblemTypeInfo]:
    """
    List all supported canonical optimization problem types with their
    mathematical forms, variable definitions, and supported constraints.
    """
    return ProblemService.get_supported_problem_types()


@router.post("/validate", response_model=ProblemValidationResponse)
async def validate_problem_direct(payload: DirectValidateRequest) -> ProblemValidationResponse:
    """
    Validate a problem definition directly from instance data without persistence.
    """
    return ProblemService.validate_problem_definition(
        problem_type=payload.problem_type,
        instance_data=payload.instance,
    )


@router.post("/evaluate-direct", response_model=EvaluationResult)
async def evaluate_direct(payload: DirectEvaluateRequest) -> EvaluationResult:
    """
    Directly evaluate a candidate solution against an ad-hoc problem instance
    without requiring a registered problem ID.
    """
    try:
        return ProblemService.evaluate_candidate_direct(
            problem_type=payload.problem_type,
            instance_data=payload.instance,
            candidate=payload.candidate,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )


@router.post("/parse-draft", response_model=ProblemDraftResponse)
async def parse_draft(draft_req: ProblemDraftRequest) -> ProblemDraftResponse:
    """
    Draft parsing: convert natural language problem description into a reviewable draft.
    Requires explicit human confirmation before canonical problem creation.
    """
    return ProblemService.parse_problem_draft(draft_req)


@router.post("", response_model=ProblemResponse, status_code=status.HTTP_201_CREATED)
async def create_problem(problem_in: ProblemCreate) -> ProblemResponse:
    """
    Create and validate a new canonical optimization problem (Max-Cut, Assignment, or TSP).
    Independent Pydantic schema validation runs before persistence.
    """
    try:
        return await ProblemService.create_problem(problem_in)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create problem: {str(e)}",
        )


@router.get("", response_model=List[ProblemResponse])
async def list_problems() -> List[ProblemResponse]:
    """List registered canonical problems."""
    return await ProblemService.list_problems()


@router.get("/{problem_id}", response_model=ProblemResponse)
async def get_problem(problem_id: str) -> ProblemResponse:
    """Retrieve problem definition by ID."""
    problem = await ProblemService.get_problem(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with ID '{problem_id}' was not found.",
        )
    return problem


@router.get("/{problem_id}/metadata", response_model=Dict[str, Any])
async def get_problem_metadata(problem_id: str) -> Dict[str, Any]:
    """Retrieve structural statistics and mathematical metadata for a problem."""
    problem = await ProblemService.get_problem(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with ID '{problem_id}' was not found.",
        )
    return {
        "problem_id": problem.id,
        "problem_type": problem.problem_type,
        "name": problem.name,
        "variables": [v.model_dump() for v in problem.variables],
        "objective": problem.objective.model_dump() if problem.objective else None,
        "constraints": [c.model_dump() for c in problem.constraints],
        "metadata": problem.metadata,
        "validation_status": problem.validation_status,
    }


@router.post("/{problem_id}/validate", response_model=ProblemValidationResponse)
async def validate_problem(problem_id: str) -> ProblemValidationResponse:
    """Validate an existing problem definition against domain constraints."""
    problem = await ProblemService.get_problem(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with ID '{problem_id}' was not found.",
        )
    return ProblemService.validate_problem_definition(
        problem_type=problem.problem_type,
        instance_data=problem.instance,
        problem_id=problem.id,
    )


@router.post("/{problem_id}/evaluate", response_model=EvaluationResult)
async def evaluate_candidate(problem_id: str, payload: EvaluationRequest) -> EvaluationResult:
    """
    Evaluate candidate solution against registered problem using independent evaluator engine.
    Calculates objective value and checks feasibility without trusting solver self-reporting.
    """
    try:
        return await ProblemService.evaluate_candidate_for_problem(
            problem_id=problem_id,
            candidate=payload.candidate,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(val_err).lower() else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )
