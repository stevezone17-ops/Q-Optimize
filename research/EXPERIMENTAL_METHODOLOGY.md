# Stage 10.2 — Controlled Experimental Methodology

**Project:** Q-Optimize — AI-Assisted Hybrid Quantum-Classical Optimization Framework  
**Protocol Config:** `research/experiment_configs/benchmark_protocol.json`  
**Date:** 2026-11-25

---

## 1. Research Problem & Questions

Evaluate the empirical solution quality, feasibility, convergence efficiency, and scaling behavior of hybrid quantum-classical variational algorithms (**Standard QAOA** and **Adaptive QAOA**) against established classical baselines (**Exact Solver**, **Simulated Annealing**, **Genetic Algorithm**) and assess **AI/ML Solver Recommendation** accuracy across canonical combinatorial optimization problems.

- **RQ1:** How do QAOA and classical heuristics scale in solution quality and runtime across Max-Cut, Assignment, and TSP topologies?
- **RQ2:** Do adaptive parameter initialization, warm-start transfer, dynamic depth growth, and optimizer switching improve QAOA objective quality or evaluation efficiency over fixed-depth Standard QAOA?
- **RQ3:** How accurately does the ML/Rule-Based Solver Recommender select optimal or near-optimal solvers compared to a static baseline?
- **RQ4:** Under which problem constraints and qubit dimensions ($n \le 10$ vs. $n = 16$) do classical metaheuristics outperform Qiskit Aer simulation?

---

## 2. Experimental Hypotheses (Falsifiable)

- **H1:** Adaptive QAOA with warm-start parameter transfer and optimizer switching achieves equal or higher approximation ratios than cold-started Standard QAOA under comparable evaluation budgets on Max-Cut instances.
- **H2:** On heavily constrained permutation problems (Assignment, TSP), QAOA feasibility degrades faster with qubit count than classical constraint-preserving heuristics unless penalty multipliers are tuned and circuit depth increases.
- **H3:** Structural graph/matrix features allow the AI Solver Recommender to achieve lower decision regret than always choosing a single static heuristic.

---

## 3. Experimental Variables & Controls

- **Independent Variables:** Problem family (`max_cut`, `assignment`, `tsp`), instance size ($N$), graph density/weights, solver algorithm (`exact`, `simulated_annealing`, `genetic_algorithm`, `standard_qaoa`, `adaptive_qaoa`), and adaptive ablation configuration.
- **Dependent Variables:** Best objective, mean/median/std objective, feasibility rate, optimality gap (%), approximation ratio ($r$), wall-clock execution time (s), and function evaluation count.
- **Controlled Variables:**
  - **Paired Instances:** Every compared solver runs on the exact same canonical JSON instance identified by its SHA-256 fingerprint.
  - **Random Seed Policy:** Dataset generation uses fixed deterministic seeds (`1001`–`3010`); solver trials use deterministic offsets `seed_k = 42 + k * 17` for $k \in \{0, 1, 2\}$.
  - **Independent Evaluation:** All candidate solutions are scored by Phase 2 domain evaluators (`EvaluatorFactory`), never trusting solver self-reports.

---

## 4. Computational Budgets & Fairness Disclosure

| Solver | Configuration & Computational Budget | Simulation / Hardware Target |
|---|---|---|
| **Exact Solver** | Deterministic branch-and-bound / enumeration (1 trial) | Host CPU |
| **Simulated Annealing** | `max_iterations=250`, `T0=100.0`, `cooling_rate=0.95`, 3 trials | Host CPU |
| **Genetic Algorithm** | `population_size=30`, `max_iterations=80`, `mutation_rate=0.1`, 3 trials | Host CPU |
| **Standard QAOA** | `p_depth=1`, `shots=512`, `COBYLA`, `max_evaluations=40`, 3 trials ($n \le 10$ qubits) | Qiskit `AerSimulator` (CPU) |
| **Adaptive QAOA** | `initial_depth=1`, `max_depth=2`, `shots=512`, `COBYLA -> Nelder-Mead`, `max_evaluations_total=50`, 3 trials ($n \le 10$ qubits) | Qiskit `AerSimulator` (CPU) |

**Disclosure:** Because classical heuristics evaluate $O(10^2 - 10^3)$ states directly in native Python/NumPy while QAOA executes statevector/shot simulation of $2^n$-dimensional Hilbert spaces on classical CPU via `AerSimulator`, wall-clock runtimes are not directly comparable as physical quantum hardware speeds. No physical quantum advantage is claimed.
