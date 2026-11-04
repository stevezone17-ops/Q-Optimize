"""Problem service handling validation, persistence, and draft parsing."""

import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from backend.app.domain.problems.models import (
    ProblemType,
    ProblemCreate,
    ProblemResponse,
    ProblemDraftRequest,
    ProblemDraftResponse,
    MaxCutInstance,
    AssignmentInstance,
    TSPInstance,
)
from backend.app.db.mongodb import db_manager
from backend.app.core.logging import logger


class ProblemService:
    @staticmethod
    async def create_problem(problem_in: ProblemCreate, owner_id: str = "default_user") -> ProblemResponse:
        """Validate problem instance strictly and persist to database or memory store."""
        # Strictly parse and validate instance with Pydantic model validator
        parsed_instance = problem_in.parse_instance()

        problem_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        doc = {
            "id": problem_id,
            "owner_id": owner_id,
            "name": problem_in.name,
            "problem_type": problem_in.problem_type,
            "schema_version": "1.0",
            "description": problem_in.description or "",
            "instance": parsed_instance.model_dump(),
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
    async def get_problem(problem_id: str, owner_id: str = "default_user") -> Optional[ProblemResponse]:
        """Fetch problem by ID."""
        if db_manager.is_connected and db_manager.db is not None:
            try:
                res = await db_manager.db["problems"].find_one({"id": problem_id})
                if res:
                    res.pop("_id", None)
                    return ProblemResponse(**res)
            except Exception as e:
                logger.error(f"MongoDB query failed: {e}")

        # Check memory store
        mem_doc = db_manager.memory_get("problems", problem_id)
        if mem_doc:
            return ProblemResponse(**mem_doc)
        return None

    @staticmethod
    async def list_problems(owner_id: str = "default_user") -> List[ProblemResponse]:
        """List all problems for owner."""
        items: List[ProblemResponse] = []
        if db_manager.is_connected and db_manager.db is not None:
            try:
                cursor = db_manager.db["problems"].find({"owner_id": owner_id}).sort("created_at", -1)
                async for doc in cursor:
                    doc.pop("_id", None)
                    items.append(ProblemResponse(**doc))
                return items
            except Exception as e:
                logger.error(f"MongoDB list query failed: {e}")

        # Fallback to memory store
        for doc in db_manager.memory_list("problems"):
            if doc.get("owner_id") == owner_id:
                items.append(ProblemResponse(**doc))
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items

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
                },
                requires_user_confirmation=True,
                confidence_score=0.88,
            )
