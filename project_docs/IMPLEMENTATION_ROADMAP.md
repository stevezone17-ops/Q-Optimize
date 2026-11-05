# Implementation Roadmap

Build incrementally. Each phase ends with tests, documentation updates, and a focused Git commit.

## Phase 0 — Project setup
- [x] Create repository structure (`backend/app`, `frontend/src`, `research`, `docs`, `project_docs`).
- [x] Configure React/TypeScript/Vite and FastAPI.
- [x] Add linting, formatting, and tests (Pytest, Vitest, Testing Library).
- [x] Add `.env.example` and `.gitignore`.
- [x] Add health endpoint (`/health` and `/api/v1/health`).
**Exit:** frontend/backend start locally and baseline tests pass. (Achieved & Verified)

## Phase 1 — Product shell
- [x] Landing page, dashboard, navigation (9-section technical sidebar).
- [x] Problem Builder and workspace pages (Max-Cut, Assignment, TSP, Natural Language Draft).
- [x] Responsive design system and typed API client (`frontend/src/services/api.ts`).
**Exit:** pages navigate and real API health is displayed; no fake solver results. (Achieved & Verified)

## Phase 2 — Canonical problem domain
- [x] Versioned schemas (Max-Cut, Assignment, TSP with Pydantic validation).
- [x] Canonical representations with decision variables, mathematical objectives, and formal constraints.
- [x] Independent objective evaluators (MaxCutEvaluator, AssignmentEvaluator, TSPEvaluator) and evaluator factory.
- [x] Reusable constraint validation engine returning structured violation objects.
- [x] Structural graph, matrix, and tour metadata calculation.
- [x] Versioned API endpoints (/types, /validate, /evaluate, /evaluate-direct, /metadata).
- [x] Interactive Solution Evaluator in the frontend Problem Builder.
- [x] Hand-calculated small-instance tests with verified ground truths (52 Pytest + 7 Vitest).
**Exit:** known examples produce correct values. (Achieved & Verified)

## Phase 3 — Formulations & Ising Hamiltonian Modeling
- [x] Canonical QUBO builder with upper-triangular indexing and sparse/dense export.
- [x] Max-Cut QUBO minimization mapping with graph degree and edge coupling terms.
- [x] Square Assignment QUBO with exact row/column penalty expansions and rectangular rejection.
- [x] Position-based TSP QUBO with cyclic transitions, city/step penalties, and start pinning.
- [x] Reusable penalty management module with mathematically proven sufficiency bounds.
- [x] Analytical QUBO-to-Ising conversion via $x_i = (1 - Z_i)/2$, computing local fields $h_i$, couplings $J_{ij}$, and offset $C$.
- [x] Independent mathematical verification engine with exhaustive $2^n$ state-space truth tables ($n \le 12$).
- [x] Versioned API endpoints (/generate, /qubo, /ising, /verify, /{id}, /{id}/metadata, /{id}/export).
- [x] Interactive Formulation Studio in the React/TypeScript frontend (heatmap, LaTeX inspector, verification panel).
- [x] Comprehensive test coverage (80 backend pytest + 12 frontend vitest passing).
**Exit:** mathematical consistency, energy equivalence, and truth-table verification tests pass. (Achieved & Verified)

## Phase 4 — Classical solvers
- [x] Classical solver architecture, `IClassicalSolver` interface, and Pydantic execution models.
- [x] Exact small-instance solver (symmetry-reduced $2^{n-1}$ Max-Cut, Hungarian $O(n^3)$ Assignment, pinned TSP enumeration).
- [x] Genetic Algorithm solver with problem-specific chromosomes (binary, permutation with OX crossover and 2-opt/swap mutations).
- [x] Simulated Annealing solver with Metropolis acceptance, exponential and linear cooling, and domain neighborhood moves.
- [x] Classical execution pipeline with thread-pooled background workers, cooperative cancellation, and lifecycle persistence.
- [x] Classical benchmarking engine with multi-solver comparative evaluations, stochastic trials, and exact optimality gap metrics.
- [x] Interactive Classical Optimization Lab in frontend (Single Solver Lab, Comparative Benchmark Suite, Execution Audit History).
- [x] Comprehensive test coverage and verification (117 backend pytest + 19 frontend vitest passing).
**Exit:** candidates are independently evaluated against ground-truth problem definitions; exact baseline benchmarks established. (Achieved & Verified)

## Phase 5 — QAOA
- [ ] Qiskit/Aer integration.
- [ ] QAOA for Max-Cut first.
- [ ] Parameter optimizer, measurement mapping, circuit metadata.
- [ ] Independent evaluation.
**Exit:** bounded reproducible simulations work.

## Phase 6 — Adaptive QAOA
- [ ] Define baseline and adaptive strategies.
- [ ] Implement controlled comparisons.
- [ ] Record budgets, convergence, multiple seeds.
- [ ] Analyze results without assuming improvement.

## Phase 7 — AI and ML
- [ ] Structured natural-language draft parser.
- [ ] Clarification and confirmation workflow.
- [ ] Deterministic validation.
- [ ] Benchmark feature extraction.
- [ ] Rule-based recommender baseline.
- [ ] ML recommendation evaluation on held-out instances.

## Phase 8 — Experiments and visualizations
- [ ] Background jobs and experiment history.
- [ ] Comparison charts and noise experiments.
- [ ] Report export and reproducibility metadata.

## Phase 9 — Final hardening
- [ ] Security, resource limits, accessibility, regression tests.
- [ ] Deployment, final report, demo, viva material.
