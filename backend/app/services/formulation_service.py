"""Service managing QUBO/Ising formulation generation, persistence, and verification."""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from backend.app.domain.formulations.models import (
    QuboModel,
    IsingModel,
    FormulationResponse,
    FormulationType,
    GenerateQuboRequest,
    VerificationResult,
)
from backend.app.formulations.engine import FormulationEngine
from backend.app.formulations.verification import FormulationVerifier
from backend.app.services.problem_service import ProblemService
from backend.app.db.mongodb import db_manager
from backend.app.core.logging import logger


class FormulationService:
    _engine = FormulationEngine()

    @classmethod
    async def generate_formulation(
        cls, req: GenerateQuboRequest, owner_id: str = "default_user"
    ) -> FormulationResponse:
        """
        Generate canonical QUBO and corresponding Ising spin Hamiltonian for a problem.
        Persists formulation to database or in-memory store.
        """
        problem_type: str
        instance_data: Dict[str, Any]
        prob_id: Optional[str] = req.problem_id

        if req.problem_id:
            problem = await ProblemService.get_problem(req.problem_id, owner_id=owner_id)
            if not problem:
                raise ValueError(f"Problem '{req.problem_id}' was not found.")
            problem_type = problem.problem_type
            instance_data = problem.instance
        elif req.problem_type and req.instance:
            problem_type = req.problem_type
            instance_data = req.instance
        else:
            raise ValueError("Must provide either a registered 'problem_id' or both 'problem_type' and 'instance'.")

        # 1. Generate canonical QUBO
        qubo = cls._engine.generate_qubo(
            problem_type=problem_type,
            problem_instance=instance_data,
            penalty_coefficients=req.penalty_coefficients,
        )

        # 2. Derive equivalent Ising Hamiltonian
        ising = cls._engine.qubo_to_ising(qubo)

        formulation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        response = FormulationResponse(
            id=formulation_id,
            problem_id=prob_id,
            owner_id=owner_id,
            formulation_type=FormulationType.QUBO,
            schema_version="1.0",
            qubo=qubo,
            ising=ising,
            created_at=now,
        )

        # Persist formulation
        doc = response.model_dump()
        if db_manager.is_connected and db_manager.db is not None:
            try:
                await db_manager.db["formulations"].insert_one(dict(doc))
            except Exception as e:
                logger.error(f"Failed to persist formulation to MongoDB: {e}. Storing in memory fallback.")
                db_manager.memory_insert("formulations", formulation_id, doc)
        else:
            db_manager.memory_insert("formulations", formulation_id, doc)

        return response

    @classmethod
    async def get_formulation(cls, formulation_id: str, owner_id: str = "default_user") -> Optional[FormulationResponse]:
        """Retrieve stored formulation by ID."""
        if db_manager.is_connected and db_manager.db is not None:
            try:
                res = await db_manager.db["formulations"].find_one({"id": formulation_id})
                if res:
                    res.pop("_id", None)
                    return FormulationResponse(**res)
            except Exception as e:
                logger.error(f"MongoDB query failed for formulation: {e}")

        # Check memory store
        mem_doc = db_manager.memory_get("formulations", formulation_id)
        if mem_doc:
            return FormulationResponse(**mem_doc)
        return None

    @classmethod
    async def verify_formulation(
        cls,
        formulation_id: Optional[str] = None,
        problem_id: Optional[str] = None,
        problem_type: Optional[str] = None,
        instance: Optional[Dict[str, Any]] = None,
        qubo: Optional[QuboModel] = None,
        owner_id: str = "default_user",
    ) -> VerificationResult:
        """Run exhaustive independent verification comparing original objective, QUBO, and Ising energies."""
        target_problem_type: str
        target_instance: Dict[str, Any]
        target_qubo: QuboModel

        if formulation_id:
            formulation = await cls.get_formulation(formulation_id, owner_id=owner_id)
            if not formulation or not formulation.qubo:
                raise ValueError(f"Formulation with ID '{formulation_id}' was not found.")
            target_qubo = formulation.qubo

            # Resolve problem instance
            if formulation.problem_id:
                prob = await ProblemService.get_problem(formulation.problem_id, owner_id=owner_id)
                if not prob:
                    raise ValueError(f"Underlying problem '{formulation.problem_id}' was not found.")
                target_problem_type = prob.problem_type
                target_instance = prob.instance
            elif problem_type and instance:
                target_problem_type = problem_type
                target_instance = instance
            else:
                target_problem_type = target_qubo.metadata.get("problem_type", "max_cut")
                target_instance = instance or {}
        elif problem_id:
            prob = await ProblemService.get_problem(problem_id, owner_id=owner_id)
            if not prob:
                raise ValueError(f"Problem '{problem_id}' was not found.")
            target_problem_type = prob.problem_type
            target_instance = prob.instance
            target_qubo = qubo or cls._engine.generate_qubo(target_problem_type, target_instance)
        elif problem_type and instance:
            target_problem_type = problem_type
            target_instance = instance
            target_qubo = qubo or cls._engine.generate_qubo(target_problem_type, target_instance)
        else:
            raise ValueError("Insufficient parameters for verification: provide formulation_id, problem_id, or problem instance.")

        return FormulationVerifier.verify(
            problem_type=target_problem_type,
            instance_data=target_instance,
            qubo=target_qubo,
        )
