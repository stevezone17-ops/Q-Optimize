"""Benchmarking and performance evaluation engine for classical optimization solvers."""

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
from backend.app.solvers.classical.models import (
    SolverResult,
    ConvergencePoint,
)
from backend.app.solvers.classical.exceptions import (
    SolverNotFoundError,
    UnsupportedProblemTypeError,
)
from backend.app.db.mongodb import db_manager
from backend.app.core.logging import logger


class BenchmarkRequest(BaseModel):
    """Payload to initiate a multi-solver classical benchmark."""
    name: Optional[str] = Field("Classical Benchmark", description="Human-readable benchmark name")
    problem_id: Optional[str] = Field(None, description="ID of registered canonical problem")
    problem_type: Optional[ProblemType] = Field(None, description="Problem type if using ad-hoc instance")
    instance: Optional[Dict[str, Any]] = Field(None, description="Ad-hoc instance definition")
    solver_ids: List[str] = Field(
        default_factory=lambda: ["exact", "genetic_algorithm", "simulated_annealing"],
        description="Solvers to benchmark against problem instance",
    )
    solver_configs: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-solver configuration parameter overrides",
    )
    trials: int = Field(1, ge=1, le=20, description="Number of repetitions per stochastic solver")
    base_seed: int = Field(42, description="Base random seed for reproducible benchmark execution")


class SolverBenchmarkSummary(BaseModel):
    """Statistical summary of a solver across benchmark trials."""
    solver_id: str
    solver_name: str
    trials_count: int
    best_objective: float
    mean_objective: float
    worst_objective: float
    std_objective: float
    feasibility_rate: float = Field(..., description="Proportion of trials producing feasible solutions (0.0 to 1.0)")
    mean_runtime_ms: float
    min_runtime_ms: float
    max_runtime_ms: float
    mean_evaluations: float
    optimality_gap_percent: Optional[float] = Field(None, description="Gap to exact global optimum: |f - f*| / |f*| * 100%")
    best_solution: Any = None
    convergence_sample: List[ConvergencePoint] = Field(default_factory=list, description="Convergence trace from the best trial")


class BenchmarkResult(BaseModel):
    """Comprehensive benchmark comparison result across multiple solvers."""
    benchmark_id: str = Field(default_factory=lambda: f"bench-{uuid.uuid4().hex[:12]}")
    name: str
    problem_type: ProblemType
    problem_id: Optional[str] = None
    exact_optimum: Optional[float] = None
    summaries: List[SolverBenchmarkSummary]
    total_runtime_seconds: float
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ClassicalBenchmarkEngine:
    """
    Executes multiple classical solvers across multiple trials, computes rigorous
    statistical comparisons (mean, std, min, max, feasibility rate, optimality gap),
    and persists benchmark suites for analysis.
    """

    @classmethod
    async def _resolve_problem(
        cls, req: BenchmarkRequest, owner_id: str = "default_user"
    ) -> tuple[ProblemType, Dict[str, Any]]:
        """Resolve canonical problem definition from request."""
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
        cls, req: BenchmarkRequest, owner_id: str = "default_user"
    ) -> BenchmarkResult:
        """
        Execute benchmark comparing requested solvers against the target problem.
        """
        target_problem_type, target_instance = await cls._resolve_problem(req, owner_id)
        benchmark_id = f"bench-{uuid.uuid4().hex[:12]}"
        t_start = time.perf_counter()

        # Validate that all requested solvers exist and support problem type
        solvers_to_run = []
        for s_id in req.solver_ids:
            clean_id = s_id.strip().lower()
            solver = ClassicalSolverFactory.get_solver(clean_id)
            solver.check_problem_support(target_problem_type)
            solvers_to_run.append((clean_id, solver))

        # Check if exact solver is in the suite; if so, run it first to establish global optimum
        exact_optimum: Optional[float] = None
        exact_entry = next(((cid, s) for cid, s in solvers_to_run if cid == "exact"), None)

        if exact_entry:
            _, exact_solver = exact_entry
            cfg_dict = req.solver_configs.get("exact", {})
            parsed_cfg = exact_solver.validate_config(cfg_dict)
            exact_res: SolverResult = exact_solver.solve(
                problem_type=target_problem_type,
                instance=target_instance,
                config=parsed_cfg,
                seed=req.base_seed,
            )
            exact_optimum = exact_res.objective_value

        summaries: List[SolverBenchmarkSummary] = []

        # Execute trials for each solver
        for solver_id, solver in solvers_to_run:
            # Deterministic exact solver only needs 1 trial
            num_trials = 1 if solver_id == "exact" else req.trials
            cfg_dict = req.solver_configs.get(solver_id, {})
            parsed_cfg = solver.validate_config(cfg_dict)

            trial_results: List[SolverResult] = []

            for trial_idx in range(num_trials):
                trial_seed = req.base_seed + trial_idx * 17
                res: SolverResult = solver.solve(
                    problem_type=target_problem_type,
                    instance=target_instance,
                    config=parsed_cfg,
                    seed=trial_seed,
                )
                trial_results.append(res)

            # Aggregate trial statistics
            objectives = [r.objective_value for r in trial_results if r.objective_value is not None]
            runtimes_ms = [r.runtime_seconds * 1000.0 for r in trial_results]
            evaluations = [r.evaluations for r in trial_results]
            feasible_count = sum(1 for r in trial_results if r.is_feasible)

            # Determine best trial: max for Max-Cut, min for Assignment/TSP
            is_max = target_problem_type == ProblemType.MAX_CUT
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

            mean_runtime = float(np.mean(runtimes_ms))
            min_runtime = float(np.min(runtimes_ms))
            max_runtime = float(np.max(runtimes_ms))
            mean_evals = float(np.mean(evaluations))

            # Optimality gap calculation
            gap_percent: Optional[float] = None
            if exact_optimum is not None and len(objectives) > 0:
                diff = abs(best_obj - exact_optimum)
                denom = abs(exact_optimum) + 1e-9
                gap_percent = round((diff / denom) * 100.0, 4)

            summary = SolverBenchmarkSummary(
                solver_id=solver.solver_id,
                solver_name=solver.name,
                trials_count=num_trials,
                best_objective=best_obj,
                mean_objective=mean_obj,
                worst_objective=worst_obj,
                std_objective=std_obj,
                feasibility_rate=feas_rate,
                mean_runtime_ms=round(mean_runtime, 3),
                min_runtime_ms=round(min_runtime, 3),
                max_runtime_ms=round(max_runtime, 3),
                mean_evaluations=mean_evals,
                optimality_gap_percent=gap_percent,
                best_solution=best_trial.candidate_solution,
                convergence_sample=best_trial.convergence_history,
            )
            summaries.append(summary)

        total_runtime = time.perf_counter() - t_start

        benchmark_result = BenchmarkResult(
            benchmark_id=benchmark_id,
            name=req.name or "Classical Benchmark",
            problem_type=target_problem_type,
            problem_id=req.problem_id,
            exact_optimum=exact_optimum,
            summaries=summaries,
            total_runtime_seconds=round(total_runtime, 4),
        )

        # Persist benchmark
        await cls._persist_benchmark(benchmark_result)
        return benchmark_result

    @classmethod
    async def _persist_benchmark(cls, result: BenchmarkResult) -> None:
        """Store benchmark in memory and MongoDB if available."""
        res_dict = result.model_dump()
        db_manager.memory_insert("benchmarks", result.benchmark_id, res_dict)

        if db_manager.is_connected and db_manager.db is not None:
            try:
                await db_manager.db["benchmarks"].update_one(
                    {"benchmark_id": result.benchmark_id},
                    {"$set": res_dict},
                    upsert=True,
                )
            except Exception as e:
                logger.warning(f"Could not persist benchmark to MongoDB ({e}); cached in memory.")

    @classmethod
    async def get_benchmark(cls, benchmark_id: str) -> Optional[BenchmarkResult]:
        """Retrieve a stored benchmark result by ID."""
        data = db_manager.memory_get("benchmarks", benchmark_id)
        if data:
            return BenchmarkResult(**data)

        if db_manager.is_connected and db_manager.db is not None:
            doc = await db_manager.db["benchmarks"].find_one({"benchmark_id": benchmark_id})
            if doc:
                doc.pop("_id", None)
                return BenchmarkResult(**doc)

        return None

    @classmethod
    async def list_benchmarks(cls, limit: int = 50) -> List[BenchmarkResult]:
        """List recent benchmark suites ordered newest first."""
        results: List[BenchmarkResult] = []
        raw_list = db_manager.memory_list("benchmarks")
        for item in raw_list:
            results.append(BenchmarkResult(**item))

        if db_manager.is_connected and db_manager.db is not None:
            try:
                cursor = db_manager.db["benchmarks"].find().sort("created_at", -1).limit(limit)
                docs = await cursor.to_list(length=limit)
                for doc in docs:
                    doc.pop("_id", None)
                    b = BenchmarkResult(**doc)
                    if not any(r.benchmark_id == b.benchmark_id for r in results):
                        results.append(b)
            except Exception as e:
                logger.warning(f"Error fetching benchmarks from MongoDB: {e}")

        results.sort(key=lambda b: b.created_at, reverse=True)
        return results[:limit]
