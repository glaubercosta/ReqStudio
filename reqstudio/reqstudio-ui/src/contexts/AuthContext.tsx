/**
 * AuthContext — gestão de autenticação global (Story 2.5).
 *
 * Design:
 * - access_token em memória (variável do módulo apiClient), não no localStorage
 * - Silent refresh ao montar: tenta POST /refresh para restaurar sessão
 * - Escuta evento 'auth:logout' para forçar logout quando refresh falha
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import {
  AUTH_LOGOUT_EVENT,
  authApi,
  setAccessToken,
  type UserData,
} from '@/services/apiClient'

interface AuthState {
  user: UserData | null
  isAuthenticated: boolean
  isLoading: boolean
}

interface AuthContextValue extends AuthState {
  login:    (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout:   () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true, // true enquanto tenta silent refresh
  })

  // ── Silent Refresh ao montar ────────────────────────────────────────────────
  useEffect(() => {
    let mounted = true

    async function silentRefresh() {
      try {
        const res = await authApi.refresh()
        setAccessToken(res.data.access_token)
        const me = await authApi.me()
        if (mounted) {
          setState({ user: me.data, isAuthenticated: true, isLoading: false })
        }
      } catch {
        // 401 é esperado na primeira carga sem sessão ativa — não é um erro
        if (mounted) {
          setState({ user: null, isAuthenticated: false, isLoading: false })
        }
      }
    }

    silentRefresh()
    return () => { mounted = false }
  }, [])

  // ── Escuta evento de logout global (401 não recuperável) ────────────────────
  useEffect(() => {
    const handleForceLogout = () => {
      setAccessToken(null)
      setState({ user: null, isAuthenticated: false, isLoading: false })
    }
    window.addEventListener(AUTH_LOGOUT_EVENT, handleForceLogout)
    return () => window.removeEventListener(AUTH_LOGOUT_EVENT, handleForceLogout)
  }, [])

  // ── Actions ─────────────────────────────────────────────────────────────────

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login({ email, password })
    setAccessToken(res.data.access_token)
    const me = await authApi.me()
    setState({ user: me.data, isAuthenticated: true, isLoading: false })
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    await authApi.register({ email, password })
    // Após registro, faz login automaticamente
    await login(email, password)
  }, [login])

  const logout = useCallback(async () => {
    await authApi.logout()
    setAccessToken(null)
    setState({ user: null, isAuthenticated: false, isLoading: false })
  }, [])

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de <AuthProvider>')
  return ctx
}
