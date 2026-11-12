/** Authentication API service for Q-Optimize */

import { request } from './api'

export type UserRole = 'admin' | 'researcher' | 'user'

export interface UserResponse {
  id: string
  email: string
  username: string
  full_name?: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserResponse
}

export interface UserCreatePayload {
  email: string
  username: string
  password: string
  full_name?: string
  role?: UserRole
}

export interface UserLoginPayload {
  username_or_email: string
  password: string
}

export const TOKEN_KEY = 'q_optimize_access_token'
export const REFRESH_TOKEN_KEY = 'q_optimize_refresh_token'
export const USER_KEY = 'q_optimize_user'

export const authService = {
  getStoredToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },

  getStoredUser(): UserResponse | null {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as UserResponse
    } catch {
      return null
    }
  },

  setAuthData(data: TokenResponse) {
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
  },

  clearAuthData() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },

  async register(payload: UserCreatePayload): Promise<UserResponse> {
    return request<UserResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async login(payload: UserLoginPayload): Promise<TokenResponse> {
    const data = await request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    this.setAuthData(data)
    return data
  },

  async refreshToken(): Promise<TokenResponse> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }
    const data = await request<TokenResponse>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    this.setAuthData(data)
    return data
  },

  async getCurrentUser(): Promise<UserResponse> {
    return request<UserResponse>('/auth/me')
  },

  async logout(): Promise<void> {
    try {
      await request<{ detail: string }>('/auth/logout', { method: 'POST' })
    } catch {
      // Best-effort logout acknowledgement
    } finally {
      this.clearAuthData()
    }
  },
}

