/**
 * ProjectCard — card de projeto no dashboard (Story 3.2).
 * Exibe: nome, domínio, barra de progresso, última atividade.
 */

import { useNavigate } from 'react-router-dom'
import type { Project } from '@/services/projectsApi'

const DOMAIN_COLORS: Record<string, string> = {
  'Saúde':        'var(--rs-success)',
  'Finanças':     '#F59E0B',
  'Jurídico':     '#8B5CF6',
  'Educação':     '#06B6D4',
  'Tecnologia':   'var(--rs-primary)',
  'Varejo':       '#EC4899',
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
  // progress_summary é populado pela Story 3.4 (sessões)
  const ps = project.progress_summary
  if (!ps) return 0
  const completed = typeof ps.completed_steps === 'number' ? ps.completed_steps : 0
  const total = typeof ps.total_steps === 'number' ? ps.total_steps : 1
  return Math.round((completed / total) * 100)
}

interface Props {
  project: Project
}

export function ProjectCard({ project }: Props) {
  const navigate = useNavigate()
  const progress = getProgress(project)
  const color = getDomainColor(project.business_domain)

  return (
    <article
      id={`project-card-${project.id}`}
      onClick={() => navigate(`/projects/${project.id}`)}
      className="group cursor-pointer rounded-[var(--radius-lg)] border border-border bg-card p-[var(--space-4)] flex flex-col gap-[var(--space-3)] transition-all duration-200 hover:border-[var(--rs-primary)] hover:shadow-lg hover:-translate-y-0.5"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-[var(--space-2)]">
        <div
          className="w-9 h-9 rounded-[var(--radius-md)] flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
          style={{ backgroundColor: color }}
        >
          {project.name.charAt(0).toUpperCase()}
        </div>
        {project.status === 'archived' && (
          <span
            className="text-caption px-2 py-0.5 rounded-full font-medium"
            style={{
              backgroundColor: 'color-mix(in srgb, var(--rs-text-muted) 15%, transparent)',
              color: 'var(--rs-text-muted)',
            }}
          >
            Arquivado
          </span>
        )}
      </div>

      {/* Name & domain */}
      <div className="flex-1 min-w-0">
        <h3 className="text-body font-semibold truncate group-hover:text-[var(--rs-primary)] transition-colors">
          {project.name}
        </h3>
        {project.business_domain && (
          <p className="text-body-sm text-muted-foreground mt-0.5">
            {project.business_domain}
          </p>
        )}
        {project.description && (
          <p className="text-body-sm text-muted-foreground mt-[var(--space-1)] line-clamp-2">
            {project.description}
          </p>
        )}
      </div>

      {/* Progress */}
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
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Atualizado {formatDate(project.updated_at)}</span>
      </div>
    </article>
  )
}
