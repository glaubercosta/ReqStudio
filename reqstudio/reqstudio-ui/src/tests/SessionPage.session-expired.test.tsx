import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import SessionPage from '@/pages/SessionPage'

vi.mock('@/hooks/useSession', () => ({
  useSession: () => ({
    session: {
      id: 'sess-1',
      project_id: 'proj-1',
      status: 'active',
      artifact_state: null,
    },
    messages: [],
    isThinking: false,
    streamingMessage: null,
    error: {
      code: 'SESSION_EXPIRED',
      message: 'Sua sessão expirou. Faça login novamente para retomar.',
    },
    sendMessage: vi.fn(),
    isLoadingSession: false,
    isLoadingMessages: false,
  }),
}))

vi.mock('@/hooks/useProject', () => ({
  useProject: () => ({
    data: {
      id: 'proj-1',
      name: 'Projeto Teste',
      business_domain: 'Logistica',
    },
  }),
}))

vi.mock('@/components/chat/ChatInput', () => ({
  ChatInput: () => <div />,
}))

vi.mock('@/components/chat/ChatMessage', () => ({
  ChatMessage: () => null,
}))

vi.mock('@/components/chat/TypingIndicator', () => ({
  TypingIndicator: () => null,
}))

vi.mock('@/components/chat/SessionTelemetryWidget', () => ({
  SessionTelemetryWidget: () => null,
}))

describe('SessionPage expired-session recovery', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders guided recovery message and both recovery actions', () => {
    render(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(
      screen.getAllByText('Sua sessão expirou. Faça login novamente para retomar.').length,
    ).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: 'Fazer login' }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: 'Voltar aos projetos' }).length).toBeGreaterThan(0)
  })

  it('navigates to login when clicking the primary recovery CTA', () => {
    render(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
          <Route path="/login" element={<div>login-page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getAllByRole('button', { name: 'Fazer login' })[0])
    expect(screen.getByText('login-page')).toBeInTheDocument()
  })

  it('navigates to projects when clicking the secondary recovery CTA', () => {
    render(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
          <Route path="/projects" element={<div>projects-page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getAllByRole('button', { name: 'Voltar aos projetos' })[0])
    expect(screen.getByText('projects-page')).toBeInTheDocument()
  })
})
