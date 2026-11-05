# Q-Optimize

> **An AI-Assisted Hybrid Quantum-Classical Optimization Framework with Adaptive QAOA and Intelligent Solver Selection**

[![Status: Phase 3 Complete](https://img.shields.io/badge/Status-Phase%203%20QUBO%20%26%20Ising%20Formulation-38BDF8.svg)](#)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](#)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](#)
[![React: 18](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript-61DAFB.svg)](#)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](#)
[![Tests: 80 Pytest | 12 Vitest](https://img.shields.io/badge/Tests-92%20Passing-emerald.svg)](#)

---

## 1. Overview

**Q-Optimize** is a scientific research and computing platform designed to assist researchers, educators, and developers in describing combinatorial optimization problems, generating verified QUBO and Ising mathematical formulations, executing quantum simulation algorithms (QAOA) alongside exact and heuristic classical baselines, and evaluating solutions with independent mathematical verification.

### Core Principles
- **Mathematical Correctness Before Polish:** Formulations, constraint penalties, and variable orders are verified against exhaustive small-instance truth tables.
- **Upper-Triangular Storage Standard:** All QUBO quadratic terms strictly enforce $i < j$ storage, eliminating double-counting and off-diagonal ambiguity.
- **Analytical Spin Mapping:** Transformations from binary variables $x_i \in \{0, 1\}$ to Pauli-$Z$ spins $Z_i \in \{-1, +1\}$ are exact and mathematically verified across all $2^n$ states.
- **Independent Evaluator Truth:** Solution candidates from any solver are re-evaluated by an independent evaluator directly against the canonical problem definition.
- **Scientific Reproducibility:** Every experiment preserves problem instances, random seeds, optimizer iterations, library versions, and raw bitstring traces.
- **Zero Fabricated Metrics:** No simulated advantage or pseudo-quantum execution is presented as real physical quantum hardware advantage.

---

## 2. Platform Architecture

```text
Q-Optimize/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/           # Versioned REST endpoints (health, problems, formulations, experiments)
│   │   ├── core/             # Configuration, logging, CORS middleware
│   │   ├── domain/           # Canonical problem schemas & formulation domain models
│   │   ├── db/               # MongoDB manager with in-memory local fallback
│   │   ├── services/         # Problem & formulation lifecycle services
│   │   ├── evaluation/       # Independent objective evaluator & constraint validation engine
│   │   ├── formulations/     # QUBO builders, penalty managers, Ising converters, verification engine
│   │   ├── solvers/          # Classical & QAOA solver interfaces (Phases 4 & 5)
│   │   └── workers/          # Background task queue interfaces (Phase 8)
│   └── tests/                # Pytest unit, constraint, formulation, and API test suite (80 tests)
├── frontend/                 # React 18 + TypeScript + Vite frontend
│   └── src/
│       ├── app/              # App root and view management
│       ├── components/ui/    # Accessible dark-first scientific UI component library
│       ├── components/layout/# AppLayout, Sidebar (9 workspace tabs), Header
│       ├── features/         # Problem editors, SolutionEvaluatorModal, Formulation Studio components
│       │   ├── problem-builder/     # MaxCutEditor, AssignmentEditor, TSPEditor
│       │   └── formulation-studio/  # QuboHeatmap, IsingInspector, VerificationPanel
│       ├── pages/            # Overview, ProblemBuilder, FormulationStudio, Lab Previews, Learn, Settings
│       ├── services/         # Centralized API service and typed endpoints (problemService, formulationService)
│       ├── hooks/            # useBackendHealth polling and diagnostic hook
│       └── tests/            # Vitest and Testing Library test suite (12 tests)
├── research/                 # Reproducible research datasets, configs, and notebooks
├── docs/                     # Supplemental documentation
└── project_docs/             # Canonical project requirements and specifications
```

---

## 3. Implemented Capabilities (Phases 1, 2, & 3)

### Phase 3: QUBO Generation, Constraint Penalties & Ising Hamiltonian Modeling
1. **Canonical QUBO Builder & Representation:**
   - Universal energy function:
     $$E_{\text{QUBO}}(x) = \sum_i Q_{ii} x_i + \sum_{i < j} Q_{ij} x_i x_j + c$$
   - Enforces upper-triangular indexing ($i \le j$) with automatic normalization of symmetric off-diagonal additions ($Q_{ji} \to Q_{ij}$).
   - Reusable squared constraint expansion: converts expressions of form $P = \lambda (\sum_k w_k x_k - C)^2$ into exact linear, quadratic, and constant contributions without numerical drift.
   - Dual export capabilities: dense 2D matrices (upper-triangular or symmetric) and sparse dictionary mappings with variable ordering metadata.

2. **Problem-Specific QUBO Generators:**
   - **Max-Cut:**
     Minimization mapping $E_{\text{QUBO}}(x) = - \text{Cut}(x)$, yielding $Q_{ii} = -\text{deg}_w(i)$, $Q_{ij} = 2 w_{ij}$ for $(i, j) \in E$, offset $c = 0.0$.
   - **Square Assignment Problem:**
     Enforces one-to-one matching via row penalties $A \sum_i (\sum_j x_{ij} - 1)^2$ and column penalties $B \sum_j (\sum_i x_{ij} - 1)^2$. Non-square matrices are strictly rejected with actionable diagnostic errors.
   - **Travelling Salesperson Problem (TSP):**
     $n^2$ position variables $x_{i, p}$ indicating city $i$ at step $p$. Objective encodes distance along cyclic transition $((p+1) \bmod n)$. Penalties enforce exactly one city per step and one step per city, plus optional designated start pinning ($x_{\text{start}, 0} = 1$).

3. **Penalty Management Module:**
   - Reusable `PenaltyManager` calculating mathematically proven sufficiency lower bounds:
     $$A_{\text{min}}^{\text{Assignment}} > \max_{(i,j)} c_{ij} - \min_{(i,j)} c_{ij}$$
     $$A_{\text{min}}^{\text{TSP}} > \max_{(i,j)} D_{ij} - \min_{(i,j)} D_{ij}$$
   - Provides default recommendations, warning thresholds, and validation of user-specified penalty multipliers.

4. **Analytical QUBO-to-Ising Conversion Engine:**
   - Applies the standard physics convention $x_i = \frac{1 - Z_i}{2}$ where Pauli-$Z$ eigenvalues $Z_i \in \{-1, +1\}$ correspond to classical binary states $x_i \in \{0, 1\}$.
   - Exact mathematical derivation for on-site magnetic fields $h_i$, spin couplings $J_{ij}$, and energy offset $C$:
     $$h_i = -\frac{a_i}{2} - \frac{1}{4} \sum_{j \ne i} b_{ij}$$
     $$J_{ij} = \frac{b_{ij}}{4}$$
     $$C = c + \frac{1}{2} \sum_i a_i + \frac{1}{4} \sum_{i < j} b_{ij}$$
   - Generates formatted LaTeX Hamiltonian expressions and spin mapping lookup tables.

5. **Exhaustive Truth-Table Verification Module:**
   - For instances with $n \le 12$ variables (up to $4,096$ states), the backend enumerates all $2^n$ binary bitstrings.
   - Verifies numerical equivalence between $E_{\text{QUBO}}(x)$ and $H_{\text{Ising}}(Z)$ to within tolerance $10^{-6}$.
   - Cross-checks feasible state energies against the Phase 2 independent objective evaluators to prove formulation fidelity.

6. **Interactive Formulation Studio (Frontend):**
   - High-contrast interactive QUBO heatmap displaying linear on-diagonal terms and quadratic off-diagonal couplings with coordinate tooltips.
   - Ising Spin Inspector rendering LaTeX Hamiltonians, local fields $h_i$, and pairwise couplings $J_{ij}$.
   - Live penalty parameter sliders with dynamic bounds checking.
   - One-click exhaustive mathematical verification panel displaying state counts, minimum energies, and proof summaries.
   - Multi-format formulation export: JSON dense matrix, sparse terms dictionary, and LaTeX equation.

---

## 4. API Endpoints (Phase 3 Active)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health and MongoDB/memory status |
| `GET` | `/api/v1/problems/types` | List supported problem families with formulas and constraints |
| `POST` | `/api/v1/problems/validate` | Validate an ad-hoc problem definition without saving |
| `POST` | `/api/v1/problems/evaluate-direct` | Evaluate a candidate solution against an ad-hoc instance |
| `POST` | `/api/v1/problems` | Create and validate a canonical problem |
| `GET` | `/api/v1/problems` | List registered problems |
| `GET` | `/api/v1/problems/{id}` | Retrieve problem definition by ID |
| `GET` | `/api/v1/problems/{id}/metadata` | Retrieve structural statistics and canonical metadata |
| `POST` | `/api/v1/problems/{id}/validate` | Validate stored problem against domain constraints |
| `POST` | `/api/v1/problems/{id}/evaluate` | Evaluate candidate solution against stored problem |
| `POST` | `/api/v1/problems/parse-draft` | Natural language problem drafting (draft-only, human-confirmed) |
| `POST` | `/api/v1/formulations/generate` | Generate QUBO and Ising formulation for stored problem or ad-hoc instance |
| `POST` | `/api/v1/formulations/qubo` | Generate standalone QUBO model with custom penalty multipliers |
| `POST` | `/api/v1/formulations/ising` | Generate standalone Ising Hamiltonian from QUBO model |
| `POST` | `/api/v1/formulations/verify` | Exhaustively verify formulation energy against Ising and original objective ($n \le 12$) |
| `GET` | `/api/v1/formulations/{id}` | Retrieve saved formulation by ID |
| `GET` | `/api/v1/formulations/{id}/metadata`| Retrieve formulation metadata, variable counts, and assumptions |
| `GET` | `/api/v1/formulations/{id}/export` | Export formulation in `dense`, `sparse`, `ising`, or `full` format |

---

## 5. Getting Started

### Prerequisites
- **Python:** 3.12+
- **Node.js:** v20+ / v22+
- **npm:** 10+

### Backend Setup

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Running Test Suites

```bash
# Backend test suite (80 tests across schemas, evaluators, constraints, QUBO, Ising, verification, and APIs)
python -m pytest backend/tests -v

# Frontend test suite (12 tests across App shell, Problem Builder, and Formulation Studio)
node -e "process.chdir('frontend'); require('child_process').execSync('npm.cmd run test', {stdio: 'inherit'});"

# Production build check
node -e "process.chdir('frontend'); require('child_process').execSync('npm.cmd run build', {stdio: 'inherit'});"
```

---

## 6. Known Limitations (Phase 3 Boundaries)
- **Exhaustive State Verification:** The verification engine runs exhaustive truth tables on up to $n = 12$ variables ($4,096$ states) to prevent timeouts. Larger instances rely on structural property checks.
- **Solvers and Circuits:** Classical solvers (SA, Tabu, GA, Branch & Bound) and Quantum QAOA circuits (AerSimulator, ansatz layers) remain strictly scheduled for Phases 4 and 5.
- **Natural Language Parsing:** Remains strictly draft-only; human confirmation is mandatory before canonical creation.

---

## 7. License

Licensed under the MIT License. Developed for research and educational purposes.
