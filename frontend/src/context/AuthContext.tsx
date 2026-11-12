/** Global Authentication React Context */

import React, { createContext, useContext, useState, useEffect } from 'react'
import {
  authService,
  UserResponse,
  TokenResponse,
  UserLoginPayload,
  UserCreatePayload,
} from '../services/authService'

interface AuthContextType {
  user: UserResponse | null
  isAuthenticated: boolean
  isLoading: boolean
  isModalOpen: boolean
  modalMode: 'login' | 'register'
  login: (payload: UserLoginPayload) => Promise<TokenResponse>
  register: (payload: UserCreatePayload) => Promise<UserResponse>
  logout: () => Promise<void>
  openAuthModal: (mode?: 'login' | 'register') => void
  closeAuthModal: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false)
  const [modalMode, setModalMode] = useState<'login' | 'register'>('login')

  useEffect(() => {
    // Initial verification from localStorage
    const storedUser = authService.getStoredUser()
    const token = authService.getStoredToken()

    if (storedUser && token) {
      setUser(storedUser)
      // Background verify token validity with /auth/me
      authService
        .getCurrentUser()
        .then((verified) => setUser(verified))
        .catch(() => {
          // Token expired or invalid
          authService.clearAuthData()
          setUser(null)
        })
        .finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (payload: UserLoginPayload): Promise<TokenResponse> => {
    const res = await authService.login(payload)
    setUser(res.user)
    setIsModalOpen(false)
    return res
  }

  const register = async (payload: UserCreatePayload): Promise<UserResponse> => {
    const res = await authService.register(payload)
    // Auto-login upon successful registration
    await login({ username_or_email: payload.username, password: payload.password })
    return res
  }

  const logout = async (): Promise<void> => {
    await authService.logout()
    setUser(null)
  }

  const openAuthModal = (mode: 'login' | 'register' = 'login') => {
    setModalMode(mode)
    setIsModalOpen(true)
  }

  const closeAuthModal = () => {
    setIsModalOpen(false)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        isModalOpen,
        modalMode,
        login,
        register,
        logout,
        openAuthModal,
        closeAuthModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

