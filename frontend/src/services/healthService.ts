import { request } from './api'
import { BackendHealthResponse } from '../types'

export const healthService = {
  async getHealth(): Promise<BackendHealthResponse> {
    return request<BackendHealthResponse>('/health')
  },
}
