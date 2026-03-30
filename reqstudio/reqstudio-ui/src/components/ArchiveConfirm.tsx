/**
 * ArchiveConfirm — confirmação inline de arquivamento (UX-DR16, Story 3.5).
 */

import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { projectsApi, type Project } from '@/services/projectsApi'
import { projectsQueryKey } from '@/hooks/useProjects'

interface Props {
  project: Project
  onClose: () => void
}

export function ArchiveConfirm({ project, onClose }: Props) {
  const qc = useQueryClient()
  const [loading, setLoading] = useState(false)
  const isArchived = project.status === 'archived'

  const handle = async () => {
    setLoading(true)
    try {
      await projectsApi.update(project.id, {
        status: isArchived ? 'active' : 'archived',
      })
      await qc.invalidateQueries({ queryKey: projectsQueryKey('active') })
      await qc.invalidateQueries({ queryKey: projectsQueryKey('archived') })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="rounded-[var(--radius-md)] border border-border p-[var(--space-3)] space-y-[var(--space-2)] bg-card shadow-md"
      role="alertdialog"
    >
      <p className="text-body-sm font-medium">
        {isArchived
          ? `Restaurar "${project.name}"?`
          : `Arquivar "${project.name}"?`}
      </p>
      <p className="text-caption text-muted-foreground">
        {isArchived
          ? 'O projeto voltará para a lista de ativos.'
          : 'O projeto ficará oculto da lista principal. Dados preservados.'}
      </p>
      <div className="flex gap-[var(--space-2)]">
        <Button variant="outline" size="sm" onClick={onClose} disabled={loading}>
          Cancelar
        </Button>
        <Button
          size="sm"
          disabled={loading}
          onClick={handle}
          id={isArchived ? 'btn-restore-project' : 'btn-archive-project'}
          style={!isArchived ? { backgroundColor: 'var(--rs-warning)', color: 'white' } : undefined}
        >
          {loading ? '...' : isArchived ? 'Restaurar' : 'Arquivar'}
        </Button>
      </div>
    </div>
  )
}
