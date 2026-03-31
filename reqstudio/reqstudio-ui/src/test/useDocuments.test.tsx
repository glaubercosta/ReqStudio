import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useDocuments, useUploadDocument, useDeleteDocument } from '../hooks/useDocuments';
import { listDocuments, uploadDocument, deleteDocument } from '../services/documentsApi';
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('../services/documentsApi', () => ({
  listDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useDocuments hook', () => {
  const projectId = 'proj-123';
  const mockDocs = [{ id: '1', filename: 'test.md', status: 'ready' }];

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient.clear();
  });

  it('useDocuments fetches a list of documents successfully', async () => {
    vi.mocked(listDocuments).mockResolvedValueOnce({ data: { items: mockDocs, total: 1 } } as any);

    const { result } = renderHook(() => useDocuments(projectId), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.data.items).toEqual(mockDocs);
    expect(listDocuments).toHaveBeenCalledWith(projectId);
  });

  it('useUploadDocument calls upload API and invalidates the list', async () => {
    vi.mocked(uploadDocument).mockResolvedValueOnce({ data: mockDocs[0] } as any);
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useUploadDocument(projectId), { wrapper });
    
    const file = new File(['text'], 'demo.txt', { type: 'text/plain' });
    result.current.mutate(file);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    
    expect(uploadDocument).toHaveBeenCalledWith(projectId, file);
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['documents', 'list', projectId] });
  });

  it('useDeleteDocument calls delete API and invalidates cache', async () => {
    vi.mocked(deleteDocument).mockResolvedValueOnce();
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useDeleteDocument(projectId), { wrapper });
    
    result.current.mutate('doc-1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(deleteDocument).toHaveBeenCalledWith(projectId, 'doc-1');
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['documents', 'list', projectId] });
  });
});
