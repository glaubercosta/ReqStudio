/**
 * ProjectModal — testes de criação e edição (Stories 3.3).
 *
 * Cobre: renderização, validação inline, submit, erro de API, modo edição.
 */
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '@/test/utils'
import { ProjectModal } from '@/components/ProjectModal'
import * as projectsApi from '@/services/projectsApi'
import { ReqStudioApiError } from '@/services/apiClient'

// ── Mock projectsApi ──────────────────────────────────────────────────────────

vi.mock('@/services/projectsApi', async (importOriginal) => {
  const actual = await importOriginal<typeof projectsApi>()
  return {
    ...actual,
    projectsApi: {
      create: vi.fn(),
      update: vi.fn(),
      list:   vi.fn(),
      get:    vi.fn(),
    },
  }
})

const mockCreate = vi.mocked(projectsApi.projectsApi.create)
const mockUpdate = vi.mocked(projectsApi.projectsApi.update)

const mockProject: projectsApi.Project = {
  id: 'abc-123',
  name: 'Projeto Existente',
  description: 'Descrição',
  business_domain: 'Saúde',
  status: 'active',
  progress_summary: null,
  tenant_id: 'tenant-1',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const onClose = vi.fn()

describe('ProjectModal — modo criação', () => {
  beforeEach(() => { vi.clearAllMocks(); onClose.mockClear() })

  it('renderiza o título correto no modo criação', () => {
    render(<ProjectModal open={true} onClose={onClose} />)
    expect(screen.getByText('Novo projeto')).toBeInTheDocument()
  })

  it('não renderiza nada quando open=false', () => {
    render(<ProjectModal open={false} onClose={onClose} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('mostra erro de validação se nome estiver vazio', async () => {
    render(<ProjectModal open={true} onClose={onClose} />)
    await userEvent.click(screen.getByRole('button', { name: /criar projeto/i }))
    expect(screen.getByText('Nome é obrigatório.')).toBeInTheDocument()
    expect(mockCreate).not.toHaveBeenCalled()
  })

  it('chama create com dados corretos ao submeter', async () => {
    mockCreate.mockResolvedValue({ data: { ...mockProject, name: 'Novo Projeto' } })
    render(<ProjectModal open={true} onClose={onClose} />)

    await userEvent.type(screen.getByLabelText(/nome/i), 'Novo Projeto')
    await userEvent.click(screen.getByRole('button', { name: /criar projeto/i }))

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Novo Projeto' }),
      )
    })
  })

  it('exibe mensagem de sucesso após criar', async () => {
    mockCreate.mockResolvedValue({ data: mockProject })
    render(<ProjectModal open={true} onClose={onClose} />)

    await userEvent.type(screen.getByLabelText(/nome/i), 'Teste')
    await userEvent.click(screen.getByRole('button', { name: /criar projeto/i }))

    await waitFor(() => {
      expect(screen.getByText(/criado com sucesso/i)).toBeInTheDocument()
    })
  })

  it('exibe erro da API em banner', async () => {
    mockCreate.mockRejectedValue(
      new ReqStudioApiError(
        { code: 'INTERNAL_ERROR', message: 'Erro no servidor', help: '', actions: [], severity: 'recoverable' },
        500,
      ),
    )
    render(<ProjectModal open={true} onClose={onClose} />)

    await userEvent.type(screen.getByLabelText(/nome/i), 'Projeto Erro')
    await userEvent.click(screen.getByRole('button', { name: /criar projeto/i }))

    await waitFor(() => {
      expect(screen.getByText('Erro no servidor')).toBeInTheDocument()
    })
  })

  it('fecha o modal ao pressionar Escape', async () => {
    render(<ProjectModal open={true} onClose={onClose} />)
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalled()
  })

  it('fecha ao clicar no backdrop', async () => {
    render(<ProjectModal open={true} onClose={onClose} />)
    // O backdrop é o elemento com aria-hidden="true"
    const backdrop = document.querySelector('[aria-hidden="true"]')!
    await userEvent.click(backdrop)
    expect(onClose).toHaveBeenCalled()
  })
})

describe('ProjectModal — modo edição', () => {
  beforeEach(() => { vi.clearAllMocks(); onClose.mockClear() })

  it('renderiza o título correto no modo edição', () => {
    render(<ProjectModal open={true} onClose={onClose} project={mockProject} />)
    expect(screen.getByText('Editar projeto')).toBeInTheDocument()
  })

  it('pré-preenche os campos com os dados do projeto', () => {
    render(<ProjectModal open={true} onClose={onClose} project={mockProject} />)
    expect(screen.getByDisplayValue('Projeto Existente')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Descrição')).toBeInTheDocument()
  })

  it('chama update (não create) ao salvar', async () => {
    mockUpdate.mockResolvedValue({ data: mockProject })
    render(<ProjectModal open={true} onClose={onClose} project={mockProject} />)

    const input = screen.getByDisplayValue('Projeto Existente')
    await userEvent.clear(input)
    await userEvent.type(input, 'Nome Editado')
    await userEvent.click(screen.getByRole('button', { name: /salvar alterações/i }))

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith(
        'abc-123',
        expect.objectContaining({ name: 'Nome Editado' }),
      )
    })
    expect(mockCreate).not.toHaveBeenCalled()
  })
})
