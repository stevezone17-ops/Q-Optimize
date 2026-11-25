"""Stage 10.4 — Adaptive QAOA Research & Ablation Study Script.

Executes all 6 ablation variants supported by AdaptiveBenchmarkEngine across
representative Max-Cut, Assignment, and TSP instances from the Stage 10.2 dataset,
plus a Parameter Transfer compatibility study.

Saves raw outputs to: research/results/adaptive_qaoa_ablation_results.json
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.domain.problems.models import ProblemType
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
from backend.app.solvers.quantum.adaptive.benchmarking import (
    AdaptiveAblationVariant,
    AdaptiveBenchmarkEngine,
    AdaptiveBenchmarkRequest,
)
from backend.app.solvers.quantum.adaptive.pipeline import AdaptiveQAOAExecutionPipeline
from backend.app.solvers.quantum.models import ClassicalOptimizerType


async def run_ablation_and_transfer() -> None:
    ds_path = REPO_ROOT / "research" / "datasets" / "qoptimize_research_datasets.json"
    dataset_payload = json.loads(ds_path.read_text(encoding="utf-8"))

    # Select 5 representative instances covering all 3 problem families
    target_ids = {
        "mc_er_n6_p05_i1",
        "mc_er_n8_p05_w_i1",
        "mc_reg_n8_d3_i1",
        "assign_3x3_uniform_i1",
        "tsp_3city_euclid_i1",
    }

    selected: List[Dict[str, Any]] = []
    for ds in dataset_payload["datasets"]:
        for inst in ds["instances"]:
            if inst["instance_id"] in target_ids:
                selected.append({
                    "instance_id": inst["instance_id"],
                    "family_key": ds["family_key"],
                    "problem_type": ds["problem_type"],
                    "qubo_variables": inst["qubo_variables"],
                    "instance_data": inst["instance_data"],
                })

    ablation_studies: List[Dict[str, Any]] = []
    for item in selected:
        print(f"Running 6-variant ablation on {item['instance_id']} ({item['problem_type']}, n={item['qubo_variables']})...")
        req = AdaptiveBenchmarkRequest(
            name=f"Ablation_{item['instance_id']}",
            problem_type=ProblemType(item["problem_type"]),
            instance=item["instance_data"],
            include_variants=[
                AdaptiveAblationVariant.STANDARD_BASELINE,
                AdaptiveAblationVariant.FULL_ADAPTIVE,
                AdaptiveAblationVariant.ABLATION_NO_WARM_START,
                AdaptiveAblationVariant.ABLATION_NO_DYNAMIC_DEPTH,
                AdaptiveAblationVariant.ABLATION_NO_OPTIMIZER_SWITCHING,
                AdaptiveAblationVariant.ABLATION_FOURIER,
            ],
            initial_depth=1,
            max_depth=2,
            shots=512,
            primary_optimizer=ClassicalOptimizerType.COBYLA,
            fallback_optimizer=ClassicalOptimizerType.NELDER_MEAD,
            max_evaluations_total=50,
            trials=3,
            base_seed=42,
        )
        res = await AdaptiveBenchmarkEngine.run_benchmark(req)
        ablation_studies.append({
            "instance_id": item["instance_id"],
            "family_key": item["family_key"],
            "problem_type": item["problem_type"],
            "qubo_variables": item["qubo_variables"],
            "exact_optimum": res.exact_optimum,
            "ablation_insights": res.ablation_insights,
            "total_runtime_seconds": res.total_runtime_seconds,
            "variants": [v.model_dump() for v in res.summaries],
        })

    # Parameter Transfer Experiment:
    # Train on mc_er_n6_p05_i1 (p=1), transfer angles to mc_er_n6_p05_i2 (same family) vs cold start
    mc_instances = [
        inst for ds in dataset_payload["datasets"] if ds["family_key"] == "mc_er_n6_p05"
        for inst in ds["instances"]
    ]
    src_inst = mc_instances[0]
    tgt_inst = mc_instances[1]

    print("Running Parameter Transfer experiment (mc_er_n6_p05_i1 -> mc_er_n6_p05_i2)...")
    src_req = AdaptiveQAOARequest(
        problem_id=src_inst["instance_id"],
        problem_type=ProblemType.MAX_CUT,
        instance=src_inst["instance_data"],
        config=AdaptiveQAOAConfiguration(
            p_depth=1,
            shots=512,
            optimizer=ClassicalOptimizerType.COBYLA,
            max_evaluations=40,
            seed=42,
            strategy_config=AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.STANDARD,
                initial_depth=1,
                max_depth=1,
                max_evaluations_total=40,
            ),
        ),
    )
    src_res = AdaptiveQAOAExecutionPipeline.execute_sync(src_req)

    # Target cold start
    cold_req = AdaptiveQAOARequest(
        problem_id=tgt_inst["instance_id"],
        problem_type=ProblemType.MAX_CUT,
        instance=tgt_inst["instance_data"],
        config=AdaptiveQAOAConfiguration(
            p_depth=1,
            shots=512,
            optimizer=ClassicalOptimizerType.COBYLA,
            max_evaluations=30,
            seed=42,
            strategy_config=AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.STANDARD,
                initial_depth=1,
                max_depth=1,
                max_evaluations_total=30,
            ),
        ),
    )
    cold_res = AdaptiveQAOAExecutionPipeline.execute_sync(cold_req)

    # Target warm-started with source angles
    warm_req = AdaptiveQAOARequest(
        problem_id=tgt_inst["instance_id"],
        problem_type=ProblemType.MAX_CUT,
        instance=tgt_inst["instance_data"],
        config=AdaptiveQAOAConfiguration(
            p_depth=1,
            shots=512,
            optimizer=ClassicalOptimizerType.COBYLA,
            max_evaluations=30,
            seed=42,
            strategy_config=AdaptiveStrategyConfiguration(
                strategy_type=AdaptiveStrategyType.WARM_START,
                initialization_strategy=InitializationStrategyType.WARM_START,
                initial_depth=1,
                max_depth=1,
                max_evaluations_total=30,
                warm_start_parameters={"gamma": src_res.best_gamma, "beta": src_res.best_beta},
            ),
        ),
    )
    warm_res = AdaptiveQAOAExecutionPipeline.execute_sync(warm_req)

    transfer_study = {
        "source_instance": src_inst["instance_id"],
        "target_instance": tgt_inst["instance_id"],
        "source_gamma": src_res.best_gamma,
        "source_beta": src_res.best_beta,
        "cold_start": {
            "objective_value": cold_res.objective_value,
            "exact_optimal": cold_res.exact_optimal_value,
            "approximation_ratio": cold_res.approximation_ratio,
            "total_evaluations": cold_res.total_evaluations,
            "runtime_ms": cold_res.execution_time_ms,
        },
        "warm_start_transfer": {
            "objective_value": warm_res.objective_value,
            "exact_optimal": warm_res.exact_optimal_value,
            "approximation_ratio": warm_res.approximation_ratio,
            "total_evaluations": warm_res.total_evaluations,
            "runtime_ms": warm_res.execution_time_ms,
        },
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "simulation_disclosure": "Executed on classical Qiskit AerSimulator.",
        "ablation_studies": ablation_studies,
        "parameter_transfer_study": transfer_study,
    }

    out_path = REPO_ROOT / "research" / "results" / "adaptive_qaoa_ablation_results.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved Stage 10.4 ablation & transfer results -> {out_path}")


if __name__ == "__main__":
    asyncio.run(run_ablation_and_transfer())
