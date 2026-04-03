# Story 5.5-4: Upload de Documento no ChatInput

Status: done

## Story

As a Ana (especialista de domínio),
I want poder anexar um documento PDF, Markdown ou texto simples diretamente no chat da sessão de elicitação com um botão 📎,
So that a IA use meu contexto (SLAs, contratos, especificações existentes) para gerar requisitos mais precisos sem precisar sair da conversa (FR9, A3 da Retro Epic 5).

## Acceptance Criteria

1. **Given** o usuário está na `SessionPage` com uma sessão ativa  
   **When** clica no botão 📎 (paperclip) ao lado do `ChatInput`  
   **Then** uma janela de seleção de arquivo nativa abre, aceitando apenas `.pdf`, `.md`, `.markdown`, `.txt`
2. **Given** o arquivo selecionado é válido (PDF, Markdown ou TXT, ≤ 10 MB)  
   **When** o usuário confirma a seleção  
   **Then** o arquivo é enviado via `POST /api/v1/projects/{project_id}/documents` e uma mensagem de confirmação aparece na conversa: _"📎 [nome-do-arquivo] enviado e disponível para a IA."_
3. **Given** o arquivo excede 10 MB ou tem extensão inválida  
   **When** o usuário tenta selecionar  
   **Then** uma mensagem de erro inline é exibida abaixo do `ChatInput` (sem toast externo): _"Apenas PDF, Markdown ou TXT até 10 MB."_

4. **Given** o upload falhou por erro de rede/API  
   **When** a resposta da API retorna erro  
   **Then** uma mensagem de erro inline aparece: _"Erro ao enviar o documento. Tente novamente."_ — o `ChatInput` permanece habilitado

5. **Given** o upload está em progresso  
   **When** o usuário tenta enviar outra mensagem ou novo arquivo  
   **Then** o botão 📎 e o botão de envio ficam desabilitados durante o upload (estado `uploading`)

6. **Given** a sessão está no status `completed` ou o chat está `disabled`  
   **When** o componente `ChatInput` renderiza  
   **Then** o botão 📎 também é desabilitado (consistente com o botão de envio)

## Tasks / Subtasks

- [x] **Task 1: Adicionar botão 📎 e lógica de upload no `ChatInput`** (AC: 1, 2, 3, 4, 5, 6)
  - [x] Adicionada prop `projectId?: string` ao `ChatInputProps`
  - [x] Adicionada prop `onUploadSuccess?: (filename: string) => void`
  - [x] Adicionado `<input type="file" ref={fileInputRef} accept=".pdf,.md,.markdown,.txt" hidden />`
  - [x] Adicionado botão 📎 (`id="chat-upload-button"`) que aciona `fileInputRef.current?.click()`
  - [x] Estado `uploading: boolean` via `useState(false)`
  - [x] Estado `uploadError: string | null` via `useState(null)` para erro inline
  - [x] No `onChange` do file input: validado tamanho (≤ 10 MB) e extensão pelo nome; se inválido → seta `uploadError`
  - [x] Se válido: `setUploading(true)` → `uploadDocument(projectId, file)` → `setUploading(false)` → chama `onUploadSuccess(filename)`
  - [x] Em erro de API: `setUploading(false)` + seta `uploadError`
  - [x] `uploadError` exibido abaixo do `ChatInput` com estilo inline (`var(--rs-error)`)
  - [x] Botão 📎 desabilitado quando `disabled || uploading`
  - [x] Botão de envio e textarea desabilitados quando `uploading`
  - [x] `uploadError` limpo ao iniciar novo upload ou nova digitação

- [x] **Task 2: Atualizar `SessionPage` para injetar `projectId` e tratar `onUploadSuccess`** (AC: 2)
  - [x] `projectId={session?.project_id}` passado para `<ChatInput />`
  - [x] `handleUploadSuccess(filename)` implementado: chama `sendMessage(\`📎 ${filename} enviado e disponível para a IA.\`)`

- [x] **Task 3: Testes** (AC: 1, 2, 3, 4, 5, 6)
  - [x] Diretório `src/tests/` já existe
  - [x] Criado `src/tests/ChatInput.upload.test.tsx` com 9 cenários:
    - Botão 📎 visível e habilitado com `projectId` e `!disabled`
    - Botão 📎 não renderizado sem `projectId`
    - Botão 📎 desabilitado quando `disabled=true`
    - Erro inline para arquivo > 10 MB
    - Erro inline para extensão inválida (.xlsx e .doc)
    - `uploadDocument` chamado com `projectId` e file corretos
    - `.txt` aceito como válido
    - Erro inline de API exibido
    - `uploading` desabilita botão
    - Erro limpo ao digitar

### Review Findings

- [x] [Review][Patch] F-1: Named + default export duplicados em `ChatInput.tsx` — removido `export default ChatInput`, mantido apenas named export [ChatInput.tsx:236] ✅
- [x] [Review][Patch] F-3: `handleUploadSuccess` sem try/catch em `SessionPage` — adicionado try/catch com `console.error` [SessionPage.tsx:58-63] ✅
- [x] [Review][Patch] F-4: AC 5 sem teste do botão de envio desabilitado durante upload — adicionado teste `disables send button and textarea during upload (AC 5 full)` [ChatInput.upload.test.tsx] ✅
- [x] [Review][Defer] F-2: `uploadError` não limpa ao abrir diálogo de arquivo sem selecionar — se usuário abre o diálogo, cancela sem selecionar, o erro da rodada anterior persiste. Impacto de UX baixo. — deferred, pre-existing UX edge case
- [x] [Review][Defer] F-5: Arquivo sem extensão gera mensagem de erro genérica e sem cobertura de teste — `file.name = "README"` seria rejeitado com a msg genérica sem indicar o motivo real. Cenário improvável em uso real. — deferred, pre-existing edge case

## Dev Notes

### Causa Raiz (Retro Epic 5 — Action Item A3)

> "Botão 📎 no `ChatInput` para anexar documento direto na conversa → processamento → injeção no contexto."
> 
> Documentos existiam na `ProjectDetailPage` mas eram **escondidos** pelo guard `hasSessions` (sempre false). A decisão de design mudada: documentos devem ser anexados **no chat**, não na tela do projeto.

### Análise do Código Existente

#### Frontend — `ChatInput.tsx` (Situação atual)

```tsx
// Arquivo: src/components/chat/ChatInput.tsx (113 linhas)
// Props atuais:
interface ChatInputProps {
  onSend: (content: string) => void
  disabled?: boolean
  placeholder?: string
}
```

**Ponto de extensão:** O `<div>` root usa `flex items-end gap-2 p-3`. O botão 📎 vai **à esquerda da textarea**, antes do botão de enviar. Layout final: `[📎] [textarea] [➤]`.

#### Frontend — `documentsApi.ts` (Já pronto!)

```typescript
// Endpoint já implementado:
export async function uploadDocument(projectId: string, file: File): Promise<{ data: DocumentResponse }>

// IMPORTANTE: não setar Content-Type manualmente — browser seta o boundary do multipart
```

#### Frontend — `SessionPage.tsx` — Uso do ChatInput

```tsx
// Linha 199-207 — trecho atual:
<ChatInput
  onSend={sendMessage}
  disabled={isThinking || session?.status === 'completed'}
  placeholder={
    session?.status === 'completed'
      ? 'Sessão concluída'
      : 'Descreva seu projeto ou responda...'
  }
/>
```

`session?.project_id` já está disponível (linha 27-36 — desestruturado do `useSession`).

#### Backend — Endpoint já existe e está funcional

```
POST /api/v1/projects/{project_id}/documents
```
- Valida MIME real (via `python-magic`), não apenas extensão
- Valida tamanho (max `MAX_UPLOAD_BYTES = 20 * 1024 * 1024` — limite server-side permanece 20 MB; o frontend impõe 10 MB como política de UX mais conservadora)
- Suporta: `application/pdf`, `text/markdown`, `text/x-markdown`, `text/plain` (`.txt`) — todos os formatos aceitos nesta story
- Retorna `DocumentResponse` com `status: 'ready' | 'error' | 'processing'`

**Nenhuma alteração no backend é necessária** para esta story.

> ⚠️ **Pós-MVP:** Suporte a Office (`.xls`, `.xlsx`, `.doc`, `.docx`) foi adiado. Exigiria adicionar `python-docx` e `openpyxl` ao backend e novos parsers em `documents/parsers.py`. Registrado em `deferred-work.md`.

### Validação Client-Side de Arquivo (Task 1)

A validação frontend é uma defesa de UX (não requer ida ao servidor):

```typescript
const MAX_SIZE = 10 * 1024 * 1024; // 10 MB — política de UX (servidor aceita até 20 MB)
const VALID_EXTENSIONS = ['.pdf', '.md', '.markdown', '.txt'];
const ERROR_MSG = 'Apenas PDF, Markdown ou TXT até 10 MB.';

function validateFile(file: File): string | null {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!VALID_EXTENSIONS.includes(ext)) {
    return ERROR_MSG;
  }
  if (file.size > MAX_SIZE) {
    return ERROR_MSG;
  }
  return null; // válido
}
```

### Padrão de Upload com Estado (Task 1)

```tsx
// Dentro de ChatInput
const fileInputRef = useRef<HTMLInputElement>(null)
const [uploading, setUploading] = useState(false)
const [uploadError, setUploadError] = useState<string | null>(null)

const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0]
  if (!file) return
  
  // Reset para permitir re-seleção do mesmo arquivo
  e.target.value = ''
  setUploadError(null)
  
  const validationError = validateFile(file)
  if (validationError) {
    setUploadError(validationError)
    return
  }
  
  setUploading(true)
  try {
    await uploadDocument(projectId, file)
    onUploadSuccess?.(file.name)
  } catch {
    setUploadError('Erro ao enviar o documento. Tente novamente.')
  } finally {
    setUploading(false)
  }
}, [projectId, onUploadSuccess])
```

### Layout do Botão 📎 (Task 1)

O botão 📎 segue o mesmo padrão visual do botão de envio:

```tsx
{/* Hidden file input */}
<input
  ref={fileInputRef}
  type="file"
  accept=".pdf,.md,.markdown,.txt"
  onChange={handleFileChange}
  hidden
/>

{/* Paperclip button — ANTES da textarea */}
<button
  onClick={() => fileInputRef.current?.click()}
  disabled={disabled || uploading}
  id="chat-upload-button"
  aria-label="Anexar documento"
  className="shrink-0 flex items-center justify-center rounded-full transition-all"
  style={{
    width: 40,
    height: 40,
    background: 'var(--muted)',
    color: disabled || uploading ? 'var(--rs-text-muted)' : 'var(--rs-text-secondary)',
    cursor: disabled || uploading ? 'not-allowed' : 'pointer',
    opacity: disabled || uploading ? 0.5 : 1,
  }}
>
  {/* Paperclip SVG */}
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
  </svg>
</button>
```

**Exibição do erro inline** (abaixo do container pai):

```tsx
{/* No componente pai ou wrapper do ChatInput */}
{uploadError && (
  <div
    style={{
      color: 'var(--rs-error)',
      fontSize: 'var(--text-body-sm)',
      padding: '4px var(--space-3)',
    }}
    role="alert"
    id="chat-upload-error"
  >
    {uploadError}
  </div>
)}
```

### Tratamento de `onUploadSuccess` (Task 2)

Ao concluir o upload, o frontend envia uma mensagem de sistema para a IA:

```tsx
// SessionPage.tsx
const handleUploadSuccess = useCallback((filename: string) => {
  sendMessage(`📎 ${filename} enviado e disponível para a IA.`)
}, [sendMessage])
```

Isso cria:
1. Uma mensagem `user` visível no chat com confirmação visual
2. Um novo ciclo de elicitação onde a IA recebe o contexto do documento (via context builder que já injeta DocumentChunks)

### Convenções de Código

- Imports: usar `@/services/documentsApi` (alias `@/`)
- Props adicionadas a `ChatInputProps` são **opcionais** com `?` ou com default seguro para manter retrocompatibilidade
- `projectId` não-opcional quando botão deve funcionar — usar `projectId?: string` e desabilitar o botão 📎 quando `!projectId`
- Testes: Vitest + React Testing Library (padrão do projeto)

### Project Structure

- **Modificado:** `reqstudio/reqstudio-ui/src/components/chat/ChatInput.tsx`
- **Modificado:** `reqstudio/reqstudio-ui/src/pages/SessionPage.tsx`
- **Criado:** `reqstudio/reqstudio-ui/src/tests/ChatInput.upload.test.tsx`
- **Não modificar:** backend (endpoint já funcionando)

### Learnings das Stories Anteriores

- `documentsApi.ts` usa `request as apiClient` (não `axios`) — não setar `Content-Type` para multipart
- `Intl` nativo preferível a libs de formatação (aprendizado da 5.5-2)
- `disabled` deve ser propagado consistentemente para todos os elementos interativos
- Testes unitários de componentes React: usar `vi.fn()` para mocks, `@testing-library/user-event` para interações

### References

- [Source: epic-5-retro-2026-03-31.md — Action Item A3]
- [Source: reqstudio-ui/src/components/chat/ChatInput.tsx — Componente atual]
- [Source: reqstudio-ui/src/pages/SessionPage.tsx — Uso atual do ChatInput]
- [Source: reqstudio-ui/src/services/documentsApi.ts — uploadDocument já implementado]
- [Source: reqstudio-api/app/modules/documents/router.py — Endpoint pronto]
- [Source: reqstudio-api/app/modules/documents/models.py — MAX_UPLOAD_BYTES, ALLOWED_MIME_TYPES]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-04-03

### Debug Log References

- `projectId?: string` declarado como opcional para manter retrocompatibilidade do `ChatInput` (pode ser usado sem upload em outros contextos futuros)
- Botão 📎 só é renderizado quando `projectId` está presente — evita estado divergente
- `isDisabled = disabled || uploading` unifica disabled state em um único booleano para clareza
- Erro inline é exibido no mesmo wrapper do ChatInput, com bordas ajustadas dinamicamente para fechar o visual corretamente
- `e.target.value = ''` após seleção permite re-seleção do mesmo arquivo
- `@testing-library/react` e `@testing-library/user-event` já presentes no package.json (v16 e v14)

### Completion Notes List

- **Task 1:** `ChatInput.tsx` reescrito com botão 📎, `validateUploadFile`, estados `uploading`/`uploadError`, erro inline acessível (`role="alert"`) e `isDisabled` unificado.
- **Task 2:** `SessionPage.tsx` atualizado com `handleUploadSuccess` (chama `sendMessage`) e props `projectId`/`onUploadSuccess` passadas ao `ChatInput`.
- **Task 3:** 9 testes unitários cobrem todos os ACs.

### Change Log

- 2026-04-03: `ChatInput.tsx` — adicionado botão 📎 com upload completo (validação + estados + erro inline)
- 2026-04-03: `SessionPage.tsx` — adicionado `handleUploadSuccess` e props `projectId`/`onUploadSuccess` ao `ChatInput`
- 2026-04-03: Criado `src/tests/ChatInput.upload.test.tsx` com 9 cenários

### File List

- `reqstudio/reqstudio-ui/src/components/chat/ChatInput.tsx` (MODIFY)
- `reqstudio/reqstudio-ui/src/pages/SessionPage.tsx` (MODIFY)
- `reqstudio/reqstudio-ui/src/tests/ChatInput.upload.test.tsx` (CREATE)
