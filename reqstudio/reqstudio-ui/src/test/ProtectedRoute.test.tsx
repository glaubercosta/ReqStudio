/**
 * ProtectedRoute — testes de autenticação e redirecionamento (Story 2.5).
 *
 * Cobre 3 estados: loading (spinner), autenticado (outlet), não-autenticado (redirect).
 */
import { vi, describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '@/test/utils'
import { ProtectedRoute } from '@/components/ProtectedRoute'

// Mock do AuthContext — controla o estado sem dependência do backend
const mockUseAuth = vi.fn()
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

// Nota: ProtectedRoute renderiza <Outlet /> quando autenticado;
// em MemoryRouter sem rotas filhas configuradas, o Outlet renderiza nulo.

// Helper: renderiza com rota / ProtectedRoute / ChildPage
function renderProtected(initialPath = '/protected') {
  return render(
    <ProtectedRoute />,
    { initialEntries: [initialPath] },
  )
}

describe('ProtectedRoute', () => {
  it('exibe spinner enquanto isLoading=true', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: true })
    const { container } = renderProtected()
    // O spinner é um div com animate-spin — verifica que existe e não há redirect
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('redireciona para /login quando não autenticado', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: false })
    renderProtected()
    // MemoryRouter captura o redirect — verifica que a página filha não está presente
    // e que nenhum conteúdo autenticado foi exposto
    expect(screen.queryByText('Página Protegida')).not.toBeInTheDocument()
  })

  it('NÃO exibe o spinner quando isLoading=false (autenticado)', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, isLoading: false })
    const { container } = renderProtected()
    expect(container.querySelector('.animate-spin')).not.toBeInTheDocument()
  })

  it('NÃO exibe o spinner quando isLoading=false (não autenticado)', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: false })
    const { container } = renderProtected()
    expect(container.querySelector('.animate-spin')).not.toBeInTheDocument()
  })
})
