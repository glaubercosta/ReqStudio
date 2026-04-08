import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { artifactsApi } from '@/services/artifactsApi'
import { setAccessToken } from '@/services/apiClient'

function stubFetch(body: unknown, status = 200) {
  const mock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })
  vi.stubGlobal('fetch', mock)
  return mock
}

describe('artifactsApi', () => {
  beforeEach(() => setAccessToken('tok_test'))
  afterEach(() => {
    setAccessToken(null)
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('lista artefatos por projeto', async () => {
    const fetchMock = stubFetch({ data: [] })
    await artifactsApi.listByProject('p1')
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/artifacts/project/p1'),
      expect.anything(),
    )
  })

  it('renderiza markdown por view', async () => {
    const fetchMock = stubFetch({ data: { markdown: '# artifact' } })
    const result = await artifactsApi.render('a1', 'technical')
    expect(result.data.markdown).toContain('# artifact')
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/artifacts/a1/render?view=technical'),
      expect.anything(),
    )
  })

  it('retorna blob e filename no export', async () => {
    const blob = new Blob(['abc'], { type: 'text/markdown' })
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      blob: async () => blob,
      headers: {
        get: (key: string) =>
          key === 'Content-Disposition' ? 'attachment; filename="reqstudio_test.md"' : null,
      },
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await artifactsApi.exportFile('a1', 'markdown', 'business')

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/artifacts/a1/export?format=markdown&view=business&show_ids=false'),
      expect.objectContaining({ credentials: 'include' }),
    )
    expect(result.filename).toBe('reqstudio_test.md')
    expect(result.blob).toBe(blob)
  })

  it('retorna erro de export quando endpoint falha', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ error: { code: 'EXPORT_FAILED', message: 'Falha no export', help: '', actions: [], severity: 'error' } }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      artifactsApi.exportFile('a1', 'json', 'business'),
    ).rejects.toThrow('Falha no export')
  })
})
