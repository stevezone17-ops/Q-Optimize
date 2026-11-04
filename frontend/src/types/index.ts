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
  coordinates?: Record<string, [number, number]>
}

export type ProblemInstance = MaxCutInstance | AssignmentInstance | TSPInstance

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
