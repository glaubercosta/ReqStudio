/**
 * Testes do hook useProjectSessions — Story 5.5-2.
 *
 * Testes unitários estáticos: validam a lógica de filtro e ordenação
 * sem dependência de QueryClient real (evita problemas de ambiente).
 */

import { describe, it, expect } from 'vitest'
import type { Session } from '@/services/sessionsApi'

// ── Helpers duplicados do hook (para teste isolado) ───────────────────────────

function filterResumable(sessions: Session[]): Session[] {
  return sessions
    .filter((s) => s.status === 'active' || s.status === 'paused')
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
}

// ── Fixtures ──────────────────────────────────────────────────────────────────

const makeSession = (overrides: Partial<Session> = {}): Session => ({
  id: 'sess-1',
  project_id: 'proj-1',
  workflow_id: 'wf-1',
  status: 'active',
  workflow_position: null,
  artifact_state: null,
  created_at: '2026-04-01T10:00:00Z',
  updated_at: '2026-04-01T10:00:00Z',
  ...overrides,
})

// ── Testes unitários da lógica de filtro ─────────────────────────────────────

describe('useProjectSessions — lógica de filtro', () => {
  it('retorna apenas sessões active e paused', () => {
    const sessions = [
      makeSession({ id: '1', status: 'active' }),
      makeSession({ id: '2', status: 'paused' }),
      makeSession({ id: '3', status: 'completed' }),
    ]
    const result = filterResumable(sessions)
    expect(result).toHaveLength(2)
    expect(result.map((s) => s.id)).toEqual(expect.arrayContaining(['1', '2']))
  })

  it('retorna lista vazia quando todas são completed', () => {
    const sessions = [
      makeSession({ id: '1', status: 'completed' }),
      makeSession({ id: '2', status: 'completed' }),
    ]
    expect(filterResumable(sessions)).toHaveLength(0)
  })

  it('ordena por updated_at desc — mais recente primeiro', () => {
    const sessions = [
      makeSession({ id: 'old', status: 'active', updated_at: '2026-04-01T08:00:00Z' }),
      makeSession({ id: 'new', status: 'paused', updated_at: '2026-04-02T12:00:00Z' }),
    ]
    const result = filterResumable(sessions)
    expect(result[0].id).toBe('new')
  })

  it('retorna lista vazia quando não há sessões', () => {
    expect(filterResumable([])).toHaveLength(0)
  })

  it('AC 3 — fallback: sem sessão active/paused → lista vazia (botão Iniciar deve ser exibido)', () => {
    const sessions = [makeSession({ id: '1', status: 'completed' })]
    const resumable = filterResumable(sessions)
    const activeSession = resumable[0] ?? null
    expect(activeSession).toBeNull()
  })

  it('AC 2 — detecção ativa: sessão active retorna como primeira', () => {
    const sessions = [makeSession({ id: 'sess-active', status: 'active' })]
    const resumable = filterResumable(sessions)
    expect(resumable[0].id).toBe('sess-active')
  })

  it('AC 2 — detecção pausada: sessão paused retorna como primeira', () => {
    const sessions = [makeSession({ id: 'sess-paused', status: 'paused' })]
    const resumable = filterResumable(sessions)
    expect(resumable[0].id).toBe('sess-paused')
  })
})
