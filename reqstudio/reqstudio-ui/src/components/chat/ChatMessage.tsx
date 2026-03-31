/**
 * ChatMessage — bolha de mensagem no chat (Story 5.6).
 *
 * User messages: indigo médio (rs-user-message), alinhada à direita.
 * Assistant messages: card neutro com avatar, alinhada à esquerda.
 */

import type { Message } from '@/services/sessionsApi'

interface ChatMessageProps {
  message: Message
  isStreaming?: boolean
}

export function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
      style={{ marginBottom: 'var(--space-3)' }}
    >
      {/* Avatar */}
      {!isUser && (
        <div
          className="shrink-0 flex items-center justify-center rounded-full"
          style={{
            width: 32,
            height: 32,
            background: 'var(--rs-primary)',
            color: 'white',
            fontSize: 'var(--text-body-sm)',
            fontWeight: 'var(--font-weight-semibold)',
          }}
        >
          IA
        </div>
      )}

      {/* Bubble */}
      <div
        className={`relative max-w-[80%] rounded-2xl px-4 py-3 ${isStreaming ? 'animate-pulse' : ''}`}
        style={{
          background: isUser ? 'var(--rs-user-message)' : 'var(--rs-surface)',
          color: isUser ? 'white' : 'var(--rs-text-primary)',
          border: isUser ? 'none' : '1px solid var(--border)',
          fontSize: 'var(--text-body)',
          lineHeight: 'var(--leading-body)',
          borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
        }}
      >
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
        {isStreaming && (
          <span
            className="inline-block ml-1"
            style={{ color: 'var(--rs-text-muted)' }}
          >
            ▊
          </span>
        )}
      </div>
    </div>
  )
}

export default ChatMessage
