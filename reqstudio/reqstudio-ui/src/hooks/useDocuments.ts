import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteDocument, listDocuments, uploadDocument } from '../services/documentsApi';

export const documentKeys = {
  all: ['documents'] as const,
  lists: () => [...documentKeys.all, 'list'] as const,
  list: (projectId: string) => [...documentKeys.lists(), projectId] as const,
};

export function useDocuments(projectId: string) {
  return useQuery({
    queryKey: documentKeys.list(projectId),
    queryFn: () => listDocuments(projectId),
    enabled: !!projectId,
  });
}

export function useUploadDocument(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => uploadDocument(projectId, file),
    onSuccess: () => {
      // Refresh the document list upon successful upload
      queryClient.invalidateQueries({ queryKey: documentKeys.list(projectId) });
    },
  });
}

export function useDeleteDocument(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => deleteDocument(projectId, documentId),
    onSuccess: () => {
      // Refresh the document list upon successful deletion
      queryClient.invalidateQueries({ queryKey: documentKeys.list(projectId) });
    },
  });
}
