"""Hybrid Quantum-Classical Optimization Benchmarking Engine."""

import math
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from backend.app.domain.problems.models import ProblemType
from backend.app.services.problem_service import ProblemService
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.solvers.classical.models import SolverResult
from backend.app.solvers.quantum.models import (
    QAOAConfiguration,
    QAOAExecutionRequest,
    QAOAExecutionResult,
    CircuitMetadata,
)
from backend.app.solvers.quantum.pipeline import QAOAExecutionPipeline
from backend.app.db.mongodb import db_manager
from backend.app.core.logging import logger


class HybridBenchmarkRequest(BaseModel):
    """Execution payload to benchmark QAOA alongside classical solvers."""
    name: Optional[str] = Field("Hybrid Quantum-Classical Benchmark", description="Benchmark label")
    problem_id: Optional[str] = Field(None, description="Registered canonical problem ID")
    problem_type: Optional[ProblemType] = Field(None, description="Problem family for ad-hoc problems")
    instance: Optional[Dict[str, Any]] = Field(None, description="Ad-hoc problem instance definition")
    include_solvers: List[str] = Field(
        default_factory=lambda: ["exact", "genetic_algorithm", "simulated_annealing", "qaoa"],
        description="Solvers included in the comparative benchmark",
    )
    qaoa_config: QAOAConfiguration = Field(
        default_factory=QAOAConfiguration,
        description="QAOA ansatz and simulation parameters",
    )
    classical_configs: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-solver configuration overrides for classical solvers",
    )
    trials: int = Field(1, ge=1, le=10, description="Repetitions for stochastic solvers")
    base_seed: int = Field(42, description="Base seed for reproducibility")


class HybridSolverBenchmarkSummary(BaseModel):
    """Performance statistics for a single solver within a hybrid benchmark."""
    solver_id: str
    solver_name: str
    solver_category: str = Field(..., description="'quantum_variational', 'classical_exact', or 'classical_metaheuristic'")
    is_quantum_simulator: bool = False
    trials_count: int
    best_objective: float
    mean_objective: float
    worst_objective: float
    std_objective: float
    feasibility_rate: float
    approximation_ratio: Optional[float] = Field(None, description="Approximation ratio r relative to exact global optimum")
    optimality_gap_percent: Optional[float] = Field(None, description="Optimality gap percentage relative to exact optimum")
    mean_runtime_ms: float
    min_runtime_ms: float
    max_runtime_ms: float
    mean_evaluations: float
    best_solution: Any = None
    circuit_metadata: Optional[CircuitMetadata] = None
    hardware_transparency_note: Optional[str] = None


class HybridBenchmarkResult(BaseModel):
    """Consolidated comparative benchmark result across quantum and classical engines."""
    benchmark_id: str = Field(default_factory=lambda: f"hbench-{uuid.uuid4().hex[:12]}")
    name: str
    problem_type: ProblemType
    problem_id: Optional[str] = None
    exact_optimum: Optional[float] = None
    summaries: List[HybridSolverBenchmarkSummary]
    total_runtime_seconds: float
    hardware_transparency_note: str = (
        "Quantum variational algorithm (QAOA) runs on classical CPU simulation via Qiskit Aer. "
        "Runtime reflects classical simulation overhead. No physical quantum hardware speedup is claimed."
    )
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HybridBenchmarkEngine:
    """
    Executes and statistically compares QAOA against deterministic and heuristic
    classical optimization solvers (Exact, GA, SA) on the same canonical problem instance.
    """

    @classmethod
    async def _resolve_problem(
        cls, req: HybridBenchmarkRequest, owner_id: str = "default_user"
    ) -> tuple[ProblemType, Dict[str, Any]]:
        """Resolves target problem type and instance representation."""
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
    async def run_benchmark(
        cls, req: HybridBenchmarkRequest, owner_id: str = "default_user"
    ) -> HybridBenchmarkResult:
        """Runs the hybrid benchmark suite across all requested solvers."""
        target_problem_type, target_instance = await cls._resolve_problem(req, owner_id)
        benchmark_id = f"hbench-{uuid.uuid4().hex[:12]}"
        t_start = time.perf_counter()

        requested_solvers = [s.strip().lower() for s in req.include_solvers]

        # 1. First, check if exact solver is requested or run it to determine ground truth
        exact_optimum: Optional[float] = None
        exact_solver = ClassicalSolverFactory.get_solver("exact")

        try:
            exact_cfg = exact_solver.validate_config(req.classical_configs.get("exact", {}))
            exact_res = exact_solver.solve(
                problem_type=target_problem_type,
                instance=target_instance,
                config=exact_cfg,
                seed=req.base_seed,
            )
            exact_optimum = exact_res.objective_value
        except Exception as e:
            logger.warning(f"Could not compute exact optimum baseline: {e}")

        summaries: List[HybridSolverBenchmarkSummary] = []
        is_max = target_problem_type == ProblemType.MAX_CUT

        # 2. Run Classical Solvers
        classical_ids = [s for s in requested_solvers if s in ["exact", "genetic_algorithm", "simulated_annealing"]]
        for c_id in classical_ids:
            solver = ClassicalSolverFactory.get_solver(c_id)
            solver.check_problem_support(target_problem_type)

            num_trials = 1 if c_id == "exact" else req.trials
            cfg_dict = req.classical_configs.get(c_id, {})
            parsed_cfg = solver.validate_config(cfg_dict)

            trial_results: List[SolverResult] = []
            for trial_idx in range(num_trials):
                seed = req.base_seed + trial_idx * 17
                res: SolverResult = solver.solve(
                    problem_type=target_problem_type,
                    instance=target_instance,
                    config=parsed_cfg,
                    seed=seed,
                )
                trial_results.append(res)

            objectives = [r.objective_value for r in trial_results if r.objective_value is not None]
            runtimes_ms = [r.runtime_seconds * 1000.0 for r in trial_results]
            evaluations = [r.evaluations for r in trial_results]
            feasible_count = sum(1 for r in trial_results if r.is_feasible)

            if is_max:
                best_trial = max(trial_results, key=lambda r: r.objective_value if r.objective_value is not None else -float("inf"))
                best_obj = max(objectives) if objectives else 0.0
                worst_obj = min(objectives) if objectives else 0.0
            else:
                best_trial = min(trial_results, key=lambda r: r.objective_value if r.objective_value is not None else float("inf"))
                best_obj = min(objectives) if objectives else 0.0
                worst_obj = max(objectives) if objectives else 0.0

            mean_obj = float(np.mean(objectives)) if objectives else 0.0
            std_obj = float(np.std(objectives)) if len(objectives) > 1 else 0.0
            feas_rate = feasible_count / max(1, num_trials)

            # Optimality gap & approximation ratio
            gap_percent: Optional[float] = None
            approx_ratio: Optional[float] = None

            if exact_optimum is not None and len(objectives) > 0:
                diff = abs(best_obj - exact_optimum)
                denom = abs(exact_optimum) + 1e-9
                gap_percent = round((diff / denom) * 100.0, 4)

                if is_max:
                    approx_ratio = round(best_obj / max(1e-9, exact_optimum), 4)
                else:
                    approx_ratio = round(exact_optimum / max(1e-9, best_obj), 4)

            category = "classical_exact" if c_id == "exact" else "classical_metaheuristic"

            summaries.append(
                HybridSolverBenchmarkSummary(
                    solver_id=solver.solver_id,
                    solver_name=solver.name,
                    solver_category=category,
                    is_quantum_simulator=False,
                    trials_count=num_trials,
                    best_objective=best_obj,
                    mean_objective=mean_obj,
                    worst_objective=worst_obj,
                    std_objective=std_obj,
                    feasibility_rate=feas_rate,
                    approximation_ratio=approx_ratio,
                    optimality_gap_percent=gap_percent,
                    mean_runtime_ms=round(float(np.mean(runtimes_ms)), 3),
                    min_runtime_ms=round(float(np.min(runtimes_ms)), 3),
                    max_runtime_ms=round(float(np.max(runtimes_ms)), 3),
                    mean_evaluations=float(np.mean(evaluations)),
                    best_solution=best_trial.candidate_solution,
                    hardware_transparency_note="Executed natively on host classical CPU.",
                )
            )

        # 3. Run QAOA Quantum Variational Solver (if requested)
        if "qaoa" in requested_solvers:
            num_trials = req.trials
            qaoa_results: List[QAOAExecutionResult] = []

            for trial_idx in range(num_trials):
                seed = req.base_seed + trial_idx * 17
                trial_config = req.qaoa_config.model_copy()
                trial_config.seed = seed

                qaoa_req = QAOAExecutionRequest(
                    problem_id=req.problem_id,
                    problem_type=target_problem_type,
                    instance=target_instance,
                    config=trial_config,
                )

                q_res = QAOAExecutionPipeline._run_qaoa_workflow_sync(
                    execution_id=f"hbench-qaoa-{trial_idx}-{uuid.uuid4().hex[:6]}",
                    problem_type=target_problem_type,
                    instance=target_instance,
                    req=qaoa_req,
                    cancellation_event=None,
                )
                qaoa_results.append(q_res)

            q_objectives = [r.objective_value for r in qaoa_results if r.objective_value is not None]
            q_runtimes_ms = [r.runtime_seconds * 1000.0 for r in qaoa_results]
            q_evals = [r.optimization_result.total_evaluations for r in qaoa_results]
            q_feasible_count = sum(1 for r in qaoa_results if r.is_feasible)

            if is_max:
                best_q_trial = max(qaoa_results, key=lambda r: r.objective_value if r.objective_value is not None else -float("inf"))
                q_best_obj = max(q_objectives) if q_objectives else 0.0
                q_worst_obj = min(q_objectives) if q_objectives else 0.0
            else:
                best_q_trial = min(qaoa_results, key=lambda r: r.objective_value if r.objective_value is not None else float("inf"))
                q_best_obj = min(q_objectives) if q_objectives else 0.0
                q_worst_obj = max(q_objectives) if q_objectives else 0.0

            q_mean_obj = float(np.mean(q_objectives)) if q_objectives else 0.0
            q_std_obj = float(np.std(q_objectives)) if len(q_objectives) > 1 else 0.0
            q_feas_rate = q_feasible_count / max(1, num_trials)

            q_gap_percent: Optional[float] = None
            q_approx_ratio: Optional[float] = None

            if exact_optimum is not None and len(q_objectives) > 0:
                diff = abs(q_best_obj - exact_optimum)
                denom = abs(exact_optimum) + 1e-9
                q_gap_percent = round((diff / denom) * 100.0, 4)

                if is_max:
                    q_approx_ratio = round(q_best_obj / max(1e-9, exact_optimum), 4)
                else:
                    q_approx_ratio = round(exact_optimum / max(1e-9, q_best_obj), 4)

            summaries.append(
                HybridSolverBenchmarkSummary(
                    solver_id="qaoa",
                    solver_name="Quantum Approximate Optimization Algorithm (QAOA)",
                    solver_category="quantum_variational",
                    is_quantum_simulator=True,
                    trials_count=num_trials,
                    best_objective=q_best_obj,
                    mean_objective=q_mean_obj,
                    worst_objective=q_worst_obj,
                    std_objective=q_std_obj,
                    feasibility_rate=q_feas_rate,
                    approximation_ratio=q_approx_ratio,
                    optimality_gap_percent=q_gap_percent,
                    mean_runtime_ms=round(float(np.mean(q_runtimes_ms)), 3),
                    min_runtime_ms=round(float(np.min(q_runtimes_ms)), 3),
                    max_runtime_ms=round(float(np.max(q_runtimes_ms)), 3),
                    mean_evaluations=float(np.mean(q_evals)),
                    best_solution=best_q_trial.candidate_solution,
                    circuit_metadata=best_q_trial.sampling_result.circuit_metadata,
                    hardware_transparency_note=best_q_trial.hardware_transparency_note,
                )
            )

        total_runtime = time.perf_counter() - t_start

        # Sort summaries: for Max-Cut descending by best_objective, for others ascending
        if is_max:
            summaries.sort(key=lambda s: s.best_objective, reverse=True)
        else:
            summaries.sort(key=lambda s: s.best_objective)

        result = HybridBenchmarkResult(
            benchmark_id=benchmark_id,
            name=req.name or "Hybrid Quantum-Classical Benchmark",
            problem_type=target_problem_type,
            problem_id=req.problem_id,
            exact_optimum=exact_optimum,
            summaries=summaries,
            total_runtime_seconds=round(total_runtime, 4),
        )

        # Persist benchmark result
        await cls._persist_benchmark(result)
        return result

    @classmethod
    async def _persist_benchmark(cls, bench: HybridBenchmarkResult) -> None:
        """Stores benchmark result in MongoDB or memory fallback."""
        data = bench.model_dump()
        db_manager.memory_insert("hybrid_benchmarks", bench.benchmark_id, data)

        if db_manager.is_connected and db_manager.db is not None:
            try:
                await db_manager.db["hybrid_benchmarks"].replace_one(
                    {"benchmark_id": bench.benchmark_id},
                    data,
                    upsert=True,
                )
            except Exception as e:
                logger.warning(f"Could not persist hybrid benchmark to MongoDB ({e}).")

    @classmethod
    async def get_benchmark(cls, benchmark_id: str) -> Optional[HybridBenchmarkResult]:
        """Retrieves a persisted hybrid benchmark result by ID."""
        mem = db_manager.memory_get("hybrid_benchmarks", benchmark_id)
        if mem:
            return HybridBenchmarkResult.model_validate(mem)

        if db_manager.is_connected and db_manager.db is not None:
            doc = await db_manager.db["hybrid_benchmarks"].find_one({"benchmark_id": benchmark_id})
            if doc:
                return HybridBenchmarkResult.model_validate(doc)
        return None

    @classmethod
    async def list_benchmarks(cls, limit: int = 25) -> List[HybridBenchmarkResult]:
        """Lists recent hybrid benchmark suites."""
        results: List[HybridBenchmarkResult] = []
        raw_list = db_manager.memory_list("hybrid_benchmarks")
        for item in raw_list:
            try:
                results.append(HybridBenchmarkResult.model_validate(item))
            except Exception:
                pass

        if db_manager.is_connected and db_manager.db is not None:
            try:
                cursor = db_manager.db["hybrid_benchmarks"].find().sort("created_at", -1).limit(limit)
                async for doc in cursor:
                    if not any(r.benchmark_id == doc.get("benchmark_id") for r in results):
                        results.append(HybridBenchmarkResult.model_validate(doc))
            except Exception:
                pass

        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[:limit]
