import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ArtifactPage from '@/pages/ArtifactPage'
import { artifactsApi } from '@/services/artifactsApi'

vi.mock('@/services/artifactsApi', () => ({
  artifactsApi: {
    get: vi.fn(),
    render: vi.fn(),
    coverage: vi.fn(),
    versions: vi.fn(),
    exportFile: vi.fn(),
  },
}))

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/artifacts/art-1']}>
        <Routes>
          <Route path="/artifacts/:id" element={<ArtifactPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ArtifactPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(artifactsApi.get).mockResolvedValue({
      data: {
        id: 'art-1',
        project_id: 'proj-1',
        session_id: 'sess-1',
        artifact_type: 'prd',
        title: 'PRD Merenda',
        artifact_state: {
          metadata: { total_coverage: 0.75 },
          sections: [
            { id: 's1', title: 'Objetivo', content: 'Conteudo', coverage: 0.8, sources: ['m1', 'm2'] },
          ],
        },
        coverage_data: null,
        version: 3,
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    })

    vi.mocked(artifactsApi.render).mockResolvedValue({
      data: { markdown: '# PRD Merenda\n\n## Objetivo\n\nConteudo' },
    })

    vi.mocked(artifactsApi.coverage).mockResolvedValue({
      data: {
        artifact_id: 'art-1',
        total_coverage: 0.75,
        sections: [
          { id: 's1', title: 'Objetivo', coverage: 0.8, coverage_band: 'high', card_state: 'complete' },
        ],
      },
    })

    vi.mocked(artifactsApi.versions).mockResolvedValue({
      data: [
        {
          id: 'v3',
          artifact_id: 'art-1',
          version: 3,
          state_snapshot: { metadata: { total_coverage: 0.75 }, sections: [] },
          change_reason: 'Ajuste final',
          changed_by: 'analista',
          created_at: new Date().toISOString(),
        },
      ],
    })

    vi.mocked(artifactsApi.exportFile).mockResolvedValue({
      blob: new Blob(['ok'], { type: 'text/plain' }),
      filename: 'artifact.md',
      durationMs: 10,
    })

  })

  it('renders core controls and switches to technical view', async () => {
    renderPage()

    await waitFor(() => {
      expect(artifactsApi.get).toHaveBeenCalledWith('art-1')
    })
    await screen.findByText('PRD Merenda')
    expect(screen.getByText('Cobertura do artefato')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'MD Negocio' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'MD Tecnico' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'JSON' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Tecnico' }))

    await waitFor(() => {
      expect(artifactsApi.render).toHaveBeenLastCalledWith('art-1', 'technical', false)
    })
  })

  it('exports technical markdown from dedicated action', async () => {
    const createObjectURL = vi.fn(() => 'blob:artifact')
    const revokeObjectURL = vi.fn()
    const originalCreate = URL.createObjectURL
    const originalRevoke = URL.revokeObjectURL

    URL.createObjectURL = createObjectURL
    URL.revokeObjectURL = revokeObjectURL

    renderPage()
    await screen.findByText('PRD Merenda')

    await userEvent.click(screen.getByRole('button', { name: 'MD Tecnico' }))

    await waitFor(() => {
      expect(artifactsApi.exportFile).toHaveBeenCalledWith('art-1', 'markdown', 'technical', false)
      expect(createObjectURL).toHaveBeenCalled()
      expect(revokeObjectURL).toHaveBeenCalled()
    })

    URL.createObjectURL = originalCreate
    URL.revokeObjectURL = originalRevoke
  })

  it('shows feedback when export fails', async () => {
    vi.mocked(artifactsApi.exportFile).mockRejectedValueOnce(new Error('boom'))

    renderPage()
    await screen.findByText('PRD Merenda')

    await userEvent.click(screen.getByRole('button', { name: 'JSON' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Falha ao exportar o artefato. Tente novamente em alguns instantes.',
    )
  })
})
