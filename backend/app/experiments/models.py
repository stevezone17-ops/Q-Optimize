"""Pydantic v2 domain models for the experiments subsystem."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    VALIDATING = "validating"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class ExperimentAlgorithm(str, Enum):
    EXACT = "exact"
    GENETIC_ALGORITHM = "genetic_algorithm"
    SIMULATED_ANNEALING = "simulated_annealing"
    QAOA = "qaoa"
    ADAPTIVE_QAOA = "adaptive_qaoa"


class ExperimentResourceBudget(BaseModel):
    max_runtime_seconds: float = Field(default=300.0, ge=1.0, le=3600.0)
    max_shots: int = Field(default=1024, ge=1, le=100000)
    max_qaoa_layers: int = Field(default=5, ge=1, le=20)
    max_iterations: int = Field(default=1000, ge=1, le=100000)
    max_workers: int = Field(default=4, ge=1, le=16)


class ExperimentConfiguration(BaseModel):
    algorithms: List[ExperimentAlgorithm] = Field(
        default_factory=lambda: [ExperimentAlgorithm.SIMULATED_ANNEALING]
    )
    problem_type: str = Field(..., description="Problem type: max_cut | assignment | tsp")
    problem_instance: Dict[str, Any] = Field(
        ..., description="Problem instance parameters"
    )
    num_trials: int = Field(default=1, ge=1, le=50)
    seeds: Optional[List[int]] = Field(default=None)
    resource_budget: ExperimentResourceBudget = Field(
        default_factory=ExperimentResourceBudget
    )
    algorithm_configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    description: str = Field(default="")
    tags: List[str] = Field(default_factory=list)

    @field_validator("problem_type")
    @classmethod
    def validate_problem_type(cls, v: str) -> str:
        allowed = {"max_cut", "assignment", "tsp"}
        if v not in allowed:
            raise ValueError(f"problem_type must be one of {allowed}, got '{v}'")
        return v


class ExperimentMetadata(BaseModel):
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    python_version: str = ""
    platform: str = ""
    qiskit_version: str = ""
    numpy_version: str = ""
    scipy_version: str = ""
    reproducibility_hash: str = ""


class ExperimentResult(BaseModel):
    algorithm: str
    trial_index: int = 0
    seed: Optional[int] = None
    objective_value: Optional[float] = None
    best_solution: Optional[Dict[str, Any]] = None
    runtime_seconds: float = 0.0
    is_feasible: bool = False
    num_evaluations: int = 0
    convergence_history: List[float] = Field(default_factory=list)
    algorithm_metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    status: str = "pending"


class ExperimentRun(BaseModel):
    run_id: str
    experiment_id: str
    algorithm: str
    trial_index: int = 0
    seed: Optional[int] = None
    status: ExperimentStatus = ExperimentStatus.QUEUED
    result: Optional[ExperimentResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class Experiment(BaseModel):
    experiment_id: str
    name: str
    configuration: ExperimentConfiguration
    status: ExperimentStatus = ExperimentStatus.DRAFT
    metadata: ExperimentMetadata = Field(default_factory=ExperimentMetadata)
    runs: List[ExperimentRun] = Field(default_factory=list)
    results: List[ExperimentResult] = Field(default_factory=list)
    error_message: Optional[str] = None
    progress: float = 0.0  # 0.0 – 1.0
