# API Specification

## Conventions
Base path: `/api/v1`. Use JSON, Pydantic validation, consistent errors, pagination, and authentication for private resources. Long-running jobs return an experiment ID; clients poll status.

## Initial endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/auth/register` | Register |
| POST | `/auth/login` | Sign in |
| GET | `/auth/me` | Current user |
| POST | `/problems` | Create problem |
| GET | `/problems` | List own problems |
| GET | `/problems/types` | List supported problem types with metadata, variables, and constraints |
| POST | `/problems/validate` | Directly validate a problem definition without persistence |
| POST | `/problems/evaluate-direct` | Directly evaluate candidate solution against an ad-hoc problem instance |
| GET | `/problems/{id}` | Get own problem |
| GET | `/problems/{id}/metadata` | Get structural statistics and canonical metadata |
| POST | `/problems/{id}/validate` | Validate an existing problem against domain constraints |
| POST | `/problems/{id}/evaluate` | Independently evaluate candidate solution against stored problem |
| PATCH | `/problems/{id}` | Update own problem |
| DELETE | `/problems/{id}` | Delete own problem |
| POST | `/problems/parse-draft` | AI-assisted draft |
| POST | `/formulations/generate` | Generate formulation |
| GET | `/formulations/{id}` | Retrieve formulation |
| POST | `/experiments` | Create and enqueue experiment |
| GET | `/experiments` | List own experiments |
| GET | `/experiments/{id}` | Status and summary |
| GET | `/experiments/{id}/result` | Completed result |
| POST | `/experiments/compare` | Compare experiments |
| POST | `/reports` | Request report |

## Example problem request
```json
{
  "name": "Max-Cut demo",
  "problem_type": "max_cut",
  "instance": {
    "nodes": ["A", "B", "C"],
    "edges": [["A", "B", 1.0], ["B", "C", 1.0]]
  }
}
```

## Example candidate evaluation request
```json
{
  "candidate": {
    "A": 0,
    "B": 1,
    "C": 0
  }
}
```

## Example experiment request
```json
{
  "problem_id": "problem-id",
  "solver_name": "qaoa",
  "solver_config": {
    "p": 1,
    "shots": 1024,
    "optimizer": "COBYLA",
    "max_iterations": 100,
    "seed": 42
  }
}
```

## Status values
`queued`, `running`, `succeeded`, `failed`, `cancelled`. Validate state transitions. Failed jobs must not appear successful.

## Rules
Validate before enqueueing; never accept arbitrary Python code; enforce ownership; apply request and execution limits; do not expose stack traces or secrets.
