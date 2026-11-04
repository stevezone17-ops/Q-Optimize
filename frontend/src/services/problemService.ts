import { request } from './api'
import {
  ProblemCreatePayload,
  ProblemResponse,
  ProblemDraftRequest,
  ProblemDraftResponse,
} from '../types'

export const problemService = {
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

  async parseDraft(payload: ProblemDraftRequest): Promise<ProblemDraftResponse> {
    return request<ProblemDraftResponse>('/problems/parse-draft', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
