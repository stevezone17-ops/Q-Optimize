# Research Methodology

## Proposed research
Investigate adaptive QAOA parameter strategies and ML-assisted solver recommendation for selected combinatorial optimization problems.

## Research questions
- RQ1: How does QAOA quality vary with problem size and structure?
- RQ2: Do defined adaptive parameter strategies improve solution quality or convergence under a fixed evaluation budget?
- RQ3: Can problem features support useful solver recommendations compared with a rule-based baseline?
- RQ4: How do selected simulated noise settings affect QAOA quality and variability?
- RQ5: Under which tested conditions do classical methods outperform or match QAOA?

## Hypotheses
Treat as hypotheses, not promised outcomes:
- H1: Some adaptive strategies may improve QAOA quality or convergence on selected instance families.
- H2: A recommender may reduce recommendation regret on held-out instances.
- H3: Increasing noise under the chosen model may degrade quality or increase variability.

Negative or inconclusive results are valid.

## Instance families
Max-Cut graphs with varied size/density/topology; Assignment instances with varied dimensions/cost structures; small TSP instances. Record generator seeds and data provenance.

## Baselines
Exact solver for small instances, Genetic Algorithm, Simulated Annealing, relevant greedy baseline, standard QAOA initialization, and adaptive QAOA variants.

## Metrics
Objective value, feasibility rate, violations, approximation ratio/optimality gap when a valid optimum or bound exists, runtime, evaluation budget, convergence, seed variability, circuit depth, shots, and noise sensitivity. Define formulas and direction before experiments.

## Controls
Same instance for compared solvers; documented configurations; fixed and reported seeds; repeated stochastic runs; equivalent budgets where possible; record machine/software versions; separate formulation and solver time.

## Analysis
Report sample count, mean, standard deviation, median, quantiles, and confidence intervals where justified. Preserve raw per-run data. Use statistical tests only when assumptions and sample sizes support them.

## Reproducibility
Preserve instances, generator seeds, formulations, variable order, solver configuration, run seeds, software versions, environment metadata, raw results, and analysis scripts.

## Threats to validity
Small simulator-limited instances, generated-data bias, penalty/encoding choices, unequal budgets, parser errors, ML leakage, simplified noise models, and limited generalizability.

## Reporting rule
Never fabricate results. Simulator-based experiments do not establish quantum advantage.
