/**
 * ChatInput — input expansível com auto-resize e botão de upload (Stories 5.6, 5.5-4).
 *
 * - Enter = enviar (desktop)
 * - Shift+Enter = nova linha
 * - Botão de enviar com ícone
 * - Auto-resize até 6 linhas
 * - Botão 📎 para anexar PDF, Markdown ou TXT (≤ 10 MB)
 */

import { useCallback, useRef, useState, type KeyboardEvent } from 'react'
import { uploadDocument } from '@/services/documentsApi'

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024 // 10 MB — política de UX (servidor aceita até 20 MB)
const VALID_UPLOAD_EXTENSIONS = ['.pdf', '.md', '.markdown', '.txt']

function validateUploadFile(file: File): string | null {
  const fileName = file.name.toLowerCase()
  const hasValidExt = VALID_UPLOAD_EXTENSIONS.some((ext) => fileName.endsWith(ext))

  if (!hasValidExt) return 'Formato não suportado. Use PDF, Markdown ou TXT.'
  if (file.size > MAX_UPLOAD_BYTES) return 'Arquivo muito grande. Máximo: 10 MB.'
  return null
}

interface ChatInputProps {
  onSend: (content: string) => void
  disabled?: boolean
  placeholder?: string
  /** Project ID — required to enable the 📎 upload button */
  projectId?: string
  /** Called with the filename after a successful upload */
  onUploadSuccess?: (filename: string) => void
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Descreva seu projeto ou responda a pergunta...',
  projectId,
  onUploadSuccess,
}: ChatInputProps) {
  const [value, setValue] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const isDisabled = disabled || uploading

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || isDisabled) return
    onSend(trimmed)
    setValue('')
    setUploadError(null)
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, isDisabled, onSend])

  const handleKey = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value)
    setUploadError(null)
    // Auto-resize
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px' // max ~6 linhas
  }, [])

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) {
        setUploadError(null)
        return
      }

      // Reset input so the same file can be selected again
      e.target.value = ''
      setUploadError(null)

      const validationError = validateUploadFile(file)
      if (validationError) {
        setUploadError(validationError)
        return
      }

      if (!projectId) return // guard — button is hidden when !projectId anyway

      setUploading(true)
      try {
        await uploadDocument(projectId, file)
        onUploadSuccess?.(file.name)
      } catch {
        setUploadError('Erro ao enviar o documento. Tente novamente.')
      } finally {
        setUploading(false)
      }
    },
    [projectId, onUploadSuccess],
  )

  return (
    <div>
      {/* Main input bar */}
      <div
        className="flex items-end gap-2 p-3"
        style={{
          background: 'var(--rs-surface)',
          borderTop: '1px solid var(--border)',
          borderRadius: uploadError ? 'var(--radius-lg) var(--radius-lg) 0 0' : '0 0 var(--radius-lg) var(--radius-lg)',
        }}
      >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.md,.markdown,.txt"
          onChange={handleFileChange}
          hidden
          aria-hidden="true"
        />

        {/* Upload button — only rendered when projectId is provided */}
        {projectId && (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isDisabled}
            id="chat-upload-button"
            aria-label="Anexar documento (PDF, Markdown ou TXT até 10 MB)"
            className="shrink-0 flex items-center justify-center rounded-full transition-all"
            style={{
              width: 40,
              height: 40,
              background: 'var(--muted)',
              color: isDisabled ? 'var(--rs-text-muted)' : 'var(--rs-text-secondary)',
              cursor: isDisabled ? 'not-allowed' : 'pointer',
              opacity: isDisabled ? 0.5 : 1,
            }}
          >
            {/* Paperclip icon */}
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>
        )}

        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKey}
          disabled={isDisabled}
          placeholder={placeholder}
          rows={1}
          className="flex-1 resize-none outline-none bg-transparent"
          style={{
            fontSize: 'var(--text-body)',
            lineHeight: 'var(--leading-body)',
            color: 'var(--rs-text-primary)',
            padding: 'var(--space-2) var(--space-3)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            minHeight: 40,
            maxHeight: 160,
            transition: 'border-color 0.15s',
            opacity: isDisabled ? 0.7 : 1,
          }}
          id="chat-input"
          aria-label="Mensagem para a IA"
        />

        <button
          type="button"
          onClick={handleSend}
          disabled={isDisabled || !value.trim()}
          className="shrink-0 flex items-center justify-center rounded-full transition-all"
          style={{
            width: 40,
            height: 40,
            background: isDisabled || !value.trim() ? 'var(--muted)' : 'var(--rs-primary)',
            color: 'white',
            cursor: isDisabled || !value.trim() ? 'not-allowed' : 'pointer',
            opacity: isDisabled || !value.trim() ? 0.5 : 1,
          }}
          id="chat-send-button"
          aria-label="Enviar mensagem"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 2L11 13" />
            <path d="M22 2L15 22L11 13L2 9L22 2Z" />
          </svg>
        </button>
      </div>

      {/* Inline upload error */}
      {uploadError && (
        <div
          role="alert"
          id="chat-upload-error"
          style={{
            color: 'var(--rs-error)',
            fontSize: 'var(--text-body-sm)',
            padding: '6px var(--space-3) 8px',
            background: 'var(--rs-surface)',
            borderTop: '1px solid hsla(0, 72%, 58%, 0.2)',
            borderRadius: '0 0 var(--radius-lg) var(--radius-lg)',
          }}
        >
          ⚠️ {uploadError}
        </div>
      )}
    </div>
  )
}
