/**
 * apiClient.ts — testes do cliente HTTP central (Story 2.5).
 *
 * Cobre: token management, request com auth header, retry em 401,
 * dispatch do evento auth:logout quando refresh falha.
 *
 * Estratégia: vi.stubGlobal('fetch', vi.fn()) — sem dependência de MSW.
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  setAccessToken,
  getAccessToken,
  AUTH_LOGOUT_EVENT,
  authApi,
} from '@/services/apiClient'

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeFetchResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as unknown as Response
}

function stubFetch(response: Response | Response[]) {
  const mock = vi.fn()
  if (Array.isArray(response)) {
    response.forEach(r => mock.mockResolvedValueOnce(r))
  } else {
    mock.mockResolvedValue(response)
  }
  vi.stubGlobal('fetch', mock)
  return mock
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('apiClient — token management', () => {
  it('getAccessToken retorna null por padrão', () => {
    setAccessToken(null)
    expect(getAccessToken()).toBeNull()
  })

  it('setAccessToken / getAccessToken funcionam corretamente', () => {
    setAccessToken('tok_abc')
    expect(getAccessToken()).toBe('tok_abc')
    setAccessToken(null)
    expect(getAccessToken()).toBeNull()
  })
})

describe('apiClient — authApi.login', () => {
  beforeEach(() => { setAccessToken(null) })
  afterEach(() => { vi.unstubAllGlobals() })

  it('faz POST para /api/v1/auth/login com as credenciais', async () => {
    const body = { data: { access_token: 'tok_login', token_type: 'bearer' } }
    const fetchMock = stubFetch(makeFetchResponse(body))

    const result = await authApi.login({ email: 'u@test.com', password: 'Pass1!' })

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/login'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(result.data.access_token).toBe('tok_login')
  })

  it('lança ReqStudioApiError quando o servidor retorna erro', async () => {
    const errorBody = {
      error: { code: 'INVALID_CREDENTIALS', message: 'Credenciais inválidas', help: '', actions: [], severity: 'warning' },
    }
    stubFetch(makeFetchResponse(errorBody, 401))

    await expect(authApi.login({ email: 'x@x.com', password: 'wrong' })).rejects.toThrow('Credenciais inválidas')
  })
})

describe('apiClient — authApi.register', () => {
  afterEach(() => { vi.unstubAllGlobals() })

  it('faz POST para /api/v1/auth/register', async () => {
    const body = { data: { id: 'u1', email: 'n@test.com', tenant_id: 't1' } }
    const fetchMock = stubFetch(makeFetchResponse(body, 201))

    await authApi.register({ email: 'n@test.com', password: 'Pass1!' })

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/register'),
      expect.objectContaining({ method: 'POST' }),
    )
  })
})

describe('apiClient — authApi.me', () => {
  beforeEach(() => { setAccessToken('tok_me') })
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('envia Authorization header com o access token', async () => {
    const body = { data: { id: 'u1', email: 'u@test.com', tenant_id: 't1' } }
    const fetchMock = stubFetch(makeFetchResponse(body))

    await authApi.me()

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/me'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer tok_me' }),
      }),
    )
  })
})

describe('apiClient — 401 retry com refresh', () => {
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('após 401, tenta refresh e refaz a request com novo token', async () => {
    const refreshBody = { data: { access_token: 'tok_new', token_type: 'bearer' } }
    const meBody = { data: { id: 'u1', email: 'u@test.com', tenant_id: 't1' } }

    // Sequência: 1ª call /me → 401, 2ª call /refresh → ok, 3ª call /me → ok
    const fetchMock = stubFetch([
      makeFetchResponse({ error: { code: 'UNAUTHORIZED', message: 'Não autorizado', help: '', actions: [], severity: 'critical' } }, 401),
      makeFetchResponse(refreshBody, 200),
      makeFetchResponse(meBody, 200),
    ])

    await authApi.me()

    expect(fetchMock).toHaveBeenCalledTimes(3)
    // 3ª call deve ter o novo token
    expect(fetchMock.mock.calls[2][1]).toEqual(
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer tok_new' }),
      }),
    )
  })

  it('dispatcha auth:logout quando refresh também falha', async () => {
    const errorBody = { error: { code: 'SESSION_EXPIRED', message: 'Expirado', help: '', actions: [], severity: 'critical' } }
    stubFetch([
      makeFetchResponse(errorBody, 401), // /me falha
      makeFetchResponse(errorBody, 401), // /refresh também falha
    ])

    const logoutSpy = vi.fn()
    window.addEventListener(AUTH_LOGOUT_EVENT, logoutSpy)

    await expect(authApi.me()).rejects.toThrow()
    expect(logoutSpy).toHaveBeenCalled()

    window.removeEventListener(AUTH_LOGOUT_EVENT, logoutSpy)
  })
})
