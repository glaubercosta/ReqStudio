/**
 * ChatInput — input expansível com auto-resize (Story 5.6).
 *
 * - Enter = enviar (desktop)
 * - Shift+Enter = nova linha
 * - Botão de enviar com ícone
 * - Auto-resize até 6 linhas
 */

import { useCallback, useRef, useState, type KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (content: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Descreva seu projeto ou responda a pergunta...',
}: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, disabled, onSend])

  const handleKey = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value)
    // Auto-resize
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px' // max ~6 linhas
  }, [])

  return (
    <div
      className="flex items-end gap-2 p-3"
      style={{
        background: 'var(--rs-surface)',
        borderTop: '1px solid var(--border)',
        borderRadius: '0 0 var(--radius-lg) var(--radius-lg)',
      }}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKey}
        disabled={disabled}
        placeholder={placeholder}
        rows={1}
        className="flex-1 resize-none outline-none bg-transparent"
        style={{
          fontSize: 'var(--text-body)',
          lineHeight: 'var(--leading-body)',
          color: 'var(--rs-text-primary)',
          padding: 'var(--space-2) var(--space-3)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          minHeight: 40,
          maxHeight: 160,
          transition: 'border-color 0.15s',
        }}
        id="chat-input"
        aria-label="Mensagem para a IA"
      />

      <button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        className="shrink-0 flex items-center justify-center rounded-full transition-all"
        style={{
          width: 40,
          height: 40,
          background: disabled || !value.trim() ? 'var(--muted)' : 'var(--rs-primary)',
          color: 'white',
          cursor: disabled || !value.trim() ? 'not-allowed' : 'pointer',
          opacity: disabled || !value.trim() ? 0.5 : 1,
        }}
        id="chat-send-button"
        aria-label="Enviar mensagem"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 2L11 13" />
          <path d="M22 2L15 22L11 13L2 9L22 2Z" />
        </svg>
      </button>
    </div>
  )
}

export default ChatInput
