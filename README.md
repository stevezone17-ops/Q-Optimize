# Q-Optimize

> **An AI-Assisted Hybrid Quantum-Classical Optimization Framework with Adaptive QAOA and Intelligent Solver Selection**

[![Status: Phase 1 Complete](https://img.shields.io/badge/Status-Phase%201%20Foundation-38BDF8.svg)](#)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](#)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](#)
[![React: 18](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript-61DAFB.svg)](#)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](#)

---

## 1. Overview

**Q-Optimize** is a scientific research and computing platform designed to assist researchers, educators, and developers in describing combinatorial optimization problems, generating verified QUBO and Ising mathematical formulations, executing quantum simulation algorithms (QAOA) alongside exact and heuristic classical baselines, and evaluating solutions with independent mathematical verification.

### Core Principles
- **Mathematical Correctness Before Polish:** Formulations, constraint penalties, and variable orders are verified against exhaustive small-instance truth tables.
- **Independent Evaluator Truth:** Solution candidates from any solver are re-evaluated by an independent evaluator directly against the canonical problem definition.
- **Scientific Reproducibility:** Every experiment preserves problem instances, random seeds, optimizer iterations, library versions, and raw bitstring traces.
- **Zero Fabricated Metrics:** No simulated advantage or pseudo-quantum execution is presented as real physical quantum hardware advantage.

---

## 2. Platform Architecture (Phase 1 Foundation)

```text
Q-Optimize/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/           # Versioned REST endpoints (health, problems, formulations, experiments)
│   │   ├── core/             # Configuration, logging, CORS middleware
│   │   ├── domain/           # Canonical problem schemas (Max-Cut, Assignment, TSP)
│   │   ├── db/               # MongoDB manager with in-memory local fallback
│   │   ├── services/         # Problem validation and draft parsing services
│   │   ├── formulations/     # Formulation interfaces (Phase 3)
│   │   ├── solvers/          # Classical & QAOA solver interfaces (Phases 4 & 5)
│   │   ├── evaluation/       # Independent evaluator interfaces (Phase 2)
│   │   └── workers/          # Background task queue interfaces (Phase 8)
│   └── tests/                # Pytest unit and integration test suite
├── frontend/                 # React 18 + TypeScript + Vite frontend
│   └── src/
│       ├── app/              # App root and view management
│       ├── components/ui/    # Accessible dark-first scientific UI component library
│       ├── components/layout/# AppLayout, Sidebar (9 workspace tabs), Header
│       ├── features/         # MaxCutEditor, AssignmentEditor, TSPEditor, NaturalLanguageDraft
│       ├── pages/            # LandingPage, Overview, ProblemBuilder, Lab Previews, Learn, Settings
│       ├── services/         # Centralized API service and typed endpoints
│       ├── hooks/            # useBackendHealth polling and diagnostic hook
│       └── tests/            # Vitest and Testing Library test suite
├── research/                 # Reproducible research datasets, configs, and notebooks
├── docs/                     # Supplemental documentation
└── project_docs/             # Canonical project requirements and specifications
```

---

## 3. Implemented Capabilities (Phase 1)

1. **Scientific Dark-First UI/UX:**
   - Deep midnight navy (`#06080F`), slate charcoal (`#0A0F1D`), electric sky-blue accents (`#38BDF8`), violet highlights (`#8B5CF6`), and amber telemetry tags (`#F59E0B`).
   - Accessible responsive layout with subtle scientific grid patterns and smooth Framer Motion transitions.

2. **Landing Page:**
   - Interactive hero explaining hybrid quantum-classical computing.
   - 4-stage optimization workflow breakdown (Canonical Definition &rarr; QUBO/Ising &rarr; Dual Solvers &rarr; Independent Verification).
   - Overview of combinatorial problem families and classical baselines.

3. **Workspace & Navigation:**
   - Full 9-section sidebar: **Overview**, **Problem Builder**, **Formulation Studio**, **Quantum Lab**, **Classical Lab**, **Comparison Lab**, **My Experiments**, **Learn**, and **Settings**.
   - Real-time backend connectivity pill indicating FastAPI status and latency.

4. **Interactive Problem Builder:**
   - **Max-Cut:** Vertices manager, weighted edge list with duplicate & self-loop prevention, live topology graph canvas preview ($|V|$, $|E|$, density, total weight).
   - **Assignment Problem:** Agent and task dimension manager, interactive cost matrix ($C_{ij}$) with row/column checks.
   - **Travelling Salesperson (TSP):** City manager, symmetric/asymmetric distance matrix ($D_{ij}$), non-zero diagonal prevention.
   - **Natural Language Draft:** Draft-only workflow requiring explicit human verification and confirmation before persistence.
   - **Review & Confirmation Screen:** Displays extracted entities, objective direction, constraints, and assumptions prior to database persistence.

5. **FastAPI Backend:**
   - Versioned REST API (`/api/v1`) with `/health` diagnostic endpoint.
   - Strict Pydantic v2 schemas and validation for all three initial problem types.
   - Database manager with MongoDB connectivity and automatic in-memory fallback for offline development.
   - Structured logging, CORS middleware, and safe global exception handling.

---

## 4. Getting Started

### Prerequisites
- **Python:** 3.12+
- **Node.js:** v20+ / v22+
- **npm:** 10+

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (optional but recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment example
copy .env.example .env

# Run FastAPI development server
uvicorn backend.app.main:app --reload --port 8000
```

The API documentation will be available at `http://localhost:8000/docs`.

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The web application will be live at `http://localhost:5173`.

---

## 5. Running Automated Tests

### Backend Test Suite
```bash
python -m pytest backend/tests -v
```
Validates:
- Health and environment diagnostics endpoints (`/health` and `/api/v1/health`).
- Pydantic schema validation for Max-Cut, Assignment, and TSP (including self-loop detection, dimension mismatch, and diagonal checks).
- Problem creation, retrieval, and natural language draft extraction endpoints.

### Frontend Test Suite
```bash
cd frontend
npm run test
```
Validates:
- Landing page rendering and hero banner assertions.
- Workspace navigation and sidebar switching.
- Problem Builder inputs, family tab switching, and review modal presentation.

### Production Build & Type Checking
```bash
cd frontend
npm run build
```

---

## 6. Implementation Roadmap

- [x] **Phase 0:** Project setup, environment configuration, health endpoints.
- [x] **Phase 1:** Platform foundation, scientific dark-first UI, Problem Builder, draft parsing, API integration.
- [ ] **Phase 2:** Canonical problem domain evaluators and feasibility validators.
- [ ] **Phase 3:** QUBO and Ising formulation engine with exhaustive equivalence testing.
- [ ] **Phase 4:** Classical solver baselines (Exact small-instance, Genetic Algorithm, Simulated Annealing).
- [ ] **Phase 5:** Quantum engine with Qiskit Aer QAOA statevector simulation.
- [ ] **Phase 6:** Adaptive QAOA parameter strategies.
- [ ] **Phase 7:** Machine learning-assisted solver recommendation.
- [ ] **Phase 8:** Background worker experiment queue, comparison analytics, and export.
- [ ] **Phase 9:** Security hardening, resource quotas, and final delivery.

---

## 7. License

Licensed under the MIT License. Developed for research and educational purposes.
