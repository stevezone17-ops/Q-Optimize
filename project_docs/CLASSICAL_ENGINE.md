# Classical Optimization Engine

## Purpose
Provide transparent baselines on the same canonical problem instances used by quantum solvers.

## Required methods
- **Exact solver:** exhaustive enumeration for very small binary instances or an appropriate OR-Tools/SciPy formulation. Record whether optimality is proven.
- **Genetic Algorithm:** document chromosome encoding, initialization, fitness, feasibility handling, selection, crossover, mutation, elitism, population size, stopping rule, and seed.
- **Simulated Annealing:** document state, neighbourhood, initial temperature, cooling schedule, iterations, feasibility handling, stopping rule, and seed.
- **Greedy baseline:** include only where meaningful and clearly label as heuristic.

## Common solver interface
Define a typed interface such as `solve(problem, config, seed) -> SolverResult`. Avoid untyped ad-hoc dictionaries.

## Common result
Solver name/version, candidate, independently computed objective, feasibility, violations, runtime, iterations/evaluations, seed/configuration, optimality status if proven, termination reason, and warnings.

## Fair comparison
Use identical instances, documented budgets, multiple seeds for stochastic methods, and comparable stopping criteria. Report distributions rather than only best runs. Separate formulation time, solver time, and total workflow latency.
