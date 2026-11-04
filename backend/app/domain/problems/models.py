"""Canonical problem schemas and domain models for Q-Optimize."""

from enum import Enum
from typing import List, Tuple, Dict, Any, Optional, Union
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, model_validator, field_validator


class ProblemType(str, Enum):
    MAX_CUT = "max_cut"
    ASSIGNMENT = "assignment"
    TSP = "tsp"


# ---------------------------------------------------------
# Problem Instances
# ---------------------------------------------------------

class MaxCutInstance(BaseModel):
    """Max-Cut graph specification: nodes and weighted edges."""
    nodes: List[str] = Field(..., description="Unique node identifiers, e.g. ['A', 'B', 'C']")
    edges: List[Tuple[str, str, float]] = Field(
        ..., 
        description="List of weighted edges [u, v, weight] where u and v are node identifiers"
    )

    @field_validator("nodes")
    @classmethod
    def validate_nodes(cls, v: List[str]) -> List[str]:
        if len(v) < 2:
            raise ValueError("Max-Cut requires at least 2 nodes.")
        if len(v) != len(set(v)):
            raise ValueError("Node names must be unique.")
        for node in v:
            if not node or not str(node).strip():
                raise ValueError("Node names cannot be empty.")
        return [str(n).strip() for n in v]

    @model_validator(mode="after")
    def validate_edges(self) -> "MaxCutInstance":
        node_set = set(self.nodes)
        seen_edges = set()
        for edge in self.edges:
            if len(edge) != 3:
                raise ValueError(f"Each edge must be a triplet [u, v, weight]. Received: {edge}")
            u, v, w = edge
            if u not in node_set or v not in node_set:
                raise ValueError(f"Edge ({u}, {v}) references non-existent node. Available nodes: {self.nodes}")
            if u == v:
                raise ValueError(f"Self-loops are not allowed in Max-Cut: ({u}, {u})")
            
            # Undirected canonical pair
            canonical = tuple(sorted([u, v]))
            if canonical in seen_edges:
                raise ValueError(f"Duplicate edge detected between {u} and {v}.")
            seen_edges.add(canonical)
        return self


class AssignmentInstance(BaseModel):
    """Linear Assignment problem: agents, tasks, and cost matrix."""
    agents: List[str] = Field(..., description="List of unique agent names")
    tasks: List[str] = Field(..., description="List of unique task names")
    cost_matrix: List[List[float]] = Field(
        ..., 
        description="2D cost matrix of dimension len(agents) x len(tasks)"
    )

    @field_validator("agents")
    @classmethod
    def validate_agents(cls, v: List[str]) -> List[str]:
        if len(v) < 1:
            raise ValueError("Assignment requires at least 1 agent.")
        if len(v) != len(set(v)):
            raise ValueError("Agent identifiers must be unique.")
        return [str(a).strip() for a in v]

    @field_validator("tasks")
    @classmethod
    def validate_tasks(cls, v: List[str]) -> List[str]:
        if len(v) < 1:
            raise ValueError("Assignment requires at least 1 task.")
        if len(v) != len(set(v)):
            raise ValueError("Task identifiers must be unique.")
        return [str(t).strip() for t in v]

    @model_validator(mode="after")
    def validate_matrix(self) -> "AssignmentInstance":
        num_agents = len(self.agents)
        num_tasks = len(self.tasks)
        if len(self.cost_matrix) != num_agents:
            raise ValueError(
                f"Cost matrix row count ({len(self.cost_matrix)}) does not match agent count ({num_agents})."
            )
        for i, row in enumerate(self.cost_matrix):
            if len(row) != num_tasks:
                raise ValueError(
                    f"Cost matrix row {i} length ({len(row)}) does not match task count ({num_tasks})."
                )
        return self


class TSPInstance(BaseModel):
    """Travelling Salesperson Problem: cities and distance matrix."""
    cities: List[str] = Field(..., description="List of unique city names")
    distance_matrix: List[List[float]] = Field(
        ..., 
        description="Square distance matrix of dimension len(cities) x len(cities)"
    )
    coordinates: Optional[Dict[str, Tuple[float, float]]] = Field(
        default=None, 
        description="Optional 2D planar coordinates for visualization"
    )

    @field_validator("cities")
    @classmethod
    def validate_cities(cls, v: List[str]) -> List[str]:
        if len(v) < 3:
            raise ValueError("TSP requires at least 3 cities.")
        if len(v) != len(set(v)):
            raise ValueError("City names must be unique.")
        return [str(c).strip() for c in v]

    @model_validator(mode="after")
    def validate_matrix(self) -> "TSPInstance":
        n = len(self.cities)
        if len(self.distance_matrix) != n:
            raise ValueError(
                f"Distance matrix must be square with size {n}x{n}. Found {len(self.distance_matrix)} rows."
            )
        for i, row in enumerate(self.distance_matrix):
            if len(row) != n:
                raise ValueError(
                    f"Row {i} has length {len(row)}, expected {n}."
                )
            for j, dist in enumerate(row):
                if i == j and dist != 0:
                    raise ValueError(f"Distance from city {self.cities[i]} to itself must be 0. Found {dist}.")
                if dist < 0:
                    raise ValueError(f"Distance between {self.cities[i]} and {self.cities[j]} cannot be negative ({dist}).")
        return self


InstanceType = Union[MaxCutInstance, AssignmentInstance, TSPInstance]


# ---------------------------------------------------------
# Problem CRUD Schemas
# ---------------------------------------------------------

class ProblemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    problem_type: ProblemType
    description: Optional[str] = Field(default="", max_length=1000)
    instance: Dict[str, Any] = Field(..., description="Problem instance data according to problem_type schema")

    def parse_instance(self) -> InstanceType:
        if self.problem_type == ProblemType.MAX_CUT:
            return MaxCutInstance.model_validate(self.instance)
        elif self.problem_type == ProblemType.ASSIGNMENT:
            return AssignmentInstance.model_validate(self.instance)
        elif self.problem_type == ProblemType.TSP:
            return TSPInstance.model_validate(self.instance)
        raise ValueError(f"Unsupported problem type: {self.problem_type}")


class ProblemResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str = "anonymous_or_default"
    name: str
    problem_type: ProblemType
    schema_version: str = "1.0"
    description: str = ""
    instance: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------
# Natural Language Draft Schemas (Human-confirmed AI Draft)
# ---------------------------------------------------------

class ProblemDraftRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=2000, description="Natural language problem description")
    problem_type_hint: Optional[ProblemType] = None


class ProblemDraftResponse(BaseModel):
    """Draft proposed problem for user review. Must be confirmed before creating a canonical problem."""
    problem_type: ProblemType
    name: str
    description: str
    objective: Dict[str, Any]
    entities: Dict[str, Any]
    data: Dict[str, Any]
    constraints: List[str]
    assumptions: List[str]
    missing_information: List[str]
    suggested_instance: Dict[str, Any]
    requires_user_confirmation: bool = True
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)
    disclaimer: str = (
        "This is an AI-generated draft proposal. Review entities, costs/weights, "
        "and constraints before confirming. Natural language parsing is draft-only."
    )
