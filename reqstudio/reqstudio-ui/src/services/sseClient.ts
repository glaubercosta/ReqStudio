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

// SSE event delimiter is two consecutive line breaks; line-end may be LF or CRLF
// (per spec). The previous implementation split only on `\n\n`, which silently
// dropped events on servers/proxies that emit CRLF.
const SSE_EVENT_SEPARATOR = /\r?\n\r?\n/
const SSE_LINE_SEPARATOR = /\r?\n/

async function parseSseStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: SSEEvent) => void,
): Promise<void> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split(SSE_EVENT_SEPARATOR)
      buffer = events.pop() ?? ''

      for (const block of events) {
        if (!block.trim()) continue

        let eventType = 'message'
        const dataLines: string[] = []

        for (const line of block.split(SSE_LINE_SEPARATOR)) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7)
          } else if (line.startsWith('data: ')) {
            dataLines.push(line.slice(6))
          } else if (line.startsWith('data:')) {
            // Per SSE spec, "data:" without space is also valid
            dataLines.push(line.slice(5))
          }
        }

        if (dataLines.length > 0) {
          const data = dataLines.join('\n')
          try {
            const parsed = JSON.parse(data)
            onEvent({ type: eventType as SSEEvent['type'], data: parsed })
          } catch {
            console.warn(`[SSE] Malformed JSON in event "${eventType}", data length: ${data.length}`)
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

function emitNoBodyError(onEvent: (event: SSEEvent) => void): void {
  onEvent({
    type: 'error',
    data: {
      code: 'NO_RESPONSE_BODY',
      message: 'Servidor retornou resposta sem conteúdo.',
    },
  })
}

/**
 * Conecta ao endpoint SSE de kickstart e itera sobre os eventos (Story 7.1).
 *
 * @param sessionId  ID da sessão ativa
 * @param onEvent    Callback para cada evento SSE
 * @param signal     AbortSignal para cancelamento
 */
export async function streamKickstart(
  sessionId: string,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const createRequest = async () => {
    const token = getAccessToken()
    return fetch(`${API_BASE}/api/v1/sessions/${sessionId}/kickstart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({}),
      credentials: 'include',
      signal,
    })
  }

  let res = await createRequest()

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
    onEvent({
      type: 'error',
      data: {
        code: body?.error?.code ?? 'HTTP_ERROR',
        message: body?.error?.message ?? res.statusText,
      },
    })
    return
  }

  if (!res.body) {
    emitNoBodyError(onEvent)
    return
  }

  await parseSseStream(res.body, onEvent)
}

/**
 * Conecta ao endpoint SSE de return-greeting e itera sobre os eventos (Story 7.3).
 *
 * @param sessionId  ID da sessão pausada
 * @param onEvent    Callback para cada evento SSE
 * @param signal     AbortSignal para cancelamento
 */
export async function streamReturnGreeting(
  sessionId: string,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const createRequest = async () => {
    const token = getAccessToken()
    return fetch(`${API_BASE}/api/v1/sessions/${sessionId}/return-greeting`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({}),
      credentials: 'include',
      signal,
    })
  }

  let res = await createRequest()

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
    onEvent({
      type: 'error',
      data: {
        code: body?.error?.code ?? 'HTTP_ERROR',
        message: body?.error?.message ?? res.statusText,
      },
    })
    return
  }

  if (!res.body) {
    emitNoBodyError(onEvent)
    return
  }

  await parseSseStream(res.body, onEvent)
}

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

  if (!res.body) {
    emitNoBodyError(onEvent)
    return
  }

  await parseSseStream(res.body, onEvent)
}
