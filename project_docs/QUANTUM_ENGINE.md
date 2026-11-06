# Quantum Optimization Engine Specification

## 1. Purpose & Scope
The Quantum Optimization Engine provides the mathematical and algorithmic bridge between high-level combinatorial optimization problems (Max-Cut, Assignment, TSP) and quantum hardware/simulation algorithms (QAOA). 

Phase 3 establishes the foundation:
- Rigorous Quadratic Unconstrained Binary Optimization (QUBO) construction.
- Mathematically bounded constraint penalty modeling.
- Exact analytical QUBO-to-Ising Hamiltonian conversion.
- Exhaustive truth-table verification proving that $E_{\text{QUBO}}(x) \equiv H_{\text{Ising}}(Z)$ and matches canonical problem objectives.

> **Important Boundary:** QAOA parameterized quantum circuits, mixer Hamiltonians, Trotterized layers, AerSimulator statevectors, and classical parameter optimizers are strictly scheduled for Phase 5. Simulation outputs are never reported as physical quantum hardware executions.

---

## 2. Canonical QUBO Mathematical Foundation

### 2.1 Universal QUBO Formulation
For a binary decision vector $x \in \{0, 1\}^n$, the objective is defined as:
\[
E_{\text{QUBO}}(x) = \sum_{i=1}^n Q_{ii} x_i + \sum_{1 \le i < j \le n} Q_{ij} x_i x_j + c = x^T Q x + c
\]
where:
- $Q_{ii}$ are linear coefficients on the diagonal (since $x_i^2 = x_i$ for $x_i \in \{0, 1\}$).
- $Q_{ij}$ ($i < j$) are quadratic interaction terms.
- $c \in \mathbb{R}$ is a scalar constant energy offset.
- The objective sense is strictly **minimization**.

### 2.2 Upper-Triangular Matrix Convention
To avoid double-counting off-diagonal entries in symmetric formulations:
- All internal storage and dictionary keys enforce $i < j$.
- Adding a symmetric off-diagonal term between variable indices $(u, v)$ with $u \ne v$ automatically normalizes to $(\min(u, v), \max(u, v))$.
- Dense export is supported in two explicit forms:
  1. **Upper-Triangular Matrix:** $Q_{ij} = 0$ for all $i > j$.
  2. **Symmetric Matrix:** $Q^{\text{sym}}_{ij} = Q^{\text{sym}}_{ji} = \frac{1}{2} Q_{ij}$ for $i \ne j$, and $Q^{\text{sym}}_{ii} = Q_{ii}$.

---

## 3. Constraint Penalty Modeling & Quadratic Expansion

### 3.1 Squared Penalty Expansion
Linear equality constraints of the form $\sum_{k=1}^m w_k x_k = C$ are integrated into the QUBO objective via quadratic penalty terms:
\[
P(x) = \lambda \left( \sum_{k=1}^m w_k x_k - C \right)^2
\]
Expanding this expression algebraically:
\[
P(x) = \lambda \left[ \sum_{k=1}^m w_k^2 x_k^2 + 2 \sum_{1 \le k < l \le m} w_k w_l x_k x_l - 2 C \sum_{k=1}^m w_k x_k + C^2 \right]
\]
Applying the idempotence of binary variables ($x_k^2 = x_k$):
\[
P(x) = \lambda \left[ \sum_{k=1}^m (w_k^2 - 2 C w_k) x_k + 2 \sum_{1 \le k < l \le m} w_k w_l x_k x_l + C^2 \right]
\]
Thus, the penalty expansion contributes:
- **Linear on-diagonal terms:** $\Delta Q_{kk} = \lambda (w_k^2 - 2 C w_k)$
- **Quadratic coupling terms:** $\Delta Q_{kl} = 2 \lambda w_k w_l$ for $k < l$
- **Constant energy offset:** $\Delta c = \lambda C^2$

For standard one-hot constraints ($\sum_{k=1}^m x_k = 1$, where $w_k = 1$ and $C = 1$):
- $\Delta Q_{kk} = \lambda (1 - 2) = -\lambda$
- $\Delta Q_{kl} = 2 \lambda$ ($k < l$)
- $\Delta c = \lambda$

### 3.2 Penalty Management & Sufficiency Bounds
If penalty multipliers $\lambda$ are set too low, the global minimum of the QUBO may correspond to an infeasible solution that cheats on constraints to lower the objective. The `PenaltyManager` enforces sufficient bounds:

1. **Square Assignment Problem:**
   With matching costs $c_{ij}$:
   \[
   A_{\text{min}} > \max_{(i,j)} c_{ij} - \min_{(i,j)} c_{ij}
   \]
   Recommended default: $A = B = 1.5 \times \Delta c_{\text{max}} + 1.0$.

2. **Travelling Salesperson Problem (TSP):**
   With pairwise distance matrix $D_{ij}$:
   \[
   A_{\text{min}} > \max_{(i,j)} D_{ij} - \min_{(i,j)} D_{ij}
   \]
   Recommended default: $A = B = 1.5 \times D_{\text{max}} + 1.0$.

---

## 4. Problem-Specific QUBO Formulations

### 4.1 Max-Cut
Given an undirected weighted graph $G = (V, E)$ with edge weights $w_{ij}$:
\[
\text{Cut}(x) = \sum_{(i,j) \in E} w_{ij} (x_i + x_j - 2 x_i x_j)
\]
To maximize cut weight via minimization, set $E_{\text{QUBO}}(x) = - \text{Cut}(x)$:
\[
E_{\text{QUBO}}(x) = \sum_{(i,j) \in E} w_{ij} (2 x_i x_j - x_i - x_j)
\]
Summing over all incident edges for each vertex $i \in V$:
- **Linear on-diagonal:** $Q_{ii} = - \text{deg}_w(i) = - \sum_{j \in N(i)} w_{ij}$
- **Quadratic coupling:** $Q_{ij} = 2 w_{ij}$ for $(i, j) \in E$ ($i < j$)
- **Constant offset:** $c = 0.0$

### 4.2 Linear Assignment Problem
Given an $n \times n$ square cost matrix $c_{ij}$ between agents $i$ and tasks $j$:
- **Decision variables:** $x_{ij} \in \{0, 1\}$ ($n^2$ variables in row-major order: $x_{00}, x_{01}, \dots, x_{(n-1)(n-1)}$).
- **Objective:** $\sum_{i=1}^n \sum_{j=1}^n c_{ij} x_{ij}$
- **Row constraints (each agent assigned to exactly 1 task):**
  \[
  P_{\text{row}} = A \sum_{i=1}^n \left( \sum_{j=1}^n x_{ij} - 1 \right)^2
  \]
- **Column constraints (each task assigned to exactly 1 agent):**
  \[
  P_{\text{col}} = B \sum_{j=1}^n \left( \sum_{i=1}^n x_{ij} - 1 \right)^2
  \]
- **Combined QUBO Coefficients:**
  - $Q_{(ij),(ij)} = c_{ij} - A - B$
  - $Q_{(ij),(ik)} = 2A$ for $j < k$ (same row)
  - $Q_{(ij),(kj)} = 2B$ for $i < k$ (same column)
  - Constant offset: $c = n(A + B)$
- **Non-Square Instances:** Rectangular instances are rejected with an explicit error explaining that QUBO matching requires square cost matrices or explicit dummy padding.

### 4.3 Travelling Salesperson Problem (TSP)
Given $n$ cities with distance matrix $D_{ij}$:
- **Decision variables:** $x_{i, p} \in \{0, 1\}$ representing city $i$ visited at position $p \in \{0, \dots, n-1\}$ ($n^2$ variables).
- **Distance objective along cyclic tour:**
  \[
  \sum_{p=0}^{n-1} \sum_{i=1}^n \sum_{j=1, j \ne i}^n D_{ij} x_{i, p} x_{j, (p+1) \bmod n}
  \]
- **City uniqueness penalty (each city visited exactly once):**
  \[
  A \sum_{i=1}^n \left( \sum_{p=0}^{n-1} x_{i, p} - 1 \right)^2
  \]
- **Step uniqueness penalty (each position contains exactly one city):**
  \[
  B \sum_{p=0}^{n-1} \left( \sum_{i=1}^n x_{i, p} - 1 \right)^2
  \]
- **Designated Start Pinning (Optional):**
  If starting city $s$ is fixed at step $0$:
  \[
  P_{\text{start}} = \lambda_{\text{start}} (x_{s, 0} - 1)^2 = \lambda_{\text{start}} (1 - x_{s, 0})
  \]

---

## 5. Analytical QUBO-to-Ising Conversion

### 5.1 Physics Spin Transformation
We map classical binary variables $x_i \in \{0, 1\}$ to Pauli-$Z$ eigenvalues $Z_i \in \{-1, +1\}$ using the standard mapping:
\[
x_i = \frac{1 - Z_i}{2}
\]
Notice:
- When $Z_i = +1$ (spin up $|0\rangle$), $x_i = 0$.
- When $Z_i = -1$ (spin down $|1\rangle$), $x_i = 1$.

### 5.2 Derivation of Hamiltonian Coefficients
Given the upper-triangular QUBO energy function:
\[
E(x) = \sum_{i=1}^n a_i x_i + \sum_{1 \le i < j \le n} b_{ij} x_i x_j + c
\]
Substitute $x_i = \frac{1 - Z_i}{2}$ and $x_j = \frac{1 - Z_j}{2}$:
\[
H(Z) = \sum_i a_i \left( \frac{1 - Z_i}{2} \right) + \sum_{i < j} b_{ij} \left( \frac{1 - Z_i}{2} \right) \left( \frac{1 - Z_j}{2} \right) + c
\]
Expanding the products:
\[
\frac{1 - Z_i}{2} \frac{1 - Z_j}{2} = \frac{1 - Z_i - Z_j + Z_i Z_j}{4}
\]
Group terms by operator order:
1. **Constant Term $C$:**
   \[
   C = c + \frac{1}{2} \sum_{i=1}^n a_i + \frac{1}{4} \sum_{1 \le i < j \le n} b_{ij}
   \]
2. **Linear On-Site Magnetic Fields $h_i$ (multiplying $Z_i$):**
   $Z_i$ receives $-\frac{a_i}{2}$ from the linear term and $-\frac{b_{ij}}{4}$ from every quadratic term containing variable $i$:
   \[
   h_i = -\frac{a_i}{2} - \frac{1}{4} \sum_{j \ne i} b_{ij}
   \]
   where $b_{ij} = b_{ji}$ is the symmetric coupling between $i$ and $j$.
3. **Pairwise Spin Couplings $J_{ij}$ (multiplying $Z_i Z_j$ for $i < j$):**
   \[
   J_{ij} = \frac{b_{ij}}{4}
   \]

The resulting Ising Hamiltonian is:
\[
H(Z) = \sum_{i=1}^n h_i Z_i + \sum_{1 \le i < j \le n} J_{ij} Z_i Z_j + C
\]

---

## 6. Independent Exhaustive Verification Engine

To ensure absolute mathematical rigor and prevent silent formulation errors:
1. **Exhaustive Truth-Table Enumeration:**
   For any problem instance with $n \le 12$ binary variables (up to $2^{12} = 4,096$ states), the `FormulationVerifier` generates all $2^n$ bitstrings $x \in \{0, 1\}^n$.
2. **Dual-Energy Comparison:**
   For each bitstring $x$:
   - Compute classical QUBO energy $E_{\text{QUBO}}(x)$.
   - Map $x \to Z$ via $Z_i = 1 - 2x_i$ and compute Ising energy $H_{\text{Ising}}(Z)$.
   - Assert $|E_{\text{QUBO}}(x) - H_{\text{Ising}}(Z)| < 10^{-6}$.
3. **Cross-Check with Phase 2 Evaluators:**
   For feasible solutions, verify that $E_{\text{QUBO}}(x)$ corresponds to the independently evaluated original objective value (e.g. $-\text{Cut}(x)$ for Max-Cut, matching cost for Assignment, tour distance for TSP).
4. **Feasibility Barrier Verification:**
   Verify that all infeasible bitstrings have penalty energies strictly exceeding feasible optimums, confirming penalty parameter sufficiency.

---

## 7. Phase 5: QAOA Variational Quantum Optimization Engine

### 7.1 Algorithmic Foundations of QAOA
The Quantum Approximate Optimization Algorithm (QAOA) is a hybrid quantum-classical variational algorithm designed to find near-optimal solutions to combinatorial optimization problems mapped to Ising Hamiltonians.

1. **Initial State (Uniform Superposition):**
   Starting with $n$ qubits initialized in $|0\rangle^{\otimes n}$, apply Hadamard gates $H^{\otimes n}$ to generate the equal superposition:
   \[
   |\psi_0\rangle = \frac{1}{\sqrt{2^n}} \sum_{x \in \{0, 1\}^n} |x\rangle
   \]

2. **Alternating Unitary Layers ($p$ depth):**
   For $l = 1, \dots, p$, sequentially apply problem cost and mixer unitaries parameterized by variational angles $\gamma_l \in [0, 2\pi]$ and $\beta_l \in [0, \pi]$:
   \[
   |\psi(\vec{\gamma}, \vec{\beta})\rangle = \prod_{l=1}^p \left( e^{-i \beta_l H_M} e^{-i \gamma_l H_C} \right) |\psi_0\rangle
   \]

3. **Expectation Objective:**
   Evaluate the variational expectation value:
   \[
   F_p(\vec{\gamma}, \vec{\beta}) = \langle \psi(\vec{\gamma}, \vec{\beta}) | H_C | \psi(\vec{\gamma}, \vec{\beta}) \rangle
   \]
   A classical optimization routine iteratively updates $(\vec{\gamma}, \vec{\beta})$ to minimize $F_p$.

---

## 8. QAOA Hamiltonians & Gate Synthesis

### 8.1 Cost Hamiltonian Unitary Decomposition
The cost Hamiltonian $H_C = \sum_i h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + C$ decomposes into commuting single-qubit and two-qubit rotation unitaries:
\[
e^{-i \gamma H_C} = e^{-i \gamma C} \prod_{i=1}^n e^{-i \gamma h_i Z_i} \prod_{1 \le i < j \le n} e^{-i \gamma J_{ij} Z_i Z_j}
\]

Under standard Qiskit gate definitions:
- $R_Z(\phi) = \exp(-i \frac{\phi}{2} Z)$
- $R_{ZZ}(\theta) = \exp(-i \frac{\theta}{2} Z \otimes Z)$

Therefore, the exact required rotation angles are scaled by a factor of 2:
- **Linear term on qubit $i$:** $R_Z(2 \gamma h_i)$
- **Coupling term on qubits $(i, j)$:** $R_{ZZ}(2 \gamma J_{ij})$
- **Global scalar phase:** $e^{-i \gamma C}$

### 8.2 Mixer Hamiltonian Unitary Decomposition
The standard transverse-field mixer is defined as the sum of Pauli-$X$ operators:
\[
H_M = \sum_{i=1}^n X_i
\]
Because $[X_i, X_j] = 0$ for $i \ne j$, the mixer unitary decomposes into independent single-qubit $R_X$ gates:
\[
e^{-i \beta H_M} = \prod_{i=1}^n e^{-i \beta X_i} = \prod_{i=1}^n R_X(2 \beta)
\]

---

## 9. Parameterized Circuit Construction & Resource Limits

The `QAOACircuitBuilder` constructs standard Qiskit `QuantumCircuit` instances parameterized with `ParameterVector("gamma", p)` and `ParameterVector("beta", p)`:
- Uniform Hadamard initialization: $H$ gate on all $n$ qubits.
- Alternating application of cost $U(H_C, \gamma_l)$ and mixer $U(H_M, \beta_l)$ layers for $l = 1, \dots, p$.
- Fast parameter binding via `.assign_parameters()` without rebuilding circuit graphs.
- Measurement mapping: `measure_all()` onto classical registers in little-endian order.

**Platform Resource Safety Guardrails:**
- Qubit ceiling: $n \le 20$ (Qiskit Aer CPU statevector and shot limit).
- Depth ceiling: $p \le 10$.
- Shot ceiling: $\text{shots} \le 50,000$.

---

## 10. Classical Parameter Optimization Loop

The `QAOAOptimizer` implements classical outer-loop optimization over the variational parameters $(\vec{\gamma}, \vec{\beta}) \in \mathbb{R}^{2p}$:
- **Supported Optimizers:**
  - `COBYLA` (Constrained Optimization BY Linear Approximation) — default derivative-free optimizer robust to finite sampling shot noise.
  - `SLSQP` (Sequential Least Squares Programming) — bounded gradient/approximation optimizer.
  - `Nelder-Mead` — downhill simplex direct search method.
  - `L-BFGS-B` — limited-memory quasi-Newton optimization.
- **Initialization Strategies:**
  - `linear_ramp`: Trotterized adiabatic ramp $\gamma_l = \frac{l}{p} \cdot \Delta t$, $\beta_l = (1 - \frac{l}{p}) \cdot \Delta t$.
  - `random`: Uniformly sampled $\gamma_l \in [0, 2\pi]$ and $\beta_l \in [0, \pi]$.
  - `zeros`: Initialization at origin $[0, \dots, 0]$.
- **Expectation Modes:**
  - `statevector`: Exact analytical expectation $\langle \psi | H_C | \psi \rangle$ via Qiskit Aer statevector simulator.
  - `shots`: Empirical expectation computed by sampling $N_{\text{shots}}$ bitstrings and evaluating $\frac{1}{N} \sum_{k} E(x^{(k)})$.

---

## 11. Solution Decoding & Independent Verification

Measurement outcomes from Qiskit Aer are returned as count dictionaries of binary bitstrings.

### 11.1 Little-Endian Bit-Order Mapping
In Qiskit, bitstrings are indexed from right to left (qubit 0 is at index $n-1$, qubit $n-1$ is at index 0):
\[
x_k = \text{int}(\text{bitstring}[n - 1 - k]) \quad \text{for } k = 0, \dots, n-1
\]

### 11.2 Domain-Specific Solution Reconstruction
- **Max-Cut:** Bit 0 maps to Partition Set $V \setminus S$, bit 1 maps to Partition Set $S$.
- **Assignment:** Decision variable $x_{i, j}$ maps agent $i$ to task $j$.
- **TSP:** Decision variable $x_{i, p}$ maps city $i$ to position $p$.

### 11.3 Independent Verification & Best Feasible Candidate Selection
Rather than blindly selecting the most frequently sampled bitstring, `QAOASolutionDecoder`:
1. Evaluates all unique measured bitstrings.
2. Validates hard constraints using Phase 2 constraint validators.
3. Evaluates true problem objective values using Phase 2 independent objective evaluators (`MaxCutEvaluator`, `AssignmentEvaluator`, `TSPEvaluator`).
4. Selects the `best_feasible_solution` based on true problem direction (maximization for Max-Cut, minimization for Assignment/TSP).

---

## 12. Hybrid Quantum-Classical Benchmarking

The `HybridBenchmarkEngine` evaluates QAOA side-by-side against deterministic and heuristic classical solvers:
- **Approximation Ratio ($r$):**
  - For maximization (Max-Cut): $r = \frac{C_{\text{QAOA}}}{C_{\text{exact}}}$.
  - For minimization (Assignment, TSP): $r = \frac{C_{\text{exact}}}{C_{\text{QAOA}}}$.
- **Optimality Gap:** $|f - f^*| / |f^*| \times 100\%$.
- **Computational Budget:** Classical evaluations vs. simulated quantum circuit executions ($N_{\text{evals}} \times \text{shots}$).
- **Scientific Hardware Transparency Guarantee:** All execution records and UI views clearly report that simulations run on CPU Qiskit Aer simulators, with no quantum supremacy claimed.


---

## 13. Phase 6: Adaptive QAOA Research & Dynamic Parameter Strategies

### 13.1 Research Motivation & Paradigm
Standard QAOA fixes circuit depth $p$ before optimization and optimizes $2p$ continuous angles $(\vec{\gamma}, \vec{\beta})$ from random or trotterized initializations using a static classical optimizer. For deeper circuits ($p \ge 2$), standard QAOA faces several fundamental limitations:
1. **Barren plateaus & local minima:** Random initializations in higher-dimensional angle landscapes lead to poor local convergence.
2. **Fixed computational expressibility:** Under-parameterized circuits ($p=1$) cannot represent complex ground states, while arbitrarily high fixed depths ($p \ge 4$) suffer from optimization overhead.
3. **Rigid optimizer schedules:** A single classical optimizer cannot balance broad initial exploratory search with high-precision local refinement.

Phase 6 implements a modular, scientifically grounded **Adaptive QAOA Research Architecture** where layer depth, parameter initializations, and classical optimizers dynamically adapt during optimization based on live energy feedback.

```
       ┌────────────────────────────────────────────────────────┐
       │             Adaptive QAOA Variational Loop             │
       └────────────────────────────────────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ 1. Parameter Initialization (Fourier, Ramp, WarmStart) │
       └────────────────────────────────────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ 2. Layer Construction & Qiskit Aer Circuit Execution   │
       └────────────────────────────────────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ 3. Convergence & Stagnation Monitor (Energy Trajectory)│
       └────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
      [Continue Local]      [Switch Optimizer]     [Expand Depth p->p+1]
      Same depth & solver   Coarse -> Fine local   Warm-start transfer
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ 4. Termination & Independent Phase 2 Solution Decoding │
       └────────────────────────────────────────────────────────┘
```

---

## 14. Adaptive Parameter Initialization Strategies

The `ParameterInitializerFactory` and strategy classes in `backend/app/solvers/quantum/adaptive/initializers.py` generate initial angles $(\vec{\gamma}, \vec{\beta}) \in \mathbb{R}^{2p}$:

### 14.1 Linear Adiabatic Ramp Initializer
Discretizes the adiabatic evolution schedule from driver Hamiltonian $H_M$ to problem Hamiltonian $H_C$:
\[
\gamma_l = \frac{l}{p} \cdot \Delta t, \quad \beta_l = \left(1 - \frac{l}{p}\right) \cdot \Delta t \quad \text{for } l = 1, \dots, p
\]
where $\Delta t = 0.75$ radians by default.

### 14.2 Fourier Parameterization Initializer
Re-parameterizes the $2p$ variational angles using discrete cosine and sine frequency components $\vec{u}, \vec{v} \in \mathbb{R}^q$ (where $q < p$ for deep circuits):
\[
\gamma_l = \sum_{k=1}^q u_k \sin\left[ \left(k - \frac{1}{2}\right) \left(l - \frac{1}{2}\right) \frac{\pi}{p} \right]
\]
\[
\beta_l = \sum_{k=1}^q v_k \cos\left[ \left(k - \frac{1}{2}\right) \left(l - \frac{1}{2}\right) \frac{\pi}{p} \right]
\]
This smooth frequency representation drastically reduces parameter space dimension while enforcing adiabatic continuity.

### 14.3 Warm-Start Initializer
Extracts optimal angles $(\vec{\gamma}^*, \vec{\beta}^*)$ from an existing depth-$p_1$ run or related problem instance, applying dimension-matching interpolation to seed depth $p_2$.

---

## 15. Warm-Start Parameter Transfer & Inter-Depth Interpolation

The `ParameterTransferService` (`backend/app/solvers/quantum/adaptive/transfer.py`) maps optimized angle vectors $(\vec{\gamma}^{(p)}, \vec{\beta}^{(p)})$ to target depth $p+1$ (or cross-instance):

1. **Linear Interpolation:**
   Maps continuous coordinate $t \in [0, 1]$ across layers, creating smooth parameter curves:
   \[
   \gamma^{(p+1)}_k = \text{interp}\left( \frac{k - 1}{p}, \vec{\gamma}^{(p)} \right)
   \]
2. **Layer Padding:**
   Retains first $p$ optimized layers and appends near-zero perturbations for new layer $p+1$.
3. **Adiabatic Extension:**
   Extrapolates the final derivative $\frac{d\gamma}{dl}$ to compute the boundary parameters of the newly inserted layer.

The service performs automated compatibility checks returning a `TransferCompatibilityReport` with a confidence score before applying transitions.

---

## 16. Dynamic Classical Optimizer Scheduling & Arbitration

The `AdaptiveOptimizerController` (`backend/app/solvers/quantum/adaptive/optimizer_controller.py`) manages transitions across classical optimizers:
- **Static Mode:** Maintains a single fixed optimizer throughout the run.
- **Adaptive Fallback Mode:** Optimizes with a fast, derivative-free optimizer (`COBYLA`). Upon detecting energy stagnation exceeding a patience window, smoothly transfers parameter coordinates to a local refinement optimizer (`Nelder-Mead` or `SLSQP`).
- **Multi-Stage Mode:** Runs coarse global simplex exploration followed by high-precision quasi-Newton gradient descent.
- **Audit Logging:** Every optimizer transition is logged with step index, elapsed time, pre-switch energy, and post-switch energy.

---

## 17. Dynamic Circuit Depth Management & Layer Progression

The `AdaptiveDepthManager` (`backend/app/solvers/quantum/adaptive/depth_manager.py`) arbitrates dynamic circuit growth:
- **Growth Trigger:** Layer expansion $p \to p+1$ is triggered when relative energy improvement falls below threshold $\epsilon$ over the stagnation window:
  \[
  \frac{|E_t - E_{t - W}|}{\max(1.0, |E_{t - W}|)} < \epsilon
  \]
- **Warm-Start Injection:** The existing optimal parameters at depth $p$ are smoothly interpolated to initialize the expanded $2(p+1)$ parameter vector.
- **Ceiling Guardrail:** Hard ceiling of $p \le 10$ prevents circuit depth explosion on classical simulators.

---

## 18. Convergence Monitoring & Multi-Objective Termination

The `AdaptiveConvergenceMonitor` (`backend/app/solvers/quantum/adaptive/convergence_monitor.py`) tracks the variational energy trajectory $\langle H_C \rangle_t$ and decides tactical actions:
- `CONTINUE_OPTIMIZATION`: Energy improving sufficiently; continue active optimizer.
- `SWITCH_OPTIMIZER`: Stagnation observed; transition to fallback optimizer.
- `EXPAND_DEPTH`: Optimization stagnated at current depth; expand $p \to p+1$ if under depth ceiling.
- `TERMINATE`: Multi-objective stopping condition satisfied:
  - `CONVERGED`: Energy delta below convergence tolerance $\tau$.
  - `STAGNATED`: Max stagnation patience exhausted at maximum depth ceiling.
  - `MAX_EVALUATIONS_REACHED`: Evaluation budget consumed.
  - `TIMEOUT`: Execution time exceeded.
  - `CANCELLED`: Cooperative user cancellation requested.

---

## 19. Unified Adaptive QAOA Execution Pipeline

The `AdaptiveQAOAExecutionPipeline` (`backend/app/solvers/quantum/adaptive/pipeline.py`) coordinates all components:
- Thread-pooled asynchronous background worker pool (`qopt-aqaoa-`).
- In-flight cooperative cancellation token passing.
- Persistent state tracking across `PENDING`, `RUNNING`, `COMPLETED`, `CANCELLED`, `FAILED`.
- MongoDB storage in `adaptive_executions` with memory fallback.
- Little-endian measurement decoding with independent Phase 2 candidate solution verification.

---

## 20. Empirical Benchmarking & Ablation Study Engine

The `AdaptiveBenchmarkEngine` (`backend/app/solvers/quantum/adaptive/benchmarking.py`) evaluates the scientific validity of each adaptive component:
- **Baseline:** Standard fixed-depth QAOA.
- **Full Adaptive:** Warm-start + dynamic depth + adaptive optimizer fallback.
- **Ablation Studies:**
  - `ablation_no_warm_start`: Dynamic depth with random initialization (isolates value of warm-starts).
  - `ablation_no_dynamic_depth`: Adaptive optimizer on fixed depth (isolates value of depth growth).
  - `ablation_no_optimizer_switching`: Dynamic depth with static optimizer (isolates value of optimizer switching).
  - `ablation_fourier`: Direct comparison of discrete frequency parameterization vs angle optimization.
- **Automated Insights Synthesis:** Produces empirical scientific findings on which components contribute most to solution quality, approximation ratio $r$, and evaluation efficiency.
