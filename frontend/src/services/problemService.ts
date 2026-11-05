import { request } from './api'
import {
  ProblemType,
  ProblemCreatePayload,
  ProblemResponse,
  ProblemDraftRequest,
  ProblemDraftResponse,
  ProblemTypeInfo,
  ProblemValidationResponse,
  EvaluationResult,
} from '../types'

export const problemService = {
  async listProblemTypes(): Promise<ProblemTypeInfo[]> {
    return request<ProblemTypeInfo[]>('/problems/types')
  },

  async createProblem(payload: ProblemCreatePayload): Promise<ProblemResponse> {
    return request<ProblemResponse>('/problems', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async listProblems(): Promise<ProblemResponse[]> {
    return request<ProblemResponse[]>('/problems')
  },

  async getProblem(id: string): Promise<ProblemResponse> {
    return request<ProblemResponse>(`/problems/${id}`)
  },

  async getProblemMetadata(id: string): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>(`/problems/${id}/metadata`)
  },

  async validateProblem(id: string): Promise<ProblemValidationResponse> {
    return request<ProblemValidationResponse>(`/problems/${id}/validate`, {
      method: 'POST',
    })
  },

  async validateProblemDirect(
    problemType: ProblemType,
    instance: Record<string, unknown>
  ): Promise<ProblemValidationResponse> {
    return request<ProblemValidationResponse>('/problems/validate', {
      method: 'POST',
      body: JSON.stringify({
        problem_type: problemType,
        instance,
      }),
    })
  },

  async evaluateDirect(
    problemType: ProblemType,
    instance: Record<string, unknown>,
    candidate: unknown
  ): Promise<EvaluationResult> {
    return request<EvaluationResult>('/problems/evaluate-direct', {
      method: 'POST',
      body: JSON.stringify({
        problem_type: problemType,
        instance,
        candidate,
      }),
    })
  },

  async evaluateProblem(id: string, candidate: unknown): Promise<EvaluationResult> {
    return request<EvaluationResult>(`/problems/${id}/evaluate`, {
      method: 'POST',
      body: JSON.stringify({
        candidate,
      }),
    })
  },

  async parseDraft(payload: ProblemDraftRequest): Promise<ProblemDraftResponse> {
    return request<ProblemDraftResponse>('/problems/parse-draft', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
