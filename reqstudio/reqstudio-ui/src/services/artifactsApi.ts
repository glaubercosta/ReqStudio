import { API_BASE, getAccessToken, ReqStudioApiError, request } from './apiClient'

export type ArtifactView = 'business' | 'technical'
export type ArtifactExportFormat = 'markdown' | 'json'

export interface ArtifactSection {
  id: string
  title: string
  content: string
  coverage: number
  sources: string[]
}

export interface ArtifactState {
  sections: ArtifactSection[]
  metadata: {
    total_coverage: number
  }
}

export interface Artifact {
  id: string
  project_id: string
  session_id: string | null
  artifact_type: string
  title: string
  artifact_state: ArtifactState
  coverage_data: Record<string, unknown> | null
  version: number
  status: string
  created_at: string
  updated_at: string
}

export interface ArtifactCoverageSection {
  id: string
  title: string
  coverage: number
  coverage_band: 'low' | 'medium' | 'high'
  card_state: 'pending' | 'active' | 'complete'
}

export interface ArtifactCoverage {
  artifact_id: string
  total_coverage: number
  sections: ArtifactCoverageSection[]
}

export interface ArtifactVersion {
  id: string
  artifact_id: string
  version: number
  state_snapshot: ArtifactState
  change_reason: string | null
  changed_by: string | null
  created_at: string
}

function parseFilename(contentDisposition: string | null): string | null {
  if (!contentDisposition) return null
  const match = /filename="([^"]+)"/i.exec(contentDisposition)
  return match?.[1] ?? null
}

async function exportRequest(path: string): Promise<{ blob: Blob; filename: string; durationMs: number | null }> {
  const headers: Record<string, string> = {}
  const token = getAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method: 'GET',
    credentials: 'include',
    headers,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ReqStudioApiError(
      body.error ?? { code: 'EXPORT_ERROR', message: 'Falha ao exportar artefato.' },
      res.status,
    )
  }

  const contentDisposition = res.headers.get('Content-Disposition')
  const filename = parseFilename(contentDisposition) ?? 'artifact-export'
  const durationMsHeader = res.headers.get('X-Export-Duration-Ms')
  const durationMs = durationMsHeader ? Number(durationMsHeader) : null

  return {
    blob: await res.blob(),
    filename,
    durationMs: Number.isFinite(durationMs) ? durationMs : null,
  }
}

export const artifactsApi = {
  listByProject: (projectId: string) =>
    request<{ data: Artifact[] }>(`/api/v1/artifacts/project/${projectId}`),

  get: (artifactId: string) =>
    request<{ data: Artifact }>(`/api/v1/artifacts/${artifactId}`),

  render: (artifactId: string, view: ArtifactView, showIds = false) =>
    request<{ data: { markdown: string } }>(
      `/api/v1/artifacts/${artifactId}/render?view=${view}&show_ids=${showIds}`,
    ),

  coverage: (artifactId: string) =>
    request<{ data: ArtifactCoverage }>(`/api/v1/artifacts/${artifactId}/coverage`),

  versions: (artifactId: string) =>
    request<{ data: ArtifactVersion[] }>(`/api/v1/artifacts/${artifactId}/versions`),

  exportFile: (artifactId: string, format: ArtifactExportFormat, view: ArtifactView = 'business', showIds = false) =>
    exportRequest(`/api/v1/artifacts/${artifactId}/export?format=${format}&view=${view}&show_ids=${showIds}`),
}
