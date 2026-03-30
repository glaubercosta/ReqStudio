/**
 * projectsApi.ts — testes dos endpoints de projetos (Story 3.1 / 3.2).
 *
 * Cobre: list, get, create, update — verificando URL, método HTTP,
 * body enviado e payload retornado.
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { projectsApi } from '@/services/projectsApi'
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

const fakeProject = {
  id: 'p1',
  name: 'Projeto API',
  description: 'Desc',
  business_domain: 'Saúde',
  status: 'active' as const,
  progress_summary: null,
  tenant_id: 't1',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('projectsApi.list', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('chama GET /api/v1/projects com status e paginação', async () => {
    const fetchMock = stubFetch({ data: { items: [fakeProject], total: 1, page: 1, size: 20, pages: 1 } })

    await projectsApi.list('active', 1, 20)

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/projects?status=active&page=1&size=20'),
      expect.objectContaining({ credentials: 'include' }),
    )
  })

  it('usa "active" como status default', async () => {
    const fetchMock = stubFetch({ data: { items: [], total: 0, page: 1, size: 20, pages: 0 } })
    await projectsApi.list()
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('status=active'),
      expect.anything(),
    )
  })

  it('retorna os dados corretamente', async () => {
    stubFetch({ data: { items: [fakeProject], total: 1, page: 1, size: 20, pages: 1 } })
    const result = await projectsApi.list()
    expect(result.data.items[0].name).toBe('Projeto API')
    expect(result.data.total).toBe(1)
  })
})

describe('projectsApi.get', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('chama GET /api/v1/projects/:id', async () => {
    const fetchMock = stubFetch({ data: fakeProject })
    await projectsApi.get('p1')
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/projects/p1'),
      expect.anything(),
    )
  })

  it('retorna os dados do projeto', async () => {
    stubFetch({ data: fakeProject })
    const result = await projectsApi.get('p1')
    expect(result.data.id).toBe('p1')
    expect(result.data.name).toBe('Projeto API')
  })

  it('lança ReqStudioApiError em 404', async () => {
    stubFetch(
      { error: { code: 'RESOURCE_NOT_FOUND', message: 'Projeto não encontrado', help: '', actions: [], severity: 'warning' } },
      404,
    )
    await expect(projectsApi.get('nao-existe')).rejects.toThrow('Projeto não encontrado')
  })
})

describe('projectsApi.create', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('chama POST /api/v1/projects com o payload correto', async () => {
    const fetchMock = stubFetch({ data: fakeProject }, 201)

    await projectsApi.create({ name: 'Novo Projeto', business_domain: 'Saúde' })

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/projects'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'Novo Projeto', business_domain: 'Saúde' }),
      }),
    )
  })

  it('retorna o projeto criado', async () => {
    stubFetch({ data: { ...fakeProject, name: 'Novo Projeto' } }, 201)
    const result = await projectsApi.create({ name: 'Novo Projeto' })
    expect(result.data.name).toBe('Novo Projeto')
  })
})

describe('projectsApi.update', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

  it('chama PATCH /api/v1/projects/:id com o payload correto', async () => {
    const fetchMock = stubFetch({ data: { ...fakeProject, name: 'Editado' } })

    await projectsApi.update('p1', { name: 'Editado' })

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/projects/p1'),
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ name: 'Editado' }),
      }),
    )
  })

  it('arquiva o projeto enviando status archived', async () => {
    const fetchMock = stubFetch({ data: { ...fakeProject, status: 'archived' } })

    await projectsApi.update('p1', { status: 'archived' })

    expect(fetchMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ body: JSON.stringify({ status: 'archived' }) }),
    )
  })
})
