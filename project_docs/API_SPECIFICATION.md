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
