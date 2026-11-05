# Q-Optimize Progress Tracker

Allowed statuses: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETED`, `NEEDS REVIEW`.

| Phase | Workstream | Status | Dependencies | Test status | Notes |
|---|---|---|---|---|---|
| 0 | Project setup | COMPLETED | None | PASSED | Repository structure, React/TS/Vite, FastAPI, .env.example, .gitignore, /health endpoints |
| 1 | Product shell and UI | COMPLETED | Phase 0 | PASSED | Dark-first scientific UI, Problem Builder, Landing Page, Navigation, Draft Parser, Typed API |
| 2 | Canonical problem domain | COMPLETED | Phase 0 | PASSED | Canonical problem models, independent evaluators, constraint validation engine, metadata extraction, frontend evaluator |
| 3 | QUBO and Ising formulations | COMPLETED | Phase 2 | PASSED | Canonical QUBO builder, upper-triangular indexing, penalty manager, Max-Cut/Assignment/TSP formulations, Ising analytical converter, exhaustive $2^n$ state verification, Formulation Studio UI |
| 4 | Classical solvers | IN PROGRESS | Phase 2 | PASSED (Stage 4.7) | Stages 4.1–4.7 complete: Exact, GA, SA solvers, execution pipeline, benchmarking engine, rich Classical Lab UI (Single Solver Lab, Domain Visualizers, Multi-Solver Benchmark Suite, Audit History), 117 Pytest + 19 Vitest passing |
| 5 | QAOA engine | NOT STARTED | Phase 3 | Not run | Interface specifications defined |
| 6 | Adaptive QAOA research | NOT STARTED | Phase 5 | Not run | |
| 7 | AI and ML modules | NOT STARTED | Phases 2, 4, 5 | Not run | Draft parser workflow established |
| 8 | Experiments and visualizations | NOT STARTED | Phases 4–7 | Not run | Empty states prepared |
| 9 | Hardening and delivery | NOT STARTED | Prior phases | Not run | |

## Current milestone
Phase 3 (QUBO Generation, Constraint Penalty Modeling, and QUBO-to-Ising Hamiltonian Conversion) implemented and mathematically verified. Canonical upper-triangular QUBO representation, squared constraint expansion, penalty sufficiency bounds, Max-Cut / Square Assignment / Position-based TSP formulations, analytical spin mapping ($x_i = (1 - Z_i)/2$), exhaustive truth-table verification across all $2^n$ states ($n \le 12$), API endpoints, and interactive Formulation Studio in the frontend are fully operational.

## Change log
| Date | Change | Evidence/commit |
|---|---|---|
| 2026-11-04 | Initial documentation package | Initial commit |
| 2026-11-04 | Phase 0 & Phase 1 Foundation: backend FastAPI setup, Pydantic problem schemas, MongoDB manager with memory fallback, dark-first scientific UI, Problem Builder (Max-Cut, Assignment, TSP), natural-language draft workflow, landing page, and automated test suites | Git commit `feat: initialize Q-Optimize platform and application foundation` |
| 2026-11-05 | Phase 2 Problem Domain: Canonical problem domain representations, independent evaluators (MaxCutEvaluator, AssignmentEvaluator, TSPEvaluator), reusable constraint validator engine, typed metadata extraction, API endpoints (/types, /validate, /evaluate, /evaluate-direct, /metadata), frontend Candidate Solution Evaluator modal, and 52 Pytest + 7 Vitest tests passing | Git commit `feat: implement optimization problem domain and validation engine` |
| 2026-11-05 | Phase 3 QUBO & Ising Formulations: Canonical QUBO builder with upper-triangular indexing, squared penalty expansion, PenaltyManager sufficiency bounds, Max-Cut, square Assignment, and cyclic TSP QUBO models, exact analytical QUBO-to-Ising converter ($h_i, J_{ij}, C$), exhaustive truth-table verification ($2^n$ states, $n \le 12$), versioned endpoints (/generate, /qubo, /ising, /verify, /{id}/export), interactive Formulation Studio in React/TS, and 80 Pytest + 12 Vitest tests passing | Git commit `feat: implement QUBO generation and Ising Hamiltonian formulation` |
| 2026-11-05 | Stage 4.1 Classical Solver Architecture: Common IClassicalSolver interface, Pydantic contracts (SolverRequest, SolverResult, SolverStatus, SolverMetadata), ClassicalSolverRegistry & Factory, REST endpoints (/solvers/classical, /validate, /execute), interactive Classical Lab shell in frontend, and 88 Pytest + 15 Vitest tests passing | Git commit `feat: establish classical solver architecture and interfaces` |
| 2026-11-05 | Stage 4.2 Exact Classical Solver: Deterministic ExactSolver implementation for Max-Cut (symmetry-reduced 2^(n-1) binary search), Assignment (Hungarian algorithm via SciPy), and TSP (permutation enumeration with starting vertex pinning), independent evaluator validation, size/time safety bounds, Classical Lab UI execution, and 94 Pytest + 16 Vitest tests passing | Git commit `feat: implement exact classical optimization solver` |
| 2026-11-05 | Stage 4.3 Genetic Algorithm Solver: GeneticAlgorithmSolver implementation with problem-specific representations (binary strings for Max-Cut, permutations with Order Crossover OX and swap/inversion mutations for Assignment and TSP), tournament/roulette selection, elitism, convergence history tracing, seed reproducibility, independent evaluator verification, and 100 Pytest + 16 Vitest tests passing | Git commit `feat: implement genetic algorithm optimization engine` |
| 2026-11-05 | Stage 4.4 Simulated Annealing Solver: SimulatedAnnealingSolver implementation with Metropolis acceptance transitions, exponential and linear cooling schedules, 1-flip neighborhood (Max-Cut), pairwise agent swap (Assignment), 2-opt edge inversion and vertex swap (TSP), independent evaluator verification, temperature convergence tracing, Classical Lab parameter controls, and 106 Pytest + 17 Vitest tests passing | Git commit `feat: implement simulated annealing optimization engine` |
| 2026-11-05 | Stage 4.5 Classical Execution Pipeline: ClassicalExecutionPipeline with thread-pooled background dispatch, lifecycle tracking (PENDING, RUNNING, COMPLETED, CANCELLED, FAILED), MongoDB/memory persistence, cooperative cancellation, lightweight status polling endpoint (/status), recent executions listing (/executions), typed client service, and 112 Pytest + 17 Vitest tests passing | Git commit `feat: integrate classical solver execution pipeline` |
| 2026-11-05 | Stage 4.6 Classical Benchmarking & Evaluation: ClassicalBenchmarkEngine supporting multi-solver simultaneous evaluation, multi-trial stochastic sampling, statistical variance (mean, standard deviation, min, max), 100% independent feasibility verification, exact optimality gap calculation relative to global optimum ($|f - f^*| / |f^*| \times 100\%$), persistent benchmark storage (/benchmark, /benchmarks, /benchmarks/{id}), and 117 Pytest + 17 Vitest tests passing | Git commit `feat: implement classical benchmarking and performance evaluation` |
| 2026-11-05 | Stage 4.7 Classical Optimization Lab Frontend: Three-mode UI (Single Solver Lab, Comparative Benchmark Suite, Execution Audit History), domain-specific solution visualizers (Partition S vs V\S for Max-Cut, Agent->Task matching grid for Assignment, Route chip sequences for TSP), convergence trace cards, live background execution polling, side-by-side benchmark comparison tables with rank badges and optimality gap indicators, and 117 Pytest + 19 Vitest tests passing | Git commit `feat: complete classical optimization lab frontend` |

## Blockers and decisions
- **Decided:** Upper-triangular matrix convention ($i < j$) is strictly enforced across all internal representations and export routines, preventing double-counting of quadratic terms in symmetric formulations.
- **Decided:** Spin variable transformation convention is defined strictly as $x_i = \frac{1 - Z_i}{2}$ where Pauli-$Z$ eigenvalues $Z_i \in \{-1, +1\}$ correspond to classical binary states $\{0, 1\}$.
- **Decided:** Rectangular (non-square) cost matrices for the Assignment Problem are rejected during QUBO generation with an explicit error, preventing ill-defined unbalanced QUBOs unless padded.
- **Decided:** Exhaustive truth-table verification is bounded to $n \le 12$ binary variables ($4,096$ states) to prevent exponential timeouts during interactive calls.
- **Decided:** Independent evaluators are the single source of truth for objective value and feasibility verification, never trusting solver self-reporting.
- **Decided:** Zero fabricated metrics or simulated quantum advantage claims are allowed on the dashboard.
