import { describe, it, expect, vi, beforeEach } from 'vitest';
import { uploadDocument, listDocuments, deleteDocument } from '../services/documentsApi';
import * as apiClientModule from '../services/apiClient';

vi.mock('../services/apiClient', () => ({
  request: vi.fn(),
}));

describe('documentsApi', () => {
  const projectId = 'proj-123';
  const mockDoc = { id: 'doc-1', filename: 'test.md', status: 'ready', size_bytes: 100 };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('uploadDocument should use FormData and call apiClient with correct path', async () => {
    vi.mocked(apiClientModule.request).mockResolvedValueOnce({ data: mockDoc });
    
    const file = new File(['# content'], 'test.md', { type: 'text/markdown' });
    const result = await uploadDocument(projectId, file);
    
    expect(result.data).toEqual(mockDoc);
    expect(apiClientModule.request).toHaveBeenCalledWith(
      `/api/v1/projects/${projectId}/documents`,
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      })
    );
  });

  it('listDocuments should call correct endpoint and return array', async () => {
    vi.mocked(apiClientModule.request).mockResolvedValueOnce({ data: { items: [mockDoc], total: 1 } });
    
    const result = await listDocuments(projectId);
    
    expect(result.data.items).toHaveLength(1);
    expect(result.data.items[0].filename).toBe('test.md');
    expect(apiClientModule.request).toHaveBeenCalledWith(`/api/v1/projects/${projectId}/documents`);
  });

  it('deleteDocument should send DELETE request to specific document', async () => {
    vi.mocked(apiClientModule.request).mockResolvedValueOnce({});
    
    await deleteDocument(projectId, 'doc-1');
    
    expect(apiClientModule.request).toHaveBeenCalledWith(
      `/api/v1/projects/${projectId}/documents/doc-1`,
      expect.objectContaining({ method: 'DELETE' })
    );
  });
});
