# Stage 10.9 — Project Evaluation Checklist & Troubleshooting

## 1. Required Software
- Python `3.12+` (`pip install -r backend/requirements.txt`)
- Node.js `20+` & npm `10+`
- MongoDB `7.0` (optional; automatic in-memory fallback is active if MongoDB is stopped)
- Docker & Docker Compose (optional, for containerized demo)

## 2. Environment Configuration
- Copy `.env.example` to `.env` (for local dev, `APP_ENV=development` and a non-empty `JWT_SECRET_KEY`).
- In production (`APP_ENV=production`), `DEBUG` must be `false` and `JWT_SECRET_KEY` must be a strong 32+ char secret.

## 3. Startup Commands
```powershell
# Terminal 1: Backend API
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Frontend UI
npm run dev --prefix frontend
```

## 4. Verification Before Evaluation
```powershell
python -m pytest backend/tests -q      # Expected: 382 passed
npm run test --prefix frontend -- --run # Expected: 61 passed
npm run build --prefix frontend         # Expected: 0 errors
```

## 5. Backup Plan & Failure Scenarios
- **MongoDB unavailable:** Backend automatically activates `in_memory_fallback` so all UI & solver demos still work seamlessly.
- **Slow QAOA simulation during live demo:** Keep demo graphs at $N \le 6$ nodes and `shots=512, max_evaluations=30` (completes in `< 1.5s`).
- **Pre-generated Offline Evidence:** All 12 figures (`research/figures/`), `FINAL_YEAR_PROJECT_REPORT.pdf`, and JSON benchmark traces are saved locally in `research/`.
