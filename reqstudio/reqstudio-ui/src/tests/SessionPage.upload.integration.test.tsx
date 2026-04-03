import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import SessionPage from '@/pages/SessionPage'

const sendMessageMock = vi.fn()

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
    error: null,
    sendMessage: sendMessageMock,
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
  ChatInput: ({ onUploadSuccess }: { onUploadSuccess?: (filename: string) => void }) => (
    <button onClick={() => onUploadSuccess?.('contrato.pdf')} aria-label="mock-upload">
      mock-upload
    </button>
  ),
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

describe('SessionPage upload integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('encadeia onUploadSuccess para sendMessage com texto de confirmacao', () => {
    render(
      <MemoryRouter initialEntries={['/sessions/sess-1']}>
        <Routes>
          <Route path="/sessions/:id" element={<SessionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    const uploadButtons = screen.getAllByRole('button', { name: 'mock-upload' })
    fireEvent.click(uploadButtons[0])

    expect(sendMessageMock).toHaveBeenCalledWith('📎 contrato.pdf enviado e disponível para a IA.')
  })
})
