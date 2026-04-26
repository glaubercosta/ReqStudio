/**
 * Sessions API service (Story 5.6).
 *
 * Endpoints:
 *   - Sessions: CRUD dentro de um projeto
 *   - Messages: listagem de mensagens
 *   - Elicit: SSE streaming para elicitação
 */

import { request } from './apiClient'
import type { PaginatedList } from './types'

// ── Types ────────────────────────────────────────────────────────────────────

export interface Session {
  id: string
  project_id: string
  workflow_id: string
  status: string
  workflow_position: Record<string, unknown> | null
  artifact_state: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  message_index: number
  input_tokens?: number
  output_tokens?: number
  cost_usd?: number
  latency_ms?: number
  model?: string
  created_at: string
}

interface SessionListResponse {
  data: PaginatedList<Session>
}

interface SessionResponse {
  data: Session
}

interface MessageListResponse {
  data: PaginatedList<Message>
}

// ── API ──────────────────────────────────────────────────────────────────────

export const sessionsApi = {
  list: (projectId: string) =>
    request<SessionListResponse>(`/api/v1/projects/${projectId}/sessions`),

  get: (sessionId: string) =>
    request<SessionResponse>(`/api/v1/sessions/${sessionId}`),

  create: (projectId: string) =>
    request<SessionResponse>(`/api/v1/projects/${projectId}/sessions`, {
      method: 'POST',
      body: JSON.stringify({}),
    }),

  updateStatus: (sessionId: string, status: string) =>
    request<SessionResponse>(`/api/v1/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  listMessages: (sessionId: string, page = 1, size = 50) =>
    request<MessageListResponse>(
      `/api/v1/sessions/${sessionId}/messages?page=${page}&size=${size}`,
    ),
}
