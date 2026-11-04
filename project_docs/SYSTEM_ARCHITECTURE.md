# System Architecture

## Architectural style
Start with a modular monolith. Use background jobs for long-running solver executions. Do not introduce microservices without a demonstrated need.

## High-level architecture
```mermaid
flowchart TD
 U[Browser] --> FE[React TypeScript]
 FE --> API[FastAPI]
 API --> AUTH[Authentication]
 API --> PS[Problem Service]
 API --> FS[Formulation Service]
 API --> ES[Experiment Service]
 PS --> VAL[Validation and Evaluators]
 FS --> QUBO[QUBO and Ising]
 ES --> QUEUE[Background Queue]
 QUEUE --> QS[QAOA and Qiskit]
 QUEUE --> CS[Classical Solvers]
 QS --> EVAL[Evaluation]
 CS --> EVAL
 EVAL --> DB[(MongoDB)]
 API --> DB
```

## Responsibilities
- **Frontend:** authentication, problem builder, formulation viewer, solver forms, job status, results, and visualizations.
- **API:** validation, authorization, versioned endpoints, job creation and status.
- **Problem domain:** canonical schemas, objective functions, feasibility checks.
- **Formulation domain:** QUBO encoders, QUBO-to-Ising conversion, variable ordering, penalty metadata.
- **Solver domain:** common interface, QAOA/classical adapters, configuration validation, timeout handling.
- **Evaluation:** independently recompute objective and feasibility; compute documented metrics.
- **Persistence:** users, problems, experiments, job status, and results.

## Repository structure
```text
Q-Optimize/
├── frontend/
├── backend/
├── research/
├── docs/
└── project_docs/
```

## Execution lifecycle
```mermaid
sequenceDiagram
 Browser->>API: Submit confirmed problem and solver configuration
 API->>API: Validate problem and configuration
 API->>DB: Create queued experiment
 API->>Queue: Enqueue job
 API-->>Browser: Return experiment ID
 Queue->>Solver: Execute
 Solver-->>Evaluator: Candidate and metadata
 Evaluator->>Evaluator: Recompute objective and feasibility
 Evaluator->>DB: Persist result
 Browser->>API: Poll status
 API-->>Browser: Return status and result
```

## Design constraints
Use a canonical problem representation independent of solver choice. The evaluator is the source of truth. Record variable ordering and bitstring convention. Keep quantum dependencies isolated. Enforce per-user resource ownership.
