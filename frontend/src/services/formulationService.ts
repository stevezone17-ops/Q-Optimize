import { request } from './api'
import {
  FormulationResponse,
  GenerateFormulationPayload,
  VerifyFormulationPayload,
  VerificationResult,
  QuboModel,
  IsingModel,
} from '../types'

export const formulationService = {
  async generateFormulation(payload: GenerateFormulationPayload): Promise<FormulationResponse> {
    return request<FormulationResponse>('/formulations/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async generateQuboOnly(payload: GenerateFormulationPayload): Promise<QuboModel> {
    return request<QuboModel>('/formulations/qubo', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async convertQuboToIsing(qubo: QuboModel): Promise<IsingModel> {
    return request<IsingModel>('/formulations/ising', {
      method: 'POST',
      body: JSON.stringify({ qubo }),
    })
  },

  async getFormulation(id: string): Promise<FormulationResponse> {
    return request<FormulationResponse>(`/formulations/${id}`)
  },

  async getFormulationMetadata(id: string): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>(`/formulations/${id}/metadata`)
  },

  async verifyFormulation(payload: VerifyFormulationPayload): Promise<VerificationResult> {
    return request<VerificationResult>('/formulations/verify', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async exportFormulation(id: string, format = 'all'): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>(`/formulations/${id}/export?format=${format}`)
  },
}
