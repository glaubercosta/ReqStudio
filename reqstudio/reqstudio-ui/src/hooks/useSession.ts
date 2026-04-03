/**
 * useSession — hook para gerenciar sessão de elicitação (Stories 5.6, 5.7, 5.8).
 *
 * Combina:
 *   - TanStack Query para session data e messages
 *   - SSE client para streaming de respostas
 *   - Estado local para typing indicator e streaming content
 *   - Auto-pause on exit / auto-resume on mount (Story 5.8)
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { API_BASE } from '@/services/apiClient'
import { sessionsApi, type Message } from '@/services/sessionsApi'
import { streamElicit, type SSEEvent } from '@/services/sseClient'

interface UseSessionOptions {
  sessionId: string
}

export interface StreamingMessage {
  content: string
  isStreaming: boolean
}

export function useSession({ sessionId }: UseSessionOptions) {
  const queryClient = useQueryClient()
  const [isThinking, setIsThinking] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState<StreamingMessage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

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

  // ── Auto-pause on exit / resume on mount (Story 5.8) ──
  useEffect(() => {
    if (!sessionId || !session) return
    if (session.status === 'completed') return

    // Resume if paused
    if (session.status === 'paused') {
      sessionsApi.updateStatus(sessionId, 'active').then(() => {
        queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
      }).catch(() => { /* silenciar erros de resume */ })
    }

    // Pause on page hide/close
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        // Use sendBeacon for reliability on page close
        const token = localStorage.getItem('access_token')
        const url = `${API_BASE}/api/v1/sessions/${sessionId}`
        const body = JSON.stringify({ status: 'paused' })
        // fetch with keepalive for reliability on page close
        fetch(url, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body,
          keepalive: true,
          credentials: 'include',
        }).catch(() => { /* best effort */ })
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      // Pause on unmount (navigating away)
      if (session.status === 'active') {
        sessionsApi.updateStatus(sessionId, 'paused').catch(() => {})
      }
    }
  }, [sessionId, session?.status, session, queryClient])

  // ── Send message (SSE streaming) ──
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isThinking) return

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
          setStreamingMessage(prev => ({
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
          setError(event.data.message ?? 'Erro ao processar resposta da IA.')
          setIsThinking(false)
          setStreamingMessage(null)
        }
      }, abortRef.current.signal)
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setError('Conexão perdida. Tente novamente.')
        setIsThinking(false)
        setStreamingMessage(null)
      }
    }
  }, [sessionId, messages.length, isThinking, queryClient])

  // ── Cancel ──
  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setIsThinking(false)
    setStreamingMessage(null)
  }, [])

  // ── Pause (manual) ──
  const pause = useCallback(async () => {
    if (!sessionId || session?.status !== 'active') return
    await sessionsApi.updateStatus(sessionId, 'paused')
    queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
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
    isLoadingSession: sessionQuery.isLoading,
    isLoadingMessages: messagesQuery.isLoading,
  }
}
