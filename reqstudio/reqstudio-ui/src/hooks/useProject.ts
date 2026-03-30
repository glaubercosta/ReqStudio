/**
 * useProject — TanStack Query hook para buscar projeto por ID (Story 3.4).
 */

import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/services/projectsApi'

export const projectQueryKey = (id: string) => ['project', id]

export function useProject(id: string) {
  return useQuery({
    queryKey: projectQueryKey(id),
    queryFn: () => projectsApi.get(id).then(r => r.data),
    enabled: !!id,
    staleTime: 30_000,
  })
}
