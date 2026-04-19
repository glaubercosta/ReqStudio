/**
 * SessionPage — tela de sessão com split view (desktop) ou tabs (mobile).
 * Story 5.6: layout, Story 5.7: streaming.
 *
 * Desktop (≥1024px): chat 40% | artefato 60%
 * Mobile (<1024px):  tabs [Conversa | Artefato] com badge "Atualizado"
 */

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { UIEvent } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useSession } from '@/hooks/useSession'
import { useProject } from '@/hooks/useProject'
import { artifactsApi, type Artifact, type ArtifactExportFormat, type ArtifactView } from '@/services/artifactsApi'
import { ChatMessage } from '@/components/chat/ChatMessage'
import { ChatInput } from '@/components/chat/ChatInput'
import { TypingIndicator } from '@/components/chat/TypingIndicator'
import { SessionTelemetryWidget } from '@/components/chat/SessionTelemetryWidget'
import type { Message } from '@/services/sessionsApi'

type Tab = 'chat' | 'artifact'
type DesktopLayoutMode = 'chat' | 'split' | 'artifact'
const ELICITATION_STEPS = [
  'Contexto',
  'Usuários e stakeholders',
  'Objetivos de negócio',
  'Processo atual',
  'Restrições',
]

interface SessionChatPanelProps {
  sessionId: string
  projectId: string
  projectName: string
  projectDomain?: string | null
  sessionStatus?: 'active' | 'paused' | 'completed' | string
  messages: Message[]
  isThinking: boolean
  streamingMessage: { content: string; isStreaming: boolean } | null
  error: { code: string; message: string } | null
  sendMessage: (content: string) => Promise<void>
  markUserActivity: () => void
  isLoadingMessages: boolean
  navigate: ReturnType<typeof useNavigate>
  onUploadSuccess: (filename: string) => void
  workflowPosition: Record<string, unknown> | null
  isKickstarting: boolean
  isReturning: boolean
}

function SessionChatPanel({
  sessionId,
  projectId,
  projectName,
  projectDomain,
  sessionStatus,
  messages,
  isThinking,
  streamingMessage,
  error,
  sendMessage,
  markUserActivity,
  isLoadingMessages,
  navigate,
  onUploadSuccess,
  workflowPosition,
  isKickstarting,
  isReturning,
}: SessionChatPanelProps) {
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const autoScrollResetRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const suppressNextScrollActivityRef = useRef(false)
  const shouldAutoScrollRef = useRef(true)

  useEffect(() => {
    shouldAutoScrollRef.current = true
    suppressNextScrollActivityRef.current = false
    if (autoScrollResetRef.current) {
      clearTimeout(autoScrollResetRef.current)
      autoScrollResetRef.current = null
    }
  }, [sessionId])

  useLayoutEffect(() => {
    if (isLoadingMessages) return
    if (!shouldAutoScrollRef.current) return
    const container = messagesContainerRef.current
    if (!container) return

    suppressNextScrollActivityRef.current = true
    container.scrollTop = container.scrollHeight

    if (autoScrollResetRef.current) {
      clearTimeout(autoScrollResetRef.current)
    }
    autoScrollResetRef.current = setTimeout(() => {
      suppressNextScrollActivityRef.current = false
      autoScrollResetRef.current = null
    }, 0)
  }, [isLoadingMessages, isThinking, messages.length, sessionId, streamingMessage?.content])

  useEffect(() => {
    return () => {
      if (autoScrollResetRef.current) {
        clearTimeout(autoScrollResetRef.current)
      }
    }
  }, [])

  const handleMessagesScroll = useCallback((event: UIEvent<HTMLDivElement>) => {
    const container = event.currentTarget
    if (suppressNextScrollActivityRef.current) {
      suppressNextScrollActivityRef.current = false
      if (autoScrollResetRef.current) {
        clearTimeout(autoScrollResetRef.current)
        autoScrollResetRef.current = null
      }
      return
    }
    const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight
    shouldAutoScrollRef.current = distanceToBottom < 64
    markUserActivity()
  }, [markUserActivity])

  const handleUpload = useCallback(
    (filename: string) => {
      onUploadSuccess(filename)
    },
    [onUploadSuccess],
  )

  const currentStepRaw = workflowPosition?.current_step
  const parsedStep = typeof currentStepRaw === 'number'
    ? currentStepRaw
    : Number(currentStepRaw ?? 1)
  const currentStep = Number.isFinite(parsedStep)
    ? Math.min(Math.max(Math.trunc(parsedStep), 1), ELICITATION_STEPS.length)
    : 1
  const totalSteps = ELICITATION_STEPS.length
  const completed = workflowPosition?.completed === true || sessionStatus === 'completed'
  const progressPercent = completed ? 100 : Math.round((currentStep / totalSteps) * 100)
  const currentStepLabel = completed ? 'Entrevista concluída' : ELICITATION_STEPS[currentStep - 1]

  return (
    <div className="flex flex-col h-full" style={{ minHeight: 0 }}>
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
              {projectName}
            </h1>
            <div className="flex items-center gap-2">
              {projectDomain && (
                <span
                  className="text-caption font-medium px-2 py-0.5 rounded-full"
                  style={{
                    backgroundColor: 'var(--rs-primary-light)',
                    color: 'var(--rs-primary)',
                  }}
                >
                  {projectDomain}
                </span>
              )}
              <span className="text-caption" style={{ color: 'var(--rs-text-muted)' }}>
                {sessionStatus === 'completed' ? '✅ Concluída' : '● Ativa'}
              </span>
            </div>
          </div>
        </div>

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
              style={{ background: sessionStatus === 'completed' ? 'var(--rs-success)' : 'var(--rs-primary)' }}
            />
          </div>
        </div>
      </div>
      <div
        className="shrink-0 px-4 py-3"
        style={{ borderBottom: '1px solid var(--border)', background: 'var(--background)' }}
        data-testid="session-progress-panel"
      >
        <div className="flex items-center justify-between gap-3">
          <span className="text-caption font-medium" style={{ color: 'var(--rs-text-primary)' }}>
            {completed ? 'Fechamento' : `Etapa ${currentStep} de ${totalSteps}`}
          </span>
          <span className="text-caption" style={{ color: 'var(--rs-text-muted)' }}>
            {progressPercent}%
          </span>
        </div>
        <div className="mt-2 h-1.5 rounded-full" style={{ background: 'var(--muted)' }}>
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%`, background: 'var(--rs-primary)' }}
          />
        </div>
        <p className="mt-2 text-caption" style={{ color: 'var(--rs-text-muted)' }}>
          {currentStepLabel}
        </p>
      </div>

      <div
        ref={messagesContainerRef}
        onScroll={handleMessagesScroll}
        className="flex-1 overflow-y-auto px-4 py-4"
        style={{ background: 'var(--background)' }}
        data-testid="session-messages"
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

            {isThinking && !streamingMessage?.content && <TypingIndicator />}
          </>
        )}

        {error && (
          <div
            className="flex items-center gap-2 px-4 py-3 rounded-lg mt-3"
            style={{
              background: 'var(--muted)',
              border: '1px solid var(--rs-error)',
              color: 'var(--rs-error)',
              fontSize: 'var(--text-body-sm)',
            }}
          >
            <span>⚠️</span>
            <span>{error.message}</span>
            {error.code === 'SESSION_EXPIRED' || error.code === 'SESSION_INACTIVITY_TIMEOUT' ? (
              <div className="ml-auto flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => navigate('/login')}
                  className="px-2 py-1 rounded text-caption font-medium"
                  style={{ border: '1px solid currentColor' }}
                >
                  Fazer login
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/projects')}
                  className="px-2 py-1 rounded text-caption font-medium"
                  style={{ border: '1px solid currentColor' }}
                >
                  Voltar aos projetos
                </button>
              </div>
            ) : null}
          </div>
        )}
      </div>

      <ChatInput
        onSend={sendMessage}
        disabled={isThinking || isKickstarting || isReturning || sessionStatus === 'completed'}
        placeholder={
          sessionStatus === 'completed'
            ? 'Sessão concluída'
            : isKickstarting
              ? 'Mary está se apresentando...'
              : isReturning
                ? 'Mary está resumindo o progresso...'
                : 'Descreva seu projeto ou responda...'
        }
        projectId={projectId}
        onUploadSuccess={handleUpload}
      />
    </div>
  )
}

interface SessionArtifactPanelProps {
  previewMarkdown: string
  isLoadingPreview: boolean
  artifactId: string | null
  activeView: ArtifactView
  isExporting: ArtifactExportFormat | null
  exportError: string | null
  onChangeView: (view: ArtifactView) => void
  onExport: (format: ArtifactExportFormat) => void
  onOpenArtifact: (artifactId: string) => void
}

function SessionArtifactPanel({
  previewMarkdown,
  isLoadingPreview,
  artifactId,
  activeView,
  isExporting,
  exportError,
  onChangeView,
  onExport,
  onOpenArtifact,
}: SessionArtifactPanelProps) {
  return (
    <div className="flex flex-col h-full">
      <div
        className="shrink-0 flex items-center justify-between gap-3 px-4 py-3"
        style={{ borderBottom: '1px solid var(--border)', background: 'var(--rs-surface)' }}
      >
        <h2 className="text-h3 font-semibold" style={{ color: 'var(--rs-text-primary)' }}>
          Artefato
        </h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="text-caption px-2 py-1 rounded-md border border-border hover:bg-muted transition-colors"
            style={activeView === 'business' ? { background: 'var(--rs-primary-light)', color: 'var(--rs-primary)' } : undefined}
            onClick={() => onChangeView('business')}
          >
            Negócio
          </button>
          <button
            type="button"
            className="text-caption px-2 py-1 rounded-md border border-border hover:bg-muted transition-colors"
            style={activeView === 'technical' ? { background: 'var(--rs-primary-light)', color: 'var(--rs-primary)' } : undefined}
            onClick={() => onChangeView('technical')}
          >
            Técnico
          </button>
          {artifactId ? (
            <button
              type="button"
              id="btn-open-artifact-from-session"
              className="text-caption px-2 py-1 rounded-md border border-border hover:bg-muted transition-colors"
              onClick={() => onOpenArtifact(artifactId)}
            >
              Abrir artefato
            </button>
          ) : null}
        </div>
      </div>
      <div
        className="flex-1 overflow-y-auto px-4 py-4"
        style={{ background: 'var(--background)' }}
      >
        <div className="mb-3 flex items-center gap-2">
          <button
            type="button"
            className="text-caption px-2 py-1 rounded-md border border-border hover:bg-muted transition-colors"
            onClick={() => onExport('markdown')}
            disabled={isExporting !== null || !artifactId}
          >
            {isExporting === 'markdown' ? 'Exportando...' : 'Exportar MD'}
          </button>
          <button
            type="button"
            className="text-caption px-2 py-1 rounded-md border border-border hover:bg-muted transition-colors"
            onClick={() => onExport('json')}
            disabled={isExporting !== null || !artifactId}
          >
            {isExporting === 'json' ? 'Exportando...' : 'Exportar JSON'}
          </button>
        </div>
        {exportError ? (
          <p className="mb-3 text-caption" style={{ color: 'var(--rs-error)' }} role="alert">
            {exportError}
          </p>
        ) : null}
        {isLoadingPreview ? (
          <div className="flex justify-center py-8">
            <div
              className="w-6 h-6 rounded-full border-2 animate-spin"
              style={{ borderColor: 'var(--rs-primary)', borderTopColor: 'transparent' }}
            />
          </div>
        ) : previewMarkdown ? (
          <div
            className="prose prose-sm max-w-none"
            style={{ color: 'var(--rs-text-primary)' }}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {previewMarkdown}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-center" style={{ color: 'var(--rs-text-muted)' }}>
            <div className="text-4xl mb-4">📋</div>
            <p className="text-body" style={{ fontWeight: 'var(--font-weight-medium)' }}>
              Artefato ainda nao disponivel
            </p>
            <p className="text-body-sm mt-1">
              Continue a elicitação no chat para gerar o documento de negocio.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default function SessionPage() {
  const { id: sessionId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('chat')
  const [desktopLayout, setDesktopLayout] = useState<DesktopLayoutMode>('split')
  const [artifactUpdated, setArtifactUpdated] = useState(false)
  const [linkedArtifactId, setLinkedArtifactId] = useState<string | null>(null)
  const [artifactView, setArtifactView] = useState<ArtifactView>('business')
  const [artifactPreview, setArtifactPreview] = useState('')
  const [isLoadingArtifactPreview, setIsLoadingArtifactPreview] = useState(false)
  const [isExportingArtifact, setIsExportingArtifact] = useState<ArtifactExportFormat | null>(null)
  const [artifactExportError, setArtifactExportError] = useState<string | null>(null)

  const {
    session,
    messages,
    isThinking,
    streamingMessage,
    error,
    sendMessage,
    markUserActivity,
    isKickstarting,
    isReturning,
    isLoadingSession,
    isLoadingMessages,
  } = useSession({ sessionId: sessionId ?? '' })

  // Fetch project data from session
  const { data: project } = useProject(session?.project_id ?? '')

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

  const handleOpenArtifact = useCallback((artifactId: string) => {
    navigate(`/artifacts/${artifactId}`)
  }, [navigate])

  const handleExportArtifact = useCallback(async (format: ArtifactExportFormat) => {
    if (!linkedArtifactId) return
    setArtifactExportError(null)
    setIsExportingArtifact(format)
    try {
      const result = await artifactsApi.exportFile(linkedArtifactId, format, artifactView, false)
      const url = URL.createObjectURL(result.blob)
      const link = document.createElement('a')
      link.href = url
      link.download = result.filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch {
      setArtifactExportError('Falha ao exportar o artefato. Tente novamente em alguns instantes.')
    } finally {
      setIsExportingArtifact(null)
    }
  }, [artifactView, linkedArtifactId])

  useEffect(() => {
    const projectId = session?.project_id
    if (!projectId) {
      setLinkedArtifactId(null)
      return
    }

    let active = true
    artifactsApi.listByProject(projectId)
      .then((res) => {
        if (!active) return
        const artifacts = res.data ?? []
        const fromSession = artifacts.find((a: Artifact) => a.session_id === sessionId)
        const fallback = artifacts[0] ?? null
        setLinkedArtifactId((fromSession ?? fallback)?.id ?? null)
      })
      .catch(() => {
        if (!active) return
        setLinkedArtifactId(null)
      })

    return () => {
      active = false
    }
  }, [session?.project_id, sessionId])

  useEffect(() => {
    if (!linkedArtifactId) {
      setArtifactPreview('')
      return
    }

    let active = true
    setIsLoadingArtifactPreview(true)
    artifactsApi.render(linkedArtifactId, artifactView)
      .then((res) => {
        if (!active) return
        setArtifactPreview(res.data.markdown ?? '')
      })
      .catch(() => {
        if (!active) return
        setArtifactPreview('')
      })
      .finally(() => {
        if (!active) return
        setIsLoadingArtifactPreview(false)
      })

    return () => {
      active = false
    }
  }, [artifactView, linkedArtifactId])

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

      {/* Desktop view mode */}
      <div className="hidden lg:flex items-center gap-2 px-4 py-2 border-b border-border bg-background">
        <button
          type="button"
          className="text-caption px-2 py-1 rounded-md border border-border hover:bg-muted transition-colors"
          style={desktopLayout === 'chat' ? { background: 'var(--rs-primary-light)', color: 'var(--rs-primary)' } : undefined}
          onClick={() => setDesktopLayout('chat')}
        >
          Somente chat
        </button>
        <button
          type="button"
          className="text-caption px-2 py-1 rounded-md border border-border hover:bg-muted transition-colors"
          style={desktopLayout === 'split' ? { background: 'var(--rs-primary-light)', color: 'var(--rs-primary)' } : undefined}
          onClick={() => setDesktopLayout('split')}
        >
          Dividir tela
        </button>
        <button
          type="button"
          className="text-caption px-2 py-1 rounded-md border border-border hover:bg-muted transition-colors"
          style={desktopLayout === 'artifact' ? { background: 'var(--rs-primary-light)', color: 'var(--rs-primary)' } : undefined}
          onClick={() => setDesktopLayout('artifact')}
        >
          Somente artefato
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex min-h-0">
        {/* Desktop layouts */}
        <div className="hidden lg:flex w-full min-h-0">
          {(desktopLayout === 'chat' || desktopLayout === 'split') && (
            <div className="flex flex-col" style={{ width: desktopLayout === 'split' ? '40%' : '100%', borderRight: desktopLayout === 'split' ? '1px solid var(--border)' : 'none' }}>
              <SessionChatPanel
                sessionId={sessionId}
                projectId={session?.project_id ?? ''}
                projectName={project?.name ?? 'Sessão de Elicitação'}
                projectDomain={project?.business_domain}
                sessionStatus={session?.status}
                messages={messages}
                isThinking={isThinking}
                streamingMessage={streamingMessage}
                error={error}
                sendMessage={sendMessage}
                markUserActivity={markUserActivity}
                isLoadingMessages={isLoadingMessages}
                navigate={navigate}
                onUploadSuccess={handleUploadSuccess}
                workflowPosition={session?.workflow_position ?? null}
                isKickstarting={isKickstarting}
                isReturning={isReturning}
              />
            </div>
          )}
          {(desktopLayout === 'artifact' || desktopLayout === 'split') && (
            <div className="flex flex-col" style={{ width: desktopLayout === 'split' ? '60%' : '100%' }}>
              <SessionArtifactPanel
                previewMarkdown={artifactPreview}
                isLoadingPreview={isLoadingArtifactPreview}
                artifactId={linkedArtifactId}
                activeView={artifactView}
                isExporting={isExportingArtifact}
                exportError={artifactExportError}
                onChangeView={setArtifactView}
                onExport={handleExportArtifact}
                onOpenArtifact={handleOpenArtifact}
              />
            </div>
          )}
        </div>

        {/* Mobile tabbed */}
        <div className="lg:hidden flex flex-col w-full min-h-0">
          {activeTab === 'chat' ? (
            <SessionChatPanel
              sessionId={sessionId}
              projectId={session?.project_id ?? ''}
              projectName={project?.name ?? 'Sessão de Elicitação'}
              projectDomain={project?.business_domain}
              sessionStatus={session?.status}
              messages={messages}
              isThinking={isThinking}
              streamingMessage={streamingMessage}
              error={error}
              sendMessage={sendMessage}
              markUserActivity={markUserActivity}
              isLoadingMessages={isLoadingMessages}
              navigate={navigate}
              onUploadSuccess={handleUploadSuccess}
              workflowPosition={session?.workflow_position ?? null}
              isKickstarting={isKickstarting}
              isReturning={isReturning}
            />
          ) : (
            <SessionArtifactPanel
              previewMarkdown={artifactPreview}
              isLoadingPreview={isLoadingArtifactPreview}
              artifactId={linkedArtifactId}
              activeView={artifactView}
              isExporting={isExportingArtifact}
              exportError={artifactExportError}
              onChangeView={setArtifactView}
              onExport={handleExportArtifact}
              onOpenArtifact={handleOpenArtifact}
            />
          )}
        </div>
      </div>
    </div>
  )
}
