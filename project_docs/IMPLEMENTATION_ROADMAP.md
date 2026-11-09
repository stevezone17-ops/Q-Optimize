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
- [x] Qiskit 2.6.1 and Aer 0.17.2 integration with hardware transparency enforcement.
- [x] QAOA Cost and Mixer Hamiltonians synthesized with exact $R_Z(2\gamma h_i)$, $R_{ZZ}(2\gamma J_{ij})$, and $R_X(2\beta)$ unitaries.
- [x] Parameterized QAOA circuit builder ($p$-depth ParameterVectors, uniform superposition, fast parameter binding, measurement mapping).
- [x] Classical parameter optimizers (COBYLA, SLSQP, Nelder-Mead, L-BFGS-B) with statevector and shot expectation evaluation and convergence tracing.
- [x] Quantum execution and sampling engine with Aer transpilation, finite-shot sampling, depolarizing noise modeling, and resource bounds.
- [x] Solution decoder with little-endian bit-order mapping, domain-specific reconstruction (Max-Cut, Assignment, TSP), and independent evaluation.
- [x] Unified execution pipeline with background dispatch, status polling, cooperative cancellation, and persistent storage.
- [x] Interactive Quantum Optimization Lab in React/TypeScript (circuit blueprint, convergence curve, bitstring histogram, domain visualizers, audit log).
- [x] Hybrid Quantum-Classical Benchmarking Engine comparing QAOA against Exact, GA, and SA solvers with approximation ratio and optimality gap metrics.
- [x] Complete integration and scientific verification (159 Pytest + 26 Vitest tests passing).
**Exit:** bounded reproducible simulations work; exact baseline comparisons and independent evaluations complete. (Achieved & Verified)

## Phase 6 — Adaptive QAOA research
- [x] Adaptive QAOA research architecture, base contracts, registry, and factory (Stage 6.1).
- [x] Parameter initialization strategies: linear ramp, Fourier parameterization, warm starts, and random baseline (Stage 6.2).
- [x] Parameter transfer across depths and instances with linear interpolation and compatibility checks (Stage 6.3).
- [x] Adaptive optimizer scheduling: static, adaptive-fallback, and multi-stage coarse-to-fine schedules (Stage 6.4).
- [x] Dynamic circuit depth manager with stagnation-triggered layer progression and $p \le 10$ ceiling (Stage 6.5).
- [x] Convergence monitoring, stagnation windowing, and multi-criteria stopping conditions (Stage 6.6).
- [x] Unified execution pipeline with thread-pooled worker dispatch, cooperative cancellation, and independent solution decoding (Stage 6.7).
- [x] Adaptive QAOA Research Lab frontend with strategy presets, parameter trajectories, decision audit logs, and transfer tools (Stage 6.8).
- [x] Adaptive QAOA research benchmarking and ablation study engine with statistical metrics and automated insights (Stage 6.9).
- [x] Complete scientific validation, documentation, and empirical verification (Stage 6.10).
**Exit:** dynamic strategies benchmarked against fixed-depth QAOA baseline; statistical distributions and ablation insights rigorously verified; 100% test pass rate across 201 backend and 33 frontend tests. (Achieved & Verified)

## Phase 7 — AI and ML
- [x] AI and machine learning architecture, interfaces, and registries (Stage 7.1).
- [x] 18-dimensional optimization feature extraction engine across all problem types (Stage 7.2).
- [x] Experiment dataset builder and leakage-free group-aware training pipeline (Stage 7.3).
- [x] Intelligent solver recommender with ML inference, rule-based baseline, and safety ceilings (Stage 7.4).
- [x] Solver recommendation evaluation, Brier calibration, explainability, and OOD detection (Stage 7.5).
- [x] Natural language optimization assistant with Gemini and deterministic fallback (Stage 7.6).
- [x] AI-assisted problem formulation in Problem Builder with human confirmation gate (Stage 7.7).
- [x] Intelligent solver recommendation dashboard and audit modals across labs (Stage 7.8).
- [x] ML model monitoring, feedback loop, KS feature drift detection, and continuous learning (Stage 7.9).
- [x] Complete AI and machine learning integration, validation, and documentation (Stage 7.10).
**Exit:** natural language assistant parses, extracts, and validates problem drafts with mandatory human confirmation; intelligent recommender predicts Pareto-optimal solvers with explainability, safety bounds, and OOD safeguards; 100% test pass rate across 246 backend and 46 frontend tests. (Achieved & Verified)

## Phase 8 — Experiments and visualizations
- [ ] Background jobs and experiment history.
- [ ] Comparison charts and noise experiments.
- [ ] Report export and reproducibility metadata.

## Phase 9 — Final hardening
- [ ] Security, resource limits, accessibility, regression tests.
- [ ] Deployment, final report, demo, viva material.
