# API Specification

## 1. Conventions
Base path: `/api/v1`. All endpoints use standard JSON, strict Pydantic model validation, consistent HTTP status codes, structured error envelopes, and user tenancy checks. Long-running jobs return an experiment ID; clients poll status or receive stream events.

---

## 2. API Endpoints Overview

| Method | Endpoint | Phase | Purpose |
|---|---|---|---|
| `GET` | `/health` | Phase 1 | Health check and database connection status |
| `POST` | `/auth/register` | Phase 1 | User registration (stub/auth ready) |
| `POST` | `/auth/login` | Phase 1 | User sign in |
| `GET` | `/auth/me` | Phase 1 | Current authenticated user |
| `POST` | `/problems` | Phase 2 | Create and validate a canonical optimization problem |
| `GET` | `/problems` | Phase 2 | List registered problems for tenant |
| `GET` | `/problems/types` | Phase 2 | List supported problem families with mathematical specs and constraints |
| `POST` | `/problems/validate` | Phase 2 | Validate ad-hoc problem instance without persistence |
| `POST` | `/problems/evaluate-direct` | Phase 2 | Independently evaluate candidate solution against an ad-hoc problem |
| `GET` | `/problems/{id}` | Phase 2 | Retrieve canonical problem definition by ID |
| `GET` | `/problems/{id}/metadata` | Phase 2 | Retrieve graph statistics, cost metrics, and structural metadata |
| `POST` | `/problems/{id}/validate` | Phase 2 | Validate stored problem against domain rules |
| `POST` | `/problems/{id}/evaluate` | Phase 2 | Independently evaluate candidate solution against stored problem |
| `POST` | `/problems/parse-draft` | Phase 2 | Natural language problem drafting (draft-only, human-confirmed) |
| `POST` | `/formulations/generate` | Phase 3 | Generate canonical QUBO and Ising models for a problem |
| `POST` | `/formulations/qubo` | Phase 3 | Standalone QUBO generation with custom penalty parameters |
| `POST` | `/formulations/ising` | Phase 3 | Direct QUBO-to-Ising conversion from existing QUBO model |
| `POST` | `/formulations/verify` | Phase 3 | Exhaustive truth-table verification ($2^n$ states, $n \le 12$) |
| `GET` | `/formulations/{id}` | Phase 3 | Retrieve stored formulation by ID |
| `GET` | `/formulations/{id}/metadata` | Phase 3 | Retrieve formulation metadata, variable counts, and assumptions |
| `GET` | `/formulations/{id}/export` | Phase 3 | Export formulation in dense, sparse, ising, or full JSON |
| `GET` | `/solvers/classical` | Phase 4 | List registered classical solvers, schemas, and readiness |
| `GET` | `/solvers/classical/{id}` | Phase 4 | Retrieve metadata and configuration schema for specific solver |
| `POST` | `/solvers/classical/validate` | Phase 4 | Validate solver configuration and problem compatibility |
| `POST` | `/solvers/classical/execute` | Phase 4 | Execute solver synchronously or dispatch in background |
| `POST` | `/solvers/classical/execute/async` | Phase 4 | Submit background execution returning tracking record (202) |
| `GET` | `/solvers/classical/executions` | Phase 4 | List recent classical solver executions |
| `GET` | `/solvers/classical/executions/{id}` | Phase 4 | Retrieve full execution record, runtime, and result |
| `GET` | `/solvers/classical/executions/{id}/status` | Phase 4 | Lightweight execution status polling endpoint |
| `POST` | `/solvers/classical/executions/{id}/cancel` | Phase 4 | Cooperatively cancel active or pending execution |
| `POST` | `/solvers/classical/benchmark` | Phase 4 | Execute multi-solver benchmark suite with optimality gap |
| `GET` | `/solvers/classical/benchmarks` | Phase 4 | List recent comparative benchmark results |
| `GET` | `/solvers/classical/benchmarks/{id}` | Phase 4 | Retrieve full multi-solver benchmark comparison by ID |
| `GET` | `/solvers/quantum` | Phase 5 | Discover registered quantum solvers and backends |
| `GET` | `/solvers/quantum/backends` | Phase 5 | List quantum backends with hardware transparency metadata |
| `GET` | `/solvers/quantum/qaoa` | Phase 5 | Retrieve QAOA algorithm metadata and hyperparameter schema |
| `POST` | `/solvers/quantum/validate` | Phase 5 | Pre-flight validation of QAOA requests against qubit and shot limits |
| `POST` | `/solvers/quantum/qaoa/execute` | Phase 5 | Synchronous end-to-end QAOA execution and decoding |
| `POST` | `/solvers/quantum/qaoa/execute/async` | Phase 5 | Asynchronous thread-pooled QAOA execution dispatch |
| `GET` | `/solvers/quantum/qaoa/executions` | Phase 5 | List recent QAOA simulation executions |
| `GET` | `/solvers/quantum/qaoa/executions/{id}` | Phase 5 | Retrieve full QAOA execution results, optimal angles, and histogram |
| `GET` | `/solvers/quantum/qaoa/executions/{id}/status` | Phase 5 | Lightweight polling endpoint for in-flight execution progress |
| `POST` | `/solvers/quantum/qaoa/executions/{id}/cancel` | Phase 5 | Cooperatively cancel pending or running QAOA simulation |
| `POST` | `/solvers/quantum/benchmark` | Phase 5 | Run comparative hybrid quantum-classical benchmark suite |
| `GET` | `/solvers/quantum/benchmarks` | Phase 5 | List recent hybrid quantum-classical benchmark suites |
| `GET` | `/solvers/quantum/benchmarks/{id}` | Phase 5 | Retrieve comparative hybrid benchmark details by ID |
| `POST` | `/experiments` | Phase 6 | Create and enqueue optimization experiment |
| `GET` | `/experiments` | Phase 6 | List own experiments |
| `GET` | `/experiments/{id}` | Phase 6 | Status, configuration, and summary |
| `GET` | `/experiments/{id}/result` | Phase 6 | Completed raw result bitstrings and independently evaluated metrics |
| `POST` | `/experiments/compare` | Phase 7 | Side-by-side solver comparison |
| `POST` | `/reports` | Phase 7 | Request PDF/LaTeX benchmark report |

---

## 3. Phase 3 Formulation Endpoints Detail

### 3.1 Generate Formulation: `POST /api/v1/formulations/generate`
Generates both QUBO and Ising representations for either an existing problem ID or an ad-hoc instance payload.

**Request Payload (stored problem):**
```json
{
  "problem_id": "673f4e2b8109d784a0c841aa",
  "penalty_coefficients": {
    "A": 15.0,
    "B": 15.0
  }
}
```

**Request Payload (ad-hoc instance):**
```json
{
  "problem_type": "max_cut",
  "instance": {
    "nodes": ["A", "B", "C"],
    "edges": [["A", "B", 1.0], ["B", "C", 2.0]]
  }
}
```

**Response Payload (`201 Created`):**
```json
{
  "id": "formulation-673f4e2b8109d784a0c841aa",
  "problem_id": "673f4e2b8109d784a0c841aa",
  "owner_id": "default_user",
  "formulation_type": "qubo",
  "schema_version": "1.0",
  "qubo": {
    "variable_order": ["A", "B", "C"],
    "linear_terms": { "A": -1.0, "B": -3.0, "C": -2.0 },
    "quadratic_terms": { "A,B": 2.0, "B,C": 4.0 },
    "offset": 0.0,
    "matrix": [
      [-1.0, 2.0, 0.0],
      [0.0, -3.0, 4.0],
      [0.0, 0.0, -2.0]
    ],
    "penalties": {},
    "assumptions": ["Minimization QUBO minimizes negative cut"],
    "metadata": { "num_variables": 3, "storage_convention": "upper_triangular" }
  },
  "ising": {
    "variable_order": ["Z_A", "Z_B", "Z_C"],
    "local_fields": { "Z_A": 0.0, "Z_B": 0.0, "Z_C": 0.0 },
    "couplings": { "Z_A,Z_B": 0.5, "Z_B,Z_C": 1.0 },
    "offset": -1.5,
    "spin_mapping": { "A": "Z_A", "B": "Z_B", "C": "Z_C" },
    "latex_expression": "H = -1.5000 + 0.5000 \\, Z_A Z_B + 1.0000 \\, Z_B Z_C",
    "metadata": { "num_spins": 3, "spin_convention": "x_i = (1 - Z_i)/2" }
  },
  "created_at": "2026-11-05T10:30:00Z"
}
```

---

### 3.2 Mathematical Verification: `POST /api/v1/formulations/verify`
Performs exhaustive truth-table evaluation across all $2^n$ binary states ($n \le 12$) to verify exact energy matching $E_{\text{QUBO}}(x) \equiv H_{\text{Ising}}(Z)$ and equivalence to original objective values.

**Request Payload:**
```json
{
  "formulation_id": "formulation-673f4e2b8109d784a0c841aa",
  "tolerance": 1e-6
}
```

**Response Payload (`200 OK`):**
```json
{
  "is_verified": true,
  "num_states_tested": 8,
  "max_energy_discrepancy": 0.0,
  "tolerance": 1e-6,
  "feasible_states_count": 8,
  "min_qubo_energy": -3.0,
  "min_ising_energy": -3.0,
  "optimal_bitstring": "101",
  "feasibility_summary": "Exhaustively verified 8 states. QUBO and Ising energies strictly match to within 1e-06.",
  "discrepancies": [],
  "verified_at": "2026-11-05T10:30:05Z"
}
```

---

### 3.3 Formulation Export: `GET /api/v1/formulations/{id}/export?format={dense|sparse|ising|full}`
Exports the formulation in specified scientific formats.

- `dense`: 2D upper-triangular numerical matrix array.
- `sparse`: Dictionary of linear terms, quadratic terms, and offset.
- `ising`: LaTeX Hamiltonian string and spin mapping table.
- `full`: Complete formulation document including metadata.

---

## 4. Phase 4 Classical Engine Endpoints Detail

### 4.1 Execute Classical Solver: `POST /api/v1/solvers/classical/execute`
Executes an algorithm (Exact, GA, SA) against a stored problem or ad-hoc instance. Supports synchronous execution (default) or background dispatch (`"background": true`).

**Request Payload:**
```json
{
  "solver_id": "genetic_algorithm",
  "problem_type": "max_cut",
  "instance": {
    "nodes": ["A", "B", "C", "D"],
    "edges": [["A", "B", 1.0], ["B", "C", 2.0], ["C", "D", 1.0], ["D", "A", 2.0]]
  },
  "config": {
    "population_size": 100,
    "generations": 200,
    "mutation_rate": 0.05
  },
  "seed": 42,
  "background": false
}
```

**Response Payload (`200 OK` for sync):**
```json
{
  "execution_id": "exec-9f8d7c6b5a4e",
  "solver_id": "genetic_algorithm",
  "solver_name": "Genetic Algorithm (GA)",
  "problem_type": "max_cut",
  "status": "COMPLETED",
  "candidate_solution": { "A": 0, "B": 1, "C": 0, "D": 1 },
  "objective_value": 6.0,
  "is_feasible": true,
  "constraint_violations": [],
  "runtime_seconds": 0.012,
  "iterations": 200,
  "evaluations": 20000,
  "seed": 42,
  "optimality_status": "heuristic_feasible",
  "termination_reason": "max_generations_reached",
  "convergence_history": [
    { "iteration": 0, "best_objective": 4.0, "mean_fitness": 3.2, "timestamp_offset": 0.001 },
    { "iteration": 200, "best_objective": 6.0, "mean_fitness": 5.8, "timestamp_offset": 0.012 }
  ],
  "metadata": { "population_size": 100, "mutation_rate": 0.05 }
}
```

### 4.2 Run Classical Benchmark: `POST /api/v1/solvers/classical/benchmark`
Runs a multi-solver comparative benchmark suite across multiple trials, establishing exact ground truth and computing true optimality gaps.

**Request Payload:**
```json
{
  "name": "Classical Solver Comparison",
  "problem_type": "max_cut",
  "instance": {
    "nodes": ["A", "B", "C", "D"],
    "edges": [["A", "B", 3.0], ["B", "C", 2.0], ["C", "D", 4.0], ["D", "A", 1.0], ["A", "C", 5.0]]
  },
  "solver_ids": ["exact", "genetic_algorithm", "simulated_annealing"],
  "trials": 3,
  "base_seed": 42
}
```

**Response Payload (`200 OK`):**
```json
{
  "benchmark_id": "bench-7c6b5a4e3d2f",
  "name": "Classical Solver Comparison",
  "problem_type": "max_cut",
  "exact_optimum": 14.0,
  "total_runtime_seconds": 0.045,
  "summaries": [
    {
      "solver_id": "exact",
      "solver_name": "Exact Classical Solver",
      "trials_count": 1,
      "best_objective": 14.0,
      "mean_objective": 14.0,
      "worst_objective": 14.0,
      "std_objective": 0.0,
      "feasibility_rate": 1.0,
      "mean_runtime_ms": 1.2,
      "min_runtime_ms": 1.2,
      "max_runtime_ms": 1.2,
      "mean_evaluations": 8.0,
      "optimality_gap_percent": 0.0,
      "best_solution": { "A": 0, "B": 1, "C": 0, "D": 1 }
    },
    {
      "solver_id": "genetic_algorithm",
      "solver_name": "Genetic Algorithm (GA)",
      "trials_count": 3,
      "best_objective": 14.0,
      "mean_objective": 13.67,
      "worst_objective": 13.0,
      "std_objective": 0.47,
      "feasibility_rate": 1.0,
      "mean_runtime_ms": 14.5,
      "min_runtime_ms": 13.2,
      "max_runtime_ms": 15.8,
      "mean_evaluations": 600.0,
      "optimality_gap_percent": 0.0,
      "best_solution": { "A": 0, "B": 1, "C": 0, "D": 1 }
    }
  ],
  "created_at": "2026-11-05T13:30:00Z"
}
```

---

## 5. Phase 5 Quantum Solver Endpoints Detail

### 5.1 Execute QAOA: `POST /api/v1/solvers/quantum/qaoa/execute`
Executes end-to-end QAOA circuit construction, classical parameter optimization, measurement sampling, and solution decoding on Qiskit Aer.

**Request Payload:**
```json
{
  "problem_type": "max_cut",
  "instance": {
    "nodes": ["A", "B", "C"],
    "edges": [["A", "B", 2.0], ["B", "C", 3.0], ["A", "C", 1.0]]
  },
  "config": {
    "p_depth": 1,
    "shots": 1024,
    "simulation_mode": "ideal_shots",
    "optimizer": "COBYLA",
    "max_iterations": 30,
    "init_strategy": "linear_ramp",
    "seed": 42
  }
}
```

**Response Payload (200 OK):**
```json
{
  "execution_id": "qexec-7b3f1c29e4d0",
  "solver_id": "qaoa",
  "solver_name": "Quantum Approximate Optimization Algorithm (QAOA)",
  "problem_type": "max_cut",
  "status": "COMPLETED",
  "optimal_gamma": [0.3927],
  "optimal_beta": [0.7854],
  "optimal_expectation_value": -3.5,
  "best_sample": {
    "bitstring": "101",
    "count": 420,
    "probability": 0.41,
    "raw_binary_vector": [1, 0, 1],
    "decoded_solution": { "partition_s": ["A", "C"], "partition_v_minus_s": ["B"], "cut_value": 5.0 },
    "objective_value": 5.0,
    "is_feasible": true,
    "constraint_violations": [],
    "is_best_feasible": true,
    "is_most_frequent": true
  },
  "decoding_summary": {
    "total_samples": 1024,
    "unique_samples": 8,
    "feasible_samples": 1024,
    "infeasible_samples": 0,
    "feasible_rate": 1.0,
    "all_decoded_samples": [...]
  },
  "circuit_metadata": {
    "num_qubits": 3,
    "depth": 8,
    "gate_counts": { "h": 3, "rz": 3, "rzz": 3, "rx": 3 },
    "num_parameters": 2,
    "p_depth": 1,
    "has_measurements": true
  },
  "runtime_seconds": 0.125,
  "hardware_transparency_note": "Execution performed using Qiskit Aer simulation on classical hardware. No physical quantum processor was utilized."
}
```

### 5.2 Comparative Hybrid Benchmark: `POST /api/v1/solvers/quantum/benchmark`
Executes comparative evaluation across classical solvers and QAOA on a target problem instance.

**Request Payload:**
```json
{
  "name": "Triangle Max-Cut Hybrid Benchmark",
  "problem_type": "max_cut",
  "instance": {
    "nodes": ["A", "B", "C"],
    "edges": [["A", "B", 2.0], ["B", "C", 3.0], ["A", "C", 1.0]]
  },
  "include_solvers": ["exact", "simulated_annealing", "qaoa"],
  "qaoa_config": {
    "p_depth": 1,
    "shots": 500,
    "max_iterations": 15
  },
  "trials": 2,
  "base_seed": 42
}
```

**Response Payload (200 OK):**
```json
{
  "benchmark_id": "hbench-9a8b7c6d5e4f",
  "name": "Triangle Max-Cut Hybrid Benchmark",
  "problem_type": "max_cut",
  "exact_optimum": 5.0,
  "total_runtime_seconds": 0.28,
  "summaries": [
    {
      "solver_id": "exact",
      "solver_name": "Exact Classical Solver",
      "solver_category": "classical_exact",
      "is_quantum_simulator": false,
      "best_objective": 5.0,
      "approximation_ratio": 1.0,
      "optimality_gap_percent": 0.0,
      "feasibility_rate": 1.0,
      "mean_runtime_ms": 1.1
    },
    {
      "solver_id": "qaoa",
      "solver_name": "Quantum Approximate Optimization Algorithm (QAOA)",
      "solver_category": "quantum_variational",
      "is_quantum_simulator": true,
      "best_objective": 5.0,
      "approximation_ratio": 1.0,
      "optimality_gap_percent": 0.0,
      "feasibility_rate": 1.0,
      "mean_runtime_ms": 62.4,
      "circuit_metadata": { "num_qubits": 3, "depth": 8 }
    }
  ],
  "hardware_transparency_note": "Quantum variational algorithm (QAOA) runs on classical CPU simulation via Qiskit Aer. No physical quantum hardware speedup is claimed."
}
```



---

## 6. Phase 6 Adaptive QAOA Endpoints Detail

### 6.1 List Adaptive Strategies: `GET /api/v1/solvers/quantum/adaptive/strategies`
Lists registered adaptive research strategies and their metadata.

**Response Payload (200 OK):**
```json
[
  {
    "strategy_id": "full_adaptive",
    "name": "Full Adaptive Hybrid QAOA Framework",
    "description": "Comprehensive adaptive protocol combining Trotter/Fourier initialization, dynamic depth expansion, and optimizer switching.",
    "supported_problem_types": ["max_cut", "assignment", "tsp"],
    "requires_prior_parameters": false,
    "supports_dynamic_depth": true,
    "supports_fourier_parameterization": true
  }
]
```

### 6.2 Validate Configuration: `POST /api/v1/solvers/quantum/adaptive/validate`
Validates an adaptive strategy configuration and depth bounds before launching simulations.

**Request Payload:**
```json
{
  "problem_id": "preset_0",
  "config": {
    "shots": 1024,
    "strategy_config": {
      "strategy_type": "full_adaptive",
      "initial_depth": 1,
      "max_depth": 3,
      "depth_growth": "improvement_triggered"
    }
  }
}
```

### 6.3 Parameter Transfer Check: `POST /api/v1/solvers/quantum/adaptive/transfer/check`
Evaluates angle vector compatibility and suggests interpolation methods when mapping from depth $p_1$ to $p_2$.

**Request Payload:**
```json
{
  "source_depth": 2,
  "target_depth": 3,
  "source_gamma": [0.35, 0.72],
  "source_beta": [0.65, 0.28],
  "interpolation_method": "linear_interpolation"
}
```

**Response Payload (200 OK):**
```json
{
  "is_compatible": true,
  "source_depth": 2,
  "target_depth": 3,
  "compatibility_score": 1.0,
  "recommended_method": "linear_interpolation",
  "notes": ["Smooth linear angle mapping across depth expansion."]
}
```

### 6.4 Transfer Parameters: `POST /api/v1/solvers/quantum/adaptive/transfer/parameters`
Executes angle interpolation generating warm-start parameter vectors for target depth $p_2$.

**Response Payload (200 OK):**
```json
{
  "transferred_gamma": [0.35, 0.535, 0.72],
  "transferred_beta": [0.65, 0.465, 0.28],
  "target_depth": 3,
  "method_used": "linear_interpolation",
  "compatibility_report": {
    "is_compatible": true,
    "source_depth": 2,
    "target_depth": 3,
    "compatibility_score": 1.0,
    "recommended_method": "linear_interpolation",
    "notes": ["Transferred successfully."]
  }
}
```

### 6.5 Execute Adaptive QAOA: `POST /api/v1/solvers/quantum/adaptive/execute`
Synchronously executes adaptive variational optimization with dynamic layer growth and optimizer arbitration.

**Request Payload:**
```json
{
  "problem_type": "max_cut",
  "instance": {
    "nodes": ["0", "1", "2"],
    "edges": [["0", "1", 2.0], ["1", "2", 3.0], ["0", "2", 1.0]]
  },
  "config": {
    "shots": 1024,
    "strategy_config": {
      "strategy_type": "full_adaptive",
      "initial_depth": 1,
      "max_depth": 3,
      "depth_growth": "improvement_triggered",
      "primary_optimizer": "COBYLA",
      "fallback_optimizer": "Nelder-Mead",
      "optimizer_schedule": "adaptive_fallback",
      "max_evaluations_total": 60
    }
  }
}
```

**Response Payload (200 OK):**
```json
{
  "execution_id": "aqexec-7b8c9d0e1f2a",
  "problem_id": "ad-hoc-max_cut",
  "problem_type": "max_cut",
  "status": "COMPLETED",
  "strategy_type": "full_adaptive",
  "initial_depth": 1,
  "final_depth": 2,
  "stopping_reason": "converged",
  "best_gamma": [0.421, 0.812],
  "best_beta": [0.579, 0.188],
  "best_bitstring": "101",
  "best_solution": { "0": 1, "1": 0, "2": 1 },
  "objective_value": 5.0,
  "expected_energy": -5.0,
  "is_feasible": true,
  "approximation_ratio": 1.0,
  "optimality_gap_percent": 0.0,
  "total_evaluations": 28,
  "total_circuit_executions": 1024,
  "execution_time_ms": 194.2,
  "decisions_log": [
    {
      "timestamp_offset": 0.08,
      "from_depth": 1,
      "to_depth": 2,
      "trigger_reason": "stagnation_detected",
      "action_summary": "Expanded QAOA circuit depth from p=1 to p=2 with warm-start interpolation",
      "active_optimizer": "COBYLA"
    }
  ],
  "hardware_transparency_note": "Execution performed using Qiskit Aer CPU simulation on classical hardware. No physical quantum processor was utilized."
}
```

### 6.6 Asynchronous Execution & Lifecycle Endpoints
- `POST /api/v1/solvers/quantum/adaptive/execute/async`: Dispatches optimization to thread-pool worker.
- `GET /api/v1/solvers/quantum/adaptive/executions`: Lists recent execution records.
- `GET /api/v1/solvers/quantum/adaptive/executions/{id}`: Retrieves complete execution record and result.
- `GET /api/v1/solvers/quantum/adaptive/executions/{id}/status`: Polling endpoint returning active depth, optimizer, and status.
- `POST /api/v1/solvers/quantum/adaptive/executions/{id}/cancel`: Triggers cooperative cancellation of in-flight task.

### 6.7 Adaptive QAOA Ablation Benchmarks
- `POST /api/v1/solvers/quantum/adaptive/benchmarks`: Executes multi-variant ablation study comparing Standard baseline against Full Adaptive and components.
- `GET /api/v1/solvers/quantum/adaptive/benchmarks`: Lists past benchmark runs.
- `GET /api/v1/solvers/quantum/adaptive/benchmarks/{benchmark_id}`: Retrieves comprehensive statistical report and automated ablation insights.
