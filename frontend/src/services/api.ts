/** Centralized API request service with error handling, timeout, and GET deduplication */

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/+$/, '')

const DEFAULT_TIMEOUT_MS = 15000
const inFlightGets = new Map<string, Promise<unknown>>()

export interface ApiRequestOptions extends RequestInit {
  timeoutMs?: number
}

export class ApiError extends Error {
  status: number
  data?: unknown

  constructor(message: string, status: number, data?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

function formatErrorDetail(errorBody: unknown, fallback: string): string {
  if (!errorBody || typeof errorBody !== 'object') {
    return typeof errorBody === 'string' && errorBody.trim() ? errorBody : fallback
  }
  const detail = (errorBody as { detail?: unknown }).detail
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          const loc = Array.isArray((item as { loc?: unknown[] }).loc)
            ? (item as { loc: unknown[] }).loc.join('.')
            : ''
          return loc ? `${loc}: ${(item as { msg: string }).msg}` : String((item as { msg: string }).msg)
        }
        return String(item)
      })
      .join('; ')
  }
  return fallback
}

export async function request<T>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${normalizedEndpoint}`
  const method = (options.method || 'GET').toUpperCase()

  // Deduplicate concurrent identical GET requests without external signal
  if (method === 'GET' && !options.signal && inFlightGets.has(url)) {
    return inFlightGets.get(url) as Promise<T>
  }

  const execute = async (): Promise<T> => {
    const controller = new AbortController()
    const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

    const externalSignal = options.signal
    const onExternalAbort = () => controller.abort()
    if (externalSignal) {
      if (externalSignal.aborted) {
        controller.abort()
      } else {
        externalSignal.addEventListener('abort', onExternalAbort, { once: true })
      }
    }

    const token = typeof window !== 'undefined' ? localStorage.getItem('q_optimize_access_token') : null

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    }

    try {
      const { timeoutMs: _t, signal: _s, ...fetchOptions } = options
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        let errorBody: unknown = null
        try {
          errorBody = await response.json()
        } catch {
          try {
            errorBody = await response.text()
          } catch {
            errorBody = null
          }
        }

        const detail = formatErrorDetail(errorBody, response.statusText || `HTTP ${response.status}`)
        throw new ApiError(detail, response.status, errorBody)
      }

      if (response.status === 204) {
        return undefined as T
      }

      return (await response.json()) as T
    } catch (err: unknown) {
      clearTimeout(timeoutId)
      if (err instanceof ApiError) {
        throw err
      }
      if ((err as Error).name === 'AbortError') {
        throw new ApiError(`Request timed out after ${Math.round(timeoutMs / 1000)} seconds.`, 408)
      }
      const rawMsg = (err as Error).message || 'Unable to connect to backend service.'
      const friendlyMsg =
        rawMsg === 'Failed to fetch'
          ? `Unable to reach backend at ${API_BASE_URL}. Verify the FastAPI server is running.`
          : rawMsg
      throw new ApiError(friendlyMsg, 0)
    } finally {
      if (externalSignal) {
        externalSignal.removeEventListener('abort', onExternalAbort)
      }
    }
  }

  if (method === 'GET' && !options.signal) {
    const promise = execute().finally(() => {
      inFlightGets.delete(url)
    })
    inFlightGets.set(url, promise)
    return promise
  }

  return execute()
}
