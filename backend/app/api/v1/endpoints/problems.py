"""Problem definition and draft endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, status
from backend.app.domain.problems.models import (
    ProblemCreate,
    ProblemResponse,
    ProblemDraftRequest,
    ProblemDraftResponse,
)
from backend.app.services.problem_service import ProblemService

router = APIRouter(prefix="/problems", tags=["Problems"])


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


@router.post("/parse-draft", response_model=ProblemDraftResponse)
async def parse_draft(draft_req: ProblemDraftRequest) -> ProblemDraftResponse:
    """
    Draft parsing: convert natural language problem description into a reviewable draft.
    Requires explicit human confirmation before canonical problem creation.
    """
    return ProblemService.parse_problem_draft(draft_req)
