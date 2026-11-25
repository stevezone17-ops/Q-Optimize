"""Stage 10.1 — Final Scientific Validation of Optimization Models.

Validates Max-Cut, Linear Assignment, and TSP across:
1. Canonical schema & independent domain evaluators
2. QUBO formulation & upper-triangular convention
3. Ising Hamiltonian conversion & exact energy equivalence
4. Exhaustive 2^n state-space truth-table verification (FormulationVerifier)
5. Edge cases (zero objectives, negative objectives, degenerate optima,
   disconnected graphs, invalid matrices, infeasible states)
6. End-to-end Classical (Exact, SA, GA) and Quantum Simulation (QAOA on AerSimulator)
   solution decoding and independent evaluation parity.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.domain.problems.models import ProblemType
from backend.app.evaluation.evaluator_factory import EvaluatorFactory
from backend.app.formulations.engine import FormulationEngine
from backend.app.formulations.verification import FormulationVerifier
from backend.app.solvers.classical.factory import ClassicalSolverFactory
from backend.app.solvers.classical.models import SolverRequest
from backend.app.solvers.quantum.models import (
    ClassicalOptimizerType,
    QAOAConfiguration,
    QAOAExecutionRequest,
)
from backend.app.solvers.quantum.pipeline import QAOAExecutionPipeline


def validate_exhaustive_suite() -> List[Dict[str, Any]]:
    """Run exhaustive 2^n state-space verification across standard & edge-case instances."""
    engine = FormulationEngine()
    cases: List[Dict[str, Any]] = [
        {
            "id": "maxcut_k4_unweighted",
            "problem_type": "max_cut",
            "description": "Complete graph K4 (unit weights)",
            "instance": {
                "nodes": ["A", "B", "C", "D"],
                "edges": [
                    ["A", "B", 1.0], ["A", "C", 1.0], ["A", "D", 1.0],
                    ["B", "C", 1.0], ["B", "D", 1.0], ["C", "D", 1.0],
                ],
            },
        },
        {
            "id": "maxcut_weighted_5node",
            "problem_type": "max_cut",
            "description": "Weighted 5-node graph",
            "instance": {
                "nodes": ["n0", "n1", "n2", "n3", "n4"],
                "edges": [
                    ["n0", "n1", 2.5], ["n1", "n2", 1.5], ["n2", "n3", 3.0],
                    ["n3", "n4", 4.0], ["n4", "n0", 1.0], ["n0", "n2", 2.0],
                ],
            },
        },
        {
            "id": "maxcut_zero_weights",
            "problem_type": "max_cut",
            "description": "Edge case: All-zero edge weights (zero objective)",
            "instance": {
                "nodes": ["A", "B", "C"],
                "edges": [["A", "B", 0.0], ["B", "C", 0.0], ["A", "C", 0.0]],
            },
        },
        {
            "id": "maxcut_negative_weights",
            "problem_type": "max_cut",
            "description": "Edge case: Mixed positive & negative edge weights",
            "instance": {
                "nodes": ["A", "B", "C", "D"],
                "edges": [
                    ["A", "B", -2.0], ["B", "C", 3.5], ["C", "D", -1.5], ["D", "A", 4.0],
                ],
            },
        },
        {
            "id": "maxcut_disconnected",
            "problem_type": "max_cut",
            "description": "Edge case: Disconnected graph (2 components)",
            "instance": {
                "nodes": ["A", "B", "C", "D"],
                "edges": [["A", "B", 2.0], ["C", "D", 3.0]],
            },
        },
        {
            "id": "assignment_2x2_standard",
            "problem_type": "assignment",
            "description": "Standard 2x2 Linear Assignment (4 binary vars)",
            "instance": {
                "agents": ["W1", "W2"],
                "tasks": ["T1", "T2"],
                "cost_matrix": [[4.0, 2.0], [3.0, 5.0]],
            },
        },
        {
            "id": "assignment_3x3_standard",
            "problem_type": "assignment",
            "description": "Standard 3x3 Linear Assignment (9 binary vars, 512 states)",
            "instance": {
                "agents": ["W1", "W2", "W3"],
                "tasks": ["T1", "T2", "T3"],
                "cost_matrix": [[9.0, 2.0, 7.0], [6.0, 4.0, 3.0], [5.0, 8.0, 1.0]],
            },
        },
        {
            "id": "assignment_3x3_zero_cost",
            "problem_type": "assignment",
            "description": "Edge case: 3x3 zero-cost matrix (degenerate optimal)",
            "instance": {
                "agents": ["W1", "W2", "W3"],
                "tasks": ["T1", "T2", "T3"],
                "cost_matrix": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            },
        },
        {
            "id": "assignment_2x2_negative_cost",
            "problem_type": "assignment",
            "description": "Edge case: 2x2 negative cost matrix",
            "instance": {
                "agents": ["W1", "W2"],
                "tasks": ["T1", "T2"],
                "cost_matrix": [[-5.0, -1.0], [-2.0, -8.0]],
            },
        },
        {
            "id": "tsp_3city_symmetric",
            "problem_type": "tsp",
            "description": "3-city symmetric TSP (9 binary vars, 512 states)",
            "instance": {
                "cities": ["C0", "C1", "C2"],
                "distance_matrix": [
                    [0.0, 10.0, 15.0],
                    [10.0, 0.0, 20.0],
                    [15.0, 20.0, 0.0],
                ],
                "symmetric": True,
            },
        },
        {
            "id": "tsp_3city_asymmetric",
            "problem_type": "tsp",
            "description": "3-city asymmetric TSP (9 binary vars, 512 states)",
            "instance": {
                "cities": ["C0", "C1", "C2"],
                "distance_matrix": [
                    [0.0, 5.0, 20.0],
                    [12.0, 0.0, 8.0],
                    [7.0, 14.0, 0.0],
                ],
                "symmetric": False,
            },
        },
    ]

    results: List[Dict[str, Any]] = []
    for case in cases:
        t0 = time.perf_counter()
        qubo = engine.generate_qubo(case["problem_type"], case["instance"])
        ising = engine.qubo_to_ising(qubo)
        ver = FormulationVerifier.verify(
            problem_type=case["problem_type"],
            instance_data=case["instance"],
            qubo=qubo,
            ising=ising,
            max_states=4096,
            tolerance=1e-6,
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Verify upper-triangular QUBO invariant (i < j in variable_order)
        idx_map = {v: i for i, v in enumerate(qubo.variable_order)}
        upper_tri_valid = True
        for k in qubo.quadratic_terms.keys():
            v1, v2 = k.split(",", 1)
            if idx_map[v1] >= idx_map[v2]:
                upper_tri_valid = False
                break

        results.append({
            "id": case["id"],
            "problem_type": case["problem_type"],
            "description": case["description"],
            "num_variables": len(qubo.variable_order),
            "num_states_tested": ver.num_states_tested,
            "feasible_states_count": ver.feasible_states_count,
            "is_verified": ver.is_verified,
            "max_energy_discrepancy": ver.max_energy_discrepancy,
            "min_qubo_energy": ver.min_qubo_energy,
            "min_ising_energy": ver.min_ising_energy,
            "optimal_bitstring": ver.optimal_bitstring,
            "upper_triangular_valid": upper_tri_valid,
            "passed": ver.is_verified and upper_tri_valid,
            "feasibility_summary": ver.feasibility_summary,
            "elapsed_ms": elapsed_ms,
        })
    return results


def validate_negative_and_infeasible_edge_cases() -> List[Dict[str, Any]]:
    """Test invalid matrices and infeasible solutions explicitly."""
    engine = FormulationEngine()
    edge_results: List[Dict[str, Any]] = []

    # 1. Invalid non-square assignment matrix
    try:
        engine.generate_qubo(
            "assignment",
            {
                "agents": ["W1", "W2"],
                "tasks": ["T1", "T2", "T3"],
                "cost_matrix": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            },
        )
        edge_results.append({"case": "invalid_nonsquare_assignment", "passed": False, "detail": "Did not raise ValueError"})
    except ValueError as exc:
        edge_results.append({"case": "invalid_nonsquare_assignment", "passed": True, "detail": str(exc)})

    # 2. Infeasible assignment evaluation
    assign_eval = EvaluatorFactory.get_evaluator("assignment")
    infeasible_assign = assign_eval.evaluate(
        {
            "agents": ["W1", "W2"],
            "tasks": ["T1", "T2"],
            "cost_matrix": [[4.0, 2.0], [3.0, 5.0]],
        },
        [("W1", "T1"), ("W2", "T1")],  # Both assigned to T1
    )
    edge_results.append({
        "case": "infeasible_assignment_duplicate_task",
        "passed": not infeasible_assign.is_feasible and len(infeasible_assign.violations) > 0,
        "is_feasible": infeasible_assign.is_feasible,
        "violations": [v.model_dump() for v in infeasible_assign.violations],
    })

    # 3. Infeasible TSP tour evaluation (duplicate city)
    tsp_eval = EvaluatorFactory.get_evaluator("tsp")
    infeasible_tsp = tsp_eval.evaluate(
        {
            "cities": ["C0", "C1", "C2"],
            "distance_matrix": [[0.0, 10.0, 15.0], [10.0, 0.0, 20.0], [15.0, 20.0, 0.0]],
        },
        ["C0", "C1", "C0"],
    )
    edge_results.append({
        "case": "infeasible_tsp_duplicate_city",
        "passed": not infeasible_tsp.is_feasible and len(infeasible_tsp.violations) > 0,
        "is_feasible": infeasible_tsp.is_feasible,
        "violations": [v.model_dump() for v in infeasible_tsp.violations],
    })

    return edge_results


async def validate_end_to_end_solver_parity() -> List[Dict[str, Any]]:
    """Verify Exact, SA, GA, and QAOA solutions match independent domain evaluators."""
    test_instances = [
        {
            "id": "maxcut_4node",
            "problem_type": ProblemType.MAX_CUT,
            "instance": {
                "nodes": ["A", "B", "C", "D"],
                "edges": [["A", "B", 2.0], ["B", "C", 3.0], ["C", "D", 1.0], ["D", "A", 4.0], ["A", "C", 1.5]],
            },
        },
        {
            "id": "assignment_3x3",
            "problem_type": ProblemType.ASSIGNMENT,
            "instance": {
                "agents": ["W1", "W2", "W3"],
                "tasks": ["T1", "T2", "T3"],
                "cost_matrix": [[9.0, 2.0, 7.0], [6.0, 4.0, 3.0], [5.0, 8.0, 1.0]],
            },
        },
        {
            "id": "tsp_3city",
            "problem_type": ProblemType.TSP,
            "instance": {
                "cities": ["C0", "C1", "C2"],
                "distance_matrix": [[0.0, 10.0, 15.0], [10.0, 0.0, 20.0], [15.0, 20.0, 0.0]],
                "symmetric": True,
            },
        },
    ]

    parity_results: List[Dict[str, Any]] = []
    for item in test_instances:
        ptype = item["problem_type"]
        inst = item["instance"]
        evaluator = EvaluatorFactory.get_evaluator(ptype.value)

        # Classical solvers
        for solver_name in ["exact", "simulated_annealing", "genetic_algorithm"]:
            solver = ClassicalSolverFactory.get_solver(solver_name)
            res = solver.solve(
                problem_type=ptype,
                instance=inst,
                seed=42,
            )
            indep = evaluator.evaluate(inst, res.candidate_solution)
            parity_ok = (
                res.is_feasible == indep.is_feasible
                and abs((res.objective_value or 0.0) - (indep.objective_value or 0.0)) < 1e-6
            )
            parity_results.append({
                "instance_id": item["id"],
                "solver": solver_name,
                "reported_objective": res.objective_value,
                "independent_objective": indep.objective_value,
                "is_feasible": res.is_feasible,
                "parity_verified": parity_ok,
            })

        # QAOA on AerSimulator
        qaoa_req = QAOAExecutionRequest(
            problem_type=ptype,
            instance=inst,
            config=QAOAConfiguration(
                p_depth=1,
                shots=512,
                optimizer=ClassicalOptimizerType.COBYLA,
                max_evaluations=30,
                seed=42,
            ),
        )
        qres = await QAOAExecutionPipeline.execute_sync(qaoa_req)
        if qres.candidate_solution is not None:
            indep_q = evaluator.evaluate(inst, qres.candidate_solution)
            q_parity_ok = (
                qres.is_feasible == indep_q.is_feasible
                and abs((qres.objective_value or 0.0) - (indep_q.objective_value or 0.0)) < 1e-6
            )
        else:
            q_parity_ok = False
            indep_q = None
        parity_results.append({
            "instance_id": item["id"],
            "solver": "qaoa_aer_p1",
            "reported_objective": qres.objective_value,
            "independent_objective": indep_q.objective_value if indep_q else None,
            "is_feasible": qres.is_feasible,
            "qubo_energy": qres.qubo_energy,
            "ising_energy": qres.ising_energy,
            "parity_verified": q_parity_ok,
        })

    return parity_results


async def main() -> None:
    print("Running Stage 10.1 Scientific Validation Suite...")
    exhaustive = validate_exhaustive_suite()
    edge_cases = validate_negative_and_infeasible_edge_cases()
    parity = await validate_end_to_end_solver_parity()

    all_passed = (
        all(r["passed"] for r in exhaustive)
        and all(e["passed"] for e in edge_cases)
        and all(p["parity_verified"] for p in parity)
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "all_passed": all_passed,
        "exhaustive_verification": exhaustive,
        "negative_and_infeasible_edge_cases": edge_cases,
        "end_to_end_solver_parity": parity,
    }

    out_path = REPO_ROOT / "research" / "results" / "scientific_validation_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Exhaustive cases passed: {sum(r['passed'] for r in exhaustive)}/{len(exhaustive)}")
    print(f"Edge cases passed: {sum(e['passed'] for e in edge_cases)}/{len(edge_cases)}")
    print(f"Solver parity cases passed: {sum(p['parity_verified'] for p in parity)}/{len(parity)}")
    print(f"Saved results to: {out_path}")
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
