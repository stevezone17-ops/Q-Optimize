# Q-Optimize

> **An AI-Assisted Hybrid Quantum-Classical Optimization Framework with Adaptive QAOA and Intelligent Solver Selection**

[![Status: Phase 2 Complete](https://img.shields.io/badge/Status-Phase%202%20Problem%20Domain-38BDF8.svg)](#)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](#)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](#)
[![React: 18](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript-61DAFB.svg)](#)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](#)
[![Tests: 52 Pytest | 7 Vitest](https://img.shields.io/badge/Tests-59%20Passing-emerald.svg)](#)

---

## 1. Overview

**Q-Optimize** is a scientific research and computing platform designed to assist researchers, educators, and developers in describing combinatorial optimization problems, generating verified QUBO and Ising mathematical formulations, executing quantum simulation algorithms (QAOA) alongside exact and heuristic classical baselines, and evaluating solutions with independent mathematical verification.

### Core Principles
- **Mathematical Correctness Before Polish:** Formulations, constraint penalties, and variable orders are verified against exhaustive small-instance truth tables.
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
│   │   ├── domain/           # Canonical problem schemas (Max-Cut, Assignment, TSP)
│   │   ├── db/               # MongoDB manager with in-memory local fallback
│   │   ├── services/         # Problem validation and draft parsing services
│   │   ├── evaluation/       # Independent objective evaluator & constraint validation engine
│   │   ├── formulations/     # Formulation interfaces (Phase 3)
│   │   ├── solvers/          # Classical & QAOA solver interfaces (Phases 4 & 5)
│   │   └── workers/          # Background task queue interfaces (Phase 8)
│   └── tests/                # Pytest unit, constraint, and API test suite (52 tests)
├── frontend/                 # React 18 + TypeScript + Vite frontend
│   └── src/
│       ├── app/              # App root and view management
│       ├── components/ui/    # Accessible dark-first scientific UI component library
│       ├── components/layout/# AppLayout, Sidebar (9 workspace tabs), Header
│       ├── features/         # MaxCutEditor, AssignmentEditor, TSPEditor, SolutionEvaluatorModal
│       ├── pages/            # LandingPage, Overview, ProblemBuilder, Lab Previews, Learn, Settings
│       ├── services/         # Centralized API service and typed endpoints
│       ├── hooks/            # useBackendHealth polling and diagnostic hook
│       └── tests/            # Vitest and Testing Library test suite (7 tests)
├── research/                 # Reproducible research datasets, configs, and notebooks
├── docs/                     # Supplemental documentation
└── project_docs/             # Canonical project requirements and specifications
```

---

## 3. Implemented Capabilities (Phases 1 & 2)

### Phase 2: Problem Domain & Independent Optimization Modeling
1. **Canonical Optimization Problem Domain:**
   - Standardized representation for optimization problems: identifier, name, type, decision variables (`VariableSpec`), mathematical objective (`ObjectiveSpec`), formal constraints (`ConstraintSpec`), metadata, and validation status.
   - Decoupled from solver algorithms (QAOA, classical heuristics).

2. **Mathematical Problem Models:**
   - **Max-Cut:**
     $$\max \sum_{(i,j)\in E} w_{ij}(x_i+x_j-2x_ix_j) \quad \text{where } x_i \in \{0,1\}$$
     Validates unique vertices, endpoints, weighted/unweighted edges ($w=1.0$ default), non-finite weights, duplicate edges, self-loops, and disconnected graphs.
   - **Linear Assignment Problem:**
     $$\min \sum_{i=1}^n \sum_{j=1}^m c_{ij}x_{ij} \quad \text{where } x_{ij} \in \{0,1\}$$
     Validates agent/task identifiers, square and rectangular cost matrices, rejects invalid/NaN costs, verifies 1-to-1 matching feasibility.
   - **Travelling Salesperson Problem (TSP):**
     $$\min \sum_{k=0}^{N-1} D[\text{tour}[k], \text{tour}[k+1]] \quad \text{with } \text{tour}[N] = \text{tour}[0]$$
     Validates city identifiers, square non-negative distance matrices with zero diagonal, symmetric/asymmetric metrics, optional designated starting city, and closed Hamiltonian cycles.

3. **Independent Objective Evaluation Engine:**
   - `MaxCutEvaluator`: Calculates crossing edge weight sum, cut fraction, partitions ($S_0, S_1$), and verifies complete binary node assignment.
   - `AssignmentEvaluator`: Calculates total matching cost, verifies agent and task usage bounds, returns assignment pairs and unassigned entities.
   - `TSPEvaluator`: Calculates total tour distance, validates Hamiltonian cycle traversal, verifies return to start, and checks designated starting city constraints.
   - `EvaluatorFactory`: Dynamic resolver mapping problem types to independent evaluators.

4. **Reusable Constraint Validation Engine:**
   - `ConstraintValidator`: Tests binary domain constraints ($x_i \in \{0, 1\}$), complete graph partitions, 1-to-1 matching constraints (no duplicate agents/tasks), and Hamiltonian tour constraints (no duplicate visits, no omitted cities, closed loop).
   - Returns structured `ConstraintViolation` objects detailing constraint ID, explanation, expected, and actual values.

5. **Structural Statistics & Metadata Extraction:**
   - Graph density, edge weights (min, max, average), vertex degree distribution, and connected components count (BFS) for Max-Cut.
   - Agent/task counts, squareness, and cost statistics for Assignment.
   - Distance symmetry check, min/max/average distance, and edge counts for TSP.

6. **Interactive Solution Evaluator in Frontend:**
   - Dedicated modal in the Problem Builder allowing researchers to configure candidate solutions (partitions, agent matchings, or tour paths) and evaluate them in real time against the backend independent evaluator.
   - Displays feasibility badges, exact objective values, violation details, and domain breakdowns.

---

## 4. API Endpoints (Phase 2 Active)

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
# Backend test suite (52 tests across schemas, evaluators, constraints, APIs)
python -m pytest backend/tests -v

# Frontend test suite (7 tests)
node -e "process.chdir('frontend'); require('child_process').execSync('npm.cmd run test', {stdio: 'inherit'});"

# Production build check
node -e "process.chdir('frontend'); require('child_process').execSync('npm.cmd run build', {stdio: 'inherit'});"
```

---

## 6. Known Limitations (Phase 2 Boundaries)
- **Solvers and Formulations:** QUBO/Ising matrix generation (Phase 3), Classical heuristic solvers (Phase 4), and QAOA circuit simulations (Phase 5) are deliberately not implemented in this phase to preserve clean architectural boundaries.
- **Natural Language Parsing:** Remains strictly draft-only; human confirmation is mandatory before canonical creation.
- **Tour Coordinates:** Planar 2D visualization coordinates for TSP are optional; distance matrices serve as the primary source of truth.

---

## 7. License

Licensed under the MIT License. Developed for research and educational purposes.
