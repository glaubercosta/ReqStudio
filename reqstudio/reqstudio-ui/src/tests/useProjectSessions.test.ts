/**
 * Testes do hook real useProjectSessions — Story 5.5-2.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import type { Session } from '@/services/sessionsApi'
import { useProjectSessions } from '@/hooks/useProjectSessions'
import { sessionsApi } from '@/services/sessionsApi'

vi.mock('@/services/sessionsApi', async () => {
  const actual = await vi.importActual<typeof import('@/services/sessionsApi')>('@/services/sessionsApi')
  return {
    ...actual,
    sessionsApi: {
      ...actual.sessionsApi,
      list: vi.fn(),
    },
  }
})

const mockList = sessionsApi.list as unknown as ReturnType<typeof vi.fn>

const makeSession = (overrides: Partial<Session> = {}): Session => ({
  id: 'sess-1',
  project_id: 'proj-1',
  workflow_id: 'wf-1',
  status: 'active',
  workflow_position: null,
  artifact_state: null,
  created_at: '2026-04-01T10:00:00Z',
  updated_at: '2026-04-01T10:00:00Z',
  ...overrides,
})

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children)
  }
}

describe('useProjectSessions (hook real)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('retorna apenas active/paused e ordena por updated_at desc', async () => {
    mockList.mockResolvedValueOnce({
      data: {
        items: [
          makeSession({ id: 'completed', status: 'completed', updated_at: '2026-04-03T10:00:00Z' }),
          makeSession({ id: 'old-active', status: 'active', updated_at: '2026-04-01T10:00:00Z' }),
          makeSession({ id: 'new-paused', status: 'paused', updated_at: '2026-04-04T10:00:00Z' }),
        ],
      },
    })

    const { result } = renderHook(() => useProjectSessions('proj-1'), {
      wrapper: makeWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.map((s) => s.id)).toEqual(['new-paused', 'old-active'])
    expect(mockList).toHaveBeenCalledWith('proj-1')
  })

  it('retorna vazio quando nao ha sessao retomavel', async () => {
    mockList.mockResolvedValueOnce({
      data: {
        items: [
          makeSession({ id: 'completed-1', status: 'completed' }),
          makeSession({ id: 'completed-2', status: 'completed' }),
        ],
      },
    })

    const { result } = renderHook(() => useProjectSessions('proj-1'), {
      wrapper: makeWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })

  it('nao executa query sem projectId', () => {
    renderHook(() => useProjectSessions(''), {
      wrapper: makeWrapper(),
    })

    expect(mockList).not.toHaveBeenCalled()
  })
})
