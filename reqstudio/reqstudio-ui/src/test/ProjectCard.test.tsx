/**
 * ProjectCard — testes de renderização e interação (Story 3.2).
 */
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '@/test/utils'
import { ProjectCard } from '@/components/ProjectCard'
import type { Project } from '@/services/projectsApi'

// Mock navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return { ...actual, useNavigate: () => mockNavigate }
})

// Mock projectsApi (para ArchiveConfirm dentro do card)
vi.mock('@/services/projectsApi', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, projectsApi: { ...(actual as any).projectsApi, update: vi.fn() } }
})

const mockProject: Project = {
  id: 'card-1',
  name: 'Sistema de Saúde',
  description: 'Um sistema hospitalar',
  business_domain: 'Saúde',
  status: 'active',
  progress_summary: null,
  tenant_id: 'tenant-1',
  created_at: '2026-03-01T10:00:00Z',
  updated_at: '2026-03-15T14:00:00Z',
}

const onEdit = vi.fn()

describe('ProjectCard', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renderiza nome e domínio do projeto', () => {
    render(<ProjectCard project={mockProject} onEdit={onEdit} />)
    expect(screen.getByText('Sistema de Saúde')).toBeInTheDocument()
    expect(screen.getByText('Saúde')).toBeInTheDocument()
  })

  it('renderiza descrição do projeto', () => {
    render(<ProjectCard project={mockProject} onEdit={onEdit} />)
    expect(screen.getByText('Um sistema hospitalar')).toBeInTheDocument()
  })

  it('mostra progresso 0% para projetos sem progress_summary', () => {
    render(<ProjectCard project={mockProject} onEdit={onEdit} />)
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('navega para /projects/:id ao clicar no card', async () => {
    render(<ProjectCard project={mockProject} onEdit={onEdit} />)
    await userEvent.click(screen.getByRole('article'))
    expect(mockNavigate).toHaveBeenCalledWith('/projects/card-1')
  })

  it('NÃO navega ao clicar no botão de menu', async () => {
    render(<ProjectCard project={mockProject} onEdit={onEdit} />)
    // Simula hover para o botão aparecer (opacity-0 → visible)
    const menu = screen.getByRole('button', { name: /ações do projeto/i })
    await userEvent.click(menu)
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('abre o menu com opções Editar e Arquivar ao clicar em ⋮', async () => {
    render(<ProjectCard project={mockProject} onEdit={onEdit} />)
    await userEvent.click(screen.getByRole('button', { name: /ações do projeto/i }))
    expect(screen.getByText(/editar/i)).toBeInTheDocument()
    expect(screen.getByText(/arquivar/i)).toBeInTheDocument()
  })

  it('chama onEdit com o projeto ao clicar em Editar', async () => {
    render(<ProjectCard project={mockProject} onEdit={onEdit} />)
    await userEvent.click(screen.getByRole('button', { name: /ações do projeto/i }))
    await userEvent.click(screen.getByText(/✏️ editar/i))
    expect(onEdit).toHaveBeenCalledWith(mockProject)
  })

  it('exibe badge "Arquivado" para projetos arquivados', () => {
    render(
      <ProjectCard project={{ ...mockProject, status: 'archived' }} onEdit={onEdit} />,
    )
    expect(screen.getByText('Arquivado')).toBeInTheDocument()
  })

  it('exibe data de atualização formatada', () => {
    render(<ProjectCard project={mockProject} onEdit={onEdit} />)
    expect(screen.getByText(/atualizado/i)).toBeInTheDocument()
  })
})
