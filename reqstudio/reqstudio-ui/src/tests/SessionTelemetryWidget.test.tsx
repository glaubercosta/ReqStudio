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
    created_at: new Date().toISOString()
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
    created_at: new Date().toISOString()
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
    created_at: new Date().toISOString()
  }
]

describe('SessionTelemetryWidget', () => {
  it('renders nothing when there are no tokens', () => {
    const { container } = render(<SessionTelemetryWidget messages={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders correct total tokens and cost for assistant messages', () => {
    render(<SessionTelemetryWidget messages={mockMessages} />)
    
    // total cost: 0.005 + 0.015 = 0.02
    // total tokens: 50 + 10 + 100 + 40 = 200
    expect(screen.getByText('💰')).toBeInTheDocument()
    expect(screen.getByText('$0.02')).toBeInTheDocument()
    expect(screen.getByText('200 tokens')).toBeInTheDocument()
  })

  it('renders correct breakdown in the tooltip', () => {
    render(<SessionTelemetryWidget messages={mockMessages} />)
    
    expect(screen.getByText('150')).toBeInTheDocument() // input
    expect(screen.getByText('50')).toBeInTheDocument() // output
    expect(screen.getByText('$0.0200')).toBeInTheDocument() // detailed cost
    expect(screen.getByText('4.00s')).toBeInTheDocument() // total latency (1.5 + 2.5 = 4)
    expect(screen.getByText('gpt-mock')).toBeInTheDocument() // model
  })

  it('formats large tokens with basic k metric', () => {
    const largeMessages: Message[] = [
      {
        ...mockMessages[1],
        input_tokens: 1500,
        output_tokens: 100
      }
    ]
    render(<SessionTelemetryWidget messages={largeMessages} />)
    expect(screen.getByText('1.6k tokens')).toBeInTheDocument()
  })
})
