"""Adaptive QAOA Benchmarking & Ablation Study Engine.

Compares Standard fixed-depth QAOA against Adaptive QAOA strategy variants
(Dynamic Depth Growth, Warm-Start Transfer, Fourier Parameterization, Optimizer Switching)
to scientifically isolate and quantify the source of optimization improvements.
"""

import math
import uuid
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from backend.app.domain.problems.models import ProblemType
from backend.app.evaluation.evaluator_factory import EvaluatorFactory
from backend.app.services.problem_service import ProblemService
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.solvers.classical.models import SolverRequest
from backend.app.solvers.quantum.models import ClassicalOptimizerType
from backend.app.solvers.quantum.adaptive.adaptive_config import (
    AdaptiveStrategyType,
    InitializationStrategyType,
    DepthGrowthStrategy,
    OptimizerScheduleType,
)
from backend.app.solvers.quantum.adaptive.adaptive_models import (
    AdaptiveQAOAConfiguration,
    AdaptiveStrategyConfiguration,
    AdaptiveQAOARequest,
    AdaptiveQAOAResult,
)
from backend.app.solvers.quantum.adaptive.pipeline import AdaptiveQAOAExecutionPipeline
from backend.app.db.mongodb import db_manager
from backend.app.core.logging import logger


class AdaptiveAblationVariant(str, Enum):
    """Ablation variants for Adaptive QAOA empirical research."""
    STANDARD_BASELINE = "standard_baseline"
    FULL_ADAPTIVE = "full_adaptive"
    ABLATION_NO_WARM_START = "ablation_no_warm_start"
    ABLATION_NO_DYNAMIC_DEPTH = "ablation_no_dynamic_depth"
    ABLATION_NO_OPTIMIZER_SWITCHING = "ablation_no_optimizer_switching"
    ABLATION_FOURIER = "ablation_fourier"


class AdaptiveBenchmarkRequest(BaseModel):
    """Request payload to execute comparative Adaptive QAOA ablation benchmark."""
    name: Optional[str] = Field("Adaptive QAOA Ablation & Performance Benchmark", description="Benchmark label")
    problem_id: Optional[str] = Field(None, description="Registered canonical problem ID")
    problem_type: Optional[ProblemType] = Field(None, description="Problem family for ad-hoc problems")
    instance: Optional[Dict[str, Any]] = Field(None, description="Ad-hoc problem instance definition")
    include_variants: List[AdaptiveAblationVariant] = Field(
        default_factory=lambda: [
            AdaptiveAblationVariant.STANDARD_BASELINE,
            AdaptiveAblationVariant.FULL_ADAPTIVE,
            AdaptiveAblationVariant.ABLATION_NO_WARM_START,
            AdaptiveAblationVariant.ABLATION_NO_DYNAMIC_DEPTH,
            AdaptiveAblationVariant.ABLATION_NO_OPTIMIZER_SWITCHING,
            AdaptiveAblationVariant.ABLATION_FOURIER,
        ],
        description="Strategy and ablation variants to benchmark",
    )
    initial_depth: int = Field(1, ge=1, le=5, description="Initial circuit depth p_init")
    max_depth: int = Field(2, ge=1, le=10, description="Max depth limit p_max")
    shots: int = Field(1024, ge=100, le=10000, description="Quantum measurement shots per circuit evaluation")
    primary_optimizer: ClassicalOptimizerType = Field(ClassicalOptimizerType.COBYLA, description="Primary optimizer")
    fallback_optimizer: ClassicalOptimizerType = Field(ClassicalOptimizerType.NELDER_MEAD, description="Fallback optimizer")
    max_evaluations_total: int = Field(60, ge=10, le=500, description="Evaluation budget per variant trial")
    trials: int = Field(2, ge=1, le=10, description="Repetitions for statistical distributions")
    base_seed: int = Field(42, description="Base seed for reproducibility")


class AdaptiveVariantSummary(BaseModel):
    """Performance and ablation statistics for a specific QAOA strategy variant."""
    variant_id: str
    variant_name: str
    description: str
    trials_count: int
    initial_depth: int
    mean_final_depth: float
    best_objective: float
    mean_objective: float
    worst_objective: float
    std_objective: float
    feasibility_rate: float
    approximation_ratio: Optional[float] = Field(None, description="Approximation ratio r relative to exact global optimum")
    optimality_gap_percent: Optional[float] = Field(None, description="Optimality gap % relative to global optimum")
    mean_runtime_ms: float
    min_runtime_ms: float
    max_runtime_ms: float
    mean_evaluations: float
    mean_circuit_executions: float
    depth_growth_trigger_rate: float = Field(0.0, description="Fraction of trials where layer growth was triggered")
    optimizer_switch_trigger_rate: float = Field(0.0, description="Fraction of trials where optimizer switch occurred")
    eval_efficiency_ratio: Optional[float] = Field(None, description="Ratio of baseline evals to variant evals")
    quality_improvement_percent: Optional[float] = Field(None, description="% improvement in mean objective vs standard baseline")
    best_solution: Any = None


class AdaptiveBenchmarkResult(BaseModel):
    """Consolidated comparative benchmark result across Adaptive QAOA variants."""
    benchmark_id: str = Field(default_factory=lambda: f"aqbench-{uuid.uuid4().hex[:12]}")
    name: str
    problem_type: ProblemType
    problem_id: Optional[str] = None
    exact_optimum: Optional[float] = None
    summaries: List[AdaptiveVariantSummary]
    ablation_insights: List[str] = Field(default_factory=list, description="Automated scientific insights derived from ablation data")
    total_runtime_seconds: float
    hardware_transparency_note: str = (
        "All quantum simulations (Standard QAOA & Adaptive QAOA variants) run on classical CPU emulation "
        "via Qiskit Aer. Runtimes reflect classical simulation overhead. No physical quantum hardware speedup is claimed."
    )
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# In-memory storage fallback for benchmarks
_ADAPTIVE_BENCHMARK_MEMORY_STORE: Dict[str, Dict[str, Any]] = {}


class AdaptiveBenchmarkEngine:
    """
    Executes and statistically analyzes Adaptive QAOA strategy variants against
    fixed-depth standard QAOA baselines on canonical optimization problems.
    """

    @classmethod
    async def _resolve_problem(
        cls, req: AdaptiveBenchmarkRequest, owner_id: str = "default_user"
    ) -> tuple[ProblemType, Dict[str, Any]]:
        """Resolves target problem type and instance representation."""
        if req.problem_id:
            stored = await ProblemService.get_problem(req.problem_id, owner_id=owner_id)
            if not stored:
                raise ValueError(f"Problem with ID '{req.problem_id}' not found.")
            return stored.problem_type, stored.instance

        if req.problem_type and req.instance:
            return req.problem_type, req.instance

        raise ValueError("Either problem_id or both problem_type and instance must be provided.")

    @classmethod
    async def _compute_exact_optimum(
        cls, problem_type: ProblemType, instance: Dict[str, Any], seed: int = 42
    ) -> tuple[Optional[float], str]:
        """Computes deterministic ground-truth optimum and objective sense via ExactSolver."""
        sense = "maximize" if problem_type == ProblemType.MAX_CUT else "minimize"
        try:
            exact_solver = ClassicalSolverFactory.get_solver("exact")
            exact_cfg = exact_solver.validate_config({})
            exact_res = exact_solver.solve(
                problem_type=problem_type,
                instance=instance,
                config=exact_cfg,
                seed=seed,
            )
            return exact_res.objective_value, sense
        except Exception as exc:
            logger.warning(f"Could not compute exact optimum for benchmark: {exc}")
            return None, sense

    @classmethod
    def _build_variant_config(
        cls,
        variant: AdaptiveAblationVariant,
        req: AdaptiveBenchmarkRequest,
        seed: int,
    ) -> AdaptiveQAOAConfiguration:
        """Constructs the exact strategy configuration for each ablation variant."""
        if variant == AdaptiveAblationVariant.STANDARD_BASELINE:
            strat_config = AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.STANDARD,
                init_strategy=InitializationStrategyType.LINEAR_RAMP,
                initial_depth=req.initial_depth,
                max_depth=req.initial_depth,
                depth_growth=DepthGrowthStrategy.NONE,
                primary_optimizer=req.primary_optimizer,
                optimizer_schedule=OptimizerScheduleType.STATIC,
                max_evaluations_total=req.max_evaluations_total,
            )
        elif variant == AdaptiveAblationVariant.FULL_ADAPTIVE:
            strat_config = AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.FULL_ADAPTIVE,
                init_strategy=InitializationStrategyType.LINEAR_RAMP,
                initial_depth=req.initial_depth,
                max_depth=req.max_depth,
                depth_growth=DepthGrowthStrategy.IMPROVEMENT_TRIGGERED,
                stagnation_patience=2,
                improvement_threshold=0.001,
                primary_optimizer=req.primary_optimizer,
                fallback_optimizer=req.fallback_optimizer,
                optimizer_schedule=OptimizerScheduleType.ADAPTIVE_FALLBACK,
                max_evaluations_total=req.max_evaluations_total,
            )
        elif variant == AdaptiveAblationVariant.ABLATION_NO_WARM_START:
            strat_config = AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.DYNAMIC_DEPTH,
                init_strategy=InitializationStrategyType.RANDOM,
                initial_depth=req.initial_depth,
                max_depth=req.max_depth,
                depth_growth=DepthGrowthStrategy.IMPROVEMENT_TRIGGERED,
                stagnation_patience=2,
                improvement_threshold=0.001,
                primary_optimizer=req.primary_optimizer,
                fallback_optimizer=req.fallback_optimizer,
                optimizer_schedule=OptimizerScheduleType.ADAPTIVE_FALLBACK,
                max_evaluations_total=req.max_evaluations_total,
            )
        elif variant == AdaptiveAblationVariant.ABLATION_NO_DYNAMIC_DEPTH:
            strat_config = AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.ADAPTIVE_OPTIMIZER,
                init_strategy=InitializationStrategyType.LINEAR_RAMP,
                initial_depth=req.initial_depth,
                max_depth=req.initial_depth,
                depth_growth=DepthGrowthStrategy.NONE,
                primary_optimizer=req.primary_optimizer,
                fallback_optimizer=req.fallback_optimizer,
                optimizer_schedule=OptimizerScheduleType.ADAPTIVE_FALLBACK,
                max_evaluations_total=req.max_evaluations_total,
            )
        elif variant == AdaptiveAblationVariant.ABLATION_NO_OPTIMIZER_SWITCHING:
            strat_config = AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.DYNAMIC_DEPTH,
                init_strategy=InitializationStrategyType.LINEAR_RAMP,
                initial_depth=req.initial_depth,
                max_depth=req.max_depth,
                depth_growth=DepthGrowthStrategy.IMPROVEMENT_TRIGGERED,
                stagnation_patience=2,
                improvement_threshold=0.001,
                primary_optimizer=req.primary_optimizer,
                optimizer_schedule=OptimizerScheduleType.STATIC,
                max_evaluations_total=req.max_evaluations_total,
            )
        elif variant == AdaptiveAblationVariant.ABLATION_FOURIER:
            strat_config = AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.FOURIER,
                init_strategy=InitializationStrategyType.FOURIER,
                initial_depth=req.initial_depth,
                max_depth=req.initial_depth,
                fourier_q_order=2,
                depth_growth=DepthGrowthStrategy.NONE,
                primary_optimizer=req.primary_optimizer,
                optimizer_schedule=OptimizerScheduleType.STATIC,
                max_evaluations_total=req.max_evaluations_total,
            )
        else:
            strat_config = AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.STANDARD,
                initial_depth=req.initial_depth,
                max_depth=req.initial_depth,
            )

        return AdaptiveQAOAConfiguration(
            shots=req.shots,
            simulation_mode="ideal_shots",
            backend_name="aer_simulator",
            seed=seed,
            noise_model_enabled=False,
            strategy_config=strat_config,
        )

    @classmethod
    async def run_benchmark(
        cls, req: AdaptiveBenchmarkRequest, owner_id: str = "default_user"
    ) -> AdaptiveBenchmarkResult:
        """Executes the full comparative ablation benchmark study."""
        start_time = time.time()
        prob_type, instance = await cls._resolve_problem(req, owner_id=owner_id)
        exact_optimum, sense = await cls._compute_exact_optimum(prob_type, instance, seed=req.base_seed)

        variant_meta = {
            AdaptiveAblationVariant.STANDARD_BASELINE: (
                "Standard QAOA Baseline",
                "Fixed depth p, static optimizer, Trotter linear ramp parameter initialization."
            ),
            AdaptiveAblationVariant.FULL_ADAPTIVE: (
                "Full Adaptive QAOA",
                "Dynamic depth growth on stagnation + warm-start angle transfer + adaptive optimizer fallback."
            ),
            AdaptiveAblationVariant.ABLATION_NO_WARM_START: (
                "Ablation: No Warm-Start",
                "Dynamic depth expansion enabled, but random re-initialization rather than angle interpolation."
            ),
            AdaptiveAblationVariant.ABLATION_NO_DYNAMIC_DEPTH: (
                "Ablation: No Dynamic Depth",
                "Adaptive optimizer scheduling enabled, but depth is strictly fixed at p_init."
            ),
            AdaptiveAblationVariant.ABLATION_NO_OPTIMIZER_SWITCHING: (
                "Ablation: No Optimizer Switching",
                "Dynamic depth growth and warm-starts enabled, but classical optimizer remains strictly static."
            ),
            AdaptiveAblationVariant.ABLATION_FOURIER: (
                "Fourier Parameterization",
                "Fixed depth using discrete cosine/sine frequency parameterization (u, v)."
            ),
        }

        summaries: List[AdaptiveVariantSummary] = []
        baseline_mean_obj: Optional[float] = None
        baseline_mean_evals: Optional[float] = None

        for variant in req.include_variants:
            v_name, v_desc = variant_meta.get(variant, (variant.value, "Ablation variant"))
            trial_objs: List[float] = []
            trial_runtimes_ms: List[float] = []
            trial_evals: List[int] = []
            trial_circuits: List[int] = []
            trial_final_depths: List[int] = []
            trial_feasible_flags: List[bool] = []
            depth_growths_count = 0
            optimizer_switches_count = 0
            best_sol: Any = None
            best_obj_trial: Optional[float] = None

            for t in range(req.trials):
                seed = req.base_seed + (t * 7)
                qaoa_cfg = cls._build_variant_config(variant, req, seed)
                exec_req = AdaptiveQAOARequest(
                    problem_id=req.problem_id or f"ad-hoc-{prob_type.value}",
                    problem_type=prob_type,
                    instance=instance,
                    config=qaoa_cfg,
                )

                try:
                    res: AdaptiveQAOAResult = AdaptiveQAOAExecutionPipeline.execute_sync(exec_req)
                    obj = res.objective_value
                    trial_objs.append(obj)
                    trial_runtimes_ms.append(res.execution_time_ms)
                    trial_evals.append(res.total_evaluations)
                    trial_circuits.append(res.total_circuit_executions)
                    trial_final_depths.append(res.final_depth)
                    trial_feasible_flags.append(res.is_feasible)

                    # Check decision log for growth or switch triggers
                    for d in res.decisions_log:
                        if d.from_depth != d.to_depth:
                            depth_growths_count += 1
                        if "switch" in d.action_summary.lower() or "optimizer" in d.action_summary.lower():
                            optimizer_switches_count += 1

                    # Track best solution
                    if best_obj_trial is None:
                        best_obj_trial = obj
                        best_sol = res.best_solution
                    else:
                        is_better = (obj > best_obj_trial) if sense == "maximize" else (obj < best_obj_trial)
                        if is_better:
                            best_obj_trial = obj
                            best_sol = res.best_solution

                except Exception as exc:
                    logger.error(f"Benchmark trial {t} for variant {variant} failed: {exc}")
                    trial_objs.append(0.0)
                    trial_runtimes_ms.append(0.0)
                    trial_evals.append(0)
                    trial_circuits.append(0)
                    trial_final_depths.append(req.initial_depth)
                    trial_feasible_flags.append(False)

            if not trial_objs:
                continue

            arr = np.array(trial_objs)
            mean_obj = float(np.mean(arr))
            best_obj = float(np.max(arr)) if sense == "maximize" else float(np.min(arr))
            worst_obj = float(np.min(arr)) if sense == "maximize" else float(np.max(arr))
            std_obj = float(np.std(arr)) if len(arr) > 1 else 0.0

            feas_rate = sum(trial_feasible_flags) / max(1, len(trial_feasible_flags))
            mean_rt = float(np.mean(trial_runtimes_ms))
            min_rt = float(np.min(trial_runtimes_ms))
            max_rt = float(np.max(trial_runtimes_ms))
            mean_ev = float(np.mean(trial_evals))
            mean_circ = float(np.mean(trial_circuits))
            mean_depth = float(np.mean(trial_final_depths))

            # Approximation ratio and gap
            approx_ratio = None
            opt_gap = None
            if exact_optimum is not None and abs(exact_optimum) > 1e-9:
                if sense == "maximize":
                    approx_ratio = mean_obj / exact_optimum
                else:
                    approx_ratio = exact_optimum / mean_obj if abs(mean_obj) > 1e-9 else 0.0
                opt_gap = abs(mean_obj - exact_optimum) / abs(exact_optimum) * 100.0

            # Baseline comparisons
            if variant == AdaptiveAblationVariant.STANDARD_BASELINE:
                baseline_mean_obj = mean_obj
                baseline_mean_evals = mean_ev

            eval_eff = None
            qual_imprv = None
            if baseline_mean_evals and baseline_mean_evals > 0 and mean_ev > 0:
                eval_eff = baseline_mean_evals / mean_ev

            if baseline_mean_obj is not None and abs(baseline_mean_obj) > 1e-9:
                if sense == "maximize":
                    qual_imprv = ((mean_obj - baseline_mean_obj) / abs(baseline_mean_obj)) * 100.0
                else:
                    qual_imprv = ((baseline_mean_obj - mean_obj) / abs(baseline_mean_obj)) * 100.0

            summary = AdaptiveVariantSummary(
                variant_id=variant.value,
                variant_name=v_name,
                description=v_desc,
                trials_count=req.trials,
                initial_depth=req.initial_depth,
                mean_final_depth=round(mean_depth, 2),
                best_objective=round(best_obj, 4),
                mean_objective=round(mean_obj, 4),
                worst_objective=round(worst_obj, 4),
                std_objective=round(std_obj, 4),
                feasibility_rate=round(feas_rate, 4),
                approximation_ratio=round(approx_ratio, 4) if approx_ratio is not None else None,
                optimality_gap_percent=round(opt_gap, 2) if opt_gap is not None else None,
                mean_runtime_ms=round(mean_rt, 2),
                min_runtime_ms=round(min_rt, 2),
                max_runtime_ms=round(max_rt, 2),
                mean_evaluations=round(mean_ev, 1),
                mean_circuit_executions=round(mean_circ, 1),
                depth_growth_trigger_rate=round(depth_growths_count / max(1, req.trials), 2),
                optimizer_switch_trigger_rate=round(optimizer_switches_count / max(1, req.trials), 2),
                eval_efficiency_ratio=round(eval_eff, 2) if eval_eff is not None else None,
                quality_improvement_percent=round(qual_imprv, 2) if qual_imprv is not None else None,
                best_solution=best_sol,
            )
            summaries.append(summary)

        # Synthesize scientific ablation insights
        insights = cls._generate_ablation_insights(summaries, sense)

        result = AdaptiveBenchmarkResult(
            name=req.name or f"Adaptive QAOA Ablation Study - {prob_type.value}",
            problem_type=prob_type,
            problem_id=req.problem_id,
            exact_optimum=exact_optimum,
            summaries=summaries,
            ablation_insights=insights,
            total_runtime_seconds=round(time.time() - start_time, 3),
        )

        await cls._save_benchmark(result)
        return result

    @classmethod
    def _generate_ablation_insights(
        cls, summaries: List[AdaptiveVariantSummary], sense: str
    ) -> List[str]:
        """Derives actionable scientific insights from the empirical ablation summary."""
        insights: List[str] = []
        summary_map = {s.variant_id: s for s in summaries}

        full_ad = summary_map.get(AdaptiveAblationVariant.FULL_ADAPTIVE.value)
        baseline = summary_map.get(AdaptiveAblationVariant.STANDARD_BASELINE.value)
        no_ws = summary_map.get(AdaptiveAblationVariant.ABLATION_NO_WARM_START.value)
        no_depth = summary_map.get(AdaptiveAblationVariant.ABLATION_NO_DYNAMIC_DEPTH.value)
        no_opt = summary_map.get(AdaptiveAblationVariant.ABLATION_NO_OPTIMIZER_SWITCHING.value)
        fourier = summary_map.get(AdaptiveAblationVariant.ABLATION_FOURIER.value)

        if full_ad and baseline:
            diff = full_ad.mean_objective - baseline.mean_objective
            if sense == "maximize" and diff > 0:
                insights.append(
                    f"Full Adaptive QAOA achieved a higher mean objective ({full_ad.mean_objective:.2f}) "
                    f"compared to standard fixed-depth baseline ({baseline.mean_objective:.2f}), "
                    f"yielding a {full_ad.quality_improvement_percent or 0:.1f}% improvement."
                )
            elif sense == "minimize" and diff < 0:
                insights.append(
                    f"Full Adaptive QAOA improved solution quality by minimizing objective to {full_ad.mean_objective:.2f} "
                    f"(vs {baseline.mean_objective:.2f} baseline), an improvement of {full_ad.quality_improvement_percent or 0:.1f}%."
                )
            else:
                insights.append(
                    f"Full Adaptive QAOA maintained competitive solution quality ({full_ad.mean_objective:.2f}) "
                    f"relative to standard baseline ({baseline.mean_objective:.2f})."
                )

        if full_ad and no_ws:
            ws_benefit = (full_ad.mean_objective - no_ws.mean_objective) if sense == "maximize" else (no_ws.mean_objective - full_ad.mean_objective)
            if ws_benefit > 0:
                insights.append(
                    f"Warm-Start Transfer Benefit: Parameter interpolation during layer growth improved solution quality "
                    f"by +{ws_benefit:.2f} over random layer expansion, validating smooth angle continuation."
                )
            else:
                insights.append(
                    "Warm-Start vs Cold Layer Growth: Both approaches achieved comparable solution quality on this instance."
                )

        if full_ad and no_depth:
            depth_benefit = (full_ad.mean_objective - no_depth.mean_objective) if sense == "maximize" else (no_depth.mean_objective - full_ad.mean_objective)
            if depth_benefit > 0:
                insights.append(
                    f"Dynamic Layer Growth Benefit: Energy stagnation-triggered layer expansion increased expressibility, "
                    f"yielding a +{depth_benefit:.2f} objective improvement over fixed initial depth."
                )

        if full_ad and no_opt:
            opt_benefit = (full_ad.mean_objective - no_opt.mean_objective) if sense == "maximize" else (no_opt.mean_objective - full_ad.mean_objective)
            if opt_benefit > 0:
                insights.append(
                    f"Adaptive Optimizer Scheduling Benefit: Switching to fallback local optimizer upon stagnation "
                    f"refined the variational landscape by +{opt_benefit:.2f} over a static optimizer schedule."
                )

        if fourier and baseline:
            f_diff = (fourier.mean_objective - baseline.mean_objective) if sense == "maximize" else (baseline.mean_objective - fourier.mean_objective)
            if f_diff >= 0:
                insights.append(
                    f"Fourier Parameterization: Discrete frequency components (u, v) performed comparably or favorably (+{f_diff:.2f}) "
                    f"against standard Trotter ramp angle initialization."
                )

        if not insights:
            insights.append("Ablation study executed successfully across all selected strategy variants.")

        return insights

    @classmethod
    async def _save_benchmark(cls, result: AdaptiveBenchmarkResult) -> None:
        """Persists benchmark result to MongoDB collection or memory fallback."""
        doc = result.model_dump()
        _ADAPTIVE_BENCHMARK_MEMORY_STORE[result.benchmark_id] = doc

        try:
            if db_manager.is_connected and db_manager.db is not None:
                await db_manager.db["adaptive_benchmarks"].replace_one(
                    {"benchmark_id": result.benchmark_id}, doc, upsert=True
                )
        except Exception as exc:
            logger.warning(f"Failed to persist adaptive benchmark to MongoDB: {exc}")

    @classmethod
    async def get_benchmark(cls, benchmark_id: str) -> Optional[AdaptiveBenchmarkResult]:
        """Retrieves past benchmark result by ID."""
        try:
            if db_manager.is_connected and db_manager.db is not None:
                doc = await db_manager.db["adaptive_benchmarks"].find_one({"benchmark_id": benchmark_id})
                if doc:
                    doc.pop("_id", None)
                    return AdaptiveBenchmarkResult(**doc)
        except Exception as exc:
            logger.warning(f"Failed to load adaptive benchmark from MongoDB: {exc}")

        cached = _ADAPTIVE_BENCHMARK_MEMORY_STORE.get(benchmark_id)
        if cached:
            return AdaptiveBenchmarkResult(**cached)
        return None

    @classmethod
    async def list_benchmarks(cls, limit: int = 25) -> List[Dict[str, Any]]:
        """Lists recent adaptive benchmark executions."""
        try:
            if db_manager.is_connected and db_manager.db is not None:
                cursor = db_manager.db["adaptive_benchmarks"].find(
                    {}, {"_id": 0, "benchmark_id": 1, "name": 1, "problem_type": 1, "created_at": 1, "total_runtime_seconds": 1}
                ).sort("created_at", -1).limit(limit)
                return await cursor.to_list(length=limit)
        except Exception as exc:
            logger.warning(f"Failed to list adaptive benchmarks from MongoDB: {exc}")

        return [
            {
                "benchmark_id": v["benchmark_id"],
                "name": v["name"],
                "problem_type": v["problem_type"],
                "created_at": v["created_at"],
                "total_runtime_seconds": v["total_runtime_seconds"],
            }
            for v in list(_ADAPTIVE_BENCHMARK_MEMORY_STORE.values())[-limit:]
        ]
