"""FastAPI Endpoints for Adaptive QAOA Research & Dynamic Parameter Strategies."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.app.solvers.quantum.adaptive.strategy_registry import AdaptiveStrategyRegistry
from backend.app.solvers.quantum.adaptive.strategy_factory import AdaptiveStrategyFactory
from backend.app.solvers.quantum.adaptive.base_strategy import StrategyMetadata
from backend.app.solvers.quantum.adaptive.adaptive_models import (
    AdaptiveQAOARequest,
    AdaptiveStrategyConfiguration,
)
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import (
    AdaptiveStrategyNotFoundError,
    AdaptiveQAOAError,
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
