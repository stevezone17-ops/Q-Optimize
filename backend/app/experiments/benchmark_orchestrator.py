"""Unified multi-algorithm benchmark orchestration engine."""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.app.core.logging import logger
from backend.app.db.mongodb import db_manager
from backend.app.experiments.models import ExperimentAlgorithm, ExperimentResult

BENCHMARK_COLLECTION = "experiment_benchmarks"


class BenchmarkMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    REPEATED_TRIALS = "repeated_trials"
    MULTI_INSTANCE = "multi_instance"


class BenchmarkConfiguration(BaseModel):
    benchmark_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(default="Benchmark Run")
    problem_type: str
    problem_instance: Dict[str, Any]
    algorithms: List[ExperimentAlgorithm] = Field(
        default_factory=lambda: [ExperimentAlgorithm.SIMULATED_ANNEALING]
    )
    num_trials: int = Field(default=3, ge=1, le=50)
    seeds: Optional[List[int]] = None
    mode: BenchmarkMode = BenchmarkMode.PARALLEL
    max_workers: int = Field(default=4, ge=1, le=16)
    timeout_seconds: float = Field(default=120.0, ge=1.0)
    algorithm_configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class TrialRecord(BaseModel):
    trial_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    benchmark_id: str
    algorithm: str
    trial_index: int
    seed: Optional[int] = None
    result: Optional[ExperimentResult] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class BenchmarkRecord(BaseModel):
    benchmark_id: str
    name: str
    problem_type: str
    algorithms: List[str]
    num_trials: int
    mode: BenchmarkMode
    status: str = "pending"
    trials: List[TrialRecord] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None
    total_runtime_seconds: float = 0.0
    error_message: Optional[str] = None


def _dispatch_trial(
    algo: ExperimentAlgorithm,
    problem_type: str,
    problem_instance: Dict[str, Any],
    algo_config: Dict[str, Any],
    seed: Optional[int],
) -> Dict[str, Any]:
    """Execute a single trial for the given algorithm."""
    if seed is not None:
        algo_config = dict(algo_config)
        algo_config["seed"] = seed

    start = time.perf_counter()
    try:
        if algo == ExperimentAlgorithm.QAOA:
            from backend.app.solvers.quantum.pipeline import QAOAExecutionPipeline
            pipeline = QAOAExecutionPipeline()
            result = pipeline.execute(problem_type, problem_instance, config=algo_config)
        elif algo == ExperimentAlgorithm.ADAPTIVE_QAOA:
            from backend.app.solvers.quantum.adaptive.pipeline import AdaptiveQAOAExecutionPipeline
            pipeline = AdaptiveQAOAExecutionPipeline()
            result = pipeline.execute(problem_type, problem_instance, config=algo_config)
        else:
            from backend.app.solvers.classical.factory import ClassicalSolverFactory
            algo_map = {
                ExperimentAlgorithm.EXACT: "exact",
                ExperimentAlgorithm.GENETIC_ALGORITHM: "genetic_algorithm",
                ExperimentAlgorithm.SIMULATED_ANNEALING: "simulated_annealing",
            }
            solver = ClassicalSolverFactory.get_solver(algo_map[algo])
            result = solver.solve(problem_type, problem_instance, config=algo_config)

        elapsed = time.perf_counter() - start
        return {
            "objective_value": getattr(result, "objective_value", None),
            "best_solution": getattr(result, "best_solution", None),
            "runtime_seconds": elapsed,
            "is_feasible": getattr(result, "is_feasible", False),
            "num_evaluations": getattr(result, "num_evaluations", 0),
            "convergence_history": getattr(result, "convergence_history", []),
            "algorithm_metrics": getattr(result, "metadata", {}),
            "status": "completed",
        }
    except Exception as exc:
        elapsed = time.perf_counter() - start
        logger.error(f"Trial dispatch failed for {algo.value}: {exc}")
        return {
            "runtime_seconds": elapsed,
            "error": str(exc),
            "status": "failed",
        }


class BenchmarkOrchestrator:
    """Orchestrates multi-algorithm benchmarking with parallel execution support."""

    def run_benchmark(self, config: BenchmarkConfiguration) -> BenchmarkRecord:
        """Execute a full benchmark run and return the recorded results."""
        record = BenchmarkRecord(
            benchmark_id=config.benchmark_id,
            name=config.name,
            problem_type=config.problem_type,
            algorithms=[a.value for a in config.algorithms],
            num_trials=config.num_trials,
            mode=config.mode,
            status="running",
        )
        db_manager.memory_insert(
            BENCHMARK_COLLECTION, record.benchmark_id, record.model_dump(mode="json")
        )

        algo_configs: Dict[str, Dict[str, Any]] = {
            (k.value if hasattr(k, "value") else k): v
            for k, v in config.algorithm_configs.items()
        }

        # Build trial plan
        trials: List[TrialRecord] = []
        for algo in config.algorithms:
            for trial_idx in range(config.num_trials):
                seed = None
                if config.seeds and trial_idx < len(config.seeds):
                    seed = config.seeds[trial_idx]
                trials.append(
                    TrialRecord(
                        benchmark_id=config.benchmark_id,
                        algorithm=algo.value,
                        trial_index=trial_idx,
                        seed=seed,
                    )
                )

        overall_start = time.perf_counter()
        completed_trials: List[TrialRecord] = []

        if config.mode == BenchmarkMode.SEQUENTIAL:
            for trial in trials:
                self._execute_trial(trial, config, algo_configs)
                completed_trials.append(trial)
        else:
            max_workers = min(config.max_workers, len(trials), 8)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._execute_trial, trial, config, algo_configs): trial
                    for trial in trials
                }
                for future in as_completed(futures, timeout=config.timeout_seconds * len(trials)):
                    trial = futures[future]
                    try:
                        future.result(timeout=config.timeout_seconds)
                    except Exception as exc:
                        trial.error = str(exc)
                    completed_trials.append(trial)

        total_elapsed = time.perf_counter() - overall_start
        failed_count = sum(1 for t in completed_trials if t.error or (t.result and t.result.status != "completed"))

        record.trials = completed_trials
        record.total_runtime_seconds = total_elapsed
        record.completed_at = datetime.now(timezone.utc).isoformat()
        record.status = "completed" if failed_count == 0 else ("partially_completed" if failed_count < len(completed_trials) else "failed")

        db_manager.memory_insert(
            BENCHMARK_COLLECTION, record.benchmark_id, record.model_dump(mode="json")
        )
        logger.info(f"Benchmark '{config.benchmark_id}' finished: {record.status} in {total_elapsed:.2f}s")
        return record

    def _execute_trial(
        self,
        trial: TrialRecord,
        config: BenchmarkConfiguration,
        algo_configs: Dict[str, Dict[str, Any]],
    ) -> None:
        """Execute a single trial, updating the trial in-place."""
        algo = ExperimentAlgorithm(trial.algorithm)
        a_config = algo_configs.get(trial.algorithm, {})
        trial.started_at = datetime.now(timezone.utc).isoformat()
        raw = _dispatch_trial(algo, config.problem_type, config.problem_instance, a_config, trial.seed)
        trial.result = ExperimentResult(
            algorithm=trial.algorithm,
            trial_index=trial.trial_index,
            seed=trial.seed,
            objective_value=raw.get("objective_value"),
            best_solution=raw.get("best_solution"),
            runtime_seconds=raw.get("runtime_seconds", 0.0),
            is_feasible=raw.get("is_feasible", False),
            num_evaluations=raw.get("num_evaluations", 0),
            convergence_history=raw.get("convergence_history", []),
            algorithm_metrics=raw.get("algorithm_metrics", {}),
            error=raw.get("error"),
            status=raw.get("status", "failed"),
        )
        trial.completed_at = datetime.now(timezone.utc).isoformat()
        if raw.get("error"):
            trial.error = raw["error"]

    def get_benchmark(self, benchmark_id: str) -> Optional[BenchmarkRecord]:
        raw = db_manager.memory_get(BENCHMARK_COLLECTION, benchmark_id)
        if raw:
            return BenchmarkRecord.model_validate(raw)
        return None

    def list_benchmarks(self) -> List[BenchmarkRecord]:
        return [BenchmarkRecord.model_validate(r) for r in db_manager.memory_list(BENCHMARK_COLLECTION)]


benchmark_orchestrator = BenchmarkOrchestrator()

