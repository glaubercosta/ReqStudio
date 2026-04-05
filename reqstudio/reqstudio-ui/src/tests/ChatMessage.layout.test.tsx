import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ChatMessage } from '@/components/chat/ChatMessage'
import type { Message } from '@/services/sessionsApi'

const longMessage: Message = {
  id: 'msg-long',
  session_id: 'sess-1',
  role: 'user',
  content: 'palavra-muito-longa-'.repeat(80),
  message_index: 0,
  created_at: new Date().toISOString(),
}

describe('ChatMessage layout hardening', () => {
  it('renders long content with wrapping and bounded height styles', () => {
    const { container } = render(<ChatMessage message={longMessage} />)

    const bubble = container.querySelector('[style*="max-height: 60vh"]')
    const content = screen.getByText(longMessage.content)

    expect(bubble).not.toBeNull()
    expect(content.className).toContain('whitespace-pre-wrap')
    expect(content.className).toContain('break-words')
    expect(content).toHaveStyle({ overflowWrap: 'anywhere' })
  })
})
