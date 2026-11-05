"""API endpoints for discovering, validating, and executing classical optimization solvers."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.domain.problems.models import ProblemType
from backend.app.services.problem_service import ProblemService
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.solvers.classical.models import (
    SolverMetadata,
    SolverRequest,
    SolverResult,
    SolverConfiguration,
)
from backend.app.solvers.classical.exceptions import (
    SolverNotFoundError,
    SolverNotImplementedError,
    SolverConfigurationError,
    UnsupportedProblemTypeError,
)

router = APIRouter()


class SolverValidationRequest(BaseModel):
    """Payload for validating a solver configuration and problem compatibility."""
    solver_id: str
    problem_type: ProblemType
    config: Dict[str, Any] = Field(default_factory=dict)


class SolverValidationResponse(BaseModel):
    """Result of solver configuration validation."""
    is_valid: bool
    solver_id: str
    problem_type: ProblemType
    validated_config: Dict[str, Any]
    message: str


@router.get("", response_model=List[SolverMetadata])
async def list_classical_solvers() -> List[SolverMetadata]:
    """
    List all registered classical optimization algorithms with their supported
    problem types, configuration schemas, and implementation statuses.
    """
    return ClassicalSolverFactory.list_solvers()


@router.get("/{solver_id}", response_model=SolverMetadata)
async def get_classical_solver(solver_id: str) -> SolverMetadata:
    """
    Retrieve discovery metadata, parameter schemas, and default configurations
    for a specific classical solver.
    """
    try:
        solver = ClassicalSolverFactory.get_solver(solver_id)
        return solver.get_metadata()
    except SolverNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/validate", response_model=SolverValidationResponse)
async def validate_solver_config(payload: SolverValidationRequest) -> SolverValidationResponse:
    """
    Validate that a given solver supports the problem type and that its
    configuration parameters satisfy value and type constraints.
    """
    try:
        solver = ClassicalSolverFactory.get_solver(payload.solver_id)
        solver.check_problem_support(payload.problem_type)
        parsed_config = solver.validate_config(payload.config)
        return SolverValidationResponse(
            is_valid=True,
            solver_id=solver.solver_id,
            problem_type=payload.problem_type,
            validated_config=parsed_config.model_dump(),
            message=f"Configuration for solver '{solver.name}' is valid.",
        )
    except (SolverNotFoundError, UnsupportedProblemTypeError, SolverConfigurationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/execute", response_model=SolverResult, status_code=status.HTTP_200_OK)
async def execute_classical_solver(payload: SolverRequest) -> SolverResult:
    """
    Execute a classical optimization algorithm against a stored canonical problem or
    ad-hoc instance definition.
    """
    try:
        solver = ClassicalSolverFactory.get_solver(payload.solver_id)

        # Resolve problem definition
        target_problem_type: ProblemType
        target_instance: Dict[str, Any]

        if payload.problem_id:
            stored_problem = await ProblemService.get_problem(payload.problem_id)
            if not stored_problem:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Problem with ID '{payload.problem_id}' not found.",
                )
            target_problem_type = stored_problem.problem_type
            target_instance = stored_problem.instance
        elif payload.problem_type and payload.instance:
            target_problem_type = payload.problem_type
            target_instance = payload.instance
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either 'problem_id' or both 'problem_type' and 'instance'.",
            )

        solver.check_problem_support(target_problem_type)

        if not solver.is_implemented:
            raise SolverNotImplementedError(
                f"Solver '{solver.name}' ({solver.solver_id}) is scheduled for implementation in {solver.stage_introduced}. "
                "Current stage: Stage 4.1 (Architecture & Interfaces)."
            )

        parsed_config = solver.validate_config(payload.config)
        return solver.solve(
            problem_type=target_problem_type,
            instance=target_instance,
            config=parsed_config,
            seed=payload.seed,
        )

    except SolverNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnsupportedProblemTypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SolverNotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except (SolverConfigurationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

