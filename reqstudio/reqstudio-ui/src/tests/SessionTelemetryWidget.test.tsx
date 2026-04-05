import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SessionTelemetryWidget } from '@/components/chat/SessionTelemetryWidget'
import type { Message } from '@/services/sessionsApi'

const mockMessages: Message[] = [
  {
    id: 'msg-user',
    session_id: 'session-id',
    role: 'user',
    content: 'Quero um app',
    message_index: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: 'msg-asst-1',
    session_id: 'session-id',
    role: 'assistant',
    content: 'Entendido. Algo mais?',
    message_index: 1,
    input_tokens: 50,
    output_tokens: 10,
    cost_usd: 0.005,
    latency_ms: 1500,
    model: 'gpt-mock',
    created_at: new Date().toISOString(),
  },
  {
    id: 'msg-asst-2',
    session_id: 'session-id',
    role: 'assistant',
    content: 'Gerando.',
    message_index: 2,
    input_tokens: 100,
    output_tokens: 40,
    cost_usd: 0.015,
    latency_ms: 2500,
    model: 'gpt-mock',
    created_at: new Date().toISOString(),
  },
]

describe('SessionTelemetryWidget', () => {
  it('renders nothing when there are no tokens', () => {
    const { container } = render(<SessionTelemetryWidget messages={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders correct total tokens and cost for assistant messages', () => {
    render(<SessionTelemetryWidget messages={mockMessages} />)

    expect(screen.getByText('💰')).toBeInTheDocument()
    expect(screen.getByText('$0.02')).toBeInTheDocument()
    expect(screen.getByText('200 tokens')).toBeInTheDocument()
  })

  it('renders the same normalized cost in summary and detailed breakdown', () => {
    render(<SessionTelemetryWidget messages={mockMessages} />)

    expect(screen.getByText('150')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
    expect(screen.getByText('$0.0200')).toBeInTheDocument()
    expect(screen.getByText('4.00s')).toBeInTheDocument()
    expect(screen.getByText('gpt-mock')).toBeInTheDocument()
  })

  it('keeps tiny fractional costs stable across repeated renders', () => {
    const tinyCostMessages: Message[] = [
      {
        ...mockMessages[1],
        id: 'tiny-1',
        cost_usd: 0.0000049,
      },
      {
        ...mockMessages[2],
        id: 'tiny-2',
        cost_usd: 0.0000049,
      },
    ]

    const { rerender } = render(<SessionTelemetryWidget messages={tinyCostMessages} />)

    expect(screen.getByText('<$0.01')).toBeInTheDocument()
    expect(screen.getByText('$0.0000')).toBeInTheDocument()

    rerender(<SessionTelemetryWidget messages={tinyCostMessages} />)

    expect(screen.getByText('<$0.01')).toBeInTheDocument()
    expect(screen.getByText('$0.0000')).toBeInTheDocument()
  })

  it('formats large tokens with basic k metric', () => {
    const largeMessages: Message[] = [
      {
        ...mockMessages[1],
        input_tokens: 1500,
        output_tokens: 100,
      },
    ]
    render(<SessionTelemetryWidget messages={largeMessages} />)
    expect(screen.getByText('1.6k tokens')).toBeInTheDocument()
  })
})
