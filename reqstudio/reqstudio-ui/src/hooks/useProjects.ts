/**
 * useProjects — TanStack Query hook para listar projetos (Story 3.2).
 * Revalida on-focus e on-reconnect automaticamente.
 */

import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/services/projectsApi'

export const projectsQueryKey = (status = 'active') => ['projects', status]

export function useProjects(status = 'active') {
  return useQuery({
    queryKey: projectsQueryKey(status),
    queryFn: () => projectsApi.list(status).then(r => r.data),
    staleTime: 30_000, // 30s — evita refetch desnecessário
  })
}
