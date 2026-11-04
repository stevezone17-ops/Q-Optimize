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
- [ ] Versioned schemas.
- [ ] Max-Cut, Assignment, small TSP.
- [ ] Objective evaluators and feasibility validators.
- [ ] Exhaustive small-instance tests.
**Exit:** known examples produce correct values.

## Phase 3 — Formulations
- [ ] Define QUBO convention.
- [ ] Max-Cut QUBO.
- [ ] Assignment QUBO with documented penalties.
- [ ] Small TSP encoding and QUBO.
- [ ] QUBO-to-Ising conversion and exhaustive equivalence tests.
**Exit:** mathematical consistency tests pass.

## Phase 4 — Classical solvers
- [ ] Exact small-instance solver.
- [ ] Genetic Algorithm.
- [ ] Simulated Annealing.
- [ ] Relevant greedy baseline.
- [ ] Common result contract and multi-seed runs.
**Exit:** candidates are independently evaluated.

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

Do not mark a phase complete until its exit criteria are evidenced.
