# Q-Optimize — Database Architecture, Indexing & Operations Guide

## 1. Overview
Q-Optimize uses MongoDB as its primary persistence engine for optimization problems, QUBO/Ising formulations, experiment runs, solver records, user credentials, and benchmark datasets. A high-performance in-memory fallback layer is embedded to guarantee uninterrupted local development and testing when external database servers are offline.

---

## 2. Connection Pooling & Resilience
The connection manager (`backend/app/db/mongodb.py`) uses Motor (asynchronous driver for MongoDB) with strict connection pooling parameters:
- `maxPoolSize`: 50 connections per replica process
- `minPoolSize`: 5 warm connections maintained
- `maxIdleTimeMS`: 30,000 ms (30 seconds)
- `connectTimeoutMS`: 5,000 ms
- `serverSelectionTimeoutMS`: 2,000 ms
- `retryWrites`: True (automatic retry for transient network disconnects)
- **Exponential Backoff**: Reconnect loop retries with initial 0.3s delay doubling up to 3 attempts.

---

## 3. Collections & Indexing Specifications

Automated startup routines (`db_manager.create_indexes()`) provision composite and unique indexes:

| Collection | Indexed Field(s) | Direction / Unique | Purpose |
|:---|:---|:---:|:---|
| `users` | `username` | ASC (Unique) | O(1) Fast user login & uniqueness |
| `users` | `email` | ASC (Unique) | O(1) Email lookup & uniqueness |
| `users` | `role` | ASC | RBAC role filtering |
| `problems` | `owner_id` | ASC | User multi-tenancy isolation |
| `problems` | `problem_type` | ASC | Filtering by Max-Cut, TSP, Assignment |
| `problems` | `created_at` | DESC | Chronological ordering |
| `problems` | `is_deleted` | ASC | Fast exclusion of soft-deleted records |
| `formulations` | `problem_id` | ASC | Fast formulation retrieval by parent ID |
| `formulations` | `formulation_type` | ASC | QUBO / Ising distinction |
| `formulations` | `created_at` | DESC | Historical audit trail |
| `experiments` | `owner_id` | ASC | User experiment isolation |
| `experiments` | `status` | ASC | Lifecycle queue polling (RUNNING, DRAFT) |
| `experiments` | `created_at` | DESC | Chronological pagination |
| `experiments` | `is_deleted` | ASC | Soft-delete filtering |
| `executions` | `experiment_id` | ASC | Solver trace tracking |
| `executions` | `status` | ASC | Worker execution status |
| `benchmark_datasets` | `problem_type`, `dataset_id` | Compound | Fast benchmark dataset query |

---

## 4. Soft Deletion & Audit Integrity
Critical entities (Problems and Experiments) implement non-destructive **soft deletion**:
- Fields:
  - `is_deleted: bool` (default: `False`)
  - `deleted_at: Optional[datetime]` (timestamp of deletion)
  - `deleted_by: Optional[str]` (UUID of user who triggered deletion)
  - `version: int` (optimistic locking counter)
- API endpoints exclude soft-deleted records by default.
- Administrators can audit or recover deleted assets by providing `include_deleted=True`.

---

## 5. Backup & Disaster Recovery Procedures

### 5.1 Automated Online Backup (`mongodump`)
To perform an online, non-blocking backup with gzip compression:
```bash
# Full Database Backup
mongodump \
  --uri="mongodb://localhost:27017" \
  --db=q_optimize \
  --gzip \
  --archive="/var/backups/q_optimize_backup_$(date +%Y%m%d_%H%M%S).gz"
```

### 5.2 Point-in-Time Restoration (`mongorestore`)
To restore a snapshot archive without data loss:
```bash
# Full Database Restore
mongorestore \
  --uri="mongodb://localhost:27017" \
  --db=q_optimize \
  --gzip \
  --drop \
  --archive="/var/backups/q_optimize_backup_20261112.gz"
```

### 5.3 Diagnostic Inspection
Check latency, pool stats, and active collections via the API:
```bash
curl -X GET http://localhost:8000/health
```
Output:
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "engine": "mongodb",
    "database": "q_optimize",
    "latency_ms": 1.45,
    "pool_config": {
      "max_pool_size": 50,
      "min_pool_size": 5,
      "max_idle_time_ms": 30000
    },
    "indexes_active": 7
  }
}
```

