import { request } from './api'
import { BackendHealthResponse } from '../types'

export const healthService = {
  async getHealth(signal?: AbortSignal): Promise<BackendHealthResponse> {
    return request<BackendHealthResponse>('/health', { signal, timeoutMs: 5000 })
  },
}
