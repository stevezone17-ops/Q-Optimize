import { apiClient } from './api'
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
    const res = await apiClient.post<ProblemDraftProposal>('/ai/assistant/parse', req)
    return res.data
  },

  /**
   * Re-validate an edited problem instance draft against canonical Phase 2 validators.
   */
  async validateDraftInstance(req: NLValidateDraftRequest): Promise<DraftValidationResult> {
    const res = await apiClient.post<DraftValidationResult>('/ai/assistant/validate-draft', req)
    return res.data
  },

  /**
   * Request intelligent solver recommendation for a stored or ad-hoc problem instance.
   */
  async recommendSolver(req: SolverRecommendationRequest): Promise<SolverRecommendation> {
    const res = await apiClient.post<SolverRecommendation>('/ai/recommend', req)
    return res.data
  },

  /**
   * List all registered recommendation models.
   */
  async listModels(): Promise<ModelMetadata[]> {
    const res = await apiClient.get<ModelMetadata[]>('/ai/models')
    return res.data
  },

  /**
   * Trigger candidate model training.
   */
  async trainModel(req: ModelTrainRequest = {}): Promise<ModelTrainResponse> {
    const res = await apiClient.post<ModelTrainResponse>('/ai/train', req)
    return res.data
  },
}

