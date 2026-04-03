/**
 * Projects API client (Story 3.2).
 * Usa o mesmo fetch/interceptor de 401 do apiClient base.
 */

import { API_BASE, getAccessToken, ReqStudioApiError } from './apiClient'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> ?? {}),
  }
  const token = getAccessToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers,
  })

  const body = await res.json()
  if (!res.ok) throw new ReqStudioApiError(body.error, res.status)
  return body
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Project {
  id: string
  name: string
  description: string | null
  business_domain: string | null
  status: 'active' | 'archived'
  progress_summary: Record<string, unknown> | null
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface ProjectListData {
  items: Project[]
  total: number
  page: number
  size: number
  pages: number
}

export interface CreateProjectPayload {
  name: string
  description?: string
  business_domain?: string
}

export interface UpdateProjectPayload {
  name?: string
  description?: string
  business_domain?: string
  status?: 'active' | 'archived'
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const projectsApi = {
  list: (status = 'active', page = 1, size = 20) =>
    request<{ data: ProjectListData }>(
      `/api/v1/projects?status=${status}&page=${page}&size=${size}`,
    ),

  get: (id: string) =>
    request<{ data: Project }>(`/api/v1/projects/${id}`),

  create: (payload: CreateProjectPayload) =>
    request<{ data: Project }>('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  update: (id: string, payload: UpdateProjectPayload) =>
    request<{ data: Project }>(`/api/v1/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
}
