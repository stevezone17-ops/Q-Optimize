"""Domain models and schemas for QUBO and Ising formulations."""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class FormulationType(str, Enum):
    QUBO = "qubo"
    ISING = "ising"


class QuboModel(BaseModel):
    """
    Canonical representation of a Quadratic Unconstrained Binary Optimization problem:
        min x^T Q x + c = sum_i Q_ii x_i + sum_{i < j} Q_ij x_i x_j + c
    Upper-triangular storage convention:
        - Diagonal entries Q_ii are stored in linear_terms or matrix diagonal.
        - Off-diagonal entries Q_ij (i < j) are stored in quadratic_terms.
        - No double-counting of off-diagonal interactions.
    """
    variable_order: List[str] = Field(..., description="Ordered list of binary decision variable names")
    linear_terms: Dict[str, float] = Field(default_factory=dict, description="Diagonal coefficients Q_ii for each variable")
    quadratic_terms: Dict[str, float] = Field(
        default_factory=dict, 
        description="Upper-triangular interaction coefficients Q_ij with key format 'var_i,var_j' (i < j)"
    )
    offset: float = Field(default=0.0, description="Scalar constant offset c")
    matrix: Optional[List[List[float]]] = Field(default=None, description="Optional full n x n upper-triangular matrix")
    penalties: Dict[str, float] = Field(default_factory=dict, description="Constraint penalty coefficients used")
    assumptions: List[str] = Field(default_factory=list, description="Modeling assumptions and boundary conditions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Structural statistics and instance properties")


class IsingModel(BaseModel):
    """
    Canonical representation of an Ising spin Hamiltonian:
        H = C + sum_i h_i Z_i + sum_{i < j} J_ij Z_i Z_j
    with spin convention:
        x_i = (1 - Z_i) / 2,  where Z_i in {-1, +1}
    """
    variable_order: List[str] = Field(..., description="Ordered list of spin variable names (Z_i)")
    local_fields: Dict[str, float] = Field(default_factory=dict, description="Local on-site magnetic fields h_i")
    couplings: Dict[str, float] = Field(
        default_factory=dict, 
        description="Two-body coupling strengths J_ij with key format 'Z_i,Z_j' (i < j)"
    )
    offset: float = Field(default=0.0, description="Ising constant energy offset C")
    spin_mapping: Dict[str, str] = Field(
        default_factory=dict, 
        description="Mapping from binary variables to spin variables (e.g. x_0 -> Z_0)"
    )
    latex_expression: Optional[str] = Field(default=None, description="LaTeX formatted Hamiltonian string")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Transformation properties and validation metadata")


class FormulationResponse(BaseModel):
    """Unified API response for stored or generated formulations."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    problem_id: Optional[str] = None
    owner_id: str = "default_user"
    formulation_type: FormulationType
    schema_version: str = "1.0"
    qubo: Optional[QuboModel] = None
    ising: Optional[IsingModel] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GenerateQuboRequest(BaseModel):
    """Request payload for generating a QUBO formulation."""
    problem_id: Optional[str] = Field(default=None, description="Registered problem ID to formulate")
    problem_type: Optional[str] = Field(default=None, description="Problem type if formulating ad-hoc instance")
    instance: Optional[Dict[str, Any]] = Field(default=None, description="Ad-hoc problem instance data")
    penalty_coefficients: Optional[Dict[str, float]] = Field(default=None, description="Custom penalty parameters A, B")


class GenerateIsingRequest(BaseModel):
    """Request payload for converting a QUBO to an Ising Hamiltonian."""
    qubo: QuboModel = Field(..., description="Canonical QUBO model to convert")


class VerificationResult(BaseModel):
    """Result of independent exhaustive mathematical verification."""
    is_verified: bool = Field(..., description="True if QUBO and Ising energies match across all tested states")
    num_states_tested: int = Field(..., description="Total binary states enumerated (2^n)")
    max_energy_discrepancy: float = Field(..., description="Maximum absolute difference |E_qubo - H_ising|")
    tolerance: float = Field(default=1e-8, description="Numerical comparison tolerance")
    feasible_states_count: int = Field(..., description="Number of states satisfying all original constraints")
    min_qubo_energy: float = Field(..., description="Minimum energy found among all enumerated states")
    min_ising_energy: float = Field(..., description="Minimum Ising energy found")
    optimal_bitstring: str = Field(..., description="Binary string yielding minimal energy")
    feasibility_summary: str = Field(..., description="Summary of constraint penalty behavior")
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list, description="Sample of mismatched states if any")
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
