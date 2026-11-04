# Q-Optimize — Research Environment

This directory houses reproducible datasets, configuration definitions, notebooks, and experiment results supporting the Q-Optimize research methodology.

## Directory Structure

- `datasets/`: Canonical problem instances (Max-Cut benchmark graphs, Assignment matrices, TSP coordinate sets).
- `experiment_configs/`: Reproducible experiment execution specs, parameter sweeps, and solver configuration JSONs.
- `notebooks/`: Exploratory analysis notebooks, parameter convergence studies, and statistical validation scripts.
- `results/`: Raw per-run traces, candidate bitstrings, energy evaluations, and execution provenance logs.

## Research Questions Investigated

1. **RQ1:** How does QAOA solution quality scale with problem size and graph topology across instance families?
2. **RQ2:** Do defined adaptive parameter initialization strategies improve QAOA convergence under fixed evaluation budgets?
3. **RQ3:** Can instance topological features support effective solver recommendations compared to rule-based baselines?
4. **RQ4:** How do simulated noise models (depolarizing, readout) affect QAOA solution variance?
5. **RQ5:** Under which problem conditions do classical baselines (Exact, GA, SA) outperform QAOA simulation?
