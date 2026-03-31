/**
 * API client com interceptor de 401 e auto-refresh (Story 2.5).
 *
 * Fluxo de 401:
 *   1. Request falha com 401
 *   2. Se não for /refresh, tenta POST /auth/refresh
 *   3. Se refresh ok → retry com novo access_token
 *   4. Se refresh falhar → dispara evento 'auth:logout' → redirect /login
 */

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8001'

export interface ApiError {
  code: string
  message: string
  help: string
  actions: { label: string; route?: string; action?: string }[]
  severity: string
}

export class ReqStudioApiError extends Error {
  error: ApiError
  statusCode: number
  constructor(error: ApiError, statusCode: number) {
    super(error.message)
    this.error = error
    this.statusCode = statusCode
  }
}

// Evento global para logout forçado (escutado pelo AuthContext)
export const AUTH_LOGOUT_EVENT = 'auth:logout'

let _accessToken: string | null = null

export function setAccessToken(token: string | null) {
  _accessToken = token
}

export function getAccessToken(): string | null {
  return _accessToken
}

async function refreshAccessToken(): Promise<string | null> {
  const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) return null
  const body = await res.json()
  const token = body?.data?.access_token ?? null
  if (token) setAccessToken(token)
  return token
}

export async function request<T>(
  path: string,
  init?: RequestInit,
  isRetry = false,
): Promise<T> {
  const headers: Record<string, string> = { ...init?.headers as Record<string, string> }

  // Set default Content-Type to JSON only if body is not FormData
  if (!(init?.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  if (_accessToken) {
    headers['Authorization'] = `Bearer ${_accessToken}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers,
  })

  // 401 → tenta refresh (apenas uma vez, não para o próprio endpoint de refresh)
  if (res.status === 401 && !isRetry && !path.includes('/refresh')) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      return request<T>(path, init, true)
    }
    // Refresh falhou → força logout global
    window.dispatchEvent(new CustomEvent(AUTH_LOGOUT_EVENT))
    const body = await res.json().catch(() => ({}))
    throw new ReqStudioApiError(
      body.error ?? { code: 'SESSION_EXPIRED', message: 'Sessão expirada.' },
      401,
    )
  }

  const body = await res.json()
  if (!res.ok) {
    throw new ReqStudioApiError(body.error, res.status)
  }
  return body
}

// ── Auth endpoints ────────────────────────────────────────────────────────────

export interface RegisterPayload { email: string; password: string }
export interface LoginPayload    { email: string; password: string }

export interface UserData {
  id: string
  email: string
  tenant_id: string
}

export interface AuthTokenResponse { data: { access_token: string; token_type: string } }
export interface RegisterResponse  { data: UserData }
export interface MeResponse        { data: UserData }

export const authApi = {
  register: (payload: RegisterPayload) =>
    request<RegisterResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: (payload: LoginPayload) =>
    request<AuthTokenResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  refresh: () =>
    request<AuthTokenResponse>('/api/v1/auth/refresh', { method: 'POST' }),

  me: () => request<MeResponse>('/api/v1/auth/me'),

  logout: () =>
    fetch(`${API_BASE}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    }).catch(() => null), // silencia erros de logout
}
