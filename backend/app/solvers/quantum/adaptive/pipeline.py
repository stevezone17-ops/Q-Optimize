"""Unified Adaptive QAOA Execution Pipeline, thread-pooled dispatch, and persistence."""

import concurrent.futures
import threading
import time
import math
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import scipy.optimize as opt

from backend.app.domain.problems.models import ProblemType
from backend.app.domain.formulations.models import QuboModel
from backend.app.services.problem_service import ProblemService
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.formulations.assignment_qubo import AssignmentQuboGenerator
from backend.app.formulations.tsp_qubo import TSPQuboGenerator
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.solvers.quantum.hamiltonians import QAOACostHamiltonian
from backend.app.solvers.quantum.circuit_builder import QAOACircuitBuilder
from backend.app.solvers.quantum.optimizer import QAOAOptimizer
from backend.app.solvers.quantum.execution_engine import QuantumExecutionEngine
from backend.app.solvers.quantum.solution_decoder import QAOASolutionDecoder
from backend.app.solvers.quantum.execution_context import QuantumExecutionContext
from backend.app.solvers.quantum.backend_manager import QuantumBackendManager
from backend.app.solvers.quantum.models import (
    QAOAConfiguration,
    QuantumExecutionStatus,
    CircuitMetadata,
)
from backend.app.solvers.quantum.adaptive.adaptive_config import (
    AdaptiveStrategyType,
    StoppingConditionType,
    DepthGrowthStrategy,
    OptimizerScheduleType,
)
from backend.app.solvers.quantum.adaptive.adaptive_models import (
    AdaptiveQAOARequest,
    AdaptiveQAOAResult,
    AdaptiveExecutionRecord,
    AdaptiveStatusResponse,
    AdaptiveIteration,
    AdaptiveDecisionLog,
)
from backend.app.solvers.quantum.adaptive.initializers import ParameterInitializerFactory
from backend.app.solvers.quantum.adaptive.transfer import ParameterTransferService
from backend.app.solvers.quantum.adaptive.optimizer_controller import AdaptiveOptimizerController
from backend.app.solvers.quantum.adaptive.depth_manager import AdaptiveDepthManager
from backend.app.solvers.quantum.adaptive.convergence_monitor import AdaptiveConvergenceMonitor
from backend.app.solvers.quantum.exceptions import (
    CancellationError,
    ExecutionTimeoutError,
)
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import (
    AdaptiveQAOAError,
)
from backend.app.db.mongodb import db_manager
from backend.app.core.logging import logger


class AdaptiveQAOAExecutionPipeline:
    """
    Unified Adaptive QAOA Execution Pipeline providing asynchronous background execution,
    thread-pooled worker dispatch, lifecycle tracking, cooperative cancellation, and persistent storage.
    """

    _executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=8, thread_name_prefix="qopt-aqaoa-"
    )
    _cancellation_events: Dict[str, threading.Event] = {}
    _futures: Dict[str, concurrent.futures.Future] = {}

    @classmethod
    async def _resolve_problem(
        cls, problem_id: str, owner_id: str = "default_user"
    ) -> Tuple[ProblemType, Dict[str, Any]]:
        """Resolves target problem model by problem_id."""
        stored = await ProblemService.get_problem(problem_id, owner_id)
        if not stored:
            raise ValueError(f"Problem instance '{problem_id}' not found.")
        return stored.problem_type, stored.instance

    @classmethod
    def _generate_qubo(
        cls, problem_type: ProblemType, instance: Dict[str, Any]
    ) -> QuboModel:
        """Constructs QUBO formulation for problem instance."""
        p_type = problem_type.value if isinstance(problem_type, ProblemType) else str(problem_type).lower()
        if p_type in ["max_cut", "maxcut"]:
            return MaxCutQuboGenerator.generate(instance)
        elif p_type in ["assignment", "linear_assignment"]:
            return AssignmentQuboGenerator.generate(instance)
        elif p_type in ["tsp", "traveling_salesperson"]:
            return TSPQuboGenerator.generate(instance)
        else:
            raise ValueError(f"Unsupported problem type for QAOA: {problem_type}")

    @classmethod
    def _compute_exact_optimum(
        cls, problem_type: ProblemType, instance: Dict[str, Any], seed: int = 42
    ) -> Optional[float]:
        """Calculates deterministic classical exact optimum as ground-truth baseline if solvable."""
        try:
            exact_solver = ClassicalSolverFactory.get_solver("exact")
            exact_cfg = exact_solver.validate_config({})
            res = exact_solver.solve(
                problem_type=problem_type,
                instance=instance,
                config=exact_cfg,
                seed=seed,
            )
            return res.objective_value
        except Exception as exc:
            logger.debug(f"Exact optimum calculation skipped or unavailable: {exc}")
            return None

    @classmethod
    def execute_sync(
        cls,
        req: AdaptiveQAOARequest,
        execution_id: Optional[str] = None,
        cancellation_event: Optional[threading.Event] = None,
        owner_id: str = "default_user",
    ) -> AdaptiveQAOAResult:
        """Synchronous core execution routine for Adaptive QAOA."""
        exec_id = execution_id or f"aqexec-{uuid.uuid4().hex[:12]}"
        t_start = time.perf_counter()

        strat_cfg = req.config.strategy_config
        q_cfg = req.config

        # 1. Resolve problem synchronously from memory or service
        stored = db_manager.memory_get("problems", req.problem_id)
        if not stored:
            all_probs = db_manager.memory_list("problems")
            for p in all_probs:
                if p.get("id") == req.problem_id or p.get("problem_id") == req.problem_id:
                    stored = p
                    break
        if not stored:
            raise ValueError(f"Problem instance '{req.problem_id}' not found in storage.")
        
        prob_type = ProblemType(stored["problem_type"])
        instance = stored["instance"]

        # 2. Generate QUBO and analytical Cost Hamiltonian
        qubo = cls._generate_qubo(prob_type, instance)
        cost_ham = QAOACostHamiltonian.from_qubo(qubo)

        # 3. Ground-truth exact optimum baseline
        exact_optimum = cls._compute_exact_optimum(prob_type, instance, seed=q_cfg.seed or 42)

        # 4. Initialize Controllers
        depth_mgr = AdaptiveDepthManager(
            initial_depth=strat_cfg.initial_depth,
            max_depth=strat_cfg.max_depth,
            growth_strategy=strat_cfg.depth_growth,
            improvement_threshold=strat_cfg.improvement_threshold,
            stagnation_patience=strat_cfg.stagnation_patience,
        )

        opt_ctrl = AdaptiveOptimizerController(
            primary_optimizer=strat_cfg.primary_optimizer,
            fallback_optimizer=strat_cfg.fallback_optimizer,
            schedule_type=strat_cfg.optimizer_schedule,
            stagnation_patience=strat_cfg.stagnation_patience,
            max_evaluations_total=strat_cfg.max_evaluations_total,
        )

        conv_monitor = AdaptiveConvergenceMonitor(
            improvement_threshold=strat_cfg.improvement_threshold,
            stagnation_patience=strat_cfg.stagnation_patience,
            max_evaluations=strat_cfg.max_evaluations_total,
            time_limit_seconds=q_cfg.time_limit_seconds,
        )

        # 5. Parameter Initialization
        if strat_cfg.warm_start_parameters:
            current_gamma = list(strat_cfg.warm_start_parameters.get("gamma", []))
            current_beta = list(strat_cfg.warm_start_parameters.get("beta", []))
            if len(current_gamma) != depth_mgr.current_depth:
                current_gamma, current_beta, _ = ParameterTransferService.transfer_parameters(
                    current_gamma, current_beta, depth_mgr.current_depth
                )
        else:
            initializer = ParameterInitializerFactory.get_initializer(
                strategy_type=strat_cfg.init_strategy,
                seed=q_cfg.seed or 42,
                fourier_q_order=strat_cfg.fourier_q_order,
            )
            current_gamma, current_beta = initializer.initialize(depth_mgr.current_depth)

        iterations_log: List[AdaptiveIteration] = []
        decisions_log: List[AdaptiveDecisionLog] = []
        final_stopping_reason = StoppingConditionType.CONVERGED

        # 6. Adaptive Hybrid Outer Optimization Loop
        backend_mgr = QuantumBackendManager()
        is_terminated = False
        iteration_index = 0

        while not is_terminated:
            if cancellation_event and cancellation_event.is_set():
                final_stopping_reason = StoppingConditionType.CANCELLED
                break

            current_p = depth_mgr.current_depth
            circuit_builder = QAOACircuitBuilder(
                cost_hamiltonian=cost_ham,
                p_depth=current_p,
            )

            step_qaoa_cfg = QAOAConfiguration(
                p_depth=current_p,
                shots=q_cfg.shots,
                simulation_mode=q_cfg.simulation_mode,
                backend_name=q_cfg.backend_name,
                optimizer=opt_ctrl.current_optimizer,
                max_iterations=15,  # Adaptive step size per outer epoch
                optimizer_tol=1e-4,
                seed=q_cfg.seed,
                noise_model_enabled=q_cfg.noise_model_enabled,
                noise_error_rate=q_cfg.noise_error_rate,
                time_limit_seconds=max(5.0, q_cfg.time_limit_seconds - (time.perf_counter() - t_start)),
            )

            q_context = QuantumExecutionContext(
                time_limit_seconds=step_qaoa_cfg.time_limit_seconds,
                cancellation_token=cancellation_event,
            )

            optimizer = QAOAOptimizer(
                circuit_builder=circuit_builder,
                config=step_qaoa_cfg,
                backend_manager=backend_mgr,
                context=q_context,
            )

            # Define objective function for scipy minimizer
            def _objective_fn(x: np.ndarray) -> float:
                nonlocal iteration_index
                if cancellation_event and cancellation_event.is_set():
                    raise CancellationError("Cancelled by user request.")
                gamma_vec = [float(g) for g in x[:current_p]]
                beta_vec = [float(b) for b in x[current_p:]]
                energy = optimizer.evaluate_expectation(gamma_vec, beta_vec)

                # Record in convergence monitor & optimizer controller
                is_best, impr = conv_monitor.record_evaluation(
                    gamma=gamma_vec,
                    beta=beta_vec,
                    energy=energy,
                    eval_count=1,
                )
                opt_ctrl.record_step(
                    gamma=gamma_vec,
                    beta=beta_vec,
                    energy=energy,
                    eval_count=1,
                )

                iteration_index += 1
                iter_entry = AdaptiveIteration(
                    iteration_index=iteration_index,
                    current_depth=current_p,
                    active_optimizer=opt_ctrl.current_optimizer.value,
                    gamma=gamma_vec,
                    beta=beta_vec,
                    expected_energy=round(energy, 6),
                    best_energy=round(conv_monitor.best_energy, 6) if not math.isinf(conv_monitor.best_energy) else round(energy, 6),
                    eval_count=1,
                    timestamp_offset=round(time.perf_counter() - t_start, 4),
                )
                iterations_log.append(iter_entry)
                return energy

            # Execute outer epoch
            x0 = np.array(current_gamma + current_beta, dtype=float)
            method_str = opt_ctrl.current_optimizer.value
            if method_str.upper() == "NELDER-MEAD":
                scipy_method = "Nelder-Mead"
            elif method_str.upper() == "SLSQP":
                scipy_method = "SLSQP"
            elif method_str.upper() == "L-BFGS-B":
                scipy_method = "L-BFGS-B"
            else:
                scipy_method = "COBYLA"

            try:
                opt.minimize(
                    _objective_fn,
                    x0,
                    method=scipy_method,
                    tol=1e-4,
                    options={"maxiter": step_qaoa_cfg.max_iterations},
                )
            except (CancellationError, ExecutionTimeoutError) as exc:
                final_stopping_reason = (
                    StoppingConditionType.CANCELLED
                    if isinstance(exc, CancellationError)
                    else StoppingConditionType.TIMEOUT
                )
                break
            except Exception:
                pass

            # Evaluate next tactical action
            can_grow = depth_mgr.can_grow()
            can_switch, _ = opt_ctrl.should_transition(
                conv_monitor.stagnation_count, conv_monitor.cumulative_evaluations
            )
            action, term_reason, diag_reason = conv_monitor.evaluate_adaptive_action(
                can_grow_depth=can_grow,
                can_switch_optimizer=can_switch,
                cancellation_requested=(cancellation_event is not None and cancellation_event.is_set()),
            )

            if action == "SWITCH_OPTIMIZER":
                old_opt = opt_ctrl.current_optimizer
                new_opt = opt_ctrl.execute_transition(diag_reason or "stagnation_detected")
                decisions_log.append(
                    AdaptiveDecisionLog(
                        timestamp_offset=round(time.perf_counter() - t_start, 4),
                        from_depth=current_p,
                        to_depth=current_p,
                        trigger_reason=diag_reason or "stagnation_detected",
                        action_summary=f"Switched optimizer from {old_opt.value} to {new_opt.value}",
                        active_optimizer=new_opt.value,
                    )
                )
                current_gamma = list(opt_ctrl.best_gamma)
                current_beta = list(opt_ctrl.best_beta)

            elif action == "EXPAND_DEPTH":
                old_p = current_p
                new_p, current_gamma, current_beta = depth_mgr.grow_depth(
                    current_gamma=opt_ctrl.best_gamma,
                    current_beta=opt_ctrl.best_beta,
                    best_energy=opt_ctrl.best_energy,
                    reason=diag_reason or "improvement_triggered",
                )
                decisions_log.append(
                    AdaptiveDecisionLog(
                        timestamp_offset=round(time.perf_counter() - t_start, 4),
                        from_depth=old_p,
                        to_depth=new_p,
                        trigger_reason=diag_reason or "improvement_triggered",
                        action_summary=f"Expanded QAOA circuit depth from p={old_p} to p={new_p} with warm-start interpolation",
                        active_optimizer=opt_ctrl.current_optimizer.value,
                    )
                )
                conv_monitor.reset_stagnation_for_new_layer()
                opt_ctrl.reset_for_new_depth()

            elif action == "TERMINATE":
                final_stopping_reason = term_reason or StoppingConditionType.CONVERGED
                is_terminated = True
                break

            # Safety fallback: if evaluations exceed budget
            if conv_monitor.cumulative_evaluations >= strat_cfg.max_evaluations_total:
                final_stopping_reason = StoppingConditionType.MAX_EVALUATIONS_REACHED
                break

        # 7. Quantum Sampling & Solution Decoding
        final_depth = depth_mgr.current_depth
        final_circuit_builder = QAOACircuitBuilder(
            cost_hamiltonian=cost_ham,
            p_depth=final_depth,
        )
        unbound_circuit = final_circuit_builder.build_circuit(include_measurements=True)
        circuit_metadata = final_circuit_builder.extract_circuit_metadata(unbound_circuit)

        best_g = opt_ctrl.best_gamma or current_gamma
        best_b = opt_ctrl.best_beta or current_beta

        bound_circuit = final_circuit_builder.build_and_bind(
            gamma_vals=best_g,
            beta_vals=best_b,
            include_measurements=True,
        )

        exec_engine = QuantumExecutionEngine(backend_manager=backend_mgr)
        final_qaoa_cfg = QAOAConfiguration(
            p_depth=final_depth,
            shots=q_cfg.shots,
            simulation_mode=q_cfg.simulation_mode,
            backend_name=q_cfg.backend_name,
            noise_model_enabled=q_cfg.noise_model_enabled,
            noise_error_rate=q_cfg.noise_error_rate,
            time_limit_seconds=q_cfg.time_limit_seconds,
        )
        sampling_res = exec_engine.execute_sampling(
            circuit=bound_circuit,
            config=final_qaoa_cfg,
        )

        decoder = QAOASolutionDecoder(
            problem_type=prob_type,
            problem_instance=instance,
            qubo_model=qubo,
            cost_hamiltonian=cost_ham,
        )
        decoding_summary = decoder.decode_and_evaluate_sampling_result(sampling_res)

        best_sample = decoding_summary.best_feasible_solution or decoding_summary.most_frequent_solution
        obj_val = float(best_sample.objective_value) if best_sample and best_sample.objective_value is not None else 0.0
        best_bitstr = best_sample.bitstring if best_sample else sampling_res.most_frequent_bitstring
        best_solution_dict = best_sample.candidate_solution if best_sample else {}
        is_feas = best_sample.is_feasible if best_sample else False
        viol = best_sample.constraint_violations if best_sample else []

        # 8. Approximation Ratio & Optimality Gap
        approx_ratio = None
        opt_gap = None
        if exact_optimum is not None and exact_optimum != 0.0:
            if prob_type == ProblemType.MAX_CUT:
                # Maximization: r = QAOA / Exact
                approx_ratio = round(obj_val / exact_optimum, 4)
                opt_gap = round(abs(exact_optimum - obj_val) / abs(exact_optimum) * 100.0, 2)
            else:
                # Minimization: r = Exact / QAOA
                approx_ratio = round(exact_optimum / obj_val, 4) if obj_val != 0 else 0.0
                opt_gap = round(abs(obj_val - exact_optimum) / abs(exact_optimum) * 100.0, 2)

        runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

        # 9. Result Compilation
        result = AdaptiveQAOAResult(
            execution_id=exec_id,
            problem_id=req.problem_id,
            problem_type=prob_type,
            status=(
                QuantumExecutionStatus.COMPLETED
                if final_stopping_reason != StoppingConditionType.CANCELLED
                else QuantumExecutionStatus.CANCELLED
            ),
            strategy_type=strat_cfg.strategy_type,
            initial_depth=strat_cfg.initial_depth,
            final_depth=final_depth,
            stopping_reason=final_stopping_reason,
            best_gamma=[round(g, 6) for g in best_g],
            best_beta=[round(b, 6) for b in best_b],
            best_bitstring=best_bitstr,
            best_solution=best_solution_dict,
            objective_value=obj_val,
            expected_energy=round(conv_monitor.best_energy, 6) if not math.isinf(conv_monitor.best_energy) else 0.0,
            is_feasible=is_feas,
            constraint_violations=viol,
            approximation_ratio=approx_ratio,
            exact_optimal_value=exact_optimum,
            optimality_gap_percent=opt_gap,
            total_evaluations=conv_monitor.cumulative_evaluations,
            total_circuit_executions=sampling_res.shots,
            execution_time_ms=runtime_ms,
            iterations_log=iterations_log,
            decisions_log=decisions_log,
            circuit_metadata=circuit_metadata,
        )

        # 10. Persist Record
        record = AdaptiveExecutionRecord(
            execution_id=exec_id,
            problem_id=req.problem_id,
            problem_type=prob_type,
            status=result.status,
            strategy_type=strat_cfg.strategy_type,
            submitted_at=datetime.now(timezone.utc).isoformat(),
            started_at=datetime.now(timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            runtime_seconds=round(runtime_ms / 1000.0, 4),
            config=req.config,
            result=result,
        )
        db_manager.memory_insert("adaptive_quantum_executions", exec_id, record.model_dump())

        return result

    @classmethod
    async def submit_async(
        cls, req: AdaptiveQAOARequest, owner_id: str = "default_user"
    ) -> AdaptiveExecutionRecord:
        """Asynchronously dispatch an Adaptive QAOA task to the worker thread pool."""
        exec_id = f"aqexec-{uuid.uuid4().hex[:12]}"

        # Verify problem exists
        prob_type, _ = await cls._resolve_problem(req.problem_id, owner_id)

        record = AdaptiveExecutionRecord(
            execution_id=exec_id,
            problem_id=req.problem_id,
            problem_type=prob_type,
            status=QuantumExecutionStatus.PENDING,
            strategy_type=req.config.strategy_config.strategy_type,
            submitted_at=datetime.now(timezone.utc).isoformat(),
            config=req.config,
        )
        db_manager.memory_insert("adaptive_quantum_executions", exec_id, record.model_dump())

        cancellation_event = threading.Event()
        cls._cancellation_events[exec_id] = cancellation_event

        def _worker():
            try:
                record.status = QuantumExecutionStatus.RUNNING
                record.started_at = datetime.now(timezone.utc).isoformat()
                db_manager.memory_insert("adaptive_quantum_executions", exec_id, record.model_dump())

                res = cls.execute_sync(
                    req=req,
                    execution_id=exec_id,
                    cancellation_event=cancellation_event,
                    owner_id=owner_id,
                )
                record.status = res.status
                record.result = res
                record.completed_at = datetime.now(timezone.utc).isoformat()
                record.runtime_seconds = round(res.execution_time_ms / 1000.0, 4)
                db_manager.memory_insert("adaptive_quantum_executions", exec_id, record.model_dump())
            except Exception as exc:
                record.status = QuantumExecutionStatus.FAILED
                record.error = str(exc)
                record.completed_at = datetime.now(timezone.utc).isoformat()
                db_manager.memory_insert("adaptive_quantum_executions", exec_id, record.model_dump())
            finally:
                cls._cancellation_events.pop(exec_id, None)
                cls._futures.pop(exec_id, None)

        future = cls._executor.submit(_worker)
        cls._futures[exec_id] = future
        return record

    @classmethod
    async def get_execution(cls, execution_id: str) -> Optional[AdaptiveExecutionRecord]:
        """Retrieve full execution record from storage."""
        data = db_manager.memory_get("adaptive_quantum_executions", execution_id)
        if not data and db_manager.is_connected and db_manager.db is not None:
            try:
                data = await db_manager.db["adaptive_quantum_executions"].find_one({"execution_id": execution_id})
            except Exception:
                pass

        if data:
            return AdaptiveExecutionRecord.model_validate(data)
        return None

    @classmethod
    async def get_status(cls, execution_id: str) -> Optional[AdaptiveStatusResponse]:
        """Retrieve lightweight lifecycle status response for polling."""
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

        curr_depth = 1
        active_opt = "COBYLA"
        if record.result:
            curr_depth = record.result.final_depth
            if record.result.iterations_log:
                active_opt = record.result.iterations_log[-1].active_optimizer

        return AdaptiveStatusResponse(
            execution_id=record.execution_id,
            problem_id=record.problem_id,
            problem_type=record.problem_type,
            status=record.status,
            current_depth=curr_depth,
            active_optimizer=active_opt,
            runtime_seconds=record.runtime_seconds,
            is_completed=is_done,
            has_failed=has_failed,
            error=record.error,
        )

    @classmethod
    async def cancel_execution(cls, execution_id: str) -> Optional[AdaptiveStatusResponse]:
        """Trigger cooperative cancellation token for an in-flight execution."""
        if execution_id in cls._cancellation_events:
            cls._cancellation_events[execution_id].set()

        record = await cls.get_execution(execution_id)
        if not record:
            return None

        if record.status in [QuantumExecutionStatus.PENDING, QuantumExecutionStatus.RUNNING]:
            record.status = QuantumExecutionStatus.CANCELLED
            record.completed_at = datetime.now(timezone.utc).isoformat()
            db_manager.memory_insert("adaptive_quantum_executions", execution_id, record.model_dump())

        return await cls.get_status(execution_id)

    @classmethod
    async def list_executions(cls, limit: int = 25) -> List[AdaptiveExecutionRecord]:
        """List most recent adaptive QAOA executions."""
        raw_list = db_manager.memory_list("adaptive_quantum_executions")
        results: List[AdaptiveExecutionRecord] = []
        for item in raw_list:
            try:
                results.append(AdaptiveExecutionRecord.model_validate(item))
            except Exception:
                pass

        if db_manager.is_connected and db_manager.db is not None:
            try:
                cursor = db_manager.db["adaptive_quantum_executions"].find().sort("submitted_at", -1).limit(limit)
                async for doc in cursor:
                    if not any(r.execution_id == doc.get("execution_id") for r in results):
                        results.append(AdaptiveExecutionRecord.model_validate(doc))
            except Exception:
                pass

        results.sort(key=lambda r: r.submitted_at, reverse=True)
        return results[:limit]
