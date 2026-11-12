"""Canonical problem schemas, domain models, and metadata specifications for Q-Optimize."""

import math
from enum import Enum
from typing import List, Tuple, Dict, Any, Optional, Union
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, model_validator, field_validator


class ProblemType(str, Enum):
    MAX_CUT = "max_cut"
    ASSIGNMENT = "assignment"
    TSP = "tsp"


class ObjectiveSense(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    DRAFT = "draft"


class VariableType(str, Enum):
    BINARY = "binary"
    INTEGER = "integer"
    CONTINUOUS = "continuous"


class VariableSpec(BaseModel):
    """Specification of mathematical variables in a canonical problem."""
    name: str = Field(..., description="Variable family or name, e.g. 'x_v', 'x_ij'")
    var_type: VariableType = Field(default=VariableType.BINARY, description="Variable domain type")
    count: int = Field(..., description="Total count of scalar decision variables")
    bounds: Tuple[float, float] = Field(default=(0.0, 1.0), description="Lower and upper bounds")
    description: str = Field(..., description="Semantic meaning of decision variable")


class ConstraintSpec(BaseModel):
    """Mathematical constraint specification."""
    name: str = Field(..., description="Constraint name")
    constraint_type: str = Field(..., description="Type: binary, partition, 1-to-1 matching, tour")
    mathematical_form: str = Field(..., description="Formal mathematical expression")
    is_hard: bool = Field(default=True, description="Whether constraint is mandatory")
    description: str = Field(..., description="Description of constraint requirement")


class ObjectiveSpec(BaseModel):
    """Mathematical objective specification."""
    sense: ObjectiveSense = Field(..., description="Optimization direction (minimize or maximize)")
    mathematical_form: str = Field(..., description="Formal algebraic objective expression")
    description: str = Field(..., description="Human-readable description of optimization target")


# ---------------------------------------------------------
# Problem Instances
# ---------------------------------------------------------

class MaxCutInstance(BaseModel):
    """
    Max-Cut graph specification: nodes and weighted or unweighted edges.
    Mathematical formulation:
        max sum_{(i,j) in E} w_{ij} * (x_i + x_j - 2*x_i*x_j)
        where x_i in {0, 1}
    """
    nodes: List[str] = Field(..., description="Unique node identifiers, e.g. ['A', 'B', 'C']")
    edges: List[Any] = Field(
        ..., 
        description="List of edges: [u, v, weight] or unweighted [u, v] (defaults to weight 1.0)"
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
        normalized_edges: List[Tuple[str, str, float]] = []

        for edge in self.edges:
            if not isinstance(edge, (list, tuple)) or len(edge) not in (2, 3):
                raise ValueError(
                    f"Each edge must be a pair [u, v] or triplet [u, v, weight]. Received: {edge}"
                )

            u = str(edge[0]).strip()
            v = str(edge[1]).strip()

            if u not in node_set or v not in node_set:
                raise ValueError(
                    f"Edge ({u}, {v}) references non-existent node. Available nodes: {self.nodes}"
                )
            if u == v:
                raise ValueError(f"Self-loops are not allowed in Max-Cut: ({u}, {u})")

            # Validate weight
            if len(edge) == 3:
                try:
                    w = float(edge[2])
                except (ValueError, TypeError):
                    raise ValueError(f"Edge weight must be a valid number, got: {edge[2]}")
                if not math.isfinite(w):
                    raise ValueError(f"Edge weight must be a finite number, got: {w}")
            else:
                w = 1.0  # Unweighted default

            # Undirected canonical pair
            canonical = tuple(sorted([u, v]))
            if canonical in seen_edges:
                raise ValueError(f"Duplicate edge detected between {u} and {v}.")
            seen_edges.add(canonical)
            normalized_edges.append((u, v, w))

        self.edges = normalized_edges
        return self


class AssignmentInstance(BaseModel):
    """
    Linear Assignment problem: agents, tasks, and cost matrix.
    Mathematical formulation:
        min sum_{i=1}^n sum_{j=1}^m c_{ij} * x_{ij}
        where x_{ij} in {0, 1}
    """
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
        for a in v:
            if not a or not str(a).strip():
                raise ValueError("Agent identifiers cannot be empty.")
        return [str(a).strip() for a in v]

    @field_validator("tasks")
    @classmethod
    def validate_tasks(cls, v: List[str]) -> List[str]:
        if len(v) < 1:
            raise ValueError("Assignment requires at least 1 task.")
        if len(v) != len(set(v)):
            raise ValueError("Task identifiers must be unique.")
        for t in v:
            if not t or not str(t).strip():
                raise ValueError("Task identifiers cannot be empty.")
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
            for j, c in enumerate(row):
                try:
                    c_val = float(c)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid cost value at [{i}][{j}]: {c}")
                if not math.isfinite(c_val):
                    raise ValueError(f"Cost value at [{i}][{j}] must be finite, got: {c_val}")
        return self


class TSPInstance(BaseModel):
    """
    Travelling Salesperson Problem: cities and distance matrix.
    Mathematical formulation:
        min sum_{k=0}^{N-1} D[tour[k], tour[k+1]]
        with tour[N] = tour[0] (closed Hamiltonian cycle)
    """
    cities: List[str] = Field(..., description="List of unique city names")
    distance_matrix: List[List[float]] = Field(
        ..., 
        description="Square distance matrix of dimension len(cities) x len(cities)"
    )
    start_city: Optional[str] = Field(
        default=None, 
        description="Optional designated starting city for tour evaluation"
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
        for c in v:
            if not c or not str(c).strip():
                raise ValueError("City names cannot be empty.")
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
                try:
                    dist_val = float(dist)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid distance at [{i}][{j}]: {dist}")
                if not math.isfinite(dist_val):
                    raise ValueError(f"Distance between {self.cities[i]} and {self.cities[j]} must be finite.")
                if i == j and dist_val != 0.0:
                    raise ValueError(f"Distance from city {self.cities[i]} to itself must be 0. Found {dist_val}.")
                if dist_val < 0.0:
                    raise ValueError(f"Distance between {self.cities[i]} and {self.cities[j]} cannot be negative ({dist_val}).")

        if self.start_city is not None:
            if self.start_city not in self.cities:
                raise ValueError(
                    f"Designated start_city '{self.start_city}' not found in cities list: {self.cities}"
                )

        return self


InstanceType = Union[MaxCutInstance, AssignmentInstance, TSPInstance]


# ---------------------------------------------------------
# Canonical Specification Builders
# ---------------------------------------------------------

def build_canonical_variables(problem_type: ProblemType, instance_data: Dict[str, Any]) -> List[VariableSpec]:
    """Derive canonical mathematical variables from problem instance data."""
    if problem_type == ProblemType.MAX_CUT:
        nodes = instance_data.get("nodes", [])
        return [
            VariableSpec(
                name="x_v",
                var_type=VariableType.BINARY,
                count=len(nodes),
                bounds=(0.0, 1.0),
                description=f"Binary partition indicator for each vertex in V (x_v in {{0, 1}} for |V|={len(nodes)} vertices)",
            )
        ]
    elif problem_type == ProblemType.ASSIGNMENT:
        agents = instance_data.get("agents", [])
        tasks = instance_data.get("tasks", [])
        total_vars = len(agents) * len(tasks)
        return [
            VariableSpec(
                name="x_ij",
                var_type=VariableType.BINARY,
                count=total_vars,
                bounds=(0.0, 1.0),
                description=f"Binary assignment indicator (1 if agent i assigned to task j, else 0; {len(agents)}x{len(tasks)}={total_vars} variables)",
            )
        ]
    elif problem_type == ProblemType.TSP:
        cities = instance_data.get("cities", [])
        n = len(cities)
        return [
            VariableSpec(
                name="x_ij_or_x_it",
                var_type=VariableType.BINARY,
                count=n * n,
                bounds=(0.0, 1.0),
                description=f"Binary indicator for directed tour step between cities or city-at-time position ({n}x{n}={n*n} variables)",
            )
        ]
    return []


def build_canonical_objective(problem_type: ProblemType) -> ObjectiveSpec:
    """Derive canonical mathematical objective specification."""
    if problem_type == ProblemType.MAX_CUT:
        return ObjectiveSpec(
            sense=ObjectiveSense.MAXIMIZE,
            mathematical_form="max sum_{(i,j) in E} w_{ij} * (x_i + x_j - 2*x_i*x_j)",
            description="Maximize the total weight of edges crossing between the two disjoint partitions S and V\\S.",
        )
    elif problem_type == ProblemType.ASSIGNMENT:
        return ObjectiveSpec(
            sense=ObjectiveSense.MINIMIZE,
            mathematical_form="min sum_{i=1}^n sum_{j=1}^m c_{ij} * x_{ij}",
            description="Minimize the total cost of assigning agents to tasks subject to 1-to-1 matching constraints.",
        )
    elif problem_type == ProblemType.TSP:
        return ObjectiveSpec(
            sense=ObjectiveSense.MINIMIZE,
            mathematical_form="min sum_{k=0}^{N-1} D[tour[k], tour[k+1]] with tour[N] = tour[0]",
            description="Minimize the total closed tour travel distance visiting every city exactly once and returning to the start.",
        )
    raise ValueError(f"Unknown problem type: {problem_type}")


def build_canonical_constraints(problem_type: ProblemType, instance_data: Dict[str, Any]) -> List[ConstraintSpec]:
    """Derive canonical constraints specification."""
    if problem_type == ProblemType.MAX_CUT:
        return [
            ConstraintSpec(
                name="Binary Partition Domain",
                constraint_type="domain",
                mathematical_form="x_v in {0, 1} for all v in V",
                is_hard=True,
                description="Each vertex must be assigned to exactly one of the two partitions (subset 0 or subset 1).",
            )
        ]
    elif problem_type == ProblemType.ASSIGNMENT:
        agents = instance_data.get("agents", [])
        tasks = instance_data.get("tasks", [])
        is_sq = len(agents) == len(tasks)
        op = "=" if is_sq else "<="
        return [
            ConstraintSpec(
                name="Agent Single Assignment",
                constraint_type="matching",
                mathematical_form=f"sum_{{j=1}}^m x_{{ij}} {op} 1 for all agents i",
                is_hard=True,
                description="Each agent must be assigned to at most one task (or exactly one for square matching).",
            ),
            ConstraintSpec(
                name="Task Single Assignment",
                constraint_type="matching",
                mathematical_form=f"sum_{{i=1}}^n x_{{ij}} {op} 1 for all tasks j",
                is_hard=True,
                description="Each task must be assigned to at most one agent (or exactly one for square matching).",
            ),
            ConstraintSpec(
                name="Binary Assignment Domain",
                constraint_type="domain",
                mathematical_form="x_{ij} in {0, 1} for all i, j",
                is_hard=True,
                description="Assignment variables are strictly binary.",
            ),
        ]
    elif problem_type == ProblemType.TSP:
        return [
            ConstraintSpec(
                name="Visit Every City Exactly Once",
                constraint_type="hamiltonian",
                mathematical_form="|set(tour)| = |cities| and len(tour) = |cities| + 1",
                is_hard=True,
                description="The tour must visit each city exactly once before returning to the start.",
            ),
            ConstraintSpec(
                name="Closed Hamiltonian Cycle",
                constraint_type="cycle",
                mathematical_form="tour[N] = tour[0]",
                is_hard=True,
                description="The tour must return to the initial starting city.",
            ),
            ConstraintSpec(
                name="Sub-tour Elimination",
                constraint_type="subtour",
                mathematical_form="No disconnected closed sub-loops disjoint from main tour",
                is_hard=True,
                description="No disjoint cycles or disconnected sub-paths are permitted.",
            ),
        ]
    return []


def build_canonical_metadata(problem_type: ProblemType, instance_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compute mathematical statistics and structural metadata for the problem instance."""
    meta: Dict[str, Any] = {}

    if problem_type == ProblemType.MAX_CUT:
        nodes = instance_data.get("nodes", [])
        edges = instance_data.get("edges", [])
        n = len(nodes)
        e = len(edges)
        max_possible_edges = (n * (n - 1)) // 2 if n >= 2 else 1
        density = (e / max_possible_edges) if max_possible_edges > 0 else 0.0

        weights = [float(edge[2]) if len(edge) >= 3 else 1.0 for edge in edges]
        min_w = min(weights) if weights else 0.0
        max_w = max(weights) if weights else 0.0
        sum_w = sum(weights) if weights else 0.0
        avg_w = (sum_w / e) if e > 0 else 0.0

        # Degree calculation and connectivity check (BFS)
        adj: Dict[str, List[str]] = {n_id: [] for n_id in nodes}
        for edge in edges:
            u, v = edge[0], edge[1]
            adj[u].append(v)
            adj[v].append(u)

        degrees = [len(adj[n_id]) for n_id in nodes]
        min_deg = min(degrees) if degrees else 0
        max_deg = max(degrees) if degrees else 0
        avg_deg = (sum(degrees) / n) if n > 0 else 0.0

        # Connected components via BFS
        visited = set()
        components = 0
        for node in nodes:
            if node not in visited:
                components += 1
                queue = [node]
                visited.add(node)
                while queue:
                    curr = queue.pop(0)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

        meta = {
            "node_count": n,
            "edge_count": e,
            "graph_density": round(density, 4),
            "is_connected": components <= 1,
            "connected_components_count": components,
            "total_weight": sum_w,
            "min_edge_weight": min_w,
            "max_edge_weight": max_w,
            "average_edge_weight": round(avg_w, 4),
            "min_degree": min_deg,
            "max_degree": max_deg,
            "average_degree": round(avg_deg, 2),
        }

    elif problem_type == ProblemType.ASSIGNMENT:
        agents = instance_data.get("agents", [])
        tasks = instance_data.get("tasks", [])
        cost_matrix = instance_data.get("cost_matrix", [])
        flat_costs = [float(cell) for row in cost_matrix for cell in row]

        min_c = min(flat_costs) if flat_costs else 0.0
        max_c = max(flat_costs) if flat_costs else 0.0
        sum_c = sum(flat_costs) if flat_costs else 0.0
        avg_c = (sum_c / len(flat_costs)) if flat_costs else 0.0

        meta = {
            "agent_count": len(agents),
            "task_count": len(tasks),
            "is_square": len(agents) == len(tasks),
            "matrix_cells": len(flat_costs),
            "min_cost": min_c,
            "max_cost": max_c,
            "average_cost": round(avg_c, 4),
        }

    elif problem_type == ProblemType.TSP:
        cities = instance_data.get("cities", [])
        distance_matrix = instance_data.get("distance_matrix", [])
        start_city = instance_data.get("start_city", None)
        n = len(cities)

        # Symmetry check
        is_symmetric = True
        flat_distances = []
        for i in range(n):
            for j in range(n):
                if i != j and i < len(distance_matrix) and j < len(distance_matrix[i]):
                    d = float(distance_matrix[i][j])
                    flat_distances.append(d)
                if j > i and i < len(distance_matrix) and j < len(distance_matrix[i]):
                    if distance_matrix[i][j] != distance_matrix[j][i]:
                        is_symmetric = False

        min_d = min(flat_distances) if flat_distances else 0.0
        max_d = max(flat_distances) if flat_distances else 0.0
        sum_d = sum(flat_distances) if flat_distances else 0.0
        avg_d = (sum_d / len(flat_distances)) if flat_distances else 0.0

        meta = {
            "city_count": n,
            "is_symmetric": is_symmetric,
            "start_city": start_city or (cities[0] if cities else None),
            "total_directed_edges": len(flat_distances),
            "min_distance": min_d,
            "max_distance": max_d,
            "average_distance": round(avg_d, 4),
        }

    return meta


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
    validation_status: ValidationStatus = Field(default=ValidationStatus.VALID)
    variables: List[VariableSpec] = Field(default_factory=list)
    objective: Optional[ObjectiveSpec] = None
    constraints: List[ConstraintSpec] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    instance: Dict[str, Any]
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProblemValidationResponse(BaseModel):
    """Result of checking a problem definition against domain constraints."""
    problem_id: Optional[str] = None
    is_valid: bool
    status: ValidationStatus
    issues: List[str] = Field(default_factory=list)
    variables: List[VariableSpec] = Field(default_factory=list)
    constraints: List[ConstraintSpec] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProblemTypeInfo(BaseModel):
    """Metadata describing a supported optimization problem type."""
    type: ProblemType
    name: str
    family: str
    objective_sense: ObjectiveSense
    mathematical_form: str
    description: str
    variable_description: str
    supported_constraints: List[str]
    sample_instance: Dict[str, Any]


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
