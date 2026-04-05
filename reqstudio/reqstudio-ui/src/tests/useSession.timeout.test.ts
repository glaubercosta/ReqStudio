import { act, renderHook } from '@testing-library/react'
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { INACTIVITY_TIMEOUT_MS, isInactivityExpired, useSession } from '@/hooks/useSession'
import { sessionsApi } from '@/services/sessionsApi'
import { streamElicit } from '@/services/sseClient'

const invalidateQueriesMock = vi.fn()

vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(({ queryKey }: { queryKey: string[] }) => {
    if (queryKey[0] === 'session') {
      return {
        data: {
          data: {
            id: 'sess-1',
            project_id: 'proj-1',
            workflow_id: 'wf-1',
            status: 'active',
            workflow_position: null,
            artifact_state: null,
            created_at: '2026-04-04T10:00:00Z',
            updated_at: '2026-04-04T10:00:00Z',
          },
        },
        isLoading: false,
      }
    }

    return {
      data: {
        data: {
          items: [],
          total: 0,
          page: 1,
          size: 200,
        },
      },
      isLoading: false,
    }
  }),
  useQueryClient: () => ({
    setQueryData: vi.fn(),
    invalidateQueries: invalidateQueriesMock,
  }),
}))

vi.mock('@/services/sessionsApi', async () => {
  const actual = await vi.importActual<typeof import('@/services/sessionsApi')>('@/services/sessionsApi')
  return {
    ...actual,
    sessionsApi: {
      ...actual.sessionsApi,
      updateStatus: vi.fn(),
    },
  }
})

vi.mock('@/services/sseClient', async () => {
  const actual = await vi.importActual<typeof import('@/services/sseClient')>('@/services/sseClient')
  return {
    ...actual,
    streamElicit: vi.fn(),
  }
})

const mockUpdateStatus = sessionsApi.updateStatus as unknown as ReturnType<typeof vi.fn>
const mockStreamElicit = streamElicit as unknown as ReturnType<typeof vi.fn>

describe('useSession inactivity timeout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-04-04T10:00:00Z'))
    window.sessionStorage.clear()

    mockUpdateStatus.mockResolvedValue({
      data: {
        id: 'sess-1',
        project_id: 'proj-1',
        workflow_id: 'wf-1',
        status: 'paused',
        workflow_position: null,
        artifact_state: null,
        created_at: '2026-04-04T10:00:00Z',
        updated_at: '2026-04-04T10:30:00Z',
      },
    })
    mockStreamElicit.mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('does not expire before 30 minutes of inactivity', () => {
    const lastActivity = 1_000_000
    const beforeTimeout = lastActivity + INACTIVITY_TIMEOUT_MS - 1
    expect(isInactivityExpired(lastActivity, beforeTimeout)).toBe(false)
  })

  it('expires exactly at 30 minutes of inactivity', () => {
    const lastActivity = 1_000_000
    const atTimeout = lastActivity + INACTIVITY_TIMEOUT_MS
    expect(isInactivityExpired(lastActivity, atTimeout)).toBe(true)
  })

  it('expires only after 30 full minutes without any activity', async () => {
    const { result } = renderHook(() => useSession({ sessionId: 'sess-1' }))

    await act(async () => {
      vi.advanceTimersByTime(INACTIVITY_TIMEOUT_MS - 1)
    })
    expect(result.current.error).toBeNull()

    await act(async () => {
      vi.advanceTimersByTime(1)
    })

    expect(result.current.error).toEqual({
      code: 'SESSION_INACTIVITY_TIMEOUT',
      message: 'Sessão expirada após 30 minutos de inatividade. Faça login novamente para retomar.',
    })
    expect(mockUpdateStatus).toHaveBeenCalledWith('sess-1', 'paused')
  })

  it('keeps the session alive while the user stays active', async () => {
    const { result } = renderHook(() => useSession({ sessionId: 'sess-1' }))

    await act(async () => {
      vi.advanceTimersByTime(INACTIVITY_TIMEOUT_MS - 5_000)
      window.dispatchEvent(new Event('pointerdown'))
      vi.advanceTimersByTime(INACTIVITY_TIMEOUT_MS - 5_000)
    })

    expect(result.current.error).toBeNull()
    expect(mockUpdateStatus).not.toHaveBeenCalledWith('sess-1', 'paused')
  })

  it('does not reset inactivity when the page becomes visible again after the limit', async () => {
    const visibilityStateSpy = vi
      .spyOn(document, 'visibilityState', 'get')
      .mockReturnValue('visible')

    const { result } = renderHook(() => useSession({ sessionId: 'sess-1' }))

    await act(async () => {
      vi.advanceTimersByTime(INACTIVITY_TIMEOUT_MS + 1_000)
      document.dispatchEvent(new Event('visibilitychange'))
    })

    expect(result.current.error?.code).toBe('SESSION_INACTIVITY_TIMEOUT')

    visibilityStateSpy.mockRestore()
  })

  it('blocks sends after inactivity timeout and keeps guided recovery error visible', async () => {
    const { result } = renderHook(() => useSession({ sessionId: 'sess-1' }))

    await act(async () => {
      vi.advanceTimersByTime(INACTIVITY_TIMEOUT_MS)
    })

    expect(result.current.error?.code).toBe('SESSION_INACTIVITY_TIMEOUT')

    await act(async () => {
      await result.current.sendMessage('Ainda estou aqui')
    })

    expect(mockStreamElicit).not.toHaveBeenCalled()
    expect(result.current.error?.message).toBe(
      'Sessão expirada após 30 minutos de inatividade. Faça login novamente para retomar.',
    )
  })

  it('preserves SESSION_EXPIRED recovery messaging instead of overwriting it with inactivity copy', async () => {
    mockStreamElicit.mockImplementationOnce(async (_sessionId, _content, onEvent) => {
      onEvent({
        type: 'error',
        data: {
          code: 'SESSION_EXPIRED',
          message: 'Sua sessão expirou. Faça login novamente para retomar.',
        },
      })
    })

    const { result } = renderHook(() => useSession({ sessionId: 'sess-1' }))

    await act(async () => {
      await result.current.sendMessage('Olá')
    })

    expect(result.current.error).toEqual({
      code: 'SESSION_EXPIRED',
      message: 'Sua sessão expirou. Faça login novamente para retomar.',
    })

    await act(async () => {
      await result.current.sendMessage('Tentar de novo')
    })

    expect(result.current.error).toEqual({
      code: 'SESSION_EXPIRED',
      message: 'Sua sessão expirou. Faça login novamente para retomar.',
    })
  })
})
