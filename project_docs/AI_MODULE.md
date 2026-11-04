# AI Module

## Purpose
Assist users in translating natural language into structured problem drafts and investigate ML-based solver recommendation. AI-generated models must be validated and confirmed by a user.

## Parsing workflow
1. Receive description and optional problem type.
2. Extract entities, quantities, decision variables, objective direction, constraints, units, assumptions.
3. Identify ambiguity and missing information.
4. Return a strict structured draft.
5. Run deterministic validation.
6. Ask clarification questions when necessary.
7. Require user confirmation before creating a canonical problem.

Never invent costs, distances, capacities, or constraints.

## Example draft
```json
{
  "problem_type": "assignment",
  "objective": {"direction": "minimize", "description": "Minimize total assignment cost"},
  "entities": {"agents": ["A1", "A2"], "tasks": ["T1", "T2"]},
  "data": {"cost_matrix": [[4, 7], [6, 3]]},
  "constraints": ["each_agent_one_task", "each_task_one_agent"],
  "assumptions": [],
  "missing_information": [],
  "requires_user_confirmation": true
}
```

## Solver recommendation
Potential features: binary variable count, constraint count, graph size/density, degree statistics, formulation size, problem family, and time budget.

Start with a transparent rule-based baseline. Build an ML recommender only after collecting benchmark data with documented labels. Split train/test by generated instance families or seeds to reduce leakage. Evaluate recommendation regret or achieved objective under fixed budgets, not just classifier accuracy. Include confidence and out-of-distribution warnings.

## Safety
Treat descriptions as untrusted input. Never execute generated code. Validate outputs, keep API keys server-side, apply rate/input limits, and provide a manual workflow if the AI service is unavailable.
