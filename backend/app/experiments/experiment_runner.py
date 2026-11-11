"""Experiment runner — dispatches experiment runs to solver pipelines using ThreadPoolExecutor."""

from __future__ import annotations

import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.experiments.models import (
    Experiment,
    ExperimentAlgorithm,
    ExperimentResult,
    ExperimentRun,
    ExperimentStatus,
)
from backend.app.experiments.registry import experiment_registry
from backend.app.experiments.experiment_status import is_terminal
from backend.app.core.logging import logger


def _run_classical_solver(
    solver_id: str,
    problem_type: str,
    problem_instance: Dict[str, Any],
    algorithm_config: Dict[str, Any],
    seed: Optional[int],
) -> Dict[str, Any]:
    """Execute a classical solver and return a result dict."""
    from backend.app.solvers.classical.factory import ClassicalSolverFactory

    solver = ClassicalSolverFactory.get_solver(solver_id)
    if seed is not None:
        algorithm_config = dict(algorithm_config)
        algorithm_config["seed"] = seed

    start = time.perf_counter()
    try:
        result = solver.solve(problem_type, problem_instance, config=algorithm_config)
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
        logger.error(f"Classical solver '{solver_id}' failed: {exc}")
        return {
            "runtime_seconds": elapsed,
            "error": str(exc),
            "status": "failed",
        }


def _run_qaoa_solver(
    problem_type: str,
    problem_instance: Dict[str, Any],
    algorithm_config: Dict[str, Any],
    seed: Optional[int],
) -> Dict[str, Any]:
    """Execute QAOA pipeline and return a result dict."""
    from backend.app.solvers.quantum.pipeline import QAOAExecutionPipeline

    if seed is not None:
        algorithm_config = dict(algorithm_config)
        algorithm_config["seed"] = seed

    start = time.perf_counter()
    try:
        pipeline = QAOAExecutionPipeline()
        result = pipeline.execute(problem_type, problem_instance, config=algorithm_config)
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
        logger.error(f"QAOA solver failed: {exc}")
        return {
            "runtime_seconds": elapsed,
            "error": str(exc),
            "status": "failed",
        }


def _run_adaptive_qaoa_solver(
    problem_type: str,
    problem_instance: Dict[str, Any],
    algorithm_config: Dict[str, Any],
    seed: Optional[int],
) -> Dict[str, Any]:
    """Execute Adaptive QAOA pipeline and return a result dict."""
    from backend.app.solvers.quantum.adaptive.pipeline import AdaptiveQAOAExecutionPipeline

    if seed is not None:
        algorithm_config = dict(algorithm_config)
        algorithm_config["seed"] = seed

    start = time.perf_counter()
    try:
        pipeline = AdaptiveQAOAExecutionPipeline()
        result = pipeline.execute(problem_type, problem_instance, config=algorithm_config)
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
        logger.error(f"Adaptive QAOA solver failed: {exc}")
        return {
            "runtime_seconds": elapsed,
            "error": str(exc),
            "status": "failed",
        }


_CLASSICAL_SOLVER_MAP = {
    ExperimentAlgorithm.EXACT: "exact",
    ExperimentAlgorithm.GENETIC_ALGORITHM: "genetic_algorithm",
    ExperimentAlgorithm.SIMULATED_ANNEALING: "simulated_annealing",
}


class ExperimentRunner:
    """Dispatches experiment runs to solver pipelines in a thread pool."""

    def run_experiment(self, experiment: Experiment) -> Experiment:
        """Execute all runs for the given experiment, updating its state in-place."""
        config = experiment.configuration
        budget = config.resource_budget
        max_workers = min(budget.max_workers, 8)

        # Build run plan
        runs: List[ExperimentRun] = []
        for algo in config.algorithms:
            for trial_idx in range(config.num_trials):
                seed: Optional[int] = None
                if config.seeds and trial_idx < len(config.seeds):
                    seed = config.seeds[trial_idx]
                run = ExperimentRun(
                    run_id=str(uuid.uuid4()),
                    experiment_id=experiment.experiment_id,
                    algorithm=algo.value,
                    trial_index=trial_idx,
                    seed=seed,
                    status=ExperimentStatus.QUEUED,
                )
                runs.append(run)

        experiment.runs = runs
        total_runs = len(runs)
        completed_runs = 0

        # Update status
        experiment.status = ExperimentStatus.RUNNING
        experiment.metadata.started_at = datetime.now(timezone.utc)
        experiment_registry.update(experiment)

        algo_configs: Dict[str, Dict[str, Any]] = {
            k.value if hasattr(k, "value") else k: v
            for k, v in config.algorithm_configs.items()
        }

        def dispatch_run(run: ExperimentRun) -> ExperimentResult:
            algo = ExperimentAlgorithm(run.algorithm)
            a_config = algo_configs.get(run.algorithm, {})
            run.status = ExperimentStatus.RUNNING
            run.started_at = datetime.now(timezone.utc)

            if algo in _CLASSICAL_SOLVER_MAP:
                raw = _run_classical_solver(
                    _CLASSICAL_SOLVER_MAP[algo],
                    config.problem_type,
                    config.problem_instance,
                    a_config,
                    run.seed,
                )
            elif algo == ExperimentAlgorithm.QAOA:
                raw = _run_qaoa_solver(
                    config.problem_type, config.problem_instance, a_config, run.seed
                )
            elif algo == ExperimentAlgorithm.ADAPTIVE_QAOA:
                raw = _run_adaptive_qaoa_solver(
                    config.problem_type, config.problem_instance, a_config, run.seed
                )
            else:
                raw = {"error": f"Unknown algorithm: {run.algorithm}", "status": "failed"}

            result = ExperimentResult(
                algorithm=run.algorithm,
                trial_index=run.trial_index,
                seed=run.seed,
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
            run.result = result
            run.status = (
                ExperimentStatus.COMPLETED
                if result.status == "completed"
                else ExperimentStatus.FAILED
            )
            run.completed_at = datetime.now(timezone.utc)
            return result

        all_results: List[ExperimentResult] = []
        failed_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_run: Dict[Future, ExperimentRun] = {
                executor.submit(dispatch_run, r): r for r in runs
            }
            for future in as_completed(future_to_run):
                run = future_to_run[future]
                try:
                    result = future.result(timeout=budget.max_runtime_seconds)
                    all_results.append(result)
                    if result.status != "completed":
                        failed_count += 1
                except Exception as exc:
                    logger.error(
                        f"Run {run.run_id} raised an unhandled exception: {exc}"
                    )
                    result = ExperimentResult(
                        algorithm=run.algorithm,
                        trial_index=run.trial_index,
                        seed=run.seed,
                        error=str(exc),
                        status="failed",
                    )
                    all_results.append(result)
                    run.status = ExperimentStatus.FAILED
                    run.error_message = str(exc)
                    failed_count += 1
                completed_runs += 1
                experiment.progress = completed_runs / total_runs

        experiment.results = all_results
        now = datetime.now(timezone.utc)
        experiment.metadata.completed_at = now
        experiment.metadata.updated_at = now

        if failed_count == 0:
            experiment.status = ExperimentStatus.COMPLETED
        elif failed_count == total_runs:
            experiment.status = ExperimentStatus.FAILED
        else:
            experiment.status = ExperimentStatus.PARTIALLY_COMPLETED

        experiment.progress = 1.0
        experiment_registry.update(experiment)
        return experiment


experiment_runner = ExperimentRunner()
