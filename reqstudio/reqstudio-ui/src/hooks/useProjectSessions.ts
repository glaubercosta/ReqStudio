/**
 * useProjectSessions — TanStack Query hook para sessões retomáveis (Story 5.5-2).
 *
 * Filtra client-side sessões com status 'active' ou 'paused',
 * ordenadas por updated_at desc. O primeiro item é a sessão mais recente.
 */

import { useQuery } from '@tanstack/react-query'
import { sessionsApi } from '@/services/sessionsApi'
import type { Session } from '@/services/sessionsApi'

export const resumableSessionsKey = (id: string) => ['sessions', id, 'resumable']

export function useProjectSessions(projectId: string) {
  return useQuery({
    queryKey: resumableSessionsKey(projectId),
    queryFn: async (): Promise<Session[]> => {
      const res = await sessionsApi.list(projectId)
      const items: Session[] = res.data?.items ?? []
      return items
        .filter((s) => s.status === 'active' || s.status === 'paused')
        .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    },
    enabled: !!projectId,
    staleTime: 10_000,
  })
}
