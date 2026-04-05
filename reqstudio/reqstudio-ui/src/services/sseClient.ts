/**
 * SSE client for Elicitation Engine streaming (Story 5.7).
 *
 * Uses fetch + ReadableStream instead of EventSource because:
 *   - EventSource only supports GET; our endpoint is POST
 *   - We need Bearer auth headers
 *   - We need typed JSON parsing
 */

import {
  API_BASE,
  AUTH_LOGOUT_EVENT,
  getAccessToken,
  refreshAccessTokenOrNull,
  setAccessToken,
} from './apiClient'

export interface SSEChunk {
  content: string
  done: boolean
  metrics?: {
    input_tokens: number
    output_tokens: number
    cost_usd: number
    latency_ms: number
  } | null
}

export interface SSEError {
  code: string
  message: string
}

export type SSEEvent =
  | { type: 'message'; data: SSEChunk }
  | { type: 'done'; data: SSEChunk }
  | { type: 'error'; data: SSEError }

/**
 * Conecta ao endpoint SSE de elicitação e itera sobre os eventos.
 *
 * @param sessionId  ID da sessão ativa
 * @param content    Mensagem do usuário
 * @param onEvent    Callback para cada evento SSE
 * @param signal     AbortSignal para cancelamento
 */
export async function streamElicit(
  sessionId: string,
  content: string,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const createRequest = async () => {
    const token = getAccessToken()
    return fetch(`${API_BASE}/api/v1/sessions/${sessionId}/elicit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content }),
      credentials: 'include',
      signal,
    })
  }

  let res = await createRequest()

  // Access token expirou durante uso ativo: tenta refresh e repete 1x
  if (res.status === 401) {
    const refreshed = await refreshAccessTokenOrNull()
    if (refreshed) {
      res = await createRequest()
    } else {
      setAccessToken(null)
      window.dispatchEvent(new CustomEvent(AUTH_LOGOUT_EVENT))
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const defaultMessage = res.status === 401
      ? 'Sua sessão expirou. Faça login novamente para retomar.'
      : res.statusText
    const defaultCode = res.status === 401 ? 'SESSION_EXPIRED' : 'HTTP_ERROR'
    if (res.status === 401) {
      setAccessToken(null)
      window.dispatchEvent(new CustomEvent(AUTH_LOGOUT_EVENT))
    }
    onEvent({
      type: 'error',
      data: {
        code: body?.error?.code ?? defaultCode,
        message: body?.error?.message ?? defaultMessage,
      },
    })
    return
  }

  const reader = res.body?.getReader()
  if (!reader) return

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Parse SSE events from buffer
      const events = buffer.split('\n\n')
      buffer = events.pop() ?? '' // Keep incomplete event in buffer

      for (const block of events) {
        if (!block.trim()) continue

        let eventType = 'message'
        let data = ''

        for (const line of block.split('\n')) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7)
          } else if (line.startsWith('data: ')) {
            data = line.slice(6)
          }
        }

        if (data) {
          try {
            const parsed = JSON.parse(data)
            onEvent({ type: eventType as SSEEvent['type'], data: parsed })
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
