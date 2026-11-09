import { request } from './api'
import {
  ProblemType,
  ProblemDraftProposal,
  SolverRecommendation,
  ModelMetadata,
  ModelTrainResponse,
} from '../types'

export interface NLParseRequest {
  text: string
  problem_type_hint?: ProblemType
  provider_name?: string
}

export interface NLValidateDraftRequest {
  problem_type: ProblemType
  instance: Record<string, any>
}

export interface DraftValidationResult {
  is_valid: boolean
  status: string
  issues: string[]
  num_variables: number
  num_constraints: number
  metadata: Record<string, any>
}

export interface SolverRecommendationRequest {
  problem_id?: string
  problem_type?: ProblemType
  instance?: Record<string, any>
  user_constraints?: Record<string, any>
}

export interface ModelTrainRequest {
  algorithm_name?: string
  model_version?: string
  use_sample_test_data?: boolean
}

export const aiService = {
  /**
   * Parse natural language description into structured draft proposal.
   */
  async parseDescription(req: NLParseRequest): Promise<ProblemDraftProposal> {
    return request<ProblemDraftProposal>('/ai/assistant/parse', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  /**
   * Re-validate an edited problem instance draft against canonical Phase 2 validators.
   */
  async validateDraftInstance(req: NLValidateDraftRequest): Promise<DraftValidationResult> {
    return request<DraftValidationResult>('/ai/assistant/validate-draft', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  /**
   * Request intelligent solver recommendation for a stored or ad-hoc problem instance.
   */
  async recommendSolver(req: SolverRecommendationRequest): Promise<SolverRecommendation> {
    return request<SolverRecommendation>('/ai/recommend', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  /**
   * List all registered recommendation models.
   */
  async listModels(): Promise<ModelMetadata[]> {
    return request<ModelMetadata[]>('/ai/models')
  },

  /**
   * Trigger candidate model training.
   */
  async trainModel(req: ModelTrainRequest = {}): Promise<ModelTrainResponse> {
    return request<ModelTrainResponse>('/ai/train', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },
}
