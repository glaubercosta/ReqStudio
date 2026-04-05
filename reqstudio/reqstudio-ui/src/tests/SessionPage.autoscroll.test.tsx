import { fireEvent, render } from '@testing-library/react'
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
  ChatMessage: () => <div data-testid="chat-message" />,
}))

vi.mock('@/components/chat/TypingIndicator', () => ({
  TypingIndicator: () => null,
}))

vi.mock('@/components/chat/SessionTelemetryWidget', () => ({
  SessionTelemetryWidget: () => null,
}))

describe('SessionPage autoscroll', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useSessionMock.mockReturnValue({
      session: {
        id: 'sess-1',
        project_id: 'proj-1',
        status: 'active',
        artifact_state: null,
      },
      messages: [
        {
          id: 'msg-1',
          session_id: 'sess-1',
          role: 'assistant',
          content: 'Resposta em progresso',
          message_index: 0,
          created_at: new Date().toISOString(),
        },
      ],
      isThinking: true,
      streamingMessage: {
        content: 'streaming',
        isStreaming: true,
      },
      error: null,
      sendMessage: vi.fn(),
      markUserActivity: vi.fn(),
      isLoadingSession: false,
      isLoadingMessages: false,
    })
  })

  it('opens the session already positioned at the latest message', () => {
    useSessionMock.mockReturnValue({
      session: {
        id: 'sess-1',
        project_id: 'proj-1',
        status: 'active',
        artifact_state: null,
      },
      messages: [],
      isThinking: false,
      streamingMessage: null,
      error: null,
      sendMessage: vi.fn(),
      markUserActivity: vi.fn(),
      isLoadingSession: false,
      isLoadingMessages: true,
    })

    const { rerender, getAllByTestId } = render(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    const messagesContainer = getAllByTestId('session-messages')[0]
    let scrollTopValue = 0
    Object.defineProperty(messagesContainer, 'scrollHeight', { configurable: true, value: 1200 })
    Object.defineProperty(messagesContainer, 'clientHeight', { configurable: true, value: 300 })
    Object.defineProperty(messagesContainer, 'scrollTop', {
      configurable: true,
      get: () => scrollTopValue,
      set: (value) => {
        scrollTopValue = Number(value)
      },
    })

    useSessionMock.mockReturnValue({
      session: {
        id: 'sess-1',
        project_id: 'proj-1',
        status: 'active',
        artifact_state: null,
      },
      messages: [
        {
          id: 'msg-1',
          session_id: 'sess-1',
          role: 'user',
          content: 'Primeira interação',
          message_index: 0,
          created_at: new Date().toISOString(),
        },
        {
          id: 'msg-2',
          session_id: 'sess-1',
          role: 'assistant',
          content: 'Última resposta da IA',
          message_index: 1,
          created_at: new Date().toISOString(),
        },
      ],
      isThinking: false,
      streamingMessage: null,
      error: null,
      sendMessage: vi.fn(),
      markUserActivity: vi.fn(),
      isLoadingSession: false,
      isLoadingMessages: false,
    })

    rerender(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(scrollTopValue).toBe(1200)
  })

  it('does not force a new autoscroll when the user is reading history', async () => {
    useSessionMock.mockReturnValue({
      session: {
        id: 'sess-1',
        project_id: 'proj-1',
        status: 'active',
        artifact_state: null,
      },
      messages: [],
      isThinking: false,
      streamingMessage: null,
      error: null,
      sendMessage: vi.fn(),
      markUserActivity: vi.fn(),
      isLoadingSession: false,
      isLoadingMessages: true,
    })

    const { rerender, getAllByTestId } = render(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    const messagesContainer = getAllByTestId('session-messages')[0]
    let scrollTopValue = 0
    let scrollWrites = 0
    Object.defineProperty(messagesContainer, 'scrollHeight', { configurable: true, value: 1200 })
    Object.defineProperty(messagesContainer, 'clientHeight', { configurable: true, value: 300 })
    Object.defineProperty(messagesContainer, 'scrollTop', {
      configurable: true,
      get: () => scrollTopValue,
      set: (value) => {
        scrollTopValue = Number(value)
        scrollWrites += 1
      },
    })

    useSessionMock.mockReturnValue({
      session: {
        id: 'sess-1',
        project_id: 'proj-1',
        status: 'active',
        artifact_state: null,
      },
      messages: [
        {
          id: 'msg-1',
          session_id: 'sess-1',
          role: 'assistant',
          content: 'Resposta em progresso',
          message_index: 0,
          created_at: new Date().toISOString(),
        },
      ],
      isThinking: true,
      streamingMessage: {
        content: 'streaming',
        isStreaming: true,
      },
      error: null,
      sendMessage: vi.fn(),
      markUserActivity: vi.fn(),
      isLoadingSession: false,
      isLoadingMessages: false,
    })

    rerender(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(scrollWrites).toBe(1)

    await new Promise((resolve) => setTimeout(resolve, 0))

    scrollTopValue = 100
    fireEvent.scroll(messagesContainer)

    useSessionMock.mockReturnValue({
      session: {
        id: 'sess-1',
        project_id: 'proj-1',
        status: 'active',
        artifact_state: null,
      },
      messages: [
        {
          id: 'msg-1',
          session_id: 'sess-1',
          role: 'assistant',
          content: 'Resposta em progresso',
          message_index: 0,
          created_at: new Date().toISOString(),
        },
      ],
      isThinking: true,
      streamingMessage: {
        content: 'streaming update',
        isStreaming: true,
      },
      error: null,
      sendMessage: vi.fn(),
      markUserActivity: vi.fn(),
      isLoadingSession: false,
      isLoadingMessages: false,
    })

    rerender(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(scrollWrites).toBe(1)
  })
})
