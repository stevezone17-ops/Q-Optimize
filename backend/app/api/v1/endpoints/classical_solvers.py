"""API endpoints for discovering, validating, and executing classical optimization solvers."""

from typing import List, Dict, Any, Union
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.domain.problems.models import ProblemType
from backend.app.services.problem_service import ProblemService
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.solvers.classical.models import (
    SolverMetadata,
    SolverRequest,
    SolverResult,
    SolverConfiguration,
    ExecutionRecord,
    ExecutionStatusResponse,
)
from backend.app.solvers.classical.exceptions import (
    SolverNotFoundError,
    SolverNotImplementedError,
    SolverConfigurationError,
    UnsupportedProblemTypeError,
)
from backend.app.solvers.classical.execution import ClassicalExecutionPipeline

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


@router.get("/executions", response_model=List[ExecutionRecord])
async def list_classical_executions(limit: int = 50) -> List[ExecutionRecord]:
    """
    List recent classical solver execution records, ordered newest first.
    """
    return await ClassicalExecutionPipeline.list_executions(limit=limit)


@router.get("/executions/{execution_id}", response_model=ExecutionRecord)
async def get_classical_execution(execution_id: str) -> ExecutionRecord:
    """
    Retrieve full execution details, status, and result payload for a specific execution ID.
    """
    record = await ClassicalExecutionPipeline.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution with ID '{execution_id}' was not found.",
        )
    return record


@router.get("/executions/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_classical_execution_status(execution_id: str) -> ExecutionStatusResponse:
    """
    Lightweight polling endpoint returning execution status and timing without large result payloads.
    """
    status_resp = await ClassicalExecutionPipeline.get_status(execution_id)
    if not status_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution with ID '{execution_id}' was not found.",
        )
    return status_resp


@router.post("/executions/{execution_id}/cancel")
async def cancel_classical_execution(execution_id: str) -> Dict[str, Any]:
    """
    Cooperatively cancel an active or pending background execution.
    """
    success = await ClassicalExecutionPipeline.cancel_execution(execution_id)
    return {
        "execution_id": execution_id,
        "cancelled": success,
        "message": "Execution cancellation signal sent successfully." if success else "Execution was not running or could not be cancelled.",
    }


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


@router.post("/execute", response_model=Union[SolverResult, ExecutionRecord])
async def execute_classical_solver(payload: SolverRequest):
    """
    Execute a classical optimization algorithm against a stored canonical problem or
    ad-hoc instance definition. Supports both synchronous execution and background dispatch.
    """
    try:
        if payload.background:
            record = await ClassicalExecutionPipeline.submit_async(payload)
            return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=record.model_dump())

        return await ClassicalExecutionPipeline.execute_sync(payload)

    except SolverNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnsupportedProblemTypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SolverNotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except (SolverConfigurationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/execute/async", response_model=ExecutionRecord, status_code=status.HTTP_202_ACCEPTED)
async def execute_classical_solver_async(payload: SolverRequest) -> ExecutionRecord:
    """
    Explicitly submit a classical optimization task to execute asynchronously in the background.
    Returns 202 Accepted with an ExecutionRecord tracking ID immediately.
    """
    try:
        return await ClassicalExecutionPipeline.submit_async(payload)
    except SolverNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnsupportedProblemTypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SolverNotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except (SolverConfigurationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

