"""FastAPI Endpoints for Adaptive QAOA Research & Dynamic Parameter Strategies."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.app.solvers.quantum.adaptive.strategy_registry import AdaptiveStrategyRegistry
from backend.app.solvers.quantum.adaptive.strategy_factory import AdaptiveStrategyFactory
from backend.app.solvers.quantum.adaptive.base_strategy import StrategyMetadata
from backend.app.solvers.quantum.adaptive.adaptive_models import (
    AdaptiveQAOARequest,
    AdaptiveStrategyConfiguration,
    AdaptiveQAOAResult,
    AdaptiveExecutionRecord,
    AdaptiveStatusResponse,
)
from backend.app.solvers.quantum.adaptive.pipeline import AdaptiveQAOAExecutionPipeline
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import (
    AdaptiveStrategyNotFoundError,
    AdaptiveQAOAError,
    IncompatibleTransferError,
    IncompatibleWarmStartError,
)
from backend.app.solvers.quantum.adaptive.transfer import (
    ParameterTransferService,
    TransferCompatibilityReport,
    TransferParametersRequest,
    TransferParametersResponse,
)

router = APIRouter()


@router.get("/strategies", response_model=List[StrategyMetadata])
async def list_adaptive_strategies():
    """List all available Adaptive QAOA research strategies and their capabilities."""
    return AdaptiveStrategyRegistry.list_strategies()


@router.get("/strategies/{strategy_id}", response_model=StrategyMetadata)
async def get_adaptive_strategy(strategy_id: str):
    """Retrieve metadata and parameter specs for a specific adaptive strategy."""
    try:
        strat_cls = AdaptiveStrategyRegistry.get(strategy_id)
        return strat_cls().get_metadata()
    except AdaptiveStrategyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )


@router.post("/validate")
async def validate_adaptive_configuration(req: AdaptiveQAOARequest):
    """
    Validate an adaptive QAOA execution configuration against target strategy rules,
    depth limits, and optimization parameters before execution.
    """
    try:
        AdaptiveStrategyFactory.validate_configuration(req.config.strategy_config)
        return {
            "is_valid": True,
            "strategy": req.config.strategy_config.strategy_type.value,
            "initial_depth": req.config.strategy_config.initial_depth,
            "max_depth": req.config.strategy_config.max_depth,
            "message": "Adaptive QAOA configuration is valid."
        }
    except (ValueError, AdaptiveQAOAError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.post("/transfer/check", response_model=TransferCompatibilityReport)
async def check_parameter_transfer(req: TransferParametersRequest):
    """
    Check parameter transfer feasibility and return a detailed compatibility report.
    """
    if req.source_execution_id:
        try:
            _, _, report = await ParameterTransferService.transfer_from_execution(
                execution_id=req.source_execution_id,
                target_depth=req.target_depth,
                method=req.transfer_method,
                target_problem_type=req.target_problem_type,
            )
            return report
        except (IncompatibleWarmStartError, IncompatibleTransferError) as exc:
            return TransferCompatibilityReport(
                is_compatible=False,
                source_depth=0,
                target_depth=req.target_depth,
                compatibility_score=0.0,
                recommended_method="none",
                notes=[str(exc)],
            )
    else:
        gamma = req.source_gamma or []
        beta = req.source_beta or []
        return ParameterTransferService.check_compatibility(
            source_gamma=gamma,
            source_beta=beta,
            target_depth=req.target_depth,
            source_problem_type=req.source_problem_type,
            target_problem_type=req.target_problem_type,
        )


@router.post("/transfer/parameters", response_model=TransferParametersResponse)
async def transfer_parameters(req: TransferParametersRequest):
    """
    Execute parameter transfer producing initial angles for a target depth.
    """
    try:
        if req.source_execution_id:
            gamma, beta, report = await ParameterTransferService.transfer_from_execution(
                execution_id=req.source_execution_id,
                target_depth=req.target_depth,
                method=req.transfer_method,
                target_problem_type=req.target_problem_type,
            )
        else:
            if req.source_gamma is None or req.source_beta is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either source_execution_id or source_gamma/source_beta must be provided."
                )
            gamma, beta, report = ParameterTransferService.transfer_parameters(
                source_gamma=req.source_gamma,
                source_beta=req.source_beta,
                target_depth=req.target_depth,
                method=req.transfer_method,
                source_problem_type=req.source_problem_type,
                target_problem_type=req.target_problem_type,
            )
        return TransferParametersResponse(
            transferred_gamma=gamma,
            transferred_beta=beta,
            target_depth=req.target_depth,
            method_used=report.recommended_method if report.recommended_method != "none" else req.transfer_method,
            compatibility_report=report,
        )
    except (IncompatibleTransferError, IncompatibleWarmStartError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


# ---------------------------------------------------------------------------
# Adaptive QAOA Execution Pipeline Endpoints (Stage 6.7)
# ---------------------------------------------------------------------------

@router.post("/execute", response_model=AdaptiveQAOAResult)
async def execute_adaptive_qaoa(req: AdaptiveQAOARequest):
    """
    Execute an Adaptive QAOA optimization process synchronously,
    returning full iteration convergence history, decisions, and decoded solution.
    """
    try:
        # Pre-validate strategy configuration
        AdaptiveStrategyFactory.validate_configuration(req.config.strategy_config)
        return AdaptiveQAOAExecutionPipeline.execute_sync(req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Adaptive QAOA execution failed: {str(exc)}",
        )


@router.post("/execute/async", response_model=AdaptiveExecutionRecord)
async def submit_adaptive_qaoa_async(req: AdaptiveQAOARequest):
    """
    Asynchronously dispatch an Adaptive QAOA optimization process to background worker threads.
    Returns immediately with an execution_id for polling.
    """
    try:
        AdaptiveStrategyFactory.validate_configuration(req.config.strategy_config)
        return await AdaptiveQAOAExecutionPipeline.submit_async(req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Adaptive QAOA dispatch failed: {str(exc)}",
        )


@router.get("/executions", response_model=List[AdaptiveExecutionRecord])
async def list_adaptive_executions(limit: int = 25):
    """List recent Adaptive QAOA execution records."""
    return await AdaptiveQAOAExecutionPipeline.list_executions(limit=limit)


@router.get("/executions/{execution_id}", response_model=AdaptiveExecutionRecord)
async def get_adaptive_execution(execution_id: str):
    """Retrieve full execution record and results for an Adaptive QAOA task."""
    record = await AdaptiveQAOAExecutionPipeline.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adaptive execution '{execution_id}' not found.",
        )
    return record


@router.get("/executions/{execution_id}/status", response_model=AdaptiveStatusResponse)
async def get_adaptive_status(execution_id: str):
    """Lightweight polling endpoint returning active depth, optimizer, and lifecycle status."""
    status_resp = await AdaptiveQAOAExecutionPipeline.get_status(execution_id)
    if not status_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adaptive execution '{execution_id}' not found.",
        )
    return status_resp


@router.post("/executions/{execution_id}/cancel", response_model=AdaptiveStatusResponse)
async def cancel_adaptive_execution(execution_id: str):
    """Trigger cooperative cancellation of an in-flight Adaptive QAOA task."""
    status_resp = await AdaptiveQAOAExecutionPipeline.cancel_execution(execution_id)
    if not status_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adaptive execution '{execution_id}' not found.",
        )
    return status_resp


