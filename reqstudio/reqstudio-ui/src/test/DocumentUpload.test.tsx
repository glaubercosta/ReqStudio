import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { DocumentUpload } from '../components/DocumentUpload';
import { useUploadDocument } from '../hooks/useDocuments';
import { ReqStudioApiError } from '../services/apiClient';

vi.mock('../hooks/useDocuments', () => ({
  useUploadDocument: vi.fn(),
}));

describe('DocumentUpload component', () => {
  const mockMutate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useUploadDocument).mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isSuccess: false,
    } as any);
  });

  it('renders default state correctly', () => {
    render(<DocumentUpload projectId="proj-123" />);
    expect(screen.getByText('Clique para procurar ou arraste um arquivo')).toBeInTheDocument();
    expect(screen.getByText(/Extensões suportadas/)).toBeInTheDocument();
  });

  it('triggers file selection dialog when clicked', () => {
    const { container } = render(<DocumentUpload projectId="proj-123" />);
    const div = container.querySelector('[role="button"]');
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    const clickSpy = vi.spyOn(input, 'click');
    fireEvent.click(div!);
    expect(clickSpy).toHaveBeenCalled();
  });

  it('calls upload mutation on file drop', () => {
    render(<DocumentUpload projectId="proj-123" />);
    const dropzone = screen.getByRole('button');

    // Simulate drag over and drop
    fireEvent.dragOver(dropzone);
    
    const file = new File(['text'], 'test.pdf', { type: 'application/pdf' });
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] }
    });

    expect(mockMutate).toHaveBeenCalledWith(file, expect.any(Object));
  });

  it('shows generic error if mutation fails without specialized response', async () => {
    mockMutate.mockImplementation((_file, options) => {
      options.onError(new Error('Unknown'));
    });

    render(<DocumentUpload projectId="proj-123" />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    const file = new File(['text'], 'test.md');
    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText('Erro desconhecido de conexão.')).toBeInTheDocument();
  });

  it('demonstrates guided recovery behavior when 415 error occurs', async () => {
    mockMutate.mockImplementation((_file, options) => {
      options.onError(new ReqStudioApiError({
        code: 'UNSUPPORTED_FILE_TYPE',
        message: 'Tipo de arquivo inválido.',
        help: 'Por favor envie PDFs ou Markdown.',
        actions: [],
        severity: 'error'
      }, 415));
    });

    render(<DocumentUpload projectId="proj-123" />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    const file = new File(['MZexe'], 'virus.exe');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('Tipo de arquivo inválido.')).toBeInTheDocument();
      expect(screen.getByText('Por favor envie PDFs ou Markdown.')).toBeInTheDocument();
    });
  });
});
