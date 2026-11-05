"""Pipeline and background execution engine for classical optimization solvers."""

import concurrent.futures
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from backend.app.domain.problems.models import ProblemType
from backend.app.services.problem_service import ProblemService
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.solvers.classical.models import (
    SolverRequest,
    SolverResult,
    SolverStatus,
    ExecutionRecord,
    ExecutionStatusResponse,
)
from backend.app.solvers.classical.exceptions import (
    SolverNotFoundError,
    SolverNotImplementedError,
    SolverConfigurationError,
    UnsupportedProblemTypeError,
)
from backend.app.db.mongodb import db_manager
from backend.app.core.logging import logger


class ClassicalExecutionPipeline:
    """
    Manages classical solver execution lifecycle, supporting synchronous execution
    and thread-pooled asynchronous background dispatch, persistence, status polling,
    and cooperative cancellation.
    """

    _executor = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="qopt-classical-")
    _cancellation_events: Dict[str, threading.Event] = {}
    _futures: Dict[str, concurrent.futures.Future] = {}

    @classmethod
    async def _resolve_problem(cls, req: SolverRequest, owner_id: str = "default_user") -> tuple[ProblemType, Dict[str, Any]]:
        """Resolve problem type and canonical instance definition."""
        if req.problem_id:
            stored = await ProblemService.get_problem(req.problem_id, owner_id=owner_id)
            if not stored:
                raise ValueError(f"Problem with ID '{req.problem_id}' not found.")
            return stored.problem_type, stored.instance
        elif req.problem_type and req.instance:
            return req.problem_type, req.instance
        else:
            raise ValueError("Must provide either 'problem_id' or both 'problem_type' and 'instance'.")

    @classmethod
    def _persist_record_sync(cls, record: ExecutionRecord) -> None:
        """Synchronously persist execution record to memory store."""
        record_dict = record.model_dump()
        db_manager.memory_insert("executions", record.execution_id, record_dict)

    @classmethod
    async def _persist_record(cls, record: ExecutionRecord) -> None:
        """Persist execution record to memory store and MongoDB if available."""
        cls._persist_record_sync(record)

        if db_manager.is_connected and db_manager.db is not None:
            try:
                await db_manager.db["executions"].update_one(
                    {"execution_id": record.execution_id},
                    {"$set": record.model_dump()},
                    upsert=True,
                )
            except Exception as e:
                logger.warning(f"Could not persist execution record to MongoDB ({e}); cached in memory.")

    @classmethod
    async def execute_sync(cls, req: SolverRequest, owner_id: str = "default_user") -> SolverResult:
        """
        Execute solver synchronously using a worker thread.
        """
        target_problem_type, target_instance = await cls._resolve_problem(req, owner_id)
        solver = ClassicalSolverFactory.get_solver(req.solver_id)
        solver.check_problem_support(target_problem_type)

        if not solver.is_implemented:
            raise SolverNotImplementedError(
                f"Solver '{solver.name}' ({solver.solver_id}) is not yet implemented (scheduled for {solver.stage_introduced})."
            )

        parsed_config = solver.validate_config(req.config)
        execution_id = f"exec-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        record = ExecutionRecord(
            execution_id=execution_id,
            solver_id=solver.solver_id,
            solver_name=solver.name,
            problem_type=target_problem_type,
            problem_id=req.problem_id,
            status=SolverStatus.RUNNING,
            submitted_at=now_iso,
            started_at=now_iso,
            seed=req.seed,
            config=req.config,
        )
        await cls._persist_record(record)

        try:
            future = cls._executor.submit(
                solver.solve,
                problem_type=target_problem_type,
                instance=target_instance,
                config=parsed_config,
                seed=req.seed,
            )
            result: SolverResult = future.result()
            result.execution_id = execution_id

            record.status = result.status
            record.result = result
            record.runtime_seconds = result.runtime_seconds
            record.completed_at = datetime.now(timezone.utc).isoformat()
            await cls._persist_record(record)
            return result

        except Exception as e:
            record.status = SolverStatus.FAILED
            record.error = str(e)
            record.completed_at = datetime.now(timezone.utc).isoformat()
            await cls._persist_record(record)
            raise

    @classmethod
    async def submit_async(cls, req: SolverRequest, owner_id: str = "default_user") -> ExecutionRecord:
        """
        Enqueue a background solver execution in thread pool, returning initial record immediately.
        """
        target_problem_type, target_instance = await cls._resolve_problem(req, owner_id)
        solver = ClassicalSolverFactory.get_solver(req.solver_id)
        solver.check_problem_support(target_problem_type)

        if not solver.is_implemented:
            raise SolverNotImplementedError(
                f"Solver '{solver.name}' ({solver.solver_id}) is not yet implemented (scheduled for {solver.stage_introduced})."
            )

        parsed_config = solver.validate_config(req.config)
        execution_id = f"exec-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        record = ExecutionRecord(
            execution_id=execution_id,
            solver_id=solver.solver_id,
            solver_name=solver.name,
            problem_type=target_problem_type,
            problem_id=req.problem_id,
            status=SolverStatus.PENDING,
            submitted_at=now_iso,
            seed=req.seed,
            config=req.config,
        )
        await cls._persist_record(record)

        # Cancellation token
        cancel_event = threading.Event()
        cls._cancellation_events[execution_id] = cancel_event

        # Submit worker to ThreadPoolExecutor
        future = cls._executor.submit(
            cls._worker_thread_execute,
            execution_id=execution_id,
            solver=solver,
            problem_type=target_problem_type,
            instance=target_instance,
            config=parsed_config,
            seed=req.seed,
            cancel_event=cancel_event,
        )
        cls._futures[execution_id] = future

        return record

    @classmethod
    def _worker_thread_execute(
        cls,
        execution_id: str,
        solver: Any,
        problem_type: ProblemType,
        instance: Dict[str, Any],
        config: Any,
        seed: Optional[int],
        cancel_event: threading.Event,
    ) -> None:
        """Synchronous worker thread driving solver execution independent of event loop."""
        record_dict = db_manager.memory_get("executions", execution_id)
        if not record_dict:
            return

        record = ExecutionRecord(**record_dict)
        record.status = SolverStatus.RUNNING
        record.started_at = datetime.now(timezone.utc).isoformat()
        cls._persist_record_sync(record)

        if cancel_event.is_set():
            record.status = SolverStatus.CANCELLED
            record.completed_at = datetime.now(timezone.utc).isoformat()
            cls._persist_record_sync(record)
            cls._cleanup(execution_id)
            return

        try:
            result: SolverResult = solver.solve(
                problem_type=problem_type,
                instance=instance,
                config=config,
                seed=seed,
            )
            result.execution_id = execution_id

            if cancel_event.is_set():
                record.status = SolverStatus.CANCELLED
            else:
                record.status = result.status
                record.result = result
                record.runtime_seconds = result.runtime_seconds

            record.completed_at = datetime.now(timezone.utc).isoformat()
            cls._persist_record_sync(record)

        except Exception as e:
            record.status = SolverStatus.FAILED
            record.error = str(e)
            record.completed_at = datetime.now(timezone.utc).isoformat()
            cls._persist_record_sync(record)
        finally:
            cls._cleanup(execution_id)

    @classmethod
    def _cleanup(cls, execution_id: str) -> None:
        cls._cancellation_events.pop(execution_id, None)
        cls._futures.pop(execution_id, None)

    @classmethod
    async def get_execution(cls, execution_id: str) -> Optional[ExecutionRecord]:
        """Retrieve full execution record by ID."""
        data = db_manager.memory_get("executions", execution_id)
        if data:
            return ExecutionRecord(**data)

        if db_manager.is_connected and db_manager.db is not None:
            doc = await db_manager.db["executions"].find_one({"execution_id": execution_id})
            if doc:
                doc.pop("_id", None)
                return ExecutionRecord(**doc)

        return None

    @classmethod
    async def get_status(cls, execution_id: str) -> Optional[ExecutionStatusResponse]:
        """Retrieve lightweight execution status for rapid polling."""
        record = await cls.get_execution(execution_id)
        if not record:
            return None

        is_done = record.status in (
            SolverStatus.COMPLETED,
            SolverStatus.FAILED,
            SolverStatus.CANCELLED,
            SolverStatus.TIMED_OUT,
        )
        has_failed = record.status in (SolverStatus.FAILED, SolverStatus.CANCELLED)

        return ExecutionStatusResponse(
            execution_id=record.execution_id,
            solver_id=record.solver_id,
            problem_type=record.problem_type,
            status=record.status,
            runtime_seconds=record.runtime_seconds,
            is_completed=is_done,
            has_failed=has_failed,
            error=record.error,
        )

    @classmethod
    async def cancel_execution(cls, execution_id: str) -> bool:
        """Cooperatively cancel a pending or running background execution."""
        event = cls._cancellation_events.get(execution_id)
        if event:
            event.set()

        future = cls._futures.get(execution_id)
        if future and not future.done():
            future.cancel()

        record = await cls.get_execution(execution_id)
        if record and record.status in (SolverStatus.PENDING, SolverStatus.RUNNING):
            record.status = SolverStatus.CANCELLED
            record.completed_at = datetime.now(timezone.utc).isoformat()
            cls._persist_record_sync(record)
            return True

        return False

    @classmethod
    async def list_executions(cls, limit: int = 50) -> List[ExecutionRecord]:
        """List recent execution records sorted newest first."""
        records: List[ExecutionRecord] = []
        raw_list = db_manager.memory_list("executions")
        for item in raw_list:
            records.append(ExecutionRecord(**item))

        if db_manager.is_connected and db_manager.db is not None:
            try:
                cursor = db_manager.db["executions"].find().sort("submitted_at", -1).limit(limit)
                docs = await cursor.to_list(length=limit)
                for doc in docs:
                    doc.pop("_id", None)
                    rec = ExecutionRecord(**doc)
                    if not any(r.execution_id == rec.execution_id for r in records):
                        records.append(rec)
            except Exception as e:
                logger.warning(f"Error fetching executions from MongoDB: {e}")

        # Sort descending by submitted_at
        records.sort(key=lambda r: r.submitted_at, reverse=True)
        return records[:limit]
