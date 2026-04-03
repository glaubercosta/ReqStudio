/**
 * ProjectDetailPage — detalhe do projeto com boas-vindas contextuais (Story 3.4).
 *
 * WelcomeScreen (UX-DR8):
 *  - Sem sessões: "Vamos começar! Descreva o problema..."
 *  - Com sessões: lista de sessões, docs importados, artefatos
 *  - Zero vazamento de contexto entre tenants (FR3, FR6)
 */

import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/ThemeToggle'
import { ProjectModal } from '@/components/ProjectModal'
import { ArchiveConfirm } from '@/components/ArchiveConfirm'
import { useAuth } from '@/contexts/AuthContext'
import { useProject } from '@/hooks/useProject'
import { DocumentUpload } from '@/components/DocumentUpload'
import { DocumentList } from '@/components/DocumentList'
import { sessionsApi } from '@/services/sessionsApi'
import { useProjectSessions } from '@/hooks/useProjectSessions'
import type { Session } from '@/services/sessionsApi'

import { projectsQueryKey } from '@/hooks/useProjects'
import { projectQueryKey } from '@/hooks/useProject'

// ── Progress checklist ────────────────────────────────────────────────────────

interface ChecklistItem {
  id: string
  label: string
  done: boolean
}

function buildChecklist(progressSummary: Record<string, unknown> | null): ChecklistItem[] {
  // Etapas padrão de elicitação de requisitos — preenchidas pelo motor de IA (Epic 5+)
  const defaults: ChecklistItem[] = [
    { id: 'context',      label: 'Contexto do problema definido',     done: false },
    { id: 'stakeholders', label: 'Stakeholders identificados',         done: false },
    { id: 'goals',        label: 'Objetivos de negócio mapeados',     done: false },
    { id: 'flows',        label: 'Fluxos principais documentados',    done: false },
    { id: 'nfr',          label: 'Requisitos não-funcionais capturados', done: false },
    { id: 'review',       label: 'Revisão humana concluída',          done: false },
  ]

  if (!progressSummary) return defaults

  return defaults.map(item => ({
    ...item,
    done: !!(progressSummary[item.id]),
  }))
}

function getProgressPercent(checklist: ChecklistItem[]): number {
  const done = checklist.filter(i => i.done).length
  return Math.round((done / checklist.length) * 100)
}

// ── Domain color ──────────────────────────────────────────────────────────────

const DOMAIN_COLORS: Record<string, string> = {
  'Saúde':      '#10B981',
  'Finanças':   '#F59E0B',
  'Jurídico':   '#8B5CF6',
  'Educação':   '#06B6D4',
  'Tecnologia': '#4F46E5',
  'Varejo':     '#EC4899',
  'Logística':  '#F97316',
  'Governo':    '#6B7280',
}
const domainColor = (d: string | null) => d ? (DOMAIN_COLORS[d] ?? '#4F46E5') : '#4F46E5'

// ── Skeleton ──────────────────────────────────────────────────────────────────

function DetailSkeleton() {
  return (
    <div className="space-y-[var(--space-4)] max-w-3xl mx-auto pt-[var(--space-6)]">
      <div className="h-8 w-1/2 bg-muted rounded animate-pulse" />
      <div className="h-4 w-1/4 bg-muted rounded animate-pulse" />
      <div className="h-2 w-full bg-muted rounded-full animate-pulse" />
      <div className="grid grid-cols-2 gap-[var(--space-3)]">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-10 bg-muted rounded-[var(--radius-md)] animate-pulse" />
        ))}
      </div>
    </div>
  )
}

// ── Welcome Screen ────────────────────────────────────────────────────────────

function WelcomeScreen({
  projectName,
  checklist,
  progressPct,
  hasSessions,
  activeSession,
  onStart,
}: {
  projectName: string
  checklist: ChecklistItem[]
  progressPct: number
  hasSessions: boolean
  activeSession: Session | null
  onStart: () => void
}) {
  function formatRelativeTime(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime()
    if (diff < 60_000) return 'agora mesmo'
    
    const minutes = Math.floor(diff / 60_000)
    const hours = Math.floor(diff / 3_600_000)
    const days = Math.floor(diff / 86_400_000)
    const rtf = new Intl.RelativeTimeFormat('pt-BR', { numeric: 'auto' })
    
    if (minutes < 60) return rtf.format(-minutes, 'minute')
    if (hours < 24) return rtf.format(-hours, 'hour')
    return rtf.format(-days, 'day')
  }


  return (
    <div className="mt-[var(--space-6)] rounded-[var(--radius-xl)] border border-border bg-card overflow-hidden">
      {/* Top bar de progresso */}
      <div className="h-1 bg-muted">
        <div
          className="h-full transition-all duration-700"
          style={{ width: `${progressPct}%`, backgroundColor: 'var(--rs-primary)' }}
        />
      </div>

      <div className="p-[var(--space-6)]">
        {hasSessions ? (
          /* Com sessões anteriores */
          <div className="space-y-[var(--space-4)]">
            <div>
              <h2 className="text-h2 font-semibold">
                Bem-vindo de volta, <span style={{ color: 'var(--rs-primary)' }}>{projectName}</span>!
              </h2>
              <p className="text-body-sm text-muted-foreground mt-[var(--space-1)]">
                Você está a {100 - progressPct}% de completar a elicitação.
                {activeSession && (
                  <span className="block mt-0.5 text-caption" style={{ color: 'var(--rs-text-muted)' }}>
                    Última atividade: {formatRelativeTime(activeSession.updated_at)}
                  </span>
                )}
              </p>
            </div>

            {/* Checklist */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-[var(--space-2)]">
              {checklist.map(item => (
                <div
                  key={item.id}
                  className="flex items-center gap-[var(--space-2)] p-[var(--space-2)] rounded-[var(--radius-md)]"
                  style={{
                    backgroundColor: item.done
                      ? 'color-mix(in srgb, var(--rs-success) 10%, transparent)'
                      : 'color-mix(in srgb, var(--rs-text-muted) 5%, transparent)',
                  }}
                >
                  <span className="text-lg" style={{ color: item.done ? 'var(--rs-success)' : 'var(--rs-text-muted)' }}>
                    {item.done ? '✓' : '○'}
                  </span>
                  <span
                    className="text-body-sm"
                    style={{ color: item.done ? 'var(--rs-success)' : 'inherit' }}
                  >
                    {item.label}
                  </span>
                </div>
              ))}
            </div>

            <Button id="btn-continue-session" onClick={onStart} size="lg">
              Continuar sessão →
            </Button>
          </div>
        ) : (
          /* Sem sessões — estado inicial */
          <div className="flex flex-col items-center text-center gap-[var(--space-4)] py-[var(--space-4)]">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl"
              style={{ backgroundColor: 'var(--rs-primary-light)' }}
            >
              🚀
            </div>
            <div>
              <h2 className="text-h2 font-semibold">Vamos começar!</h2>
              <p className="text-body-sm text-muted-foreground mt-[var(--space-2)] max-w-md">
                Descreva o problema que este projeto precisa resolver e a IA irá guiá-lo
                pela elicitação de requisitos passo a passo.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-[var(--space-3)] w-full max-w-lg text-left">
              {[
                { icon: '💬', label: 'Descreva o problema', desc: 'Em linguagem natural' },
                { icon: '🤖', label: 'IA faz perguntas', desc: 'Elicitação guiada' },
                { icon: '📄', label: 'Gera artefatos', desc: 'PRD, histórias, etc.' },
              ].map(step => (
                <div
                  key={step.label}
                  className="rounded-[var(--radius-md)] border border-border p-[var(--space-3)]"
                >
                  <span className="text-2xl">{step.icon}</span>
                  <p className="text-body-sm font-medium mt-[var(--space-1)]">{step.label}</p>
                  <p className="text-caption text-muted-foreground">{step.desc}</p>
                </div>
              ))}
            </div>

            <Button
              id="btn-start-session"
              size="lg"
              onClick={onStart}
              style={{ backgroundColor: 'var(--rs-primary)', color: 'white' }}
            >
              Iniciar elicitação →
            </Button>

            <p
              className="text-caption px-3 py-1.5 rounded-full"
              style={{ backgroundColor: 'var(--rs-primary-light)', color: 'var(--rs-primary)' }}
            >
              ⚡ Funcionalidade de IA disponível no Epic 5
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { logout } = useAuth()

  const { data: project, isLoading, isError } = useProject(id ?? '')

  const [editOpen, setEditOpen] = useState(false)
  const [archiveOpen, setArchiveOpen] = useState(false)

  if (!id) return null

  const handleLogout = async () => { await logout(); navigate('/login', { replace: true }) }

  const handleEditClose = async () => {
    setEditOpen(false)
    await qc.invalidateQueries({ queryKey: projectQueryKey(id) })
    await qc.invalidateQueries({ queryKey: projectsQueryKey() })
  }

  const color = project ? domainColor(project.business_domain) : '#4F46E5'
  const checklist = buildChecklist(project?.progress_summary ?? null)
  const progressPct = getProgressPercent(checklist)

  const { data: resumableSessions } = useProjectSessions(id ?? '')
  const activeSession: Session | null = resumableSessions?.[0] ?? null
  const hasSessions = !!activeSession

  const handleStartSession = async () => {
    if (!id) return
    try {
      if (activeSession) {
        navigate(`/sessions/${activeSession.id}`)
      } else {
        const res = await sessionsApi.create(id)
        navigate(`/sessions/${res.data.id}`)
      }
    } catch {
      // Se falhar, fica na página
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border px-[var(--space-5)] py-[var(--space-3)] flex items-center justify-between sticky top-0 z-10 bg-background/80 backdrop-blur-sm">
        <div className="flex items-center gap-[var(--space-3)]">
          <button
            type="button"
            onClick={() => navigate('/projects')}
            className="text-muted-foreground hover:text-foreground transition-colors text-body-sm flex items-center gap-1"
          >
            ← Projetos
          </button>
          <span className="text-muted-foreground">/</span>
          <span className="text-body-sm font-medium truncate max-w-[200px]">
            {project?.name ?? '...'}
          </span>
        </div>
        <div className="flex items-center gap-[var(--space-3)]">
          <ThemeToggle />
          {project && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditOpen(true)}
                id="btn-edit-project-detail"
              >
                ✏️ Editar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setArchiveOpen(o => !o)}
                id="btn-archive-project-detail"
              >
                {project.status === 'archived' ? '♻️ Restaurar' : '📦 Arquivar'}
              </Button>
            </>
          )}
          <Button variant="outline" size="sm" onClick={handleLogout}>Sair</Button>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 px-[var(--space-5)] py-[var(--space-6)] max-w-3xl mx-auto w-full">

        {/* Archive confirm */}
        {archiveOpen && project && (
          <div className="mb-[var(--space-4)]">
            <ArchiveConfirm
              project={project}
              onClose={() => {
                setArchiveOpen(false)
                void qc.invalidateQueries({ queryKey: projectQueryKey(id) })
                void qc.invalidateQueries({ queryKey: projectsQueryKey() })
              }}
            />
          </div>
        )}

        {isLoading && <DetailSkeleton />}

        {isError && (
          <div
            className="rounded-[var(--radius-md)] p-[var(--space-4)] text-body-sm"
            style={{
              backgroundColor: 'color-mix(in srgb, var(--rs-error) 10%, transparent)',
              color: 'var(--rs-error)',
              borderLeft: '3px solid var(--rs-error)',
            }}
          >
            Projeto não encontrado ou você não tem acesso a ele.{' '}
            <button
              type="button"
              className="underline"
              onClick={() => navigate('/projects')}
            >
              Voltar à lista
            </button>
          </div>
        )}

        {project && (
          <>
            {/* Project header */}
            <div className="space-y-[var(--space-2)]">
              <div className="flex items-center gap-[var(--space-3)]">
                <div
                  className="w-11 h-11 rounded-[var(--radius-lg)] flex items-center justify-center text-lg font-bold text-white flex-shrink-0"
                  style={{ backgroundColor: color }}
                >
                  {project.name.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <h1 className="text-h1 truncate">{project.name}</h1>
                  {project.business_domain && (
                    <span
                      className="text-caption font-medium px-2 py-0.5 rounded-full"
                      style={{
                        backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
                        color,
                      }}
                    >
                      {project.business_domain}
                    </span>
                  )}
                </div>
              </div>

              {project.description && (
                <p className="text-body-sm text-muted-foreground">{project.description}</p>
              )}

              {/* Progress bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-caption text-muted-foreground">
                  <span>Progresso da elicitação</span>
                  <span style={{ color: 'var(--rs-primary)' }}>{progressPct}%</span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${progressPct}%`, backgroundColor: 'var(--rs-primary)' }}
                  />
                </div>
              </div>
            </div>

            {/* Welcome Screen (UX-DR8) */}
            <WelcomeScreen
              projectName={project.name}
              checklist={checklist}
              progressPct={progressPct}
              hasSessions={hasSessions}
              activeSession={activeSession}
              onStart={handleStartSession}
            />

            {/* Document Management Section (Story 4.3) - Only show when elicitation has begun */}
            {hasSessions && (
              <section className="mt-[var(--space-8)] border-t border-border pt-[var(--space-6)]">
                <div className="mb-6">
                  <h2 className="text-h2 font-semibold text-foreground">Documentos de Referência</h2>
                  <p className="text-body-sm text-muted-foreground mt-1">
                    Adicione SLAs, contratos, regulações ou regras de negócio existentes. Eles alimentarão o contexto da IA durante as sessões de elicitação.
                  </p>
                </div>
                <div className="space-y-6">
                  <DocumentUpload projectId={project.id} />
                  <DocumentList projectId={project.id} />
                </div>
              </section>
            )}
          </>
        )}
      </main>

      {/* Edit modal */}
      {project && (
        <ProjectModal
          open={editOpen}
          onClose={handleEditClose}
          project={project}
        />
      )}
    </div>
  )
}
