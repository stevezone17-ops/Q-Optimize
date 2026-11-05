"""Structured models for objective evaluation and candidate verification."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
from backend.app.evaluation.constraints import ConstraintViolation


class ObjectiveSense(str, Enum):
    """Optimization objective direction."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class CandidateSolution(BaseModel):
    """Container for a candidate optimization solution."""
    assignment: Any = Field(..., description="Candidate assignment, partition, or tour")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional solver or candidate metadata")


class EvaluationResult(BaseModel):
    """Independent evaluation verification result."""
    problem_id: Optional[str] = Field(default=None, description="Problem identifier if evaluated from registered problem")
    problem_type: str = Field(..., description="Problem type: max_cut, assignment, tsp")
    objective_sense: ObjectiveSense = Field(..., description="Optimization direction (minimize/maximize)")
    objective_value: float = Field(..., description="Calculated objective value")
    is_feasible: bool = Field(..., description="True if candidate satisfies all problem constraints strictly")
    violations: List[ConstraintViolation] = Field(default_factory=list, description="Structured constraint violations")
    details: Dict[str, Any] = Field(default_factory=dict, description="Domain-specific details (partitions, legs, costs)")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluationRequest(BaseModel):
    """API request schema for evaluating a candidate solution."""
    candidate: Any = Field(..., description="Candidate partition (MaxCut), assignment (Assignment), or tour (TSP)")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Optional evaluation settings")
