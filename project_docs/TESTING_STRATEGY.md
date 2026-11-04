# Testing Strategy

## Philosophy
Mathematical correctness is a release blocker. A polished interface cannot compensate for incorrect objectives, constraints, variable ordering, or energy conversions.

## Backend unit tests
Problem schemas, objective evaluators, feasibility checkers, QUBO construction, QUBO-to-Ising conversion, bitstring mapping, solver configuration, and metrics.

## Mathematical property tests
For small instances:
- Enumerate all binary assignments.
- Compare direct objective and QUBO energy, including documented offsets/penalties.
- Compare QUBO and Ising energies under the documented substitution.
- Verify feasibility against hand-checked cases.
- Verify objective direction and variable ordering.

## Integration tests
API/database, API/background queue, worker/solver, solver/evaluator, persistence/retrieval, and ownership checks.

## Frontend tests
Navigation, form validation, confirmation workflow, API states, job status, results mapping, responsive navigation, and accessibility basics.

## End-to-end
Create problem → validate/confirm → formulate → run solver → poll status → inspect independently evaluated result → save and reload.

## Scientific validation
Use known small instances, multiple seeds, reproducible configurations, and recomputable raw metrics. Failed jobs must never be shown as successful.

## Security
Test authentication, cross-user access, input limits, secret handling, rate limits, and safe errors.

## Release gate
Tests pass, failure cases are handled, documentation is updated, no fake results are shown, and mathematical outputs are independently validated.
