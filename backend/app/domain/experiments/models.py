"""Domain models for experiments and jobs."""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentCreate(BaseModel):
    problem_id: str
    solver_name: str
    solver_config: Dict[str, Any] = Field(default_factory=dict)


class ExperimentResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str = "default_user"
    problem_id: str
    formulation_id: Optional[str] = None
    solver_name: str
    solver_config: Dict[str, Any]
    status: ExperimentStatus = ExperimentStatus.QUEUED
    environment: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
