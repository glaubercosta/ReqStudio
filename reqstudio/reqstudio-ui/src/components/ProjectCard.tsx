/**
 * ProjectCard — card com menu de ações (editar / arquivar) (Stories 3.2, 3.3, 3.5).
 */

import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Project } from '@/services/projectsApi'
import { ArchiveConfirm } from '@/components/ArchiveConfirm'

const DOMAIN_COLORS: Record<string, string> = {
  'Saúde':      '#10B981',
  'Finanças':   '#F59E0B',
  'Jurídico':   '#8B5CF6',
  'Educação':   '#06B6D4',
  'Tecnologia': 'var(--rs-primary)',
  'Varejo':     '#EC4899',
  'Logística':  '#F97316',
  'Governo':    '#6B7280',
}

function getDomainColor(domain: string | null): string {
  if (!domain) return 'var(--rs-primary)'
  return DOMAIN_COLORS[domain] ?? 'var(--rs-primary)'
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

function getProgress(project: Project): number {
  const ps = project.progress_summary
  if (!ps) return 0
  const completed = typeof ps['completed_steps'] === 'number' ? (ps['completed_steps'] as number) : 0
  const total = typeof ps['total_steps'] === 'number' ? (ps['total_steps'] as number) : 1
  return Math.round((completed / total) * 100)
}

interface Props {
  project: Project
  onEdit: (project: Project) => void
}

export function ProjectCard({ project, onEdit }: Props) {
  const navigate = useNavigate()
  const menuRef = useRef<HTMLDivElement>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [showArchive, setShowArchive] = useState(false)

  const progress = getProgress(project)
  const color = getDomainColor(project.business_domain)

  const handleCardClick = (e: React.MouseEvent) => {
    // Não navega se clicou no menu ou no confirm
    if (menuRef.current?.contains(e.target as Node)) return
    navigate(`/projects/${project.id}`)
  }

  return (
    <article
      id={`project-card-${project.id}`}
      onClick={handleCardClick}
      className="group relative cursor-pointer rounded-[var(--radius-lg)] border border-border bg-card p-[var(--space-4)] flex flex-col gap-[var(--space-3)] transition-all duration-200 hover:border-[var(--rs-primary)] hover:shadow-lg hover:-translate-y-0.5"
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-[var(--space-2)]">
        <div
          className="w-9 h-9 rounded-[var(--radius-md)] flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
          style={{ backgroundColor: color }}
        >
          {project.name.charAt(0).toUpperCase()}
        </div>

        {/* ⋮ menu */}
        <div ref={menuRef} className="relative flex-shrink-0">
          <button
            type="button"
            id={`project-menu-${project.id}`}
            onClick={e => { e.stopPropagation(); setMenuOpen(o => !o); setShowArchive(false) }}
            className="w-7 h-7 flex items-center justify-center rounded text-muted-foreground opacity-0 group-hover:opacity-100 hover:bg-muted transition-all"
            aria-label="Ações do projeto"
          >
            ⋮
          </button>

          {menuOpen && !showArchive && (
            <div className="absolute right-0 top-8 z-30 min-w-[140px] rounded-[var(--radius-md)] border border-border bg-card shadow-lg py-1">
              <button
                type="button"
                className="w-full text-left px-3 py-2 text-body-sm hover:bg-muted transition-colors"
                onClick={e => { e.stopPropagation(); setMenuOpen(false); onEdit(project) }}
              >
                ✏️ Editar
              </button>
              <button
                type="button"
                className="w-full text-left px-3 py-2 text-body-sm hover:bg-muted transition-colors"
                onClick={e => { e.stopPropagation(); setMenuOpen(false); setShowArchive(true) }}
              >
                {project.status === 'archived' ? '♻️ Restaurar' : '📦 Arquivar'}
              </button>
            </div>
          )}

          {/* Inline archive confirm */}
          {showArchive && (
            <div
              className="absolute right-0 top-8 z-30 w-64"
              onClick={e => e.stopPropagation()}
            >
              <ArchiveConfirm
                project={project}
                onClose={() => setShowArchive(false)}
              />
            </div>
          )}
        </div>
      </div>

      {/* Title + domain */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-body font-semibold truncate group-hover:text-[var(--rs-primary)] transition-colors">
            {project.name}
          </h3>
          {project.status === 'archived' && (
            <span
              className="text-caption px-2 py-0.5 rounded-full font-medium flex-shrink-0"
              style={{
                backgroundColor: 'color-mix(in srgb, var(--rs-text-muted) 15%, transparent)',
                color: 'var(--rs-text-muted)',
              }}
            >
              Arquivado
            </span>
          )}
        </div>
        {project.business_domain && (
          <p className="text-body-sm text-muted-foreground mt-0.5">{project.business_domain}</p>
        )}
        {project.description && (
          <p className="text-body-sm text-muted-foreground mt-[var(--space-1)] line-clamp-2">
            {project.description}
          </p>
        )}
      </div>

      {/* Progress bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-caption text-muted-foreground">Progresso</span>
          <span className="text-caption font-medium" style={{ color }}>{progress}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${progress}%`, backgroundColor: color }}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center gap-1 text-caption text-muted-foreground pt-[var(--space-1)] border-t border-border">
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Atualizado {formatDate(project.updated_at)}</span>
      </div>
    </article>
  )
}
