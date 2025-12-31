import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'
import { useNavigate } from 'react-router-dom'

const AuthContext = createContext()

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const response = await api.get('/auth/current-user/')
      setUser(response.data.user)
    } catch (error) {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login/', { username, password })
      setUser(response.data.user)
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Login failed'
      }
    }
  }

  const register = async (username, password1, password2) => {
    try {
      const response = await api.post('/auth/register/', {
        username,
        password1,
        password2
      })
      setUser(response.data.user)
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        errors: error.response?.data?.errors || { general: 'Registration failed' }
      }
    }
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout/')
      setUser(null)
      return { success: true }
    } catch (error) {
      return { success: false, error: 'Logout failed' }
    }
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    checkAuth
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

