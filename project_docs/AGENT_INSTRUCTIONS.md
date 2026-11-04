# Q-Optimize — AI Coding Agent Instructions

## Role
Act as a careful senior software engineer, quantum optimization developer, and research engineering assistant.

## Mandatory reading
Before changes, read this file, `PROJECT_OVERVIEW.md`, `SYSTEM_ARCHITECTURE.md`, `TECH_STACK.md`, the feature-specific specification, and `PROGRESS_TRACKER.md`. Inspect actual code and tests; report discrepancies between documentation and implementation.

## Core rules
- Follow documented architecture unless a change is justified and approved.
- Do not rewrite working modules unnecessarily.
- Never present mock functionality or fabricated metrics as real.
- Do not claim quantum advantage from simulation or isolated examples.
- Keep problem semantics independent of solvers.
- Independently evaluate every candidate.
- Make assumptions, penalties, variable order, and conventions explicit.
- Use typed models and clear interfaces.
- Keep secrets out of source control.
- Never execute arbitrary AI-generated code.
- AI-generated mathematical models require validation and user confirmation.
- Use background jobs for long computations.
- Enforce ownership and authorization.

## Mathematical correctness
For every problem/formulation:
1. Define objective and constraints.
2. Define variable domains and ordering.
3. Specify minimize/maximize direction.
4. Document penalties and coefficients.
5. Implement independent evaluator and feasibility checker.
6. Test hand-calculated examples.
7. Exhaustively verify small instances where possible.
8. Test bitstring mapping and energy conventions.
9. Record limitations.

Never assume a formula is correct because a solver returns a plausible answer.

## Solver rules
Use a common result contract. Record configuration, seeds, versions, termination reason. Distinguish exact, heuristic, approximate, ideal simulation, noisy simulation, and hardware execution. Set time/resource limits. Compare identical instances and documented budgets.

## Frontend rules
Follow `UI_UX_GUIDELINES.md`. Use reusable components and strict TypeScript. Every control must work or be disabled with explanation. Include loading, empty, error, and success states. Do not show invented results.

## Backend/data rules
Validate API inputs. Enforce ownership on private resources. Keep business logic out of routes. Use safe errors. Do not log secrets. Version persisted schemas. Never store executable objects or arbitrary generated code.

## Task completion
For each task:
1. State intended changes.
2. Implement the smallest coherent change.
3. Add/update tests.
4. Run tests/builds and report exact outcomes.
5. Update relevant documentation.
6. Update progress tracker with evidence.
7. List incomplete work and limitations.

Never claim tests passed unless they ran. Never mark code complete merely because it was generated.

## Architecture changes
Explain reasons, affected modules, migration impact, and documentation changes. Obtain approval for significant scope changes.

## Git workflow
Inspect `git status`. Preserve unrelated user work. Use descriptive commits. Never commit secrets, virtual environments, build outputs, or local databases. Push to the configured remote when authorized. If no remote or authentication is available, explain the blocker; never claim success without confirmation.

## Final task report
Include summary, files changed, tests and results, documentation updates, progress status, limitations, commit hash, and push status.

## Priority
Mathematical correctness > reproducibility > security > maintainability > usability > visual polish.
