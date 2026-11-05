"""FastAPI REST endpoints for QAOA Quantum Optimization Engine."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.solvers.quantum.pipeline import QAOAExecutionPipeline
from backend.app.solvers.quantum.backend_manager import QuantumBackendManager
from backend.app.solvers.quantum.benchmarking import (
    HybridBenchmarkEngine,
    HybridBenchmarkRequest,
    HybridBenchmarkResult,
)
from backend.app.solvers.quantum.models import (
    QuantumBackendInfo,
    QAOAExecutionRequest,
    QAOAExecutionResult,
    QAOAExecutionRecord,
    QAOAStatusResponse,
    QAOAConfiguration,
)
from backend.app.solvers.quantum.exceptions import (
    QuantumSolverError,
    QubitLimitExceededError,
    ShotLimitExceededError,
    BackendNotAvailableError,
)

router = APIRouter()
backend_manager = QuantumBackendManager()


@router.get("", response_model=Dict[str, Any])
async def list_quantum_solvers():
    """Discover available quantum solvers, algorithms, and simulation backends."""
    backends = backend_manager.list_available_backends()
    return {
        "solvers": [
            {
                "solver_id": "qaoa",
                "name": "Quantum Approximate Optimization Algorithm (QAOA)",
                "description": "Variational hybrid quantum-classical optimization algorithm using parameterized cost and mixer unitary layers.",
                "stage_introduced": "Phase 5",
                "is_implemented": True,
                "supported_problems": ["max_cut", "assignment", "tsp"],
                "default_p_depth": 1,
                "default_shots": 1024,
            }
        ],
        "backends": backends,
        "hardware_transparency_note": (
            "All executions run on classical CPU quantum circuit simulation via Qiskit Aer. "
            "No physical quantum hardware speedup is claimed."
        ),
    }


@router.get("/backends", response_model=List[QuantumBackendInfo])
async def list_quantum_backends():
    """List available quantum simulation backends and their hardware transparency specifications."""
    return backend_manager.list_available_backends()


@router.get("/qaoa", response_model=Dict[str, Any])
async def get_qaoa_solver_metadata():
    """Retrieve detailed descriptor, mathematical formulation, and parameter schemas for QAOA."""
    return {
        "solver_id": "qaoa",
        "name": "Quantum Approximate Optimization Algorithm (QAOA)",
        "mathematical_ansatz": "|psi(gamma, beta)> = U_M(beta_p) U_C(gamma_p) ... U_M(beta_1) U_C(gamma_1) |+>^n",
        "supported_problems": ["max_cut", "assignment", "tsp"],
        "is_implemented": True,
        "parameter_schema": {
            "p_depth": {"type": "integer", "default": 1, "minimum": 1, "maximum": 10, "description": "Number of QAOA alternating layers (p)"},
            "shots": {"type": "integer", "default": 1024, "minimum": 10, "maximum": 50000, "description": "Measurement sampling shots"},
            "simulation_mode": {"type": "string", "enum": ["ideal_shots", "statevector_exact", "noisy_simulation"], "default": "ideal_shots"},
            "optimizer": {"type": "string", "enum": ["COBYLA", "SLSQP", "Nelder-Mead", "L-BFGS-B"], "default": "COBYLA"},
            "max_iterations": {"type": "integer", "default": 100, "minimum": 1, "maximum": 500},
            "seed": {"type": "integer", "default": 42},
            "init_strategy": {"type": "string", "enum": ["random", "zeros", "linear_ramp", "custom"], "default": "random"},
            "noise_model_enabled": {"type": "boolean", "default": False},
            "time_limit_seconds": {"type": "number", "default": 60.0},
        },
    }


@router.post("/validate", response_model=Dict[str, Any])
async def validate_quantum_request(req: QAOAExecutionRequest):
    """Pre-validate problem dimensions, QUBO feasibility, and quantum resource limits before execution."""
    try:
        problem_type, instance = await QAOAExecutionPipeline._resolve_problem(req)
        qubo = QAOAExecutionPipeline._build_qubo(problem_type, instance, req.penalty_coefficients)
        num_qubits = len(qubo.variable_order)
        backend_manager.validate_resource_requirements(num_qubits, req.config.shots, req.config.simulation_mode)

        return {
            "is_valid": True,
            "problem_type": problem_type.value,
            "num_qubits": num_qubits,
            "p_depth": req.config.p_depth,
            "parameters_count": 2 * req.config.p_depth,
            "simulation_mode": req.config.simulation_mode.value,
            "resource_check": "PASSED",
        }
    except (QubitLimitExceededError, ShotLimitExceededError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Validation failed: {str(exc)}")


# ==================== QAOA EXECUTION ENDPOINTS ====================

@router.post("/qaoa/execute", response_model=QAOAExecutionResult)
async def execute_qaoa_synchronous(req: QAOAExecutionRequest):
    """Execute QAOA synchronously on a worker thread and await full optimization and sampling results."""
    try:
        return await QAOAExecutionPipeline.execute_sync(req)
    except (QubitLimitExceededError, ShotLimitExceededError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"QAOA execution failed: {str(exc)}")


@router.post("/qaoa/execute/async", response_model=QAOAStatusResponse)
async def execute_qaoa_asynchronous(req: QAOAExecutionRequest):
    """Dispatch QAOA execution to the background thread-pool queue and return immediately."""
    try:
        return await QAOAExecutionPipeline.dispatch_async(req)
    except (QubitLimitExceededError, ShotLimitExceededError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to dispatch QAOA task: {str(exc)}")


@router.get("/qaoa/executions", response_model=List[QAOAExecutionRecord])
async def list_qaoa_executions(limit: int = Query(25, ge=1, le=100)):
    """Retrieve recent QAOA simulation execution records."""
    return await QAOAExecutionPipeline.list_executions(limit=limit)


@router.get("/qaoa/executions/{execution_id}", response_model=QAOAExecutionRecord)
async def get_qaoa_execution(execution_id: str):
    """Retrieve complete QAOA execution details, optimal angles, and measurement sampling outcomes."""
    record = await QAOAExecutionPipeline.get_execution(execution_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quantum execution '{execution_id}' not found.")
    return record


@router.get("/qaoa/executions/{execution_id}/status", response_model=QAOAStatusResponse)
async def poll_qaoa_execution_status(execution_id: str):
    """Lightweight polling endpoint to monitor in-flight QAOA execution progress."""
    status_resp = await QAOAExecutionPipeline.get_status(execution_id)
    if not status_resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quantum execution '{execution_id}' not found.")
    return status_resp


@router.post("/qaoa/executions/{execution_id}/cancel", response_model=QAOAStatusResponse)
async def cancel_qaoa_execution(execution_id: str):
    """Cooperatively terminate an in-flight QAOA execution."""
    status_resp = await QAOAExecutionPipeline.cancel_execution(execution_id)
    if not status_resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quantum execution '{execution_id}' not found.")
    return status_resp


# ---------------------------------------------------------------------------
# Hybrid Quantum-Classical Benchmarking Endpoints (Stage 5.9)
# ---------------------------------------------------------------------------

@router.post("/benchmark", response_model=HybridBenchmarkResult)
async def run_hybrid_benchmark(req: HybridBenchmarkRequest):
    """
    Execute comparative hybrid benchmark comparing QAOA against classical solvers
    (ExactSolver, GeneticAlgorithmSolver, SimulatedAnnealingSolver) on a shared problem instance.
    """
    try:
        return await HybridBenchmarkEngine.run_benchmark(req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid benchmark failed: {str(exc)}",
        )


@router.get("/benchmarks", response_model=List[HybridBenchmarkResult])
async def list_hybrid_benchmarks(limit: int = Query(25, ge=1, le=100)):
    """Retrieve recent hybrid quantum-classical benchmark suites."""
    return await HybridBenchmarkEngine.list_benchmarks(limit=limit)


@router.get("/benchmarks/{benchmark_id}", response_model=HybridBenchmarkResult)
async def get_hybrid_benchmark(benchmark_id: str):
    """Retrieve full comparative results for a specific hybrid benchmark suite."""
    bench = await HybridBenchmarkEngine.get_benchmark(benchmark_id)
    if not bench:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hybrid benchmark '{benchmark_id}' not found.",
        )
    return bench

