/**
 * SessionPage — tela de sessão com split view (desktop) ou tabs (mobile).
 * Story 5.6: layout, Story 5.7: streaming.
 *
 * Desktop (≥1024px): chat 40% | artefato 60%
 * Mobile (<1024px):  tabs [Conversa | Artefato] com badge "Atualizado"
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useSession } from '@/hooks/useSession'
import { useProject } from '@/hooks/useProject'
import { ChatMessage } from '@/components/chat/ChatMessage'
import { ChatInput } from '@/components/chat/ChatInput'
import { TypingIndicator } from '@/components/chat/TypingIndicator'
import { SessionTelemetryWidget } from '@/components/chat/SessionTelemetryWidget'
import type { Message } from '@/services/sessionsApi'

type Tab = 'chat' | 'artifact'

export default function SessionPage() {
  const { id: sessionId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('chat')
  const [artifactUpdated, setArtifactUpdated] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    session,
    messages,
    isThinking,
    streamingMessage,
    error,
    sendMessage,
    isLoadingSession,
    isLoadingMessages,
  } = useSession({ sessionId: sessionId ?? '' })

  // Fetch project data from session
  const { data: project } = useProject(session?.project_id ?? '')

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage?.content])

  // Mark artifact as updated when streaming completes
  useEffect(() => {
    if (streamingMessage && !streamingMessage.isStreaming && activeTab === 'chat') {
      setArtifactUpdated(true)
    }
  }, [streamingMessage?.isStreaming, activeTab])

  const handleTabChange = useCallback((tab: Tab) => {
    setActiveTab(tab)
    if (tab === 'artifact') setArtifactUpdated(false)
  }, [])

  const handleUploadSuccess = useCallback(
    (filename: string) => {
      try {
        sendMessage(`📎 ${filename} enviado e disponível para a IA.`)
      } catch (err) {
        console.error('[SessionPage] handleUploadSuccess: sendMessage falhou', err)
      }
    },
    [sendMessage],
  )

  if (!sessionId) {
    navigate('/projects')
    return null
  }

  // ── Loading state ──
  if (isLoadingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ background: 'var(--background)' }}>
        <div
          className="w-8 h-8 rounded-full border-2 animate-spin"
          style={{ borderColor: 'var(--rs-primary)', borderTopColor: 'transparent' }}
        />
      </div>
    )
  }

  // ── Chat Panel ──
  const chatPanel = (
    <div className="flex flex-col h-full" style={{ minHeight: 0 }}>
      {/* Header */}
      <div
        className="shrink-0 flex items-center justify-between px-4 py-3"
        style={{ borderBottom: '1px solid var(--border)', background: 'var(--rs-surface)' }}
      >
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center justify-center rounded-lg transition-colors hover:opacity-80"
            style={{ width: 32, height: 32, background: 'var(--muted)' }}
            aria-label="Voltar"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-h3 font-semibold" style={{ color: 'var(--rs-text-primary)' }}>
              {project?.name ?? 'Sessão de Elicitação'}
            </h1>
            <div className="flex items-center gap-2">
              {project?.business_domain && (
                <span
                  className="text-caption font-medium px-2 py-0.5 rounded-full"
                  style={{
                    backgroundColor: 'var(--rs-primary-light)',
                    color: 'var(--rs-primary)',
                  }}
                >
                  {project.business_domain}
                </span>
              )}
              <span className="text-caption" style={{ color: 'var(--rs-text-muted)' }}>
                {session?.status === 'completed' ? '✅ Concluída' : '● Ativa'}
              </span>
            </div>
          </div>
        </div>

        {/* Save indicator & Telemetry */}
        <div className="flex items-center gap-4">
          <SessionTelemetryWidget messages={messages} />
          <div className="flex items-center gap-2">
          {isThinking && (
            <span className="text-caption" style={{ color: 'var(--rs-primary)' }}>
              Processando...
            </span>
          )}
          <span
            className="inline-block w-2 h-2 rounded-full"
            style={{ background: session?.status === 'completed' ? 'var(--rs-success)' : 'var(--rs-primary)' }}
          />
          </div>
        </div>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto px-4 py-4"
        style={{ background: 'var(--background)' }}
      >
        {isLoadingMessages ? (
          <div className="flex justify-center py-8">
            <div
              className="w-6 h-6 rounded-full border-2 animate-spin"
              style={{ borderColor: 'var(--rs-primary)', borderTopColor: 'transparent' }}
            />
          </div>
        ) : messages.length === 0 && !isThinking ? (
          <div className="flex flex-col items-center justify-center py-16 text-center" style={{ color: 'var(--rs-text-muted)' }}>
            <div className="text-4xl mb-4">💬</div>
            <p className="text-body" style={{ fontWeight: 'var(--font-weight-medium)' }}>
              Inicie a conversa
            </p>
            <p className="text-body-sm mt-1">
              Descreva o projeto que deseja especificar e a IA irá guiá-lo.
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg: Message) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {/* Streaming message */}
            {streamingMessage && streamingMessage.content && (
              <ChatMessage
                message={{
                  id: 'streaming',
                  session_id: sessionId,
                  role: 'assistant',
                  content: streamingMessage.content,
                  message_index: messages.length,
                  created_at: new Date().toISOString(),
                }}
                isStreaming={streamingMessage.isStreaming}
              />
            )}

            {/* Typing indicator */}
            {isThinking && !streamingMessage?.content && <TypingIndicator />}

            {/* Error */}
            {error && (
              <div
                className="flex items-center gap-2 px-4 py-3 rounded-lg mt-3"
                style={{
                  background: 'hsla(0, 72%, 58%, 0.1)',
                  border: '1px solid var(--rs-error)',
                  color: 'var(--rs-error)',
                  fontSize: 'var(--text-body-sm)',
                }}
              >
                <span>⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        disabled={isThinking || session?.status === 'completed'}
        placeholder={
          session?.status === 'completed'
            ? 'Sessão concluída'
            : 'Descreva seu projeto ou responda...'
        }
        projectId={session?.project_id}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  )

  // ── Artifact Panel ──
  const artifactPanel = (
    <div className="flex flex-col h-full">
      <div
        className="shrink-0 flex items-center px-4 py-3"
        style={{ borderBottom: '1px solid var(--border)', background: 'var(--rs-surface)' }}
      >
        <h2 className="text-h3 font-semibold" style={{ color: 'var(--rs-text-primary)' }}>
          Artefato
        </h2>
      </div>
      <div
        className="flex-1 overflow-y-auto px-4 py-4"
        style={{ background: 'var(--background)' }}
      >
        {session?.artifact_state ? (
          <pre
            className="text-mono whitespace-pre-wrap"
            style={{
              color: 'var(--rs-text-primary)',
              fontSize: 'var(--text-mono)',
              lineHeight: 'var(--leading-mono)',
            }}
          >
            {JSON.stringify(session.artifact_state, null, 2)}
          </pre>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-center" style={{ color: 'var(--rs-text-muted)' }}>
            <div className="text-4xl mb-4">📋</div>
            <p className="text-body" style={{ fontWeight: 'var(--font-weight-medium)' }}>
              Artefato em construção
            </p>
            <p className="text-body-sm mt-1">
              O artefato aparecerá aqui conforme a IA o constrói com você.
            </p>
          </div>
        )}
      </div>
    </div>
  )

  // ── Desktop: Split View ──
  return (
    <div className="flex flex-col h-screen" style={{ background: 'var(--background)' }}>
      {/* Mobile tabs (< 1024px) */}
      <div className="lg:hidden flex shrink-0" style={{ borderBottom: '1px solid var(--border)', background: 'var(--rs-surface)' }}>
        <button
          onClick={() => handleTabChange('chat')}
          className="flex-1 py-3 text-center text-body-sm font-medium transition-colors"
          style={{
            color: activeTab === 'chat' ? 'var(--rs-primary)' : 'var(--rs-text-muted)',
            borderBottom: activeTab === 'chat' ? '2px solid var(--rs-primary)' : '2px solid transparent',
          }}
          id="tab-chat"
        >
          💬 Conversa
        </button>
        <button
          onClick={() => handleTabChange('artifact')}
          className="flex-1 py-3 text-center text-body-sm font-medium transition-colors relative"
          style={{
            color: activeTab === 'artifact' ? 'var(--rs-primary)' : 'var(--rs-text-muted)',
            borderBottom: activeTab === 'artifact' ? '2px solid var(--rs-primary)' : '2px solid transparent',
          }}
          id="tab-artifact"
        >
          📋 Artefato
          {artifactUpdated && (
            <span
              className="absolute top-2 right-4 w-2 h-2 rounded-full"
              style={{ background: 'var(--rs-amber)' }}
              title="Atualizado"
            />
          )}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex min-h-0">
        {/* Desktop split */}
        <div className="hidden lg:flex w-full min-h-0">
          <div className="flex flex-col" style={{ width: '40%', borderRight: '1px solid var(--border)' }}>
            {chatPanel}
          </div>
          <div className="flex flex-col" style={{ width: '60%' }}>
            {artifactPanel}
          </div>
        </div>

        {/* Mobile tabbed */}
        <div className="lg:hidden flex flex-col w-full min-h-0">
          {activeTab === 'chat' ? chatPanel : artifactPanel}
        </div>
      </div>
    </div>
  )
}
