/**
 * useSession — gating tests for isKickstarting (Story 7.1 AC 6) and
 * isReturning (Story 7.3 AC 5).
 *
 * Verifies that:
 *   - isKickstarting flips true while the kickstart stream is in flight
 *     and back to false on `done` (so SessionPage disables ChatInput).
 *   - isReturning flips true for paused sessions during return-greeting
 *     and back to false on `done`.
 *   - The "completed once" ref is set only on done, allowing React Strict
 *     Mode (or any abort-before-done) to safely re-fire the effect.
 */

import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import type { ReactNode } from 'react'

import { useSession } from '@/hooks/useSession'
import { sessionsApi } from '@/services/sessionsApi'
import * as sseClient from '@/services/sseClient'

vi.mock('@/services/sessionsApi', () => ({
  sessionsApi: {
    get: vi.fn(),
    listMessages: vi.fn(),
    updateStatus: vi.fn(),
  },
  KICKSTART_SSE_URL: 'http://test/kickstart',
  RETURN_GREETING_SSE_URL: 'http://test/return-greeting',
}))

const SESSION_ID = 'sess-test-1'

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  )
}

function activeSession() {
  return {
    data: {
      id: SESSION_ID,
      project_id: 'p-1',
      tenant_id: 't-1',
      workflow_id: 'w-1',
      workflow_position: { current_step: 1 },
      status: 'active' as const,
      artifact_state: null,
      message_count: 0,
      created_at: '2026-05-01T00:00:00Z',
      updated_at: '2026-05-01T00:00:00Z',
    },
  }
}

function pausedSession() {
  const s = activeSession()
  s.data.status = 'paused' as const
  return s
}

function emptyMessages() {
  return { data: { items: [], total: 0, page: 1, size: 200, pages: 0 } }
}

describe('useSession kickstart gating (Story 7.1 AC 6)', () => {
  beforeEach(() => {
    vi.mocked(sessionsApi.get).mockResolvedValue(activeSession() as any)
    vi.mocked(sessionsApi.listMessages).mockResolvedValue(emptyMessages() as any)
    vi.mocked(sessionsApi.updateStatus).mockResolvedValue(undefined as any)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('flips isKickstarting true while stream is running, false on done', async () => {
    let emit: ((event: sseClient.SSEEvent) => void) | null = null
    let resolveStream: (() => void) | null = null

    vi.spyOn(sseClient, 'streamKickstart').mockImplementation(
      (_sessionId, onEvent) => {
        emit = onEvent
        return new Promise((resolve) => {
          resolveStream = resolve
        })
      },
    )

    const { result } = renderHook(() => useSession({ sessionId: SESSION_ID }), {
      wrapper: makeWrapper(),
    })

    // Wait for queries to settle and effect to fire
    await waitFor(() => expect(emit).not.toBeNull())
    await waitFor(() => expect(result.current.isKickstarting).toBe(true))

    // Emit done event
    await act(async () => {
      emit!({ type: 'done', data: { content: '', done: true } })
      resolveStream!()
    })

    await waitFor(() => expect(result.current.isKickstarting).toBe(false))
  })

  it('does not block re-fire after abort (kickstartDoneRef stays false until done)', async () => {
    // Simulate first mount aborted before done — the effect's ref is the
    // gatekeeper; it must remain unset until 'done' so a second mount can retry.
    let callCount = 0
    vi.spyOn(sseClient, 'streamKickstart').mockImplementation(() => {
      callCount += 1
      return Promise.reject(Object.assign(new Error('aborted'), { name: 'AbortError' }))
    })

    const { unmount, rerender } = renderHook(
      () => useSession({ sessionId: SESSION_ID }),
      { wrapper: makeWrapper() },
    )

    await waitFor(() => expect(callCount).toBeGreaterThanOrEqual(1))
    const firstCallCount = callCount

    // Force the effect to re-run by rerendering with the same sessionId
    rerender()
    unmount()

    // The ref was not set (no done received), so a fresh mount should be
    // willing to fire again. We verify by re-rendering a new hook instance.
    const { result: secondResult } = renderHook(
      () => useSession({ sessionId: SESSION_ID }),
      { wrapper: makeWrapper() },
    )

    await waitFor(() => expect(callCount).toBeGreaterThan(firstCallCount))
    // Sanity: hook is mounted and tracking state
    expect(secondResult.current.isKickstarting).toBeDefined()
  })
})

describe('useSession return-greeting gating (Story 7.3 AC 5)', () => {
  beforeEach(() => {
    vi.mocked(sessionsApi.get).mockResolvedValue(pausedSession() as any)
    vi.mocked(sessionsApi.listMessages).mockResolvedValue(emptyMessages() as any)
    vi.mocked(sessionsApi.updateStatus).mockResolvedValue(undefined as any)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('flips isReturning true for paused session, false on done', async () => {
    let emit: ((event: sseClient.SSEEvent) => void) | null = null
    let resolveStream: (() => void) | null = null

    vi.spyOn(sseClient, 'streamReturnGreeting').mockImplementation(
      (_sessionId, onEvent) => {
        emit = onEvent
        return new Promise((resolve) => {
          resolveStream = resolve
        })
      },
    )

    const { result } = renderHook(() => useSession({ sessionId: SESSION_ID }), {
      wrapper: makeWrapper(),
    })

    await waitFor(() => expect(emit).not.toBeNull())
    await waitFor(() => expect(result.current.isReturning).toBe(true))

    await act(async () => {
      emit!({ type: 'done', data: { content: '', done: true } })
      resolveStream!()
    })

    await waitFor(() => expect(result.current.isReturning).toBe(false))
  })
})
