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
