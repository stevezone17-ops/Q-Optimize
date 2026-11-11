"""API request / response schemas for experiments."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, field_validator

from backend.app.experiments.models import (
    ExperimentAlgorithm,
    ExperimentConfiguration,
    ExperimentResourceBudget,
    ExperimentStatus,
    ExperimentResult,
    ExperimentRun,
    ExperimentMetadata,
)


class ExperimentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    problem_type: str = Field(...)
    problem_instance: Dict[str, Any] = Field(...)
    algorithms: List[ExperimentAlgorithm] = Field(
        default_factory=lambda: [ExperimentAlgorithm.SIMULATED_ANNEALING]
    )
    num_trials: int = Field(default=1, ge=1, le=50)
    seeds: Optional[List[int]] = None
    resource_budget: ExperimentResourceBudget = Field(
        default_factory=ExperimentResourceBudget
    )
    algorithm_configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    description: str = ""
    tags: List[str] = Field(default_factory=list)

    @field_validator("problem_type")
    @classmethod
    def validate_problem_type(cls, v: str) -> str:
        allowed = {"max_cut", "assignment", "tsp"}
        if v not in allowed:
            raise ValueError(f"problem_type must be one of {allowed}, got '{v}'")
        return v


class ExperimentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ExperimentSummaryResponse(BaseModel):
    experiment_id: str
    name: str
    status: ExperimentStatus
    problem_type: str
    algorithms: List[str]
    num_trials: int
    progress: float
    created_at: str
    completed_at: Optional[str] = None


class ExperimentDetailResponse(BaseModel):
    experiment_id: str
    name: str
    status: ExperimentStatus
    configuration: ExperimentConfiguration
    metadata: ExperimentMetadata
    runs: List[ExperimentRun]
    results: List[ExperimentResult]
    progress: float
    error_message: Optional[str] = None


class ExperimentListResponse(BaseModel):
    experiments: List[ExperimentSummaryResponse]
    total: int
    page: int
    page_size: int


class ExperimentStatusResponse(BaseModel):
    experiment_id: str
    status: ExperimentStatus
    progress: float
    message: str = ""
