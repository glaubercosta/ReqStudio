/**
 * AuthContext — testes das actions de login, logout e silent refresh (Story 2.5).
 *
 * Cobre: login → estado autenticado, logout → limpa estado, silent refresh ok/falha,
 * evento auth:logout força logout global.
 */
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '@/test/utils'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import * as apiClientModule from '@/services/apiClient'

const clearQueryCache = vi.fn()

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQueryClient: () => ({
      clear: clearQueryCache,
    }),
  }
})

// ── Mock authApi ──────────────────────────────────────────────────────────────

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof apiClientModule>()
  return {
    ...actual,
    authApi: {
      refresh:  vi.fn(),
      me:       vi.fn(),
      login:    vi.fn(),
      register: vi.fn(),
      logout:   vi.fn(),
    },
    setAccessToken: vi.fn(),
  }
})

const mockRefresh  = vi.mocked(apiClientModule.authApi.refresh)
const mockMe       = vi.mocked(apiClientModule.authApi.me)
const mockLogin    = vi.mocked(apiClientModule.authApi.login)
const mockRegister = vi.mocked(apiClientModule.authApi.register)
const mockLogout   = vi.mocked(apiClientModule.authApi.logout)

const fakeUser = { id: 'u1', email: 'test@reqstudio.com', tenant_id: 'tenant-1' }
const fakeToken = { data: { access_token: 'tok_123', token_type: 'bearer' } }

// ── Test component ────────────────────────────────────────────────────────────

function AuthConsumer() {
  const { user, isAuthenticated, isLoading, login, logout, register } = useAuth()
  return (
    <div>
      <span data-testid="loading">{isLoading.toString()}</span>
      <span data-testid="auth">{isAuthenticated.toString()}</span>
      <span data-testid="email">{user?.email ?? 'none'}</span>
      <button onClick={() => login('a@b.com', 'pass123')}>Login</button>
      <button onClick={() => register('new@b.com', 'pass123')}>Register</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  )
}

function renderAuth() {
  return render(
    <AuthProvider>
      <AuthConsumer />
    </AuthProvider>,
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('AuthContext — silent refresh', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('começa com isLoading=true e termina false após refresh falho', async () => {
    mockRefresh.mockRejectedValue(new Error('401'))
    renderAuth()
    expect(screen.getByTestId('loading').textContent).toBe('true')
    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false')
      expect(screen.getByTestId('auth').textContent).toBe('false')
    })
  })

  it('autentica automaticamente se refresh bem-sucedido', async () => {
    mockRefresh.mockResolvedValue(fakeToken)
    mockMe.mockResolvedValue({ data: fakeUser })
    renderAuth()
    await waitFor(() => {
      expect(screen.getByTestId('auth').textContent).toBe('true')
      expect(screen.getByTestId('email').textContent).toBe('test@reqstudio.com')
    })
    expect(clearQueryCache).toHaveBeenCalled()
  })
})

describe('AuthContext — login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRefresh.mockRejectedValue(new Error('401'))
  })

  it('atualiza estado para autenticado após login bem-sucedido', async () => {
    mockLogin.mockResolvedValue(fakeToken)
    mockMe.mockResolvedValue({ data: fakeUser })
    renderAuth()

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'))
    await userEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({ email: 'a@b.com', password: 'pass123' })
      expect(screen.getByTestId('auth').textContent).toBe('true')
      expect(screen.getByTestId('email').textContent).toBe('test@reqstudio.com')
    })
    expect(clearQueryCache).toHaveBeenCalled()
  })
})

describe('AuthContext — logout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRefresh.mockResolvedValue(fakeToken)
    mockMe.mockResolvedValue({ data: fakeUser })
  })

  it('limpa estado após logout', async () => {
    mockLogout.mockResolvedValue(null)
    renderAuth()

    await waitFor(() => expect(screen.getByTestId('auth').textContent).toBe('true'))
    await userEvent.click(screen.getByRole('button', { name: /logout/i }))

    await waitFor(() => {
      expect(screen.getByTestId('auth').textContent).toBe('false')
      expect(screen.getByTestId('email').textContent).toBe('none')
    })
    expect(clearQueryCache).toHaveBeenCalled()
  })

  it('força logout ao receber evento auth:logout', async () => {
    renderAuth()
    await waitFor(() => expect(screen.getByTestId('auth').textContent).toBe('true'))

    act(() => {
      window.dispatchEvent(new CustomEvent(apiClientModule.AUTH_LOGOUT_EVENT))
    })

    await waitFor(() => {
      expect(screen.getByTestId('auth').textContent).toBe('false')
    })
    expect(clearQueryCache).toHaveBeenCalled()
  })
})

describe('AuthContext — register', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRefresh.mockRejectedValue(new Error('401'))
    mockLogin.mockResolvedValue(fakeToken)
    mockMe.mockResolvedValue({ data: fakeUser })
  })

  it('registra e faz login automaticamente', async () => {
    mockRegister.mockResolvedValue({ data: fakeUser })
    renderAuth()

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'))
    await userEvent.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({ email: 'new@b.com', password: 'pass123' })
      expect(screen.getByTestId('auth').textContent).toBe('true')
    })
  })
})
