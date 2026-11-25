"""Stage 10.3 — Classical vs Quantum Algorithm Benchmarking Script.

Executes controlled paired benchmarks across:
  - Classical: Exact Solver, Simulated Annealing, Genetic Algorithm
  - Quantum (Qiskit AerSimulator): Standard QAOA (p=1), Adaptive QAOA (p=1..2)
  - AI-Assisted: Hybrid Solver Recommender evaluation (evaluated separately)

Saves raw per-trial results and family aggregations to:
  research/results/classical_vs_quantum_benchmark.json
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.ai.recommender import IntelligentSolverRecommender
from backend.app.domain.problems.models import ProblemType
from backend.app.evaluation.evaluator_factory import EvaluatorFactory
from backend.app.experiments.statistics import (
    _mean,
    _median,
    _std,
    approximation_ratio,
    optimality_gap,
)
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.solvers.classical.models import SolverConfiguration
from backend.app.solvers.quantum.adaptive.adaptive_config import (
    AdaptiveStrategyType,
    DepthGrowthStrategy,
    InitializationStrategyType,
    OptimizerScheduleType,
)
from backend.app.solvers.quantum.adaptive.adaptive_models import (
    AdaptiveQAOAConfiguration,
    AdaptiveQAOARequest,
    AdaptiveStrategyConfiguration,
)
from backend.app.solvers.quantum.adaptive.pipeline import AdaptiveQAOAExecutionPipeline
from backend.app.solvers.quantum.models import (
    ClassicalOptimizerType,
    QAOAConfiguration,
    QAOAExecutionRequest,
)
from backend.app.solvers.quantum.pipeline import QAOAExecutionPipeline

TRIAL_SEEDS = [42, 59, 76]


def _direction_for(problem_type: str) -> str:
    return "max" if problem_type == "max_cut" else "min"


async def run_benchmarks() -> None:
    ds_path = REPO_ROOT / "research" / "datasets" / "qoptimize_research_datasets.json"
    dataset_payload = json.loads(ds_path.read_text(encoding="utf-8"))

    trial_records: List[Dict[str, Any]] = []
    recommender_records: List[Dict[str, Any]] = []
    recommender = IntelligentSolverRecommender()

    for ds in dataset_payload["datasets"]:
        family_key = ds["family_key"]
        ptype_str = ds["problem_type"]
        ptype = ProblemType(ptype_str)
        direction = _direction_for(ptype_str)
        evaluator = EvaluatorFactory.get_evaluator(ptype_str)

        for inst_entry in ds["instances"]:
            inst_id = inst_entry["instance_id"]
            n_vars = inst_entry["qubo_variables"]
            inst_data = inst_entry["instance_data"]
            print(f"Benchmarking {inst_id} ({ptype_str}, n={n_vars})...")

            # 1. Exact Solver (deterministic baseline)
            exact_solver = ClassicalSolverFactory.get_solver("exact")
            t0 = time.perf_counter()
            exact_res = exact_solver.solve(problem_type=ptype, instance=inst_data, seed=42)
            exact_rt = time.perf_counter() - t0
            exact_eval = evaluator.evaluate(inst_data, exact_res.candidate_solution)
            exact_opt = float(exact_eval.objective_value)

            trial_records.append({
                "family_key": family_key,
                "instance_id": inst_id,
                "problem_type": ptype_str,
                "qubo_variables": n_vars,
                "solver": "exact",
                "trial": 0,
                "seed": 42,
                "objective": exact_opt,
                "is_feasible": exact_eval.is_feasible,
                "optimality_gap_pct": 0.0,
                "approximation_ratio": 1.0,
                "runtime_seconds": round(exact_rt, 4),
                "evaluations": getattr(exact_res, "evaluations", None),
                "simulation_target": "host_cpu",
            })

            # 2. Classical Heuristics (SA, GA)
            sa_cfg = SolverConfiguration(max_iterations=250, time_limit_seconds=30.0)
            ga_cfg = SolverConfiguration(max_iterations=80, time_limit_seconds=30.0)

            for solver_name, cfg in [("simulated_annealing", sa_cfg), ("genetic_algorithm", ga_cfg)]:
                solver = ClassicalSolverFactory.get_solver(solver_name)
                for k, seed in enumerate(TRIAL_SEEDS):
                    t0 = time.perf_counter()
                    res = solver.solve(problem_type=ptype, instance=inst_data, config=cfg, seed=seed)
                    rt = time.perf_counter() - t0
                    indep = evaluator.evaluate(inst_data, res.candidate_solution)
                    obj = float(indep.objective_value)
                    gap = optimality_gap(obj, exact_opt) if exact_opt != 0 else 0.0
                    ratio = approximation_ratio(obj, exact_opt, direction)
                    trial_records.append({
                        "family_key": family_key,
                        "instance_id": inst_id,
                        "problem_type": ptype_str,
                        "qubo_variables": n_vars,
                        "solver": solver_name,
                        "trial": k,
                        "seed": seed,
                        "objective": obj,
                        "is_feasible": indep.is_feasible,
                        "optimality_gap_pct": round(gap, 4) if gap == gap else None,
                        "approximation_ratio": round(ratio, 4) if ratio == ratio else None,
                        "runtime_seconds": round(rt, 4),
                        "evaluations": getattr(res, "iterations_completed", None),
                        "simulation_target": "host_cpu",
                    })

            # 3. Quantum Simulation (Standard QAOA & Adaptive QAOA) for n <= 10 qubits
            if n_vars <= 10:
                for k, seed in enumerate(TRIAL_SEEDS):
                    # Standard QAOA (p=1, shots=512, COBYLA, max_evaluations=40)
                    q_req = QAOAExecutionRequest(
                        problem_type=ptype,
                        instance=inst_data,
                        config=QAOAConfiguration(
                            p_depth=1,
                            shots=512,
                            optimizer=ClassicalOptimizerType.COBYLA,
                            max_evaluations=40,
                            seed=seed,
                        ),
                    )
                    t0 = time.perf_counter()
                    q_res = await QAOAExecutionPipeline.execute_sync(q_req)
                    q_rt = time.perf_counter() - t0
                    if q_res.candidate_solution is not None:
                        indep_q = evaluator.evaluate(inst_data, q_res.candidate_solution)
                        q_obj = float(indep_q.objective_value)
                        q_feas = indep_q.is_feasible
                    else:
                        q_obj = float("nan")
                        q_feas = False
                    q_gap = optimality_gap(q_obj, exact_opt) if (q_feas and exact_opt != 0) else None
                    q_ratio = approximation_ratio(q_obj, exact_opt, direction) if q_feas else None
                    trial_records.append({
                        "family_key": family_key,
                        "instance_id": inst_id,
                        "problem_type": ptype_str,
                        "qubo_variables": n_vars,
                        "solver": "standard_qaoa",
                        "trial": k,
                        "seed": seed,
                        "objective": q_obj if q_obj == q_obj else None,
                        "is_feasible": q_feas,
                        "optimality_gap_pct": round(q_gap, 4) if q_gap is not None and q_gap == q_gap else None,
                        "approximation_ratio": round(q_ratio, 4) if q_ratio is not None and q_ratio == q_ratio else None,
                        "runtime_seconds": round(q_rt, 4),
                        "evaluations": q_res.optimization_result.total_evaluations if q_res.optimization_result else None,
                        "simulation_target": "qiskit_aer_simulator",
                    })

                    # Adaptive QAOA (p=1..2, shots=512, COBYLA -> Nelder-Mead, max_evaluations=50)
                    aq_req = AdaptiveQAOARequest(
                        problem_id=inst_id,
                        problem_type=ptype,
                        instance=inst_data,
                        config=AdaptiveQAOAConfiguration(
                            p_depth=1,
                            shots=512,
                            optimizer=ClassicalOptimizerType.COBYLA,
                            max_evaluations=50,
                            seed=seed,
                            strategy_config=AdaptiveStrategyConfiguration(
                                strategy_type=AdaptiveStrategyType.FULL_ADAPTIVE,
                                initialization_strategy=InitializationStrategyType.LINEAR_RAMP,
                                depth_growth=DepthGrowthStrategy.IMPROVEMENT_TRIGGERED,
                                optimizer_schedule=OptimizerScheduleType.ADAPTIVE_FALLBACK,
                                primary_optimizer=ClassicalOptimizerType.COBYLA,
                                fallback_optimizer=ClassicalOptimizerType.NELDER_MEAD,
                                initial_depth=1,
                                max_depth=2,
                                max_evaluations_total=50,
                            ),
                        ),
                    )
                    t0 = time.perf_counter()
                    aq_res = AdaptiveQAOAExecutionPipeline.execute_sync(aq_req)
                    aq_rt = time.perf_counter() - t0
                    aq_obj = float(aq_res.objective_value)
                    aq_feas = bool(aq_res.is_feasible)
                    aq_gap = optimality_gap(aq_obj, exact_opt) if (aq_feas and exact_opt != 0) else None
                    aq_ratio = approximation_ratio(aq_obj, exact_opt, direction) if aq_feas else None
                    trial_records.append({
                        "family_key": family_key,
                        "instance_id": inst_id,
                        "problem_type": ptype_str,
                        "qubo_variables": n_vars,
                        "solver": "adaptive_qaoa",
                        "trial": k,
                        "seed": seed,
                        "objective": aq_obj if aq_obj == aq_obj else None,
                        "is_feasible": aq_feas,
                        "optimality_gap_pct": round(aq_gap, 4) if aq_gap is not None and aq_gap == aq_gap else None,
                        "approximation_ratio": round(aq_ratio, 4) if aq_ratio is not None and aq_ratio == aq_ratio else None,
                        "runtime_seconds": round(aq_rt, 4),
                        "evaluations": aq_res.total_evaluations,
                        "final_depth": aq_res.final_depth,
                        "simulation_target": "qiskit_aer_simulator",
                    })

            # 4. AI-Assisted Solver Recommendation (evaluated separately)
            t0 = time.perf_counter()
            rec = await recommender.recommend_solver(
                problem_type=ptype,
                instance_data=inst_data,
                problem_id=inst_id,
            )
            rec_latency_ms = (time.perf_counter() - t0) * 1000.0
            recommender_records.append({
                "instance_id": inst_id,
                "family_key": family_key,
                "problem_type": ptype_str,
                "qubo_variables": n_vars,
                "recommended_solver": rec.recommended_solver,
                "confidence_score": round(rec.confidence_score, 4),
                "source": rec.recommendation_source.value,
                "is_ood": rec.is_out_of_distribution,
                "latency_ms": round(rec_latency_ms, 3),
                "exact_optimum": exact_opt,
            })

    # Aggregate summary by (problem_type, solver) and (family_key, solver)
    summary_by_family: List[Dict[str, Any]] = []
    families = sorted({r["family_key"] for r in trial_records})
    solvers = ["exact", "simulated_annealing", "genetic_algorithm", "standard_qaoa", "adaptive_qaoa"]

    for fam in families:
        for sol in solvers:
            subset = [r for r in trial_records if r["family_key"] == fam and r["solver"] == sol]
            if not subset:
                continue
            feas = [r for r in subset if r["is_feasible"] and r["objective"] is not None]
            objs = [r["objective"] for r in feas]
            gaps = [r["optimality_gap_pct"] for r in feas if r["optimality_gap_pct"] is not None]
            ratios = [r["approximation_ratio"] for r in feas if r["approximation_ratio"] is not None]
            rts = [r["runtime_seconds"] for r in subset]
            ptype = subset[0]["problem_type"]

            best_obj: Optional[float] = None
            if objs:
                best_obj = max(objs) if ptype == "max_cut" else min(objs)

            summary_by_family.append({
                "family_key": fam,
                "problem_type": ptype,
                "solver": sol,
                "total_trials": len(subset),
                "feasible_trials": len(feas),
                "feasibility_rate": round(len(feas) / len(subset), 4),
                "best_objective": round(best_obj, 4) if best_obj is not None else None,
                "mean_objective": round(_mean(objs), 4) if objs else None,
                "median_objective": round(_median(objs), 4) if objs else None,
                "std_objective": round(_std(objs), 4) if len(objs) >= 2 else 0.0,
                "mean_gap_pct": round(_mean(gaps), 4) if gaps else None,
                "mean_approx_ratio": round(_mean(ratios), 4) if ratios else None,
                "mean_runtime_s": round(_mean(rts), 4),
            })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "simulation_disclosure": "All QAOA and Adaptive QAOA executions ran on classical Qiskit AerSimulator.",
        "total_trial_records": len(trial_records),
        "summary_by_family": summary_by_family,
        "recommender_evaluation": recommender_records,
        "trial_records": trial_records,
    }

    out_path = REPO_ROOT / "research" / "results" / "classical_vs_quantum_benchmark.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Completed {len(trial_records)} benchmark trials across {len(families)} families -> {out_path}")


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
