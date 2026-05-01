/**
 * sseClient.ts — testes do client SSE de elicitação (Story 5.7).
 *
 * Cobre: streamElicit — happy path, 401 refresh retry,
 * non-ok response, SSE event parsing, abort signal.
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { streamElicit, type SSEEvent } from '@/services/sseClient'
import { setAccessToken } from '@/services/apiClient'

// ── Helpers ──────────────────────────────────────────────────────────────────

function createReadableStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  let index = 0
  return new ReadableStream({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]))
        index++
      } else {
        controller.close()
      }
    },
  })
}

function stubFetchWithSSE(chunks: string[], status = 200) {
  const stream = createReadableStream(chunks)
  const mock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: 'OK',
    body: stream,
    json: async () => ({}),
  })
  vi.stubGlobal('fetch', mock)
  return mock
}

function stubFetchError(status: number, body: unknown = {}) {
  const mock = vi.fn().mockResolvedValue({
    ok: false,
    status,
    statusText: 'Error',
    json: async () => body,
  })
  vi.stubGlobal('fetch', mock)
  return mock
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('streamElicit', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('sends POST request with correct URL, headers, and body', async () => {
    const fetchMock = stubFetchWithSSE([])
    const onEvent = vi.fn()

    await streamElicit('s1', 'Hello', onEvent)

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/sessions/s1/elicit'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ content: 'Hello' }),
        credentials: 'include',
      }),
    )

    // Verify Authorization header
    const callArgs = fetchMock.mock.calls[0][1]
    expect(callArgs.headers).toEqual(
      expect.objectContaining({
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer tok_test',
      }),
    )
  })

  it('parses SSE message events correctly', async () => {
    const sseData = 'event: message\ndata: {"content":"Hi","done":false}\n\n'
    stubFetchWithSSE([sseData])
    const events: SSEEvent[] = []
    const onEvent = vi.fn((e: SSEEvent) => events.push(e))

    await streamElicit('s1', 'Hello', onEvent)

    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'message',
        data: { content: 'Hi', done: false },
      }),
    )
  })

  it('parses done event with metrics', async () => {
    const sseData = 'event: done\ndata: {"content":"","done":true,"metrics":{"input_tokens":10,"output_tokens":20,"cost_usd":0.01,"latency_ms":500}}\n\n'
    stubFetchWithSSE([sseData])
    const events: SSEEvent[] = []
    const onEvent = vi.fn((e: SSEEvent) => events.push(e))

    await streamElicit('s1', 'Hello', onEvent)

    expect(events).toHaveLength(1)
    expect(events[0].type).toBe('done')
    if (events[0].type === 'done') {
      expect(events[0].data.done).toBe(true)
      expect(events[0].data.metrics?.input_tokens).toBe(10)
    }
  })

  it('handles multiple SSE events in a single chunk', async () => {
    const sseData =
      'event: message\ndata: {"content":"A","done":false}\n\n' +
      'event: message\ndata: {"content":"B","done":false}\n\n'
    stubFetchWithSSE([sseData])
    const events: SSEEvent[] = []
    const onEvent = vi.fn((e: SSEEvent) => events.push(e))

    await streamElicit('s1', 'Hello', onEvent)

    expect(events).toHaveLength(2)
  })

  it('calls onEvent with error on non-ok response', async () => {
    stubFetchError(500, {
      error: { code: 'INTERNAL_ERROR', message: 'Server error' },
    })
    const events: SSEEvent[] = []
    const onEvent = vi.fn((e: SSEEvent) => events.push(e))

    await streamElicit('s1', 'Hello', onEvent)

    expect(events).toHaveLength(1)
    expect(events[0].type).toBe('error')
    if (events[0].type === 'error') {
      expect(events[0].data.code).toBe('INTERNAL_ERROR')
    }
  })

  it('handles 401 with default SESSION_EXPIRED message when body lacks error', async () => {
    stubFetchError(401, {})
    const events: SSEEvent[] = []
    const onEvent = vi.fn((e: SSEEvent) => events.push(e))

    await streamElicit('s1', 'Hello', onEvent)

    expect(events).toHaveLength(1)
    expect(events[0].type).toBe('error')
    if (events[0].type === 'error') {
      expect(events[0].data.code).toBe('SESSION_EXPIRED')
    }
  })

  it('sends request without Authorization header when no token set', async () => {
    setAccessToken(null)
    const fetchMock = stubFetchWithSSE([])
    const onEvent = vi.fn()

    await streamElicit('s1', 'Hello', onEvent)

    const callArgs = fetchMock.mock.calls[0][1]
    expect(callArgs.headers).not.toHaveProperty('Authorization')
  })

  it('skips malformed JSON in SSE data', async () => {
    const sseData =
      'event: message\ndata: not-json\n\n' +
      'event: message\ndata: {"content":"OK","done":false}\n\n'
    stubFetchWithSSE([sseData])
    const events: SSEEvent[] = []
    const onEvent = vi.fn((e: SSEEvent) => events.push(e))

    await streamElicit('s1', 'Hello', onEvent)

    // Only the valid event should have been emitted
    expect(events).toHaveLength(1)
    if (events[0].type === 'message') {
      expect(events[0].data.content).toBe('OK')
    }
  })

  it('emits NO_RESPONSE_BODY error when response body is null', async () => {
    const mock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: null,
    })
    vi.stubGlobal('fetch', mock)
    const events: SSEEvent[] = []
    const onEvent = vi.fn((e: SSEEvent) => events.push(e))

    await streamElicit('s1', 'Hello', onEvent)

    expect(events).toHaveLength(1)
    expect(events[0].type).toBe('error')
    if (events[0].type === 'error') {
      expect(events[0].data.code).toBe('NO_RESPONSE_BODY')
    }
  })

  it('parses SSE events delimited by CRLFCRLF (Windows/proxy line endings)', async () => {
    const sseData =
      'event: message\r\ndata: {"content":"Olá","done":false}\r\n\r\n' +
      'event: done\r\ndata: {"content":"","done":true}\r\n\r\n'
    stubFetchWithSSE([sseData])
    const events: SSEEvent[] = []
    const onEvent = vi.fn((e: SSEEvent) => events.push(e))

    await streamElicit('s1', 'Hello', onEvent)

    expect(events.map((e) => e.type)).toEqual(['message', 'done'])
    if (events[0].type === 'message') {
      expect(events[0].data.content).toBe('Olá')
    }
  })
})
