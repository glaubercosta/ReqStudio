/**
 * ProjectsPage — dashboard com CRUD completo (Stories 3.2, 3.3, 3.5).
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { ProjectCard } from '@/components/ProjectCard'
import { ProjectCardSkeleton } from '@/components/ProjectCardSkeleton'
import { ProjectModal } from '@/components/ProjectModal'
import { useAuth } from '@/contexts/AuthContext'
import { useProjects } from '@/hooks/useProjects'
import type { Project } from '@/services/projectsApi'

// ── Empty State ───────────────────────────────────────────────────────────────

function EmptyState({ onNew, isArchived }: { onNew: () => void; isArchived: boolean }) {
  if (isArchived) {
    return (
      <div className="flex flex-col items-center justify-center py-[var(--space-12)] text-center gap-[var(--space-3)]">
        <span className="text-5xl">📦</span>
        <p className="text-body-sm text-muted-foreground">Nenhum projeto arquivado.</p>
      </div>
    )
  }
  return (
    <div className="flex flex-col items-center justify-center py-[var(--space-12)] text-center gap-[var(--space-4)]">
      <div
        className="w-20 h-20 rounded-3xl flex items-center justify-center text-4xl"
        style={{ backgroundColor: 'var(--rs-primary-light)' }}
      >
        📋
      </div>
      <div>
        <h2 className="text-h2 font-semibold">Crie seu primeiro projeto</h2>
        <p className="text-body-sm text-muted-foreground mt-[var(--space-2)] max-w-sm mx-auto">
          Organize seus requisitos em espaços de trabalho dedicados para cada cliente ou iniciativa.
        </p>
      </div>
      <Button id="btn-new-project-empty" onClick={onNew} size="lg">
        + Novo Projeto
      </Button>
    </div>
  )
}

// ── Status Tab ────────────────────────────────────────────────────────────────

function StatusTab({
  active, label, count, onClick,
}: {
  active: boolean; label: string; count?: number; onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-1.5 px-[var(--space-3)] py-[var(--space-2)] text-body-sm font-medium rounded-[var(--radius-md)] transition-colors"
      style={{
        backgroundColor: active ? 'var(--rs-primary)' : 'transparent',
        color: active ? 'white' : 'var(--rs-text-muted)',
      }}
    >
      {label}
      {count !== undefined && (
        <span
          className="text-caption px-1.5 py-0.5 rounded-full"
          style={{
            backgroundColor: active
              ? 'rgba(255,255,255,0.25)'
              : 'color-mix(in srgb, var(--rs-text-muted) 15%, transparent)',
          }}
        >
          {count}
        </span>
      )}
    </button>
  )
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function Toast({ message }: { message: string }) {
  return (
    <div
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-[var(--space-4)] py-[var(--space-3)] rounded-[var(--radius-lg)] shadow-xl text-body-sm font-medium"
      style={{ backgroundColor: 'var(--rs-success)', color: 'white' }}
      role="status"
      aria-live="polite"
    >
      ✓ {message}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ProjectsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<'active' | 'archived'>('active')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | undefined>()
  const [toast, setToast] = useState<string | null>(null)

  const { data, isLoading, isError } = useProjects(statusFilter)
  const projects = data?.items ?? []

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  const handleNewProject = () => {
    setEditingProject(undefined)
    setModalOpen(true)
  }

  const handleEdit = (project: Project) => {
    setEditingProject(project)
    setModalOpen(true)
  }

  const handleModalClose = () => {
    const wasEditing = !!editingProject
    setModalOpen(false)
    setEditingProject(undefined)
    showToast(wasEditing ? 'Projeto atualizado.' : 'Projeto criado!')
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border px-[var(--space-5)] py-[var(--space-3)] flex items-center justify-between sticky top-0 z-10 bg-background/80 backdrop-blur-sm">
        <div className="flex items-center gap-[var(--space-3)]">
          <span className="text-h3 font-semibold" style={{ color: 'var(--rs-primary)' }}>
            ReqStudio
          </span>
          <span
            className="text-caption px-2 py-0.5 rounded-full font-medium"
            style={{ backgroundColor: 'var(--rs-primary-light)', color: 'var(--rs-primary)' }}
          >
            Beta
          </span>
        </div>
        <div className="flex items-center gap-[var(--space-3)]">
          <span className="text-body-sm text-muted-foreground hidden sm:block">{user?.email}</span>
          <ThemeToggle />
          <Button variant="outline" size="sm" onClick={handleLogout}>Sair</Button>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 px-[var(--space-5)] py-[var(--space-6)] max-w-6xl mx-auto w-full">
        {/* Page header */}
        <div className="flex items-start justify-between gap-[var(--space-4)] mb-[var(--space-5)]">
          <div>
            <h1 className="text-h1">Seus Projetos</h1>
            <p className="text-body-sm text-muted-foreground mt-[var(--space-1)]">
              {isLoading ? 'Carregando...' : `${data?.total ?? 0} projeto${(data?.total ?? 0) !== 1 ? 's' : ''}`}
            </p>
          </div>
          <Button id="btn-new-project" onClick={handleNewProject} className="flex-shrink-0">
            + Novo Projeto
          </Button>
        </div>

        {/* Status tabs */}
        <div className="flex gap-[var(--space-1)] mb-[var(--space-5)] p-1 rounded-[var(--radius-md)] bg-muted w-fit">
          <StatusTab
            active={statusFilter === 'active'}
            label="Ativos"
            count={statusFilter === 'active' ? data?.total : undefined}
            onClick={() => setStatusFilter('active')}
          />
          <StatusTab
            active={statusFilter === 'archived'}
            label="Arquivados"
            count={statusFilter === 'archived' ? data?.total : undefined}
            onClick={() => setStatusFilter('archived')}
          />
        </div>

        {/* Error */}
        {isError && (
          <div
            className="rounded-[var(--radius-md)] p-[var(--space-4)] text-body-sm"
            style={{
              backgroundColor: 'color-mix(in srgb, var(--rs-error) 10%, transparent)',
              color: 'var(--rs-error)',
              borderLeft: '3px solid var(--rs-error)',
            }}
          >
            Erro ao carregar projetos. Verifique sua conexão e tente novamente.
          </div>
        )}

        {/* Skeleton */}
        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-[var(--space-4)]">
            {Array.from({ length: 6 }).map((_, i) => <ProjectCardSkeleton key={i} />)}
          </div>
        )}

        {/* Empty */}
        {!isLoading && !isError && projects.length === 0 && (
          <EmptyState onNew={handleNewProject} isArchived={statusFilter === 'archived'} />
        )}

        {/* Grid */}
        {!isLoading && projects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-[var(--space-4)]">
            {projects.map(project => (
              <ProjectCard key={project.id} project={project} onEdit={handleEdit} />
            ))}
          </div>
        )}
      </main>

      {/* Modal criação/edição */}
      <ProjectModal
        open={modalOpen}
        onClose={handleModalClose}
        project={editingProject}
      />

      {/* Toast */}
      {toast && <Toast message={toast} />}
    </div>
  )
}
