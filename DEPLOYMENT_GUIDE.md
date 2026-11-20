# Q-Optimize Deployment Guide

This guide covers deploying Q-Optimize using Docker Compose for production environments.

---

## Prerequisites

- **Docker** ≥ 24.0 ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** ≥ 2.20 (included with Docker Desktop)
- **Git** (to clone the repository)
- One of:
  - **MongoDB Atlas** account (recommended for production)
  - **Local MongoDB** (for self-hosted or development deployments)

---

## Environment Variables

Create a `.env` file at the repository root (copy from `.env.example` and fill in values):

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET_KEY` | ✅ Yes | — | Secret key for JWT signing (min 32 chars, production must not use obvious values) |
| `MONGODB_URI` | ✅ Yes | `mongodb://mongodb:27017/q_optimize` | MongoDB connection string |
| `APP_ENV` | No | `production` | Application environment (`development`, `testing`, `production`) |
| `DEBUG` | No | `false` | Enable debug mode (must be `false` in production) |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000,http://localhost:80` | Comma-separated list of allowed CORS origins |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

> [!CAUTION]
> Never commit `.env` to version control. It is listed in `.gitignore` and `.dockerignore`.

---

## Quick Start with Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/stevezone17-ops/Q-Optimize.git
cd Q-Optimize
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set JWT_SECRET_KEY and MONGODB_URI
```

### 3. Build and start all services

```bash
docker-compose up --build -d
```

### 4. Verify services are healthy

```bash
docker-compose ps
```

You should see `q-optimize-mongodb`, `q-optimize-backend`, and `q-optimize-frontend` all with status `running (healthy)`.

### 5. Access the application

- **Frontend:** http://localhost
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs

---

## MongoDB Atlas Setup (Recommended for Production)

1. **Create a free cluster** at [cloud.mongodb.com](https://cloud.mongodb.com)
2. **Create a database user** with read/write access to `q_optimize`
3. **Whitelist your IP** (or `0.0.0.0/0` for Docker-deployed apps)
4. **Get your connection string** from: Connect → Connect your application → Python → Copy the URI
5. Set in `.env`:
   ```
   MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/q_optimize?retryWrites=true&w=majority
   ```

---

## Health Check Verification

After startup, verify the backend is healthy:

```bash
# Liveness probe (is the process running?)
curl -f http://localhost:8000/health/live
# Expected: {"status": "alive", ...}

# Readiness probe (can it serve traffic?)
curl -f http://localhost:8000/health/ready
# Expected: {"status": "ready", "database": "connected", ...}
```

---

## Service Architecture

```
                    ┌─────────────────┐
   Browser ──────▶  │  Frontend :80   │  nginx:alpine
                    │  (nginx)        │
                    └────────┬────────┘
                             │ /api/ proxy
                    ┌────────▼────────┐
                    │  Backend :8000  │  python:3.12-slim
                    │  (FastAPI/      │
                    │   uvicorn)      │
                    └────────┬────────┘
                             │ MongoDB protocol
                    ┌────────▼────────┐
                    │  MongoDB :27017 │  mongo:7.0
                    │                 │
                    └─────────────────┘
```

---

## Updating the Deployment

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart only the changed services
docker-compose up --build -d

# Or to force a full rebuild
docker-compose down
docker-compose up --build -d
```

---

## Rollback Procedure

If a deployment causes issues:

```bash
# Step 1: Stop the current deployment
docker-compose down

# Step 2: Identify the last good commit
git log --oneline -10

# Step 3: Revert to the previous commit
git revert HEAD
# Or to a specific commit:
# git revert <bad-commit-hash>

# Step 4: Rebuild and start with reverted code
docker-compose up --build -d
```

---

## Troubleshooting

### Container won't start

```bash
# Check container logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb
```

**Common causes:**
- Missing or invalid `JWT_SECRET_KEY` in `.env`
- Port 80 or 8000 already in use on the host
- Insufficient disk space for Docker images

### Database connection errors

**Symptoms:** Backend health check shows `"database": "disconnected"`

**Steps:**
1. Verify `MONGODB_URI` is set correctly in `.env`
2. For Atlas: confirm IP whitelist includes your Docker host IP
3. Check MongoDB container health: `docker-compose ps mongodb`
4. Test connection manually:
   ```bash
   docker-compose exec backend python -c "from motor.motor_asyncio import AsyncIOMotorClient; print('OK')"
   ```

### CORS issues (browser console shows CORS errors)

**Symptoms:** Frontend cannot reach the backend API

**Steps:**
1. Confirm `ALLOWED_ORIGINS` in `.env` includes the exact frontend origin (e.g., `http://localhost`)
2. Restart the backend after changing environment variables:
   ```bash
   docker-compose restart backend
   ```

### Frontend shows blank page or 404 on refresh

This is expected SPA behavior. The nginx config already handles it with `try_files $uri $uri/ /index.html`. If you see this, verify the `frontend/nginx.conf` file is present and correctly copied into the container.

---

## Security Checklist

Before going to production, verify:

- [ ] `JWT_SECRET_KEY` is a randomly generated string of at least 32 characters
- [ ] `DEBUG` is set to `false`
- [ ] `APP_ENV` is set to `production`
- [ ] `ALLOWED_ORIGINS` lists only your actual frontend domain(s)
- [ ] `.env` is NOT committed to version control (`git status` should not show it)
- [ ] MongoDB Atlas network access is restricted to known IPs
- [ ] HTTPS is enabled (via a reverse proxy like Caddy, Traefik, or Nginx in front of the Docker stack)
- [ ] Docker socket is not exposed to untrusted containers

---

## CI/CD with GitHub Actions

The repository includes `.github/workflows/ci.yml` which automatically:

- Runs the full backend test suite (375 tests) on every push to `main`
- Runs the full frontend test suite (61 tests), TypeScript type check, and production build on every push to `main`

No secrets are required for the CI workflow itself (tests run in an isolated environment with a test JWT key).

To add deployment automation, set these GitHub repository secrets:
- `DOCKER_USERNAME` / `DOCKER_PASSWORD` for Docker Hub image push
- `SSH_DEPLOY_KEY` for server-side pull and restart
