"""Domain models for formulations."""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class FormulationType(str, Enum):
    QUBO = "qubo"
    ISING = "ising"


class FormulationResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    problem_id: str
    owner_id: str = "default_user"
    formulation_type: FormulationType
    schema_version: str = "1.0"
    variable_order: List[str]
    linear_terms: Dict[str, float]
    quadratic_terms: Dict[str, float]
    offset: float = 0.0
    penalties: Dict[str, float] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
