"""Domain models for benchmark datasets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    dataset_id: str
    name: str
    problem_type: str
    generator_type: str
    generator_params: Dict[str, Any] = Field(default_factory=dict)
    fingerprint: str = ""  # SHA-256 of canonical instance content
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    num_instances: int = 0
    tags: List[str] = Field(default_factory=list)
    description: str = ""


class ProblemInstance(BaseModel):
    instance_id: str
    dataset_id: str
    problem_type: str
    instance_data: Dict[str, Any]
    fingerprint: str = ""
    seed: Optional[int] = None


class BenchmarkDataset(BaseModel):
    metadata: DatasetMetadata
    instances: List[ProblemInstance] = Field(default_factory=list)
