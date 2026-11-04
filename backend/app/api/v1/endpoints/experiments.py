"""Experiment endpoints (Phases 4 & 5 Coming Soon)."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.post("")
async def create_experiment() -> Dict[str, Any]:
    """Experiment dispatch (QAOA/Classical Solvers) is scheduled for Phases 4 and 5."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Solver execution (Classical / QAOA) is scheduled for Phases 4 & 5.",
    )


@router.get("")
async def list_experiments() -> List[Dict[str, Any]]:
    """List experiments (Empty list for Phase 1)."""
    return []


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str) -> Dict[str, Any]:
    """Retrieve experiment status and summary."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Experiment '{experiment_id}' not found.",
    )
