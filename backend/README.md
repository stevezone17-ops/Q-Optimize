# Q-Optimize Backend

FastAPI Python backend providing combinatorial optimization, mathematical formulations (QUBO/Ising), classical solvers (Exact, GA, SA), quantum simulation (QAOA, Adaptive QAOA), AI recommendations, and independent verification.

---

## 1. Prerequisites

- **Python:** 3.12 (Recommended: Python 3.12.3+)
- **Virtual Environment:** Dedicated `.venv` in `backend/`

---

## 2. Virtual Environment Setup

### PowerShell (Windows)

```powershell
# Navigate to the backend directory
cd D:\Q-Optimize\backend

# Create virtual environment with Python 3.12 (if not already created)
py -3.12 -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install all backend dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **Note for PowerShell execution policy:**
> If script execution is restricted on your machine, enable it for the current process:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

### Linux / macOS / Bash

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Backend Startup

### Option A — One-Command Automated Startup (Recommended)

From `D:\Q-Optimize\backend`:
```powershell
.\start.ps1
```

From root `D:\Q-Optimize`:
```powershell
.\start-backend.ps1
```

The startup script automatically:
1. Detects project paths and the virtual environment (`.venv`).
2. Activates `.venv` if not already active.
3. Displays active Python path and version.
4. Verifies all required dependencies.
5. Sets `PYTHONPATH` correctly.
6. Launches FastAPI via Uvicorn with auto-reload.

Custom host or port:
```powershell
.\start.ps1 -HostName 0.0.0.0 -Port 8000
```

### Option B — Manual Uvicorn Command

Once `.venv` is activated:
```powershell
cd D:\Q-Optimize\backend
uvicorn app.main:app --reload --port 8000
```

---

## 4. Endpoints & Documentation

Once the server is running:
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Specification:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Liveness Probe:** [http://localhost:8000/health/live](http://localhost:8000/health/live)
- **Readiness Probe:** [http://localhost:8000/health/ready](http://localhost:8000/health/ready)
- **System Health:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 5. Running Automated Tests

With `.venv` active:
```powershell
# Run full backend test suite (382 tests)
pytest tests -v

# Run with summary only
pytest tests -q
```
