import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { artifactsApi, type ArtifactExportFormat, type ArtifactView } from '@/services/artifactsApi'

function coverageColor(value: number): string {
  if (value < 0.3) return 'var(--rs-warning)'
  if (value <= 0.7) return 'var(--rs-amber)'
  return 'var(--rs-success)'
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString('pt-BR')
}

export default function ArtifactPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [view, setView] = useState<ArtifactView>('business')
  const [showIds, setShowIds] = useState(false)
  const [isExporting, setIsExporting] = useState<ArtifactExportFormat | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)

  const artifactId = id ?? ''

  const artifactQuery = useQuery({
    queryKey: ['artifact', artifactId],
    queryFn: () => artifactsApi.get(artifactId).then(r => r.data),
    enabled: !!artifactId,
    staleTime: 30_000,
  })

  const renderQuery = useQuery({
    queryKey: ['artifact-render', artifactId, view, showIds],
    queryFn: () => artifactsApi.render(artifactId, view, showIds).then(r => r.data),
    enabled: !!artifactId,
  })

  const coverageQuery = useQuery({
    queryKey: ['artifact-coverage', artifactId],
    queryFn: () => artifactsApi.coverage(artifactId).then(r => r.data),
    enabled: !!artifactId,
    staleTime: 15_000,
  })

  const versionsQuery = useQuery({
    queryKey: ['artifact-versions', artifactId],
    queryFn: () => artifactsApi.versions(artifactId).then(r => r.data),
    enabled: !!artifactId,
  })

  const sections = useMemo(
    () => artifactQuery.data?.artifact_state.sections ?? [],
    [artifactQuery.data?.artifact_state.sections],
  )

  const totalCoverage = coverageQuery.data?.total_coverage ?? artifactQuery.data?.artifact_state.metadata.total_coverage ?? 0

  const handleExport = async (format: ArtifactExportFormat, exportView?: ArtifactView) => {
    if (!artifactId) return
    setIsExporting(format)
    setExportError(null)
    try {
      const result = await artifactsApi.exportFile(artifactId, format, exportView ?? view, showIds)
      const url = URL.createObjectURL(result.blob)
      const link = document.createElement('a')
      link.href = url
      link.download = result.filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch {
      setExportError('Falha ao exportar o artefato. Tente novamente em alguns instantes.')
    } finally {
      setIsExporting(null)
    }
  }

  if (!id) return null

  if (artifactQuery.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-8 h-8 rounded-full border-2 animate-spin" style={{ borderColor: 'var(--rs-primary)', borderTopColor: 'transparent' }} />
      </div>
    )
  }

  if (artifactQuery.isError || !artifactQuery.data) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-3xl mx-auto rounded-xl border border-border bg-card p-6">
          <p className="text-body-sm" style={{ color: 'var(--rs-error)' }}>
            Artefato não encontrado ou sem acesso.
          </p>
          <Button className="mt-4" variant="outline" onClick={() => navigate('/projects')}>
            Voltar para projetos
          </Button>
        </div>
      </div>
    )
  }

  const artifact = artifactQuery.data

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b border-border bg-background/90 backdrop-blur-sm px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="min-w-0">
            <button
              type="button"
              className="text-caption text-muted-foreground hover:text-foreground"
              onClick={() => navigate(`/projects/${artifact.project_id}`)}
            >
              ← Voltar ao projeto
            </button>
            <h1 className="text-h2 font-semibold truncate">{artifact.title}</h1>
            <p className="text-caption text-muted-foreground">
              v{artifact.version} · {artifact.artifact_type}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              id="btn-view-business"
              variant={view === 'business' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setView('business')}
            >
              Negocio
            </Button>
            <Button
              id="btn-view-technical"
              variant={view === 'technical' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setView('technical')}
            >
              Tecnico
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
        <section className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-body font-semibold">Cobertura do artefato</h2>
                <p className="text-caption text-muted-foreground">
                  {Math.round(totalCoverage * 100)}% de cobertura global
                </p>
              </div>
              {view === 'business' && (
                <label className="text-caption flex items-center gap-2">
                  <input
                    id="toggle-show-ids"
                    type="checkbox"
                    checked={showIds}
                    onChange={(e) => setShowIds(e.target.checked)}
                  />
                  Exibir IDs
                </label>
              )}
            </div>
            <div className="mt-3 h-2 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full transition-all duration-500"
                style={{
                  width: `${Math.min(Math.max(totalCoverage, 0), 1) * 100}%`,
                  backgroundColor: coverageColor(totalCoverage),
                }}
              />
            </div>
          </div>

          <div className="hidden lg:block rounded-xl border border-border bg-card">
            <div className="px-4 py-3 border-b border-border">
              <h3 className="text-body font-semibold">Documento completo</h3>
            </div>
            <div className="p-4 max-h-[65vh] overflow-auto" data-testid="artifact-document-desktop">
              {renderQuery.isLoading ? (
                <p className="text-body-sm text-muted-foreground">Renderizando documento...</p>
              ) : (
                <pre className="text-body-sm whitespace-pre-wrap">{renderQuery.data?.markdown ?? ''}</pre>
              )}
            </div>
          </div>

          <div className="lg:hidden space-y-3" data-testid="artifact-feed-mobile">
            {sections.length === 0 ? (
              <div className="rounded-xl border border-border bg-card p-4 text-body-sm text-muted-foreground">
                Nenhuma seção disponível para exibição.
              </div>
            ) : (
              sections.map((section) => (
                <article key={section.id} className="rounded-xl border border-border bg-card p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-body font-semibold">{section.title}</h3>
                    <span
                      className="text-caption px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: 'var(--rs-primary-light)', color: 'var(--rs-primary)' }}
                    >
                      {section.sources.length} citacoes
                    </span>
                  </div>
                  <p className="mt-2 text-body-sm whitespace-pre-wrap">{section.content || '_Sem conteúdo detalhado._'}</p>
                </article>
              ))
            )}
          </div>
        </section>

        <aside className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-body font-semibold mb-3">Exportar</h3>
            <div className="grid grid-cols-1 gap-2">
              <Button
                id="btn-export-business-md"
                variant="outline"
                size="sm"
                disabled={isExporting !== null}
                onClick={() => handleExport('markdown', 'business')}
              >
                {isExporting === 'markdown' ? 'Exportando...' : 'MD Negocio'}
              </Button>
              <Button
                id="btn-export-technical-md"
                variant="outline"
                size="sm"
                disabled={isExporting !== null}
                onClick={() => handleExport('markdown', 'technical')}
              >
                {isExporting === 'markdown' ? 'Exportando...' : 'MD Tecnico'}
              </Button>
              <Button
                id="btn-export-json"
                variant="outline"
                size="sm"
                disabled={isExporting !== null}
                onClick={() => handleExport('json')}
              >
                {isExporting === 'json' ? 'Exportando...' : 'JSON'}
              </Button>
            </div>
            {exportError && (
              <p
                className="mt-3 text-caption"
                style={{ color: 'var(--rs-error)' }}
                role="alert"
              >
                {exportError}
              </p>
            )}
          </div>

          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-body font-semibold mb-2">Secoes e citacoes</h3>
            <div className="space-y-2">
              {sections.length === 0 ? (
                <p className="text-caption text-muted-foreground">Sem secoes no artefato.</p>
              ) : (
                sections.map((section) => (
                  <div key={section.id} className="flex items-center justify-between text-caption">
                    <span className="truncate">{section.title}</span>
                    <span className="px-2 py-0.5 rounded-full bg-muted">
                      {section.sources.length}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-body font-semibold mb-2">Historico de versoes</h3>
            <div className="space-y-2 max-h-80 overflow-auto">
              {versionsQuery.isLoading ? (
                <p className="text-caption text-muted-foreground">Carregando versoes...</p>
              ) : (
                (versionsQuery.data ?? []).map((version) => (
                  <article key={version.id} className="rounded-md border border-border p-2">
                    <p className="text-caption font-medium">v{version.version}</p>
                    <p className="text-caption text-muted-foreground">{formatDate(version.created_at)}</p>
                    <p className="text-caption">{version.change_reason || 'Sem justificativa'}</p>
                    <p className="text-caption text-muted-foreground">Autor: {version.changed_by || 'N/A'}</p>
                  </article>
                ))
              )}
            </div>
          </div>
        </aside>
      </main>
    </div>
  )
}
