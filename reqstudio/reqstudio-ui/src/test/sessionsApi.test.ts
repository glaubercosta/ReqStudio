/**
 * sessionsApi.ts — testes dos endpoints de sessões (Story 5.6).
 *
 * Cobre: list, get, create, updateStatus, listMessages — verificando
 * URL, método HTTP, body enviado e payload retornado.
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { sessionsApi } from '@/services/sessionsApi'
import { setAccessToken } from '@/services/apiClient'

// ── Mock fetch helper ─────────────────────────────────────────────────────────

function stubFetch(body: unknown, status = 200) {
  const mock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })
  vi.stubGlobal('fetch', mock)
  return mock
}

const fakeSession = {
  id: 's1',
  project_id: 'p1',
  workflow_id: 'wf1',
  status: 'active',
  workflow_position: null,
  artifact_state: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const fakeMessage = {
  id: 'm1',
  session_id: 's1',
  role: 'user' as const,
  content: 'Hello',
  message_index: 0,
  created_at: '2026-01-01T00:00:00Z',
}

// ── sessionsApi.list ────────────────────────────────────────────────────────

describe('sessionsApi.list', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('calls GET /api/v1/projects/:projectId/sessions', async () => {
    const fetchMock = stubFetch({ data: { items: [fakeSession], total: 1, page: 1, size: 20 } })
    await sessionsApi.list('p1')
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/projects/p1/sessions'),
      expect.objectContaining({ credentials: 'include' }),
    )
  })

  it('returns session data correctly', async () => {
    stubFetch({ data: { items: [fakeSession], total: 1, page: 1, size: 20 } })
    const result = await sessionsApi.list('p1')
    expect(result.data.items[0].id).toBe('s1')
    expect(result.data.total).toBe(1)
  })
})

// ── sessionsApi.get ─────────────────────────────────────────────────────────

describe('sessionsApi.get', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('calls GET /api/v1/sessions/:sessionId', async () => {
    const fetchMock = stubFetch({ data: fakeSession })
    await sessionsApi.get('s1')
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/sessions/s1'),
      expect.anything(),
    )
  })

  it('returns session data', async () => {
    stubFetch({ data: fakeSession })
    const result = await sessionsApi.get('s1')
    expect(result.data.id).toBe('s1')
    expect(result.data.status).toBe('active')
  })
})

// ── sessionsApi.create ──────────────────────────────────────────────────────

describe('sessionsApi.create', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('calls POST /api/v1/projects/:projectId/sessions with empty body', async () => {
    const fetchMock = stubFetch({ data: fakeSession }, 201)
    await sessionsApi.create('p1')
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/projects/p1/sessions'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({}),
      }),
    )
  })

  it('returns the created session', async () => {
    stubFetch({ data: fakeSession }, 201)
    const result = await sessionsApi.create('p1')
    expect(result.data.id).toBe('s1')
    expect(result.data.project_id).toBe('p1')
  })
})

// ── sessionsApi.updateStatus ────────────────────────────────────────────────

describe('sessionsApi.updateStatus', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('calls PATCH /api/v1/sessions/:sessionId with status', async () => {
    const fetchMock = stubFetch({ data: { ...fakeSession, status: 'paused' } })
    await sessionsApi.updateStatus('s1', 'paused')
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/sessions/s1'),
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ status: 'paused' }),
      }),
    )
  })

  it('returns the updated session', async () => {
    stubFetch({ data: { ...fakeSession, status: 'completed' } })
    const result = await sessionsApi.updateStatus('s1', 'completed')
    expect(result.data.status).toBe('completed')
  })
})

// ── sessionsApi.listMessages ────────────────────────────────────────────────

describe('sessionsApi.listMessages', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('calls GET /api/v1/sessions/:sessionId/messages with default pagination', async () => {
    const fetchMock = stubFetch({ data: { items: [fakeMessage], total: 1, page: 1, size: 50 } })
    await sessionsApi.listMessages('s1')
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/sessions/s1/messages?page=1&size=50'),
      expect.anything(),
    )
  })

  it('supports custom pagination', async () => {
    const fetchMock = stubFetch({ data: { items: [], total: 0, page: 2, size: 10 } })
    await sessionsApi.listMessages('s1', 2, 10)
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/sessions/s1/messages?page=2&size=10'),
      expect.anything(),
    )
  })

  it('returns message data correctly', async () => {
    stubFetch({ data: { items: [fakeMessage], total: 1, page: 1, size: 50 } })
    const result = await sessionsApi.listMessages('s1')
    expect(result.data.items[0].content).toBe('Hello')
    expect(result.data.items[0].role).toBe('user')
  })
})
