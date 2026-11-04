# Product Requirements Document

## Product summary
Q-Optimize is a web application for defining, formulating, solving, and comparing combinatorial optimization problems using classical and quantum approaches.

## Core user journey
1. Choose a problem template or describe a problem in natural language.
2. Review extracted variables, objective, constraints, units, and assumptions.
3. Correct and confirm the problem.
4. Inspect its mathematical formulation.
5. Select and configure a solver.
6. Execute and monitor the experiment.
7. Inspect feasibility, objective value, convergence, and limitations.
8. Save or export the experiment.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | User registration and sign-in | Should |
| FR-02 | Create supported problems from templates | Must |
| FR-03 | Natural-language problem entry | Should |
| FR-04 | AI output is a reviewable draft | Must |
| FR-05 | Edit variables, objective, and constraints | Must |
| FR-06 | Validate inputs and missing information | Must |
| FR-07 | Generate supported QUBO models | Must |
| FR-08 | Convert supported QUBO models to Ising | Must |
| FR-09 | Independent objective and feasibility evaluation | Must |
| FR-10 | Classical solver execution | Must |
| FR-11 | QAOA simulation | Must |
| FR-12 | Record configurations, seeds, versions, and metrics | Must |
| FR-13 | Compare equivalent problem instances | Must |
| FR-14 | Visualize solutions and convergence | Should |
| FR-15 | Save and retrieve experiments | Should |
| FR-16 | Export experiment reports | Should |
| FR-17 | ML-based solver recommendation | Should |
| FR-18 | Noise experiments | Could |
| FR-19 | Adaptive QAOA strategies | Should |

## Non-functional requirements
Correctness, reproducibility, security, responsive and accessible UI, modular maintainable code, observability, resource limits, and transparent result labels.

## MVP acceptance criteria
All three initial problem types validate; users can inspect formulations; exact and heuristic baselines run; QAOA works on bounded instances; candidates are independently evaluated; experiments persist; failed jobs are never shown as successful.
