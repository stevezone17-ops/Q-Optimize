# Q-Optimize Progress Tracker

Allowed statuses: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETED`, `NEEDS REVIEW`.

| Phase | Workstream | Status | Dependencies | Test status | Notes |
|---|---|---|---|---|---|
| 0 | Project setup | COMPLETED | None | PASSED | Repository structure, React/TS/Vite, FastAPI, .env.example, .gitignore, /health endpoints |
| 1 | Product shell and UI | COMPLETED | Phase 0 | PASSED | Dark-first scientific UI, Problem Builder, Landing Page, Navigation, Draft Parser, Typed API |
| 2 | Canonical problem domain | COMPLETED | Phase 0 | PASSED | Canonical problem models, independent evaluators, constraint validation engine, metadata extraction, frontend evaluator |
| 3 | QUBO and Ising formulations | NOT STARTED | Phase 2 | Not run | Interface specifications defined |
| 4 | Classical solvers | NOT STARTED | Phase 2 | Not run | Interface specifications defined |
| 5 | QAOA engine | NOT STARTED | Phase 3 | Not run | Interface specifications defined |
| 6 | Adaptive QAOA research | NOT STARTED | Phase 5 | Not run | |
| 7 | AI and ML modules | NOT STARTED | Phases 2, 4, 5 | Not run | Draft parser workflow established |
| 8 | Experiments and visualizations | NOT STARTED | Phases 4–7 | Not run | Empty states prepared |
| 9 | Hardening and delivery | NOT STARTED | Prior phases | Not run | |

## Current milestone
Phase 2 (Problem Domain and Optimization Modeling) implemented and mathematically validated. Canonical problem models (Max-Cut, Assignment, TSP), independent objective evaluation engine, structured constraint verification, and interactive solution testing in the Problem Builder active.

## Change log
| Date | Change | Evidence/commit |
|---|---|---|
| 2026-11-04 | Initial documentation package | Initial commit |
| 2026-11-04 | Phase 0 & Phase 1 Foundation: backend FastAPI setup, Pydantic problem schemas, MongoDB manager with memory fallback, dark-first scientific UI, Problem Builder (Max-Cut, Assignment, TSP), natural-language draft workflow, landing page, and automated test suites | Git commit `feat: initialize Q-Optimize platform and application foundation` |
| 2026-11-05 | Phase 2 Problem Domain: Canonical problem domain representations, independent evaluators (MaxCutEvaluator, AssignmentEvaluator, TSPEvaluator), reusable constraint validator engine, typed metadata extraction, API endpoints (/types, /validate, /evaluate, /evaluate-direct, /metadata), frontend Candidate Solution Evaluator modal, and 52 Pytest + 7 Vitest tests passing | Git commit `feat: implement optimization problem domain and validation engine` |

## Blockers and decisions
- **Decided:** MongoDB abstraction includes automatic in-memory fallback for local development so that developers without a running MongoDB daemon can test endpoints seamlessly.
- **Decided:** Natural language problem parsing is strictly draft-only, requiring explicit human review and confirmation before canonical problem creation.
- **Decided:** Independent evaluators are the single source of truth for objective value and feasibility verification, never trusting solver self-reporting.
- **Decided:** Zero fabricated metrics or simulated quantum advantage claims are allowed on the dashboard.
