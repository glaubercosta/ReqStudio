import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { DocumentList } from '../components/DocumentList';
import { useDocuments, useDeleteDocument } from '../hooks/useDocuments';

vi.mock('../hooks/useDocuments', () => ({
  useDocuments: vi.fn(),
  useDeleteDocument: vi.fn(),
}));

describe('DocumentList component', () => {
  const mockDeleteMutate = vi.fn();
  const mockDocs = [
    { id: '1', filename: 'contrato.pdf', status: 'ready', size_bytes: 2048 * 1024, chunk_count: 5 },
    { id: '2', filename: 'regras.md', status: 'processing', size_bytes: 1024 * 1024, chunk_count: 0 },
    { id: '3', filename: 'ruim.pdf', status: 'error', size_bytes: 1024, chunk_count: 0 }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default happy path
    vi.mocked(useDeleteDocument).mockReturnValue({
      mutate: mockDeleteMutate,
      isPending: false,
      variables: null,
    } as any);

    vi.mocked(useDocuments).mockReturnValue({
      data: { data: { items: mockDocs, total: 3 } },
      isLoading: false,
      isError: false,
      error: null
    } as any);
  });

  it('renders loading skeleton state', () => {
    vi.mocked(useDocuments).mockReturnValueOnce({ isLoading: true } as any);
    render(<DocumentList projectId="proj-123" />);
    
    expect(screen.getByText('Buscando documentos de referência...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    vi.mocked(useDocuments).mockReturnValueOnce({ 
      isError: true, 
      error: new Error('Network failed') 
    } as any);
    render(<DocumentList projectId="proj-123" />);
    
    expect(screen.getByText('Erro ao listar documentos: Network failed')).toBeInTheDocument();
  });

  it('renders an empty state correctly without breaking', () => {
    vi.mocked(useDocuments).mockReturnValueOnce({ 
      data: { data: { items: [] } },
      isLoading: false, 
      isError: false 
    } as any);
    const { container } = render(<DocumentList projectId="proj-123" />);
    
    expect(container.firstChild).toBeNull(); // we return null for empty lists
  });

  it('renders documents with their metadata formatted', () => {
    render(<DocumentList projectId="proj-123" />);
    
    expect(screen.getByText('contrato.pdf')).toBeInTheDocument();
    expect(screen.getByText('2.00 MB')).toBeInTheDocument(); // 2048 * 1024
    expect(screen.getByText('5 trechos')).toBeInTheDocument();
  });

  it('renders correct status badges', () => {
    render(<DocumentList projectId="proj-123" />);
    
    expect(screen.getByText('Pronto')).toBeInTheDocument();
    expect(screen.getByText('Processando')).toBeInTheDocument();
    expect(screen.getByText('Erro')).toBeInTheDocument();
  });

  it('prompts confirmation when deleting a document', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    
    render(<DocumentList projectId="proj-123" />);
    const deleteButtons = screen.getAllByTitle('Excluir documento');
    
    fireEvent.click(deleteButtons[0]);
    
    expect(confirmSpy).toHaveBeenCalledWith('Remover "contrato.pdf" do contexto do projeto de vez?');
    expect(mockDeleteMutate).toHaveBeenCalledWith('1');
  });

  it('does not send delete if confirmation is denied', () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    
    render(<DocumentList projectId="proj-123" />);
    const deleteButtons = screen.getAllByTitle('Excluir documento');
    
    fireEvent.click(deleteButtons[0]);
    
    expect(confirmSpy).toHaveBeenCalled();
    expect(mockDeleteMutate).not.toHaveBeenCalled();
  });
});
