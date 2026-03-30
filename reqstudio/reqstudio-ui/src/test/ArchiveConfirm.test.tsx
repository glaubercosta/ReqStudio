/**
 * ArchiveConfirm — testes de arquivamento e restauração (Story 3.5).
 */
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '@/test/utils'
import { ArchiveConfirm } from '@/components/ArchiveConfirm'
import * as projectsApi from '@/services/projectsApi'
import type { Project } from '@/services/projectsApi'

vi.mock('@/services/projectsApi', async (importOriginal) => {
  const actual = await importOriginal<typeof projectsApi>()
  return {
    ...actual,
    projectsApi: { ...actual.projectsApi, update: vi.fn() },
  }
})

const mockUpdate = vi.mocked(projectsApi.projectsApi.update)

const activeProject: Project = {
  id: 'proj-1',
  name: 'Projeto Ativo',
  description: null,
  business_domain: null,
  status: 'active',
  progress_summary: null,
  tenant_id: 'tenant-1',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const archivedProject: Project = { ...activeProject, status: 'archived', name: 'Projeto Arquivado' }
const onClose = vi.fn()

describe('ArchiveConfirm — arquivamento', () => {
  beforeEach(() => { vi.clearAllMocks(); onClose.mockClear() })

  it('mostra mensagem de arquivamento para projeto ativo', () => {
    render(<ArchiveConfirm project={activeProject} onClose={onClose} />)
    expect(screen.getByText(/arquivar "Projeto Ativo"/i)).toBeInTheDocument()
    expect(screen.getByText(/dados preservados/i)).toBeInTheDocument()
  })

  it('botão exibe texto "Arquivar" para projeto ativo', () => {
    render(<ArchiveConfirm project={activeProject} onClose={onClose} />)
    expect(screen.getByRole('button', { name: /arquivar/i })).toBeInTheDocument()
  })

  it('chama update com status archived ao confirmar', async () => {
    mockUpdate.mockResolvedValue({ data: { ...activeProject, status: 'archived' } })
    render(<ArchiveConfirm project={activeProject} onClose={onClose} />)

    await userEvent.click(screen.getByRole('button', { name: /arquivar/i }))

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith('proj-1', { status: 'archived' })
    })
  })

  it('chama onClose após arquivar', async () => {
    mockUpdate.mockResolvedValue({ data: { ...activeProject, status: 'archived' } })
    render(<ArchiveConfirm project={activeProject} onClose={onClose} />)
    await userEvent.click(screen.getByRole('button', { name: /arquivar/i }))
    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })

  it('botão Cancelar chama onClose sem chamar update', async () => {
    render(<ArchiveConfirm project={activeProject} onClose={onClose} />)
    await userEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(onClose).toHaveBeenCalled()
    expect(mockUpdate).not.toHaveBeenCalled()
  })
})

describe('ArchiveConfirm — restauração', () => {
  beforeEach(() => { vi.clearAllMocks(); onClose.mockClear() })

  it('mostra mensagem de restauração para projeto arquivado', () => {
    render(<ArchiveConfirm project={archivedProject} onClose={onClose} />)
    expect(screen.getByText(/restaurar "Projeto Arquivado"/i)).toBeInTheDocument()
    expect(screen.getByText(/voltará para a lista de ativos/i)).toBeInTheDocument()
  })

  it('chama update com status active ao restaurar', async () => {
    mockUpdate.mockResolvedValue({ data: { ...archivedProject, status: 'active' } })
    render(<ArchiveConfirm project={archivedProject} onClose={onClose} />)

    await userEvent.click(screen.getByRole('button', { name: /restaurar/i }))

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith('proj-1', { status: 'active' })
    })
  })
})
