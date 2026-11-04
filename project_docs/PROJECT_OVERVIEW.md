# Q-Optimize — Project Overview

## Proposed title
**Q-Optimize: An AI-Assisted Hybrid Quantum-Classical Optimization Framework with Adaptive QAOA and Intelligent Solver Selection**

## Vision
A web platform that helps users describe optimization problems, inspect mathematical formulations, run classical and quantum algorithms, compare outcomes, and preserve reproducible experiments.

## Objectives
1. Accept structured and natural-language problem descriptions.
2. Validate supported optimization problems.
3. Generate QUBO and Ising representations where appropriate.
4. Implement QAOA with Qiskit simulation.
5. Implement exact small-instance baselines, Genetic Algorithm, and Simulated Annealing.
6. Investigate adaptive QAOA parameter strategies.
7. Investigate ML-assisted solver recommendation.
8. Evaluate results through repeatable experiments.
9. Provide visualizations and experiment history.

## Initial problem families
- Max-Cut.
- Assignment Problem.
- Small Travelling Salesperson Problem (TSP).

Each problem needs a formal definition, input schema, independent objective evaluator, feasibility checker, and tests before solver integration.

## Intended users
Students, educators, developers, and researchers exploring optimization and quantum computing.

## Scope boundaries
The initial product is an educational and experimental platform. It must not claim practical quantum advantage, guarantee heuristic global optima, or imply that simulator execution is real quantum hardware execution.

## Success criteria
- Supported problems can be created and validated.
- Objective and feasibility are evaluated independently of solver output.
- Exact baselines exist for small instances.
- QAOA simulation works for bounded supported instances.
- Classical candidates are independently evaluated.
- Comparisons use the same problem instance and documented settings.
- Experiments preserve configuration, seeds, and software versions.

## Principles
Mathematical correctness before polish; reproducibility before performance claims; human confirmation for AI-generated models; explicit assumptions; no fabricated metrics.
