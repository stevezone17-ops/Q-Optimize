"""Unified QAOA execution pipeline, background dispatch, and persistence."""

import concurrent.futures
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from backend.app.domain.problems.models import ProblemType
from backend.app.domain.formulations.models import QuboModel
from backend.app.services.problem_service import ProblemService
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.formulations.assignment_qubo import AssignmentQuboGenerator
from backend.app.formulations.tsp_qubo import TSPQuboGenerator
from backend.app.solvers.quantum.hamiltonians import QAOACostHamiltonian
from backend.app.solvers.quantum.circuit_builder import QAOACircuitBuilder
from backend.app.solvers.quantum.optimizer import QAOAOptimizer
from backend.app.solvers.quantum.execution_engine import QuantumExecutionEngine
from backend.app.solvers.quantum.solution_decoder import QAOASolutionDecoder
from backend.app.solvers.quantum.execution_context import QuantumExecutionContext
from backend.app.solvers.quantum.backend_manager import QuantumBackendManager
from backend.app.solvers.quantum.models import (
    QAOAExecutionRequest,
    QAOAExecutionResult,
    QAOAExecutionRecord,
    QAOAStatusResponse,
    QuantumExecutionStatus,
)
from backend.app.solvers.quantum.exceptions import (
    QuantumSolverError,
    QubitLimitExceededError,
    ShotLimitExceededError,
    CancellationError,
    ExecutionTimeoutError,
)
from backend.app.db.mongodb import db_manager
from backend.app.core.logging import logger


class QAOAExecutionPipeline:
    """
    Unified QAOA execution pipeline supporting synchronous execution,
    thread-pooled asynchronous dispatch, status polling, and cooperative cancellation.
    """

    _executor = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="qopt-qaoa-")
    _cancellation_events: Dict[str, threading.Event] = {}
    _futures: Dict[str, concurrent.futures.Future] = {}

    @classmethod
    async def _resolve_problem(
        cls,
        req: QAOAExecutionRequest,
        owner_id: str = "default_user",
    ) -> Tuple[ProblemType, Dict[str, Any]]:
        """Resolves target problem type and canonical problem instance definition."""
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
    def _build_qubo(
        cls,
        problem_type: ProblemType,
        instance: Dict[str, Any],
        penalty_coefficients: Optional[Dict[str, float]] = None,
    ) -> QuboModel:
        """Generates canonical Phase 3 QUBO formulation for the problem."""
        p_type = problem_type.value if isinstance(problem_type, ProblemType) else str(problem_type).lower()
        if p_type in ["max_cut", "maxcut"]:
            return MaxCutQuboGenerator.generate(instance)
        elif p_type in ["assignment", "linear_assignment"]:
            return AssignmentQuboGenerator.generate(instance, penalty_coefficients=penalty_coefficients)
        elif p_type in ["tsp", "traveling_salesperson"]:
            return TSPQuboGenerator.generate(instance, penalty_coefficients=penalty_coefficients)
        else:
            raise ValueError(f"Unsupported problem type for QAOA: '{problem_type}'.")

    @classmethod
    def _persist_record_sync(cls, record: QAOAExecutionRecord) -> None:
        """Persist execution record to memory store."""
        db_manager.memory_insert("quantum_executions", record.execution_id, record.model_dump())

    @classmethod
    async def _persist_record(cls, record: QAOAExecutionRecord) -> None:
        """Persist execution record to memory store and MongoDB if available."""
        cls._persist_record_sync(record)
        if db_manager.is_connected and db_manager.db is not None:
            try:
                await db_manager.db["quantum_executions"].update_one(
                    {"execution_id": record.execution_id},
                    {"$set": record.model_dump()},
                    upsert=True,
                )
            except Exception as exc:
                logger.warning(f"Could not persist quantum execution to MongoDB ({exc}); cached in memory.")

    @classmethod
    def _run_qaoa_workflow_sync(
        cls,
        execution_id: str,
        problem_type: ProblemType,
        instance: Dict[str, Any],
        req: QAOAExecutionRequest,
        cancellation_event: threading.Event,
    ) -> QAOAExecutionResult:
        """Core synchronous execution routine executed within worker thread."""
        t_start = time.perf_counter()
        ctx = QuantumExecutionContext(
            time_limit_seconds=req.config.time_limit_seconds,
            cancellation_token=cancellation_event,
        )

        # 1. Build canonical QUBO formulation
        qubo_model = cls._build_qubo(problem_type, instance, req.penalty_coefficients)
        ctx.check_status()

        # 2. Derive Cost Hamiltonian
        cost_hamiltonian = QAOACostHamiltonian.from_qubo(qubo_model)
        ctx.check_status()

        # 3. Construct QAOA parameterized circuit builder
        circuit_builder = QAOACircuitBuilder(cost_hamiltonian, p_depth=req.config.p_depth)
        ctx.check_status()

        # 4. Variational parameter optimization
        backend_manager = QuantumBackendManager()
        optimizer = QAOAOptimizer(
            circuit_builder=circuit_builder,
            config=req.config,
            backend_manager=backend_manager,
            context=ctx,
        )
        optimization_result = optimizer.optimize()
        ctx.check_status()

        # 5. Build and execute optimal circuit sampling
        bound_circuit = circuit_builder.build_and_bind(
            gamma_vals=optimization_result.optimal_gamma,
            beta_vals=optimization_result.optimal_beta,
            include_measurements=True,
        )
        ctx.check_status()

        execution_engine = QuantumExecutionEngine(backend_manager=backend_manager)
        sampling_result = execution_engine.execute_sampling(
            circuit=bound_circuit,
            config=req.config,
            context=ctx,
        )

        # 6. Decode and independently evaluate measured solutions
        decoder = QAOASolutionDecoder(
            problem_type=problem_type,
            problem_instance=instance,
            qubo_model=qubo_model,
            cost_hamiltonian=cost_hamiltonian,
        )
        decoding_summary = decoder.decode_and_evaluate_sampling_result(sampling_result)
        runtime = time.perf_counter() - t_start

        best_sample = decoding_summary.best_feasible_solution or decoding_summary.most_frequent_solution

        status = QuantumExecutionStatus.COMPLETED
        if cancellation_event and cancellation_event.is_set():
            status = QuantumExecutionStatus.CANCELLED

        return QAOAExecutionResult(
            execution_id=execution_id,
            solver_id="qaoa",
            solver_name="Quantum Approximate Optimization Algorithm (QAOA)",
            problem_type=problem_type,
            status=status,
            best_solution=best_sample,
            candidate_solution=best_sample.candidate_solution if best_sample else None,
            objective_value=best_sample.objective_value if best_sample else None,
            is_feasible=best_sample.is_feasible if best_sample else False,
            constraint_violations=best_sample.constraint_violations if best_sample else [],
            qubo_energy=best_sample.qubo_energy if best_sample else None,
            ising_energy=best_sample.ising_energy if best_sample else None,
            optimal_gamma=optimization_result.optimal_gamma,
            optimal_beta=optimization_result.optimal_beta,
            optimization_result=optimization_result,
            sampling_result=sampling_result,
            decoding_summary=decoding_summary,
            runtime_seconds=round(runtime, 4),
        )

    @classmethod
    async def execute_sync(
        cls,
        req: QAOAExecutionRequest,
        owner_id: str = "default_user",
    ) -> QAOAExecutionResult:
        """Executes QAOA synchronously on a worker thread and awaits completion."""
        target_problem_type, target_instance = await cls._resolve_problem(req, owner_id)
        execution_id = f"qexec-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        cancel_event = threading.Event()
        cls._cancellation_events[execution_id] = cancel_event

        record = QAOAExecutionRecord(
            execution_id=execution_id,
            solver_id="qaoa",
            problem_type=target_problem_type,
            problem_id=req.problem_id,
            status=QuantumExecutionStatus.RUNNING,
            submitted_at=now_iso,
            started_at=now_iso,
            config=req.config.model_dump(),
        )
        await cls._persist_record(record)

        try:
            future = cls._executor.submit(
                cls._run_qaoa_workflow_sync,
                execution_id=execution_id,
                problem_type=target_problem_type,
                instance=target_instance,
                req=req,
                cancellation_event=cancel_event,
            )
            result = future.result()

            record.status = result.status
            record.result = result
            record.runtime_seconds = result.runtime_seconds
            record.completed_at = datetime.now(timezone.utc).isoformat()
            await cls._persist_record(record)
            return result

        except Exception as exc:
            record.status = QuantumExecutionStatus.FAILED
            record.error = str(exc)
            record.completed_at = datetime.now(timezone.utc).isoformat()
            await cls._persist_record(record)
            raise
        finally:
            cls._cancellation_events.pop(execution_id, None)

    @classmethod
    async def dispatch_async(
        cls,
        req: QAOAExecutionRequest,
        owner_id: str = "default_user",
    ) -> QAOAStatusResponse:
        """Dispatches QAOA execution asynchronously to the background worker pool."""
        target_problem_type, target_instance = await cls._resolve_problem(req, owner_id)
        execution_id = f"qexec-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        cancel_event = threading.Event()
        cls._cancellation_events[execution_id] = cancel_event

        record = QAOAExecutionRecord(
            execution_id=execution_id,
            solver_id="qaoa",
            problem_type=target_problem_type,
            problem_id=req.problem_id,
            status=QuantumExecutionStatus.PENDING,
            submitted_at=now_iso,
            config=req.config.model_dump(),
        )
        await cls._persist_record(record)

        def _worker_wrapper():
            record.status = QuantumExecutionStatus.RUNNING
            record.started_at = datetime.now(timezone.utc).isoformat()
            cls._persist_record_sync(record)

            try:
                res = cls._run_qaoa_workflow_sync(
                    execution_id=execution_id,
                    problem_type=target_problem_type,
                    instance=target_instance,
                    req=req,
                    cancellation_event=cancel_event,
                )
                record.status = res.status
                record.result = res
                record.runtime_seconds = res.runtime_seconds
                record.completed_at = datetime.now(timezone.utc).isoformat()
                cls._persist_record_sync(record)
            except Exception as exc:
                record.status = QuantumExecutionStatus.FAILED
                record.error = str(exc)
                record.completed_at = datetime.now(timezone.utc).isoformat()
                cls._persist_record_sync(record)
            finally:
                cls._cancellation_events.pop(execution_id, None)
                cls._futures.pop(execution_id, None)

        future = cls._executor.submit(_worker_wrapper)
        cls._futures[execution_id] = future

        return QAOAStatusResponse(
            execution_id=execution_id,
            solver_id="qaoa",
            problem_type=target_problem_type,
            status=QuantumExecutionStatus.PENDING,
            is_completed=False,
            has_failed=False,
        )

    @classmethod
    async def get_execution(cls, execution_id: str) -> Optional[QAOAExecutionRecord]:
        """Retrieves a QAOA execution record by ID."""
        mem = db_manager.memory_get("quantum_executions", execution_id)
        if mem:
            return QAOAExecutionRecord.model_validate(mem)

        if db_manager.is_connected and db_manager.db is not None:
            doc = await db_manager.db["quantum_executions"].find_one({"execution_id": execution_id})
            if doc:
                return QAOAExecutionRecord.model_validate(doc)
        return None

    @classmethod
    async def get_status(cls, execution_id: str) -> Optional[QAOAStatusResponse]:
        """Provides lightweight polling status for an execution."""
        record = await cls.get_execution(execution_id)
        if not record:
            return None

        is_done = record.status in [
            QuantumExecutionStatus.COMPLETED,
            QuantumExecutionStatus.CANCELLED,
            QuantumExecutionStatus.FAILED,
            QuantumExecutionStatus.TIMED_OUT,
        ]
        has_failed = record.status in [
            QuantumExecutionStatus.FAILED,
            QuantumExecutionStatus.TIMED_OUT,
        ]

        return QAOAStatusResponse(
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
    async def cancel_execution(cls, execution_id: str) -> Optional[QAOAStatusResponse]:
        """Triggers cooperative cancellation for an in-flight QAOA execution."""
        if execution_id in cls._cancellation_events:
            cls._cancellation_events[execution_id].set()

        record = await cls.get_execution(execution_id)
        if not record:
            return None

        if record.status in [QuantumExecutionStatus.PENDING, QuantumExecutionStatus.RUNNING]:
            record.status = QuantumExecutionStatus.CANCELLED
            record.completed_at = datetime.now(timezone.utc).isoformat()
            await cls._persist_record(record)

        return await cls.get_status(execution_id)

    @classmethod
    async def list_executions(cls, limit: int = 25) -> List[QAOAExecutionRecord]:
        """Returns the most recent QAOA execution records."""
        results: List[QAOAExecutionRecord] = []
        raw_list = db_manager.memory_list("quantum_executions")
        for item in raw_list:
            try:
                results.append(QAOAExecutionRecord.model_validate(item))
            except Exception:
                pass

        if db_manager.is_connected and db_manager.db is not None:
            try:
                cursor = db_manager.db["quantum_executions"].find().sort("submitted_at", -1).limit(limit)
                async for doc in cursor:
                    if not any(r.execution_id == doc.get("execution_id") for r in results):
                        results.append(QAOAExecutionRecord.model_validate(doc))
            except Exception:
                pass

        results.sort(key=lambda r: r.submitted_at, reverse=True)
        return results[:limit]
