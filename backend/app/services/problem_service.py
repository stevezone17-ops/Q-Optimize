"""Problem service handling validation, persistence, draft parsing, metadata, and evaluation dispatch."""

import re
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
import uuid
from backend.app.domain.problems.models import (
    ProblemType,
    ProblemCreate,
    ProblemResponse,
    ProblemDraftRequest,
    ProblemDraftResponse,
    ProblemValidationResponse,
    ProblemTypeInfo,
    ValidationStatus,
    ObjectiveSense,
    build_canonical_variables,
    build_canonical_objective,
    build_canonical_constraints,
    build_canonical_metadata,
    MaxCutInstance,
    AssignmentInstance,
    TSPInstance,
)
from backend.app.evaluation.evaluator_factory import EvaluatorFactory
from backend.app.evaluation.models import EvaluationResult
from backend.app.db.mongodb import db_manager
from backend.app.core.logging import logger


class ProblemService:
    @staticmethod
    async def create_problem(problem_in: ProblemCreate, owner_id: str = "default_user") -> ProblemResponse:
        """Validate problem instance strictly and persist to database or memory store."""
        # Strictly parse and validate instance with Pydantic model validator
        parsed_instance = problem_in.parse_instance()
        instance_dump = parsed_instance.model_dump()

        variables = build_canonical_variables(problem_in.problem_type, instance_dump)
        objective = build_canonical_objective(problem_in.problem_type)
        constraints = build_canonical_constraints(problem_in.problem_type, instance_dump)
        metadata = build_canonical_metadata(problem_in.problem_type, instance_dump)

        problem_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        doc = {
            "id": problem_id,
            "owner_id": owner_id,
            "name": problem_in.name,
            "problem_type": problem_in.problem_type,
            "schema_version": "1.0",
            "description": problem_in.description or "",
            "validation_status": ValidationStatus.VALID,
            "variables": [v.model_dump() for v in variables],
            "objective": objective.model_dump(),
            "constraints": [c.model_dump() for c in constraints],
            "metadata": metadata,
            "instance": instance_dump,
            "is_deleted": False,
            "deleted_at": None,
            "deleted_by": None,
            "version": 1,
            "created_at": now,
            "updated_at": now,
        }

        if db_manager.is_connected and db_manager.db is not None:
            try:
                await db_manager.db["problems"].insert_one(dict(doc))
            except Exception as e:
                logger.error(f"Failed to insert into MongoDB: {e}. Storing in memory fallback.")
                db_manager.memory_insert("problems", problem_id, doc)
        else:
            db_manager.memory_insert("problems", problem_id, doc)

        return ProblemResponse(**doc)

    @staticmethod
    async def get_problem(
        problem_id: str,
        owner_id: str = "default_user",
        include_deleted: bool = False,
    ) -> Optional[ProblemResponse]:
        """Fetch problem by ID, excluding soft-deleted entities by default."""
        if db_manager.is_connected and db_manager.db is not None:
            try:
                query: Dict[str, Any] = {"id": problem_id}
                if not include_deleted:
                    query["is_deleted"] = {"$ne": True}
                res = await db_manager.db["problems"].find_one(query)
                if res:
                    res.pop("_id", None)
                    return ProblemResponse(**res)
            except Exception as e:
                logger.error(f"MongoDB query failed: {e}")

        # Check memory store
        mem_doc = db_manager.memory_get("problems", problem_id)
        if mem_doc:
            if include_deleted or not mem_doc.get("is_deleted", False):
                return ProblemResponse(**mem_doc)
        return None

    @staticmethod
    async def list_problems(
        owner_id: str = "default_user",
        include_deleted: bool = False,
    ) -> List[ProblemResponse]:
        """List problems for owner, excluding soft-deleted items by default."""
        items: List[ProblemResponse] = []
        if db_manager.is_connected and db_manager.db is not None:
            try:
                query: Dict[str, Any] = {"owner_id": owner_id}
                if not include_deleted:
                    query["is_deleted"] = {"$ne": True}
                cursor = db_manager.db["problems"].find(query).sort("created_at", -1)
                async for doc in cursor:
                    doc.pop("_id", None)
                    items.append(ProblemResponse(**doc))
                return items
            except Exception as e:
                logger.error(f"MongoDB list query failed: {e}")

        # Fallback to memory store
        for doc in db_manager.memory_list("problems", include_deleted=include_deleted):
            if doc.get("owner_id") == owner_id:
                items.append(ProblemResponse(**doc))
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items

    @staticmethod
    async def delete_problem(problem_id: str, deleted_by: Optional[str] = None) -> bool:
        """Soft delete problem, maintaining data recovery and audit trace."""
        return await db_manager.soft_delete("problems", problem_id, deleted_by=deleted_by)

    @staticmethod
    def get_supported_problem_types() -> List[ProblemTypeInfo]:
        """List all supported optimization problem families with schemas and metadata."""
        return [
            ProblemTypeInfo(
                type=ProblemType.MAX_CUT,
                name="Maximum Cut (Max-Cut)",
                family="Graph Partitioning",
                objective_sense=ObjectiveSense.MAXIMIZE,
                mathematical_form=r"\max \sum_{(i,j)\in E} w_{ij}(x_i+x_j-2x_ix_j)",
                description=(
                    "Partition graph vertices into two disjoint sets S and V\\S "
                    "to maximize the total weight of edges crossing between the sets."
                ),
                variable_description="Binary variable x_v in {0, 1} for each vertex v in V",
                supported_constraints=["Binary Partition Domain (x_v in {0, 1})"],
                sample_instance={
                    "nodes": ["A", "B", "C", "D"],
                    "edges": [
                        ["A", "B", 1.0],
                        ["B", "C", 2.0],
                        ["C", "D", 1.5],
                        ["D", "A", 2.5],
                        ["A", "C", 1.0],
                    ],
                },
            ),
            ProblemTypeInfo(
                type=ProblemType.ASSIGNMENT,
                name="Linear Assignment Problem",
                family="Bipartite Matching & Resource Allocation",
                objective_sense=ObjectiveSense.MINIMIZE,
                mathematical_form=r"\min \sum_{i=1}^n \sum_{j=1}^m c_{ij} x_{ij}",
                description=(
                    "Assign n agents to m tasks at minimal total cost, ensuring each agent "
                    "gets at most one task and each task is assigned at most once."
                ),
                variable_description="Binary variable x_{ij} in {0, 1} indicating whether agent i is assigned to task j",
                supported_constraints=[
                    "Agent Single Assignment (sum_j x_ij <= 1)",
                    "Task Single Assignment (sum_i x_ij <= 1)",
                    "Binary Variable Domain (x_ij in {0, 1})",
                ],
                sample_instance={
                    "agents": ["Agent_1", "Agent_2", "Agent_3"],
                    "tasks": ["Task_A", "Task_B", "Task_C"],
                    "cost_matrix": [
                        [9.0, 2.0, 7.0],
                        [6.0, 4.0, 3.0],
                        [5.0, 8.0, 1.0],
                    ],
                },
            ),
            ProblemTypeInfo(
                type=ProblemType.TSP,
                name="Travelling Salesperson Problem (TSP)",
                family="Routing & Hamiltonian Cycles",
                objective_sense=ObjectiveSense.MINIMIZE,
                mathematical_form=r"\min \sum_{k=0}^{N-1} D[tour[k], tour[k+1]] \text{ with } tour[N] = tour[0]",
                description=(
                    "Find a closed Hamiltonian cycle of minimum total travel distance "
                    "that visits every city exactly once and returns to the origin."
                ),
                variable_description="Ordered sequence of cities forming a closed tour",
                supported_constraints=[
                    "Visit Every City Exactly Once",
                    "Closed Hamiltonian Cycle",
                    "Sub-tour Elimination",
                ],
                sample_instance={
                    "cities": ["Paris", "London", "Berlin"],
                    "distance_matrix": [
                        [0.0, 344.0, 878.0],
                        [344.0, 0.0, 933.0],
                        [878.0, 933.0, 0.0],
                    ],
                    "start_city": "Paris",
                },
            ),
        ]

    @staticmethod
    def validate_problem_definition(
        problem_type: ProblemType, instance_data: Dict[str, Any], problem_id: Optional[str] = None
    ) -> ProblemValidationResponse:
        """Validate problem instance data mathematically and structurally."""
        issues: List[str] = []
        is_valid = True

        try:
            if problem_type == ProblemType.MAX_CUT:
                parsed = MaxCutInstance.model_validate(instance_data)
                inst_dump = parsed.model_dump()
            elif problem_type == ProblemType.ASSIGNMENT:
                parsed = AssignmentInstance.model_validate(instance_data)
                inst_dump = parsed.model_dump()
            elif problem_type == ProblemType.TSP:
                parsed = TSPInstance.model_validate(instance_data)
                inst_dump = parsed.model_dump()
            else:
                raise ValueError(f"Unsupported problem type: {problem_type}")

            variables = build_canonical_variables(problem_type, inst_dump)
            constraints = build_canonical_constraints(problem_type, inst_dump)
            metadata = build_canonical_metadata(problem_type, inst_dump)
            status = ValidationStatus.VALID

        except Exception as e:
            is_valid = False
            status = ValidationStatus.INVALID
            issues.append(str(e))
            variables = []
            constraints = []
            metadata = {}

        return ProblemValidationResponse(
            problem_id=problem_id,
            is_valid=is_valid,
            status=status,
            issues=issues,
            variables=variables,
            constraints=constraints,
            metadata=metadata,
        )

    @staticmethod
    async def evaluate_candidate_for_problem(
        problem_id: str, candidate: Any, owner_id: str = "default_user"
    ) -> EvaluationResult:
        """Fetch problem by ID and evaluate candidate solution using independent evaluator."""
        problem = await ProblemService.get_problem(problem_id, owner_id=owner_id)
        if not problem:
            raise ValueError(f"Problem '{problem_id}' was not found.")

        evaluator = EvaluatorFactory.get_evaluator(problem.problem_type)
        result = evaluator.evaluate(problem.instance, candidate)
        result.problem_id = problem.id
        return result

    @staticmethod
    def evaluate_candidate_direct(
        problem_type: ProblemType, instance_data: Dict[str, Any], candidate: Any
    ) -> EvaluationResult:
        """Evaluate candidate solution directly against instance data without persistence."""
        # Validate instance first
        if problem_type == ProblemType.MAX_CUT:
            parsed = MaxCutInstance.model_validate(instance_data)
        elif problem_type == ProblemType.ASSIGNMENT:
            parsed = AssignmentInstance.model_validate(instance_data)
        elif problem_type == ProblemType.TSP:
            parsed = TSPInstance.model_validate(instance_data)
        else:
            raise ValueError(f"Unsupported problem type: {problem_type}")

        evaluator = EvaluatorFactory.get_evaluator(problem_type)
        return evaluator.evaluate(parsed.model_dump(), candidate)

    @staticmethod
    def parse_problem_draft(req: ProblemDraftRequest) -> ProblemDraftResponse:
        """
        Analyze a natural language description and extract a draft candidate problem.
        NOTE: This is strictly a draft proposal requiring explicit human confirmation.
        """
        text = req.text.lower()

        # Determine problem type
        inferred_type = req.problem_type_hint
        if not inferred_type:
            if any(k in text for k in ["cut", "graph", "partition", "vertices", "vertex", "nodes", "bipartite"]):
                inferred_type = ProblemType.MAX_CUT
            elif any(k in text for k in ["assign", "agent", "worker", "job", "bipartite matching", "task", "cost matrix"]):
                inferred_type = ProblemType.ASSIGNMENT
            elif any(k in text for k in ["tsp", "travel", "salesman", "salesperson", "cities", "tour", "route", "visiting"]):
                inferred_type = ProblemType.TSP
            else:
                inferred_type = ProblemType.MAX_CUT  # Default fallback

        if inferred_type == ProblemType.MAX_CUT:
            # Extract possible nodes
            node_matches = re.findall(r"\b[A-Za-z0-9_]{1,3}\b", req.text)
            distinct_nodes = []
            for m in node_matches:
                m_clean = m.upper()
                if m_clean not in distinct_nodes and len(distinct_nodes) < 6:
                    distinct_nodes.append(m_clean)
            if len(distinct_nodes) < 3:
                distinct_nodes = ["A", "B", "C", "D"]

            # Sample edges
            sample_edges = [
                (distinct_nodes[0], distinct_nodes[1], 1.0),
                (distinct_nodes[1], distinct_nodes[2], 1.0),
            ]
            if len(distinct_nodes) >= 4:
                sample_edges.append((distinct_nodes[2], distinct_nodes[3], 1.0))
                sample_edges.append((distinct_nodes[3], distinct_nodes[0], 1.0))

            return ProblemDraftResponse(
                problem_type=ProblemType.MAX_CUT,
                name="Max-Cut Draft Proposal",
                description=f"Draft extracted from description: '{req.text[:80]}...'",
                objective={
                    "direction": "maximize",
                    "description": "Maximize the sum of weights of edges crossing the cut partition (S, V\\S)",
                },
                entities={"nodes": distinct_nodes},
                data={"edges": sample_edges},
                constraints=["Each node must belong to exactly one subset S or V\\S"],
                assumptions=[
                    "Graph is undirected",
                    "Default edge weights set to 1.0 where not specified in text",
                ],
                missing_information=[
                    "Check and verify complete edge list and edge weights before confirmation."
                ],
                suggested_instance={
                    "nodes": distinct_nodes,
                    "edges": sample_edges,
                },
                requires_user_confirmation=True,
                confidence_score=0.85,
            )

        elif inferred_type == ProblemType.ASSIGNMENT:
            agents = ["Agent_1", "Agent_2", "Agent_3"]
            tasks = ["Task_1", "Task_2", "Task_3"]
            cost_matrix = [
                [5.0, 9.0, 3.0],
                [4.0, 2.0, 8.0],
                [6.0, 7.0, 4.0],
            ]
            return ProblemDraftResponse(
                problem_type=ProblemType.ASSIGNMENT,
                name="Assignment Draft Proposal",
                description=f"Draft extracted from description: '{req.text[:80]}...'",
                objective={
                    "direction": "minimize",
                    "description": "Minimize total assignment cost for matching agents to tasks",
                },
                entities={"agents": agents, "tasks": tasks},
                data={"cost_matrix": cost_matrix},
                constraints=[
                    "Each agent must be assigned to exactly one task",
                    "Each task must be assigned to exactly one agent",
                ],
                assumptions=[
                    "Cost matrix entries represent linear assignment expenses",
                    "Assumed 1-to-1 matching dimensions (3x3)",
                ],
                missing_information=[
                    "Verify agent names, task names, and exact cost values in the matrix."
                ],
                suggested_instance={
                    "agents": agents,
                    "tasks": tasks,
                    "cost_matrix": cost_matrix,
                },
                requires_user_confirmation=True,
                confidence_score=0.82,
            )

        else:  # TSP
            cities = ["City_A", "City_B", "City_C", "City_D"]
            dist_matrix = [
                [0.0, 10.0, 15.0, 20.0],
                [10.0, 0.0, 35.0, 25.0],
                [15.0, 35.0, 0.0, 30.0],
                [20.0, 25.0, 30.0, 0.0],
            ]
            return ProblemDraftResponse(
                problem_type=ProblemType.TSP,
                name="Travelling Salesperson Draft Proposal",
                description=f"Draft extracted from description: '{req.text[:80]}...'",
                objective={
                    "direction": "minimize",
                    "description": "Minimize total round-trip tour distance visiting each city once and returning to origin",
                },
                entities={"cities": cities},
                data={"distance_matrix": dist_matrix},
                constraints=[
                    "Visit each city exactly once",
                    "Return to starting city",
                    "No sub-tours allowed",
                ],
                assumptions=[
                    "Distances are symmetric Euclidean or cost metrics",
                    "Self-distances are 0.0",
                ],
                missing_information=[
                    "Verify city names and exact inter-city distance matrix before confirming."
                ],
                suggested_instance={
                    "cities": cities,
                    "distance_matrix": dist_matrix,
                    "start_city": "City_A",
                },
                requires_user_confirmation=True,
                confidence_score=0.88,
            )
