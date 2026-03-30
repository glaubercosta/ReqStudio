/**
 * useProjects — testes do hook com TanStack Query (Story 3.2).
 *
 * Usa renderHook + mock do projectsApi para testar os 3 estados:
 * loading, sucesso e erro.
 */
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useProjects } from '@/hooks/useProjects'
import * as projectsApi from '@/services/projectsApi'
import { ReqStudioApiError } from '@/services/apiClient'
import type { ReactNode } from 'react'

vi.mock('@/services/projectsApi', async (importOriginal) => {
  const actual = await importOriginal<typeof projectsApi>()
  return {
    ...actual,
    projectsApi: { ...actual.projectsApi, list: vi.fn() },
  }
})

const mockList = vi.mocked(projectsApi.projectsApi.list)

const fakeListData: projectsApi.ProjectListData = {
  items: [
    {
      id: 'p1',
      name: 'Projeto Hook',
      description: null,
      business_domain: 'Saúde',
      status: 'active',
      progress_summary: null,
      tenant_id: 't1',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  size: 20,
  pages: 1,
}

// Wrapper com QueryClient novo por teste
function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  )
}

describe('useProjects', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('retorna isLoading=true inicialmente', () => {
    mockList.mockResolvedValue({ data: fakeListData })
    const { result } = renderHook(() => useProjects(), { wrapper: makeWrapper() })
    expect(result.current.isLoading).toBe(true)
  })

  it('retorna dados após fetch bem-sucedido', async () => {
    mockList.mockResolvedValue({ data: fakeListData })
    const { result } = renderHook(() => useProjects(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.data).toEqual(fakeListData)
    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].name).toBe('Projeto Hook')
  })

  it('retorna isError=true quando a API falha', async () => {
    mockList.mockRejectedValue(
      new ReqStudioApiError(
        { code: 'INTERNAL_ERROR', message: 'Servidor indisponível', help: '', actions: [], severity: 'recoverable' },
        500,
      ),
    )
    const { result } = renderHook(() => useProjects(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.data).toBeUndefined()
  })

  it('chama list com o status correto', async () => {
    mockList.mockResolvedValue({ data: { ...fakeListData, items: [] } })
    renderHook(() => useProjects('archived'), { wrapper: makeWrapper() })

    await waitFor(() => expect(mockList).toHaveBeenCalledWith('archived'))
  })

  it('usa "active" como status default', async () => {
    mockList.mockResolvedValue({ data: fakeListData })
    renderHook(() => useProjects(), { wrapper: makeWrapper() })

    await waitFor(() => expect(mockList).toHaveBeenCalledWith('active'))
  })
})
