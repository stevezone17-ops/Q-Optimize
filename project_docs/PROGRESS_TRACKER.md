# Q-Optimize Progress Tracker

Allowed statuses: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETED`, `NEEDS REVIEW`.

| Phase | Workstream | Status | Dependencies | Test status | Notes |
|---|---|---|---|---|---|
| 0 | Project setup | COMPLETED | None | PASSED | Repository structure, React/TS/Vite, FastAPI, .env.example, .gitignore, /health endpoints |
| 1 | Product shell and UI | COMPLETED | Phase 0 | PASSED | Dark-first scientific UI, Problem Builder, Landing Page, Navigation, Draft Parser, Typed API |
| 2 | Canonical problem domain | NOT STARTED | Phase 0 | Pending | Canonical schemas defined in Phase 1; independent evaluators scheduled for Phase 2 |
| 3 | QUBO and Ising formulations | NOT STARTED | Phase 2 | Not run | Interface specifications defined |
| 4 | Classical solvers | NOT STARTED | Phase 2 | Not run | Interface specifications defined |
| 5 | QAOA engine | NOT STARTED | Phase 3 | Not run | Interface specifications defined |
| 6 | Adaptive QAOA research | NOT STARTED | Phase 5 | Not run | |
| 7 | AI and ML modules | NOT STARTED | Phases 2, 4, 5 | Not run | Draft parser workflow established |
| 8 | Experiments and visualizations | NOT STARTED | Phases 4–7 | Not run | Empty states prepared |
| 9 | Hardening and delivery | NOT STARTED | Prior phases | Not run | |

## Current milestone
Phase 1 (Complete Platform Foundation) implemented and validated. Frontend workspace, Problem Builder, Landing Page, and FastAPI backend foundation active with live health integration.

## Change log
| Date | Change | Evidence/commit |
|---|---|---|
| 2026-11-04 | Initial documentation package | Initial commit |
| 2026-11-04 | Phase 0 & Phase 1 Foundation: backend FastAPI setup, Pydantic problem schemas, MongoDB manager with memory fallback, dark-first scientific UI, Problem Builder (Max-Cut, Assignment, TSP), natural-language draft workflow, landing page, and automated test suites | Git commit `feat: initialize Q-Optimize platform and application foundation` |

## Blockers and decisions
- **Decided:** MongoDB abstraction includes automatic in-memory fallback for local development so that developers without a running MongoDB daemon can test endpoints seamlessly.
- **Decided:** Natural language problem parsing is strictly draft-only, requiring explicit human review and confirmation before canonical problem creation.
- **Decided:** Zero fabricated metrics or simulated quantum advantage claims are allowed on the dashboard.
