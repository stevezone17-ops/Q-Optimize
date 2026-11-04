# Database Schema

## Principles
Use versioned, validated schemas. Every private resource must be queried using the authenticated user's owner ID. Do not trust owner IDs supplied by the browser.

## Collections

### users
`_id`, `email` (unique), `password_hash`, `display_name`, `role`, `created_at`, `updated_at`.

### problems
`_id`, `owner_id`, `name`, `problem_type`, `schema_version`, `description`, `instance`, `created_at`, `updated_at`.

### formulations
`_id`, `problem_id`, `owner_id`, `formulation_type`, `schema_version`, `variable_order`, `linear_terms`, `quadratic_terms`, `offset`, `penalties`, `assumptions`, `created_at`.

### experiments
`_id`, `owner_id`, `problem_id`, `formulation_id`, `status`, `solver_name`, `solver_config`, `environment`, `created_at`, `started_at`, `completed_at`, `error`.

### results
`_id`, `experiment_id`, `candidate_solution`, `objective_value`, `is_feasible`, `constraint_violations`, `runtime_seconds`, `metrics`, `raw_metadata`, `created_at`.

### reports
`_id`, `owner_id`, `experiment_id`, `format`, `storage_reference`, `created_at`.

## Indexes
- Unique index on `users.email`.
- `problems.owner_id, updated_at`.
- `experiments.owner_id, created_at`.
- `experiments.status`.
- `results.experiment_id`.
- `reports.owner_id, created_at`.

## Security and evolution
Hash passwords using a modern password hashing algorithm. Never store raw passwords or API keys. Validate ownership and IDs. Version problem/formulation documents and provide migrations when schemas change.
