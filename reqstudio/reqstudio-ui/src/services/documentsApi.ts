import { request as apiClient } from './apiClient';

/**
 * Representation of a Document from the backend.
 */
export interface DocumentResponse {
  id: string;
  project_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  status: 'processing' | 'ready' | 'error';
  chunk_count: number;
  tenant_id: string;
  created_at: string;
  updated_at: string | null;
}

/**
 * Upload a document to a project.
 * Important: Relies on `fetch`'s native capability to handle FormData boundary generation.
 * NEVER manually set `Content-Type: multipart/form-data` on fetch, otherwise the boundary is lost.
 */
export async function uploadDocument(projectId: string, file: File): Promise<{ data: DocumentResponse }> {
  const formData = new FormData();
  formData.append('file', file);

  // Note: we don't set Content-Type header so the browser sets it automatically with the multi-part boundary
  return apiClient<{ data: DocumentResponse }>(
    `/api/v1/projects/${projectId}/documents`,
    {
      method: 'POST',
      body: formData,
    }
  );
}

/**
 * List all uploaded documents for a project.
 */
export async function listDocuments(projectId: string): Promise<{ data: { items: DocumentResponse[]; total: number } }> {
  return apiClient<{ data: { items: DocumentResponse[]; total: number } }>(`/api/v1/projects/${projectId}/documents`);
}

/**
 * Delete a specific document.
 */
export async function deleteDocument(projectId: string, documentId: string): Promise<void> {
  await apiClient(`/api/v1/projects/${projectId}/documents/${documentId}`, {
    method: 'DELETE',
  });
}
