import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import SessionPage from '@/pages/SessionPage'

const useSessionMock = vi.fn()

vi.mock('@/hooks/useSession', () => ({
  useSession: () => useSessionMock(),
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

describe('SessionPage progress panel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows current step during active elicitation', () => {
    useSessionMock.mockReturnValue({
      session: {
        id: 'sess-1',
        project_id: 'proj-1',
        status: 'active',
        workflow_position: { current_step: 3 },
        artifact_state: null,
      },
      messages: [],
      isThinking: false,
      streamingMessage: null,
      error: null,
      sendMessage: vi.fn(),
      markUserActivity: vi.fn(),
      isLoadingSession: false,
      isLoadingMessages: false,
    })

    render(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getAllByText('Etapa 3 de 5').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Objetivos de negócio').length).toBeGreaterThan(0)
  })

  it('shows completed state when workflow is finished', () => {
    useSessionMock.mockReturnValue({
      session: {
        id: 'sess-1',
        project_id: 'proj-1',
        status: 'completed',
        workflow_position: { current_step: 5, completed: true },
        artifact_state: null,
      },
      messages: [],
      isThinking: false,
      streamingMessage: null,
      error: null,
      sendMessage: vi.fn(),
      markUserActivity: vi.fn(),
      isLoadingSession: false,
      isLoadingMessages: false,
    })

    render(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getAllByText('Fechamento').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Entrevista concluída').length).toBeGreaterThan(0)
    expect(screen.getAllByText('100%').length).toBeGreaterThan(0)
  })
})
