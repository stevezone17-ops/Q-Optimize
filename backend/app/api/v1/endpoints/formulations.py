"""Formulation endpoints for QUBO and Ising generation, conversion, and verification."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from backend.app.domain.formulations.models import (
    QuboModel,
    IsingModel,
    FormulationResponse,
    GenerateQuboRequest,
    GenerateIsingRequest,
    VerificationResult,
)
from backend.app.services.formulation_service import FormulationService
from backend.app.formulations.engine import FormulationEngine

router = APIRouter(prefix="/formulations", tags=["Formulations"])
_engine = FormulationEngine()


class VerifyFormulationRequest(BaseModel):
    formulation_id: Optional[str] = Field(default=None, description="ID of stored formulation to verify")
    problem_id: Optional[str] = Field(default=None, description="ID of registered problem to formulate and verify")
    problem_type: Optional[str] = Field(default=None, description="Problem type for direct instance verification")
    instance: Optional[Dict[str, Any]] = Field(default=None, description="Instance data for direct verification")
    qubo: Optional[QuboModel] = Field(default=None, description="Optional custom QUBO model to verify")


@router.post("/generate", response_model=FormulationResponse, status_code=status.HTTP_201_CREATED)
async def generate_formulation(req: GenerateQuboRequest) -> FormulationResponse:
    """
    Generate canonical QUBO and corresponding Ising spin Hamiltonian for a problem.
    Supports either a registered problem ID or direct problem instance data.
    """
    try:
        return await FormulationService.generate_formulation(req)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY if "not found" not in str(val_err).lower() else status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Formulation generation failed: {str(e)}",
        )


@router.post("/qubo", response_model=QuboModel)
async def generate_qubo_only(req: GenerateQuboRequest) -> QuboModel:
    """Generate and return canonical QUBO model directly."""
    try:
        formulation = await FormulationService.generate_formulation(req)
        if not formulation.qubo:
            raise ValueError("QUBO generation failed to produce a valid model.")
        return formulation.qubo
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY if "not found" not in str(val_err).lower() else status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QUBO generation failed: {str(e)}",
        )


@router.post("/ising", response_model=IsingModel)
async def convert_qubo_to_ising(req: GenerateIsingRequest) -> IsingModel:
    """Convert an existing QUBO model to its equivalent Ising spin Hamiltonian."""
    try:
        return _engine.qubo_to_ising(req.qubo)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"QUBO-to-Ising conversion failed: {str(e)}",
        )


@router.post("/verify", response_model=VerificationResult)
async def verify_formulation(req: VerifyFormulationRequest) -> VerificationResult:
    """
    Exhaustively verify mathematical equivalence across all 2^n states between:
    - Original canonical objective C(x) (via Phase 2 evaluators)
    - Generated QUBO energy E_QUBO(x)
    - Transformed Ising Hamiltonian H_Ising(Z)
    """
    try:
        return await FormulationService.verify_formulation(
            formulation_id=req.formulation_id,
            problem_id=req.problem_id,
            problem_type=req.problem_type,
            instance=req.instance,
            qubo=req.qubo,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY if "not found" not in str(val_err).lower() else status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Formulation verification failed: {str(e)}",
        )


@router.get("/{formulation_id}", response_model=FormulationResponse)
async def get_formulation(formulation_id: str) -> FormulationResponse:
    """Retrieve stored formulation by ID."""
    formulation = await FormulationService.get_formulation(formulation_id)
    if not formulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulation with ID '{formulation_id}' was not found.",
        )
    return formulation


@router.get("/{formulation_id}/metadata", response_model=Dict[str, Any])
async def get_formulation_metadata(formulation_id: str) -> Dict[str, Any]:
    """Retrieve formulation statistics, variable order, and penalty parameters."""
    formulation = await FormulationService.get_formulation(formulation_id)
    if not formulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulation with ID '{formulation_id}' was not found.",
        )
    return {
        "formulation_id": formulation.id,
        "problem_id": formulation.problem_id,
        "formulation_type": formulation.formulation_type,
        "qubo_metadata": formulation.qubo.metadata if formulation.qubo else None,
        "ising_metadata": formulation.ising.metadata if formulation.ising else None,
        "variable_order": formulation.qubo.variable_order if formulation.qubo else [],
        "penalties": formulation.qubo.penalties if formulation.qubo else {},
        "created_at": formulation.created_at,
    }


@router.get("/{formulation_id}/export", response_model=Dict[str, Any])
async def export_formulation(
    formulation_id: str,
    format: str = Query("all", description="Export format: dense, sparse, latex, or all")
) -> Dict[str, Any]:
    """Export QUBO matrix and Ising coefficients in structured format."""
    formulation = await FormulationService.get_formulation(formulation_id)
    if not formulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulation with ID '{formulation_id}' was not found.",
        )

    export_data: Dict[str, Any] = {
        "formulation_id": formulation.id,
        "format": format,
    }

    if formulation.qubo:
        if format in ("dense", "all"):
            export_data["qubo_dense_matrix"] = formulation.qubo.matrix
        if format in ("sparse", "all"):
            export_data["qubo_linear_terms"] = formulation.qubo.linear_terms
            export_data["qubo_quadratic_terms"] = formulation.qubo.quadratic_terms
            export_data["qubo_offset"] = formulation.qubo.offset

    if formulation.ising:
        if format in ("latex", "all"):
            export_data["ising_latex"] = formulation.ising.latex_expression
        if format in ("sparse", "all"):
            export_data["ising_local_fields"] = formulation.ising.local_fields
            export_data["ising_couplings"] = formulation.ising.couplings
            export_data["ising_offset"] = formulation.ising.offset

    return export_data
