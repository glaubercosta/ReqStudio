/**
 * ProjectModal — modal de criação e edição de projetos (Stories 3.3 + 3.5).
 *
 * Modo criação: nome + descrição + domínio  → POST /api/v1/projects
 * Modo edição:  mesmo formulário pre-preenchido → PATCH /api/v1/projects/:id
 */

import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { projectsApi, type Project } from '@/services/projectsApi'
import { projectsQueryKey } from '@/hooks/useProjects'
import { ReqStudioApiError } from '@/services/apiClient'

const DOMAINS = [
  'Saúde', 'Finanças', 'Jurídico', 'Educação',
  'Tecnologia', 'Varejo', 'Logística', 'Governo', 'Outro',
]

interface Props {
  open: boolean
  onClose: () => void
  project?: Project   // se fornecido, modo edição
}

interface FormState {
  name: string
  description: string
  business_domain: string
}

interface FieldErrors {
  name?: string
}

export function ProjectModal({ open, onClose, project }: Props) {
  const qc = useQueryClient()
  const nameRef = useRef<HTMLInputElement>(null)
  const isEdit = !!project

  const [form, setForm] = useState<FormState>({
    name: '',
    description: '',
    business_domain: '',
  })
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [apiError, setApiError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  // Pre-preenche no modo edição
  useEffect(() => {
    if (project) {
      setForm({
        name: project.name,
        description: project.description ?? '',
        business_domain: project.business_domain ?? '',
      })
    } else {
      setForm({ name: '', description: '', business_domain: '' })
    }
    setFieldErrors({})
    setApiError(null)
    setSuccess(false)
  }, [project, open])

  // Focus no nome ao abrir
  useEffect(() => {
    if (open) setTimeout(() => nameRef.current?.focus(), 50)
  }, [open])

  // Fecha com Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  if (!open) return null

  const validate = (): boolean => {
    const errors: FieldErrors = {}
    if (!form.name.trim()) errors.name = 'Nome é obrigatório.'
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setApiError(null)
    setLoading(true)

    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        business_domain: form.business_domain || undefined,
      }

      if (isEdit && project) {
        await projectsApi.update(project.id, payload)
      } else {
        await projectsApi.create(payload)
      }

      // Invalida a cache para forçar refetch
      await qc.invalidateQueries({ queryKey: projectsQueryKey() })
      setSuccess(true)
      setTimeout(onClose, 800)
    } catch (err) {
      if (err instanceof ReqStudioApiError) {
        setApiError(err.error.message)
      } else {
        setApiError('Erro inesperado. Tente novamente.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-modal-title"
        className="fixed inset-0 z-50 flex items-center justify-center p-[var(--space-4)]"
      >
        <div
          className="w-full max-w-md rounded-[var(--radius-xl)] border border-border bg-card shadow-2xl"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-[var(--space-5)] border-b border-border">
            <h2 id="project-modal-title" className="text-h3 font-semibold">
              {isEdit ? 'Editar projeto' : 'Novo projeto'}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground transition-colors p-1"
              aria-label="Fechar"
            >
              ✕
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-[var(--space-5)] space-y-[var(--space-4)]">

            {/* API error */}
            {apiError && (
              <div
                className="rounded-[var(--radius-md)] p-[var(--space-3)] text-body-sm"
                role="alert"
                style={{
                  backgroundColor: 'color-mix(in srgb, var(--rs-error) 10%, transparent)',
                  borderLeft: '3px solid var(--rs-error)',
                  color: 'var(--rs-error)',
                }}
              >
                {apiError}
              </div>
            )}

            {/* Success */}
            {success && (
              <div
                className="rounded-[var(--radius-md)] p-[var(--space-3)] text-body-sm"
                style={{
                  backgroundColor: 'color-mix(in srgb, var(--rs-success) 10%, transparent)',
                  borderLeft: '3px solid var(--rs-success)',
                  color: 'var(--rs-success)',
                }}
              >
                {isEdit ? 'Projeto atualizado!' : 'Projeto criado com sucesso!'}
              </div>
            )}

            {/* Nome */}
            <div className="space-y-[var(--space-1)]">
              <Label htmlFor="project-name">Nome *</Label>
              <Input
                id="project-name"
                ref={nameRef}
                placeholder="Ex: Sistema de Prontuário"
                value={form.name}
                onChange={e => {
                  setForm(p => ({ ...p, name: e.target.value }))
                  setFieldErrors(p => ({ ...p, name: undefined }))
                }}
                aria-invalid={!!fieldErrors.name}
              />
              {fieldErrors.name && (
                <p className="text-caption" style={{ color: 'var(--rs-error)' }}>
                  {fieldErrors.name}
                </p>
              )}
            </div>

            {/* Domínio */}
            <div className="space-y-[var(--space-1)]">
              <Label htmlFor="project-domain">Domínio de negócio</Label>
              <select
                id="project-domain"
                value={form.business_domain}
                onChange={e => setForm(p => ({ ...p, business_domain: e.target.value }))}
                className="w-full rounded-[var(--radius-md)] border border-input bg-background px-3 py-2 text-body-sm focus:outline-none focus:ring-2 focus:ring-[var(--rs-primary)]"
              >
                <option value="">Selecione um domínio (opcional)</option>
                {DOMAINS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>

            {/* Descrição */}
            <div className="space-y-[var(--space-1)]">
              <Label htmlFor="project-description">Descrição</Label>
              <textarea
                id="project-description"
                rows={3}
                placeholder="Descreva o objetivo do projeto..."
                value={form.description}
                onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                className="w-full rounded-[var(--radius-md)] border border-input bg-background px-3 py-2 text-body-sm focus:outline-none focus:ring-2 focus:ring-[var(--rs-primary)] resize-none"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-[var(--space-3)] pt-[var(--space-2)]">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={onClose}
                disabled={loading}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                className="flex-1"
                disabled={loading || success}
                id={isEdit ? 'btn-update-project' : 'btn-create-project'}
              >
                {loading
                  ? (isEdit ? 'Salvando...' : 'Criando...')
                  : success
                  ? '✓ Salvo'
                  : (isEdit ? 'Salvar alterações' : 'Criar projeto')}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
