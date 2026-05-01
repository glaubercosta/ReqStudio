/**
 * useSession — hook para gerenciar sessão de elicitação (Stories 5.6, 5.7, 5.8).
 *
 * Combina:
 *   - TanStack Query para session data e messages
 *   - SSE client para streaming de respostas
 *   - Estado local para typing indicator e streaming content
 *   - Auto-resume de sessão pausada
 *   - Timeout de inatividade do usuário (Story 6.0c): 30 min
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { sessionsApi, type Message } from '@/services/sessionsApi'
import { streamElicit, streamKickstart, streamReturnGreeting, type SSEEvent } from '@/services/sseClient'

interface UseSessionOptions {
  sessionId: string
}

export interface StreamingMessage {
  content: string
  isStreaming: boolean
}

export interface SessionUiError {
  code: string
  message: string
}

export const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000
const LAST_ACTIVITY_STORAGE_PREFIX = 'session_last_activity_'

export function isInactivityExpired(
  lastActivityAtMs: number,
  nowMs: number,
  timeoutMs = INACTIVITY_TIMEOUT_MS,
): boolean {
  return nowMs - lastActivityAtMs >= timeoutMs
}

export function useSession({ sessionId }: UseSessionOptions) {
  const queryClient = useQueryClient()
  const [isThinking, setIsThinking] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState<StreamingMessage | null>(null)
  const [error, setError] = useState<SessionUiError | null>(null)
  const [sessionTimedOut, setSessionTimedOut] = useState(false)
  const [sessionEndCode, setSessionEndCode] = useState<string | null>(null)
  const [isKickstarting, setIsKickstarting] = useState(false)
  const [isReturning, setIsReturning] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const kickstartDoneRef = useRef(false)
  const returnGreetingDoneRef = useRef(false)
  const lastActivityAtRef = useRef<number>(0)
  const inactivityTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Session data ──
  const sessionQuery = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => sessionsApi.get(sessionId),
    enabled: !!sessionId,
  })

  // ── Messages ──
  const messagesQuery = useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => sessionsApi.listMessages(sessionId, 1, 200),
    enabled: !!sessionId,
  })

  const messages: Message[] = messagesQuery.data?.data?.items ?? []
  const session = sessionQuery.data?.data ?? null
  const storageKey = `${LAST_ACTIVITY_STORAGE_PREFIX}${sessionId}`

  const getPersistedLastActivity = useCallback((): number => {
    if (!sessionId) return Date.now()
    const raw = window.sessionStorage.getItem(storageKey)
    if (!raw) return Date.now()
    const parsed = Number(raw)
    return Number.isFinite(parsed) ? parsed : Date.now()
  }, [sessionId, storageKey])

  const clearInactivityTimer = useCallback(() => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current)
      inactivityTimerRef.current = null
    }
  }, [])

  const triggerInactivityTimeout = useCallback(async () => {
    setSessionTimedOut(true)
    setSessionEndCode('SESSION_INACTIVITY_TIMEOUT')
    setIsThinking(false)
    setStreamingMessage(null)
    setError({
      code: 'SESSION_INACTIVITY_TIMEOUT',
      message: 'Sessão expirada após 30 minutos de inatividade. Faça login novamente para retomar.',
    })
    abortRef.current?.abort()
    window.sessionStorage.removeItem(storageKey)

    if (session?.status === 'active') {
      await sessionsApi.updateStatus(sessionId, 'paused').catch((err) => {
        console.warn('[useSession] Failed to pause on inactivity timeout:', sessionId, err)
      })
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    }
  }, [queryClient, session?.status, sessionId, storageKey])

  const scheduleInactivityTimer = useCallback(() => {
    clearInactivityTimer()
    inactivityTimerRef.current = setTimeout(async () => {
      if (isInactivityExpired(lastActivityAtRef.current, Date.now())) {
        await triggerInactivityTimeout()
      }
    }, INACTIVITY_TIMEOUT_MS)
  }, [clearInactivityTimer, triggerInactivityTimeout])

  const markUserActivity = useCallback(() => {
    if (session?.status === 'completed') return
    const now = Date.now()
    lastActivityAtRef.current = now
    if (sessionId) {
      window.sessionStorage.setItem(storageKey, String(now))
    }
    scheduleInactivityTimer()
  }, [scheduleInactivityTimer, session?.status, sessionId, storageKey])

  // ── Kickstart — abertura proativa da Mary no primeiro acesso (Story 7.1) ──
  useEffect(() => {
    if (!sessionId || !session) return
    if (session.status === 'completed' || session.status === 'paused') return
    if (messagesQuery.isLoading || !messagesQuery.isSuccess) return
    if (messages.length > 0) return
    if (isKickstarting || kickstartDoneRef.current) return

    // ref is set to true ONLY in the 'done' branch, so an abort/error during
    // the first effect run (typical in React Strict Mode) leaves it false and
    // the effect can re-fire on the second mount instead of being silently blocked.
    const abortCtrl = new AbortController()

    queueMicrotask(() => {
      if (abortCtrl.signal.aborted) return
      setIsKickstarting(true)
      setStreamingMessage({ content: '', isStreaming: true })
    })

    streamKickstart(sessionId, (event: SSEEvent) => {
      if (event.type === 'message') {
        setStreamingMessage((prev) => ({
          content: (prev?.content ?? '') + event.data.content,
          isStreaming: true,
        }))
      } else if (event.type === 'done') {
        kickstartDoneRef.current = true
        setStreamingMessage(null)
        setIsKickstarting(false)
        queryClient.invalidateQueries({ queryKey: ['messages', sessionId] })
        queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
      } else if (event.type === 'error') {
        setStreamingMessage(null)
        setIsKickstarting(false)
        queryClient.invalidateQueries({ queryKey: ['messages', sessionId] })
      }
    }, abortCtrl.signal).catch((err) => {
      if ((err as Error).name !== 'AbortError') {
        console.warn('[useSession] Kickstart stream failed:', sessionId, err)
      }
      setStreamingMessage(null)
      setIsKickstarting(false)
    })

    return () => {
      abortCtrl.abort()
    }
  }, [
    sessionId,
    session,
    session?.status,
    messages.length,
    messagesQuery.isLoading,
    messagesQuery.isSuccess,
    isKickstarting,
    queryClient,
  ])

  // ── Return greeting — retomada com contexto (Story 7.3) ──
  useEffect(() => {
    if (!sessionId || !session) return
    if (session.status !== 'paused') return
    if (sessionTimedOut) return
    if (isReturning || returnGreetingDoneRef.current) return

    // ref is set to true ONLY in the 'done' branch — see kickstart effect above
    // for the rationale (React Strict Mode compatibility).
    const abortCtrl = new AbortController()

    queueMicrotask(() => {
      if (abortCtrl.signal.aborted) return
      setIsReturning(true)
      setStreamingMessage({ content: '', isStreaming: true })
    })

    streamReturnGreeting(sessionId, (event: SSEEvent) => {
      if (event.type === 'message') {
        setStreamingMessage((prev) => ({
          content: (prev?.content ?? '') + event.data.content,
          isStreaming: true,
        }))
      } else if (event.type === 'done') {
        returnGreetingDoneRef.current = true
        setStreamingMessage(null)
        setIsReturning(false)
        queryClient.invalidateQueries({ queryKey: ['messages', sessionId] })
        queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
      } else if (event.type === 'error') {
        // Fallback silencioso: resume via API REST
        setStreamingMessage(null)
        setIsReturning(false)
        sessionsApi.updateStatus(sessionId, 'active').catch((err) => {
          console.warn('[useSession] Failed to resume after return-greeting error:', sessionId, err)
        })
        queryClient.invalidateQueries({ queryKey: ['messages', sessionId] })
        queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
      }
    }, abortCtrl.signal).catch((err) => {
      if ((err as Error).name !== 'AbortError') {
        console.warn('[useSession] Return greeting stream failed:', sessionId, err)
      }
      setStreamingMessage(null)
      setIsReturning(false)
    })

    return () => {
      abortCtrl.abort()
    }
  }, [sessionId, session, session?.status, sessionTimedOut, isReturning, queryClient])

  // ── Pause on unmount (navigating away) — best effort ──
  useEffect(() => {
    if (!sessionId || !session) return
    if (session.status === 'completed') return
    if (sessionTimedOut) return

    return () => {
      if (session.status === 'active') {
        sessionsApi.updateStatus(sessionId, 'paused').catch((err) => {
          console.warn('[useSession] Failed to pause session on unmount:', sessionId, err)
        })
      }
    }
  }, [sessionId, session?.status, session, sessionTimedOut])

  // ── Inatividade do usuário (30 min) ──
  useEffect(() => {
    if (!sessionId || !session || session.status === 'completed') return
    if (sessionTimedOut) return

    lastActivityAtRef.current = getPersistedLastActivity()
    scheduleInactivityTimer()

    const onActivity = () => markUserActivity()
    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        const now = Date.now()
        if (isInactivityExpired(lastActivityAtRef.current, now)) {
          void triggerInactivityTimeout()
          return
        }
        scheduleInactivityTimer()
      }
    }

    window.addEventListener('pointerdown', onActivity, { passive: true })
    window.addEventListener('keydown', onActivity, { passive: true })
    window.addEventListener('scroll', onActivity, { passive: true })
    document.addEventListener('visibilitychange', onVisibilityChange)

    return () => {
      clearInactivityTimer()
      window.removeEventListener('pointerdown', onActivity)
      window.removeEventListener('keydown', onActivity)
      window.removeEventListener('scroll', onActivity)
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [
    clearInactivityTimer,
    getPersistedLastActivity,
    markUserActivity,
    scheduleInactivityTimer,
    session,
    sessionId,
    sessionTimedOut,
    triggerInactivityTimeout,
  ])

  // ── Send message (SSE streaming) ──
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isThinking || sessionTimedOut) {
      if (sessionTimedOut) {
        const expiredCode = sessionEndCode === 'SESSION_EXPIRED'
          ? 'SESSION_EXPIRED'
          : 'SESSION_INACTIVITY_TIMEOUT'
        setError({
          code: expiredCode,
          message: expiredCode === 'SESSION_EXPIRED'
            ? 'Sua sessão expirou. Faça login novamente para retomar.'
            : 'Sessão expirada após 30 minutos de inatividade. Faça login novamente para retomar.',
        })
      }
      return
    }

    markUserActivity()

    // Optimistic: add user message immediately
    const optimisticUserMsg: Message = {
      id: `temp-${Date.now()}`,
      session_id: sessionId,
      role: 'user',
      content,
      message_index: messages.length,
      created_at: new Date().toISOString(),
    }

    // Update cache optimistically
    queryClient.setQueryData(['messages', sessionId], (old: unknown) => {
      const prev = old as { data: { items: Message[] } } | undefined
      return {
        data: {
          ...prev?.data,
          items: [...(prev?.data?.items ?? []), optimisticUserMsg],
        },
      }
    })

    setIsThinking(true)
    setError(null)
    setStreamingMessage({ content: '', isStreaming: true })

    // Abort controller for cancellation
    abortRef.current = new AbortController()

    try {
      await streamElicit(sessionId, content, (event: SSEEvent) => {
        if (event.type === 'message') {
          setStreamingMessage((prev) => ({
            content: (prev?.content ?? '') + event.data.content,
            isStreaming: true,
          }))
        } else if (event.type === 'done') {
          // Clear streaming message BEFORE refetch to avoid duplicate
          setStreamingMessage(null)
          setIsThinking(false)
          // Refresh messages and session from server (source of truth)
          queryClient.invalidateQueries({ queryKey: ['messages', sessionId] })
          queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
        } else if (event.type === 'error') {
          const isExpired = event.data.code === 'SESSION_EXPIRED'
          if (isExpired) {
            setSessionEndCode('SESSION_EXPIRED')
          }
          setError({
            code: event.data.code ?? 'STREAM_ERROR',
            message: event.data.message ?? 'Erro ao processar resposta da IA.',
          })
          if (isExpired) {
            setSessionTimedOut(true)
          }
          setIsThinking(false)
          setStreamingMessage(null)
          queryClient.invalidateQueries({ queryKey: ['messages', sessionId] })
        }
      }, abortRef.current.signal)
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setError({
          code: 'STREAM_ERROR',
          message: 'Conexão perdida. Tente novamente.',
        })
        setIsThinking(false)
        setStreamingMessage(null)
        queryClient.invalidateQueries({ queryKey: ['messages', sessionId] })
      }
    }
  }, [sessionId, messages.length, isThinking, queryClient, markUserActivity, sessionTimedOut, sessionEndCode])

  // ── Cancel ──
  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setIsThinking(false)
    setStreamingMessage(null)
  }, [])

  // ── Pause (manual) ──
  const pause = useCallback(async () => {
    if (!sessionId || session?.status !== 'active') return
    try {
      await sessionsApi.updateStatus(sessionId, 'paused')
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    } catch (err) {
      console.error('[useSession] Failed to pause session:', sessionId, err)
      setError({
        code: 'PAUSE_ERROR',
        message: 'Não foi possível pausar a sessão. Tente novamente.',
      })
    }
  }, [sessionId, session?.status, queryClient])

  return {
    session,
    messages,
    isThinking,
    streamingMessage,
    error,
    sendMessage,
    cancel,
    pause,
    markUserActivity,
    isKickstarting,
    isReturning,
    isLoadingSession: sessionQuery.isLoading,
    isLoadingMessages: messagesQuery.isLoading,
  }
}
