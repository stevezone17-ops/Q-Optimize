import { useState, useEffect, useCallback, useRef } from 'react'
import { healthService } from '../services/healthService'
import { BackendHealthResponse } from '../types'

export type HealthStatus = 'online' | 'connecting' | 'offline' | 'degraded'

export function useBackendHealth(pollIntervalMs: number = 15000) {
  const [health, setHealth] = useState<BackendHealthResponse | null>(null)
  const [status, setStatus] = useState<HealthStatus>('connecting')
  const [error, setError] = useState<string | null>(null)
  const [lastChecked, setLastChecked] = useState<Date | null>(null)
  const isMountedRef = useRef(true)
  const statusRef = useRef<HealthStatus>('connecting')

  const updateStatus = (next: HealthStatus) => {
    statusRef.current = next
    setStatus(next)
  }

  const checkHealth = useCallback(async (showConnecting = false) => {
    if (!isMountedRef.current) return
    if (showConnecting || statusRef.current === 'offline') {
      updateStatus('connecting')
    }
    try {
      const data = await healthService.getHealth()
      if (!isMountedRef.current) return
      setHealth(data)
      if (data.status === 'degraded') {
        updateStatus('degraded')
      } else {
        updateStatus('online')
      }
      setError(null)
      setLastChecked(new Date())
    } catch (err) {
      if (!isMountedRef.current) return
      updateStatus('offline')
      setError((err as Error).message || 'Backend unreachable')
      setLastChecked(new Date())
    }
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    checkHealth(true)

    const effectiveInterval = status === 'offline' ? Math.min(pollIntervalMs, 5000) : pollIntervalMs
    const timer = setInterval(() => {
      checkHealth(false)
    }, effectiveInterval)

    return () => {
      isMountedRef.current = false
      clearInterval(timer)
    }
  }, [checkHealth, pollIntervalMs, status])

  return {
    health,
    status,
    error,
    lastChecked,
    refetch: () => checkHealth(true),
  }
}
