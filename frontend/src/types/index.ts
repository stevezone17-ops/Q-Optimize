export type ProblemType = 'max_cut' | 'assignment' | 'tsp'

export interface MaxCutInstance {
  nodes: string[]
  edges: [string, string, number][]
}

export interface AssignmentInstance {
  agents: string[]
  tasks: string[]
  cost_matrix: number[][]
}

export interface TSPInstance {
  cities: string[]
  distance_matrix: number[][]
  start_city?: string
  coordinates?: Record<string, [number, number]>
}

export type ProblemInstance = MaxCutInstance | AssignmentInstance | TSPInstance

export interface ConstraintViolation {
  constraint_id: string
  constraint_name: string
  message: string
  expected?: unknown
  actual?: unknown
  severity: 'error' | 'warning'
}

export interface EvaluationResult {
  problem_id?: string
  problem_type: string
  objective_sense: 'minimize' | 'maximize'
  objective_value: number
  is_feasible: boolean
  violations: ConstraintViolation[]
  details: Record<string, unknown>
  evaluated_at: string
}

export interface VariableSpec {
  name: string
  var_type: 'binary' | 'integer' | 'continuous'
  count: number
  bounds: [number, number]
  description: string
}

export interface ConstraintSpec {
  name: string
  constraint_type: string
  mathematical_form: string
  is_hard: boolean
  description: string
}

export interface ObjectiveSpec {
  sense: 'minimize' | 'maximize'
  mathematical_form: string
  description: string
}

export interface ProblemValidationResponse {
  problem_id?: string
  is_valid: boolean
  status: 'valid' | 'invalid' | 'draft'
  issues: string[]
  variables: VariableSpec[]
  constraints: ConstraintSpec[]
  metadata: Record<string, unknown>
  validated_at: string
}

export interface ProblemTypeInfo {
  type: ProblemType
  name: string
  family: string
  objective_sense: 'minimize' | 'maximize'
  mathematical_form: string
  description: string
  variable_description: string
  supported_constraints: string[]
  sample_instance: Record<string, unknown>
}

export interface ProblemCreatePayload {
  name: string
  problem_type: ProblemType
  description?: string
  instance: Record<string, unknown>
}

export interface ProblemResponse {
  id: string
  owner_id: string
  name: string
  problem_type: ProblemType
  schema_version: string
  description: string
  validation_status: 'valid' | 'invalid' | 'draft'
  variables?: VariableSpec[]
  objective?: ObjectiveSpec
  constraints?: ConstraintSpec[]
  metadata?: Record<string, unknown>
  instance: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ProblemDraftRequest {
  text: string
  problem_type_hint?: ProblemType
}

export interface ProblemDraftResponse {
  problem_type: ProblemType
  name: string
  description: string
  objective: {
    direction: 'minimize' | 'maximize'
    description: string
  }
  entities: Record<string, unknown>
  data: Record<string, unknown>
  constraints: string[]
  assumptions: string[]
  missing_information: string[]
  suggested_instance: Record<string, unknown>
  requires_user_confirmation: boolean
  confidence_score: number
  disclaimer: string
}

export interface BackendHealthResponse {
  status: string
  service: string
  version: string
  environment: string
  phase: string
  timestamp: string
  database: {
    connected: boolean
    engine: string
    message?: string
    database?: string
  }
  supported_problems: ProblemType[]
}

export type NavigationItemKey =
  | 'overview'
  | 'problem-builder'
  | 'formulation-studio'
  | 'quantum-lab'
  | 'classical-lab'
  | 'comparison-lab'
  | 'my-experiments'
  | 'learn'
  | 'settings'
