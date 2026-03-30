/**
 * API client base configurado para o backend ReqStudio.
 * Base URL lida da variável de ambiente Vite.
 */

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8001'

interface ApiError {
  code: string
  message: string
  help: string
  actions: { label: string; route?: string; action?: string }[]
  severity: string
}

export class ReqStudioApiError extends Error {
  error: ApiError
  constructor(error: ApiError) {
    super(error.message)
    this.error = error
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include', // envia cookies (refresh_token)
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  const body = await res.json()

  if (!res.ok) {
    throw new ReqStudioApiError(body.error)
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

export interface AuthResponse { data: { access_token: string; token_type: string } }
export interface RegisterResponse { data: UserData }
export interface MeResponse { data: UserData }

export const authApi = {
  register: (payload: RegisterPayload) =>
    request<RegisterResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: (payload: LoginPayload) =>
    request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  me: (token: string) =>
    request<MeResponse>('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    }),
}
