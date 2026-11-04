"""Formulation endpoints (Phase 3 Coming Soon)."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/formulations", tags=["Formulations"])


@router.post("/generate")
async def generate_formulation() -> Dict[str, Any]:
    """QUBO and Ising generation are scheduled for Phase 3."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Formulation generation (QUBO/Ising) is scheduled for Phase 3. Canonical problem definition is active in Phase 1.",
    )


@router.get("/{formulation_id}")
async def get_formulation(formulation_id: str) -> Dict[str, Any]:
    """Retrieve formulation (Phase 3)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Formulation retrieval is scheduled for Phase 3.",
    )
