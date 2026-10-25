import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, type AuthMe } from '../api/client'
import { getAuthToken, setAuthToken } from './token'

type AuthState = {
  user: AuthMe | null
  loading: boolean
  refresh: () => Promise<void>
  setSession: (token: string, me: AuthMe) => void
  logout: () => Promise<void>
  logoutAll: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthMe | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    const token = getAuthToken()
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const me = await api.getAuthMe()
      setUser(me)
    } catch {
      setAuthToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const setSession = useCallback((token: string, me: AuthMe) => {
    setAuthToken(token)
    setUser(me)
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      /* ignore */
    }
    setAuthToken(null)
    setUser(null)
  }, [])

  const logoutAll = useCallback(async () => {
    try {
      await api.logoutAll()
    } catch {
      /* ignore */
    }
    setAuthToken(null)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, refresh, setSession, logout, logoutAll }),
    [user, loading, refresh, setSession, logout, logoutAll],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth outside AuthProvider')
  return ctx
}
