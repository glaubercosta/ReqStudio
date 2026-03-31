import { useDocuments, useDeleteDocument } from '../hooks/useDocuments';
import { FileText, Loader2, Trash2 } from 'lucide-react';

interface DocumentListProps {
  projectId: string;
}

export function DocumentList({ projectId }: DocumentListProps) {
  const { data, isLoading, isError, error } = useDocuments(projectId);
  const deleteMutation = useDeleteDocument(projectId);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2 rounded-lg border border-border bg-card p-6 justify-center items-center h-48">
        <Loader2 className="animate-spin text-primary mb-2" size={24} />
        <p className="text-sm text-muted-foreground">Buscando documentos de referência...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 mt-4">
        <p className="text-sm text-destructive">Erro ao listar documentos: {(error as Error).message}</p>
      </div>
    );
  }

  const items = data?.data?.items || [];

  if (items.length === 0) {
    return null; // Empty state usually handled by the layout or empty placeholder above.
  }

  return (
    <div className="mt-8 flex flex-col gap-3">
      <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider mb-2">Manutenção de Documentos</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((doc) => (
          <div
            key={doc.id}
            className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4 shadow-sm hover:border-muted-foreground/30 transition-colors group"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2 max-w-[85%]">
                <FileText className="text-muted-foreground shrink-0" size={20} />
                <span
                  title={doc.filename}
                  className="text-sm font-medium text-foreground truncate block"
                >
                  {doc.filename}
                </span>
              </div>
              
              <button
                onClick={() => {
                  if (confirm(`Remover "${doc.filename}" do contexto do projeto de vez?`)) {
                    deleteMutation.mutate(doc.id);
                  }
                }}
                disabled={deleteMutation.isPending && deleteMutation.variables === doc.id}
                className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 p-1.5 rounded-md transition-colors disabled:opacity-50"
                title="Excluir documento"
              >
                {deleteMutation.isPending && deleteMutation.variables === doc.id ? (
                  <Loader2 className="animate-spin" size={16} />
                ) : (
                  <Trash2 size={16} />
                )}
              </button>
            </div>

            <div className="flex items-center gap-3 text-xs text-muted-foreground mt-2">
              <span className="bg-muted px-2 py-0.5 rounded-full font-mono text-foreground">
                {(doc.size_bytes / 1024 / 1024).toFixed(2)} MB
              </span>
              <span className="flex items-center gap-1 text-foreground">
                <span
                  className={`w-2 h-2 rounded-full ${
                    doc.status === 'ready'
                      ? 'bg-emerald-500'
                      : doc.status === 'error'
                      ? 'bg-destructive'
                      : 'bg-amber-400 animate-pulse'
                  }`}
                />
                {doc.status === 'ready'
                  ? 'Pronto'
                  : doc.status === 'error'
                  ? 'Erro'
                  : 'Processando'}
              </span>
              <span className="text-foreground">{doc.chunk_count} trechos</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
