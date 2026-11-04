# Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React, TypeScript, Vite | Web application |
| Styling | Tailwind CSS | Responsive design |
| Components | shadcn/ui | Accessible UI |
| Animation | Framer Motion | Motion |
| Graphs | React Flow or Cytoscape.js | Graph problems |
| Charts | Plotly | Scientific visualizations |
| Backend | Python, FastAPI | REST API |
| Validation | Pydantic | Typed validation |
| Quantum | Qiskit, Qiskit Aer | Circuit construction and simulation |
| Numerics | NumPy, SciPy | Numerical operations |
| Classical optimization | OR-Tools, SciPy | Baselines |
| Database | MongoDB | Persistence |
| Background jobs | Celery and Redis, or equivalent | Long computations |
| Testing | Pytest, Vitest, React Testing Library | Automated tests |

## Dependency policy
Pin dependencies, verify Qiskit/Aer compatibility, avoid unnecessary packages, keep secrets in environment variables, and commit lockfiles and `.env.example` files—not real secrets.

## Backend `.env.example`
```dotenv
APP_ENV=development
MONGODB_URI=
MONGODB_DATABASE=q_optimize
JWT_SECRET_KEY=replace_me
REDIS_URL=redis://localhost:6379/0
FRONTEND_ORIGIN=http://localhost:5173
```

## Frontend `.env.example`
```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Local development
Frontend: `npm install` then `npm run dev`.
Backend: create a virtual environment, install `requirements.txt`, then run `uvicorn app.main:app --reload`.
