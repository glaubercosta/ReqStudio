import { useCallback, useRef, useState } from 'react';
import { useUploadDocument } from '../hooks/useDocuments';
import { ReqStudioApiError } from '../services/apiClient';
import { UploadCloud, CheckCircle2, AlertTriangle, FileText, X } from 'lucide-react';

interface DocumentUploadProps {
  projectId: string;
}

export function DocumentUpload({ projectId }: DocumentUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadError, setUploadError] = useState<{ message: string; help?: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadDocument(projectId);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const processFile = (file: File) => {
    if (!file) return;
    setUploadError(null);
    uploadMutation.mutate(file, {
      onError: (err) => {
        if (err instanceof ReqStudioApiError) {
          setUploadError({
            message: err.error?.message || 'Erro ao enviar documento.',
            help: err.error?.help,
          });
        } else {
          setUploadError({ message: 'Erro desconhecido de conexão.' });
        }
      },
    });
  };

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragOver(false);
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        processFile(e.dataTransfer.files[0]);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [uploadMutation, projectId]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
      // clear the input so the same file could be uploaded again if needed
      e.target.value = '';
    }
  };

  const handleClickArea = () => {
    if (!uploadMutation.isPending && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Target Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClickArea}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') handleClickArea();
        }}
        role="button"
        tabIndex={0}
        aria-label="Área de upload de documentos"
        className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-lg transition-colors cursor-pointer ${
          isDragOver
            ? 'border-blue-500 bg-blue-500/10'
            : uploadError
            ? 'border-red-500/50 bg-red-500/5 hover:bg-red-500/10'
            : 'border-border bg-muted/30 hover:bg-muted/50'
        } ${uploadMutation.isPending ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.md,.markdown"
          className="hidden"
          onChange={handleFileChange}
        />

        {uploadMutation.isPending ? (
          <>
            <div className="animate-spin text-primary mb-2">
              <UploadCloud size={32} />
            </div>
            <p className="text-sm font-medium text-foreground">Fazendo upload...</p>
            <p className="text-xs text-muted-foreground mt-1">Por favor aguarde enquanto transferimos e lemos o arquivo.</p>
          </>
        ) : uploadMutation.isSuccess && !uploadError ? (
          <>
            <CheckCircle2 size={32} className="text-emerald-500 mb-2" />
            <p className="text-sm font-medium text-foreground">Documento importado com sucesso!</p>
            <p className="text-xs text-muted-foreground mt-1">Acrescente mais clicando ou arrastando outro arquivo.</p>
          </>
        ) : (
          <>
            <FileText size={32} className={`${uploadError ? 'text-destructive' : 'text-muted-foreground'} mb-2`} />
            <p className={`text-sm font-medium ${uploadError ? 'text-destructive' : 'text-foreground'}`}>
              Clique para procurar ou arraste um arquivo
            </p>
            <p className="text-xs text-muted-foreground mt-1 text-center">
              Extensões suportadas: <strong>.pdf</strong>, <strong>.md</strong>.<br />
              Tamanho máximo: <strong>20 MB</strong>.
            </p>
          </>
        )}
      </div>

      {/* Guided Recovery Error Banner */}
      {uploadError && (
        <div className="flex animate-fade-in items-start gap-3 rounded-md bg-destructive/10 p-4 border border-destructive/20 mt-2">
          <AlertTriangle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-destructive">{uploadError.message}</h3>
            {uploadError.help && (
              <p className="mt-1 text-sm text-destructive/80 leading-snug">{uploadError.help}</p>
            )}
          </div>
          <button
            onClick={() => setUploadError(null)}
            className="text-destructive hover:text-destructive/80 hover:bg-destructive/10 rounded p-1 transition-colors"
            title="Fechar"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
