import { useState, useEffect, useCallback } from 'react'
import { healthService } from '../services/healthService'
import { BackendHealthResponse } from '../types'

export type HealthStatus = 'connected' | 'checking' | 'disconnected'

export function useBackendHealth(pollIntervalMs: number = 30000) {
  const [health, setHealth] = useState<BackendHealthResponse | null>(null)
  const [status, setStatus] = useState<HealthStatus>('checking')
  const [error, setError] = useState<string | null>(null)
  const [lastChecked, setLastChecked] = useState<Date | null>(null)

  const checkHealth = useCallback(async () => {
    try {
      setStatus('checking')
      const data = await healthService.getHealth()
      setHealth(data)
      setStatus('connected')
      setError(null)
      setLastChecked(new Date())
    } catch (err) {
      setStatus('disconnected')
      setError((err as Error).message || 'Backend unreachable')
      setLastChecked(new Date())
    }
  }, [])

  useEffect(() => {
    checkHealth()
    const timer = setInterval(checkHealth, pollIntervalMs)
    return () => clearInterval(timer)
  }, [checkHealth, pollIntervalMs])

  return { health, status, error, lastChecked, refetch: checkHealth }
}
