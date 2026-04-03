# Story 5.5-2: Retomar Sessão Existente na ProjectDetailPage

Status: done

## Story

As a Ana (especialista de domínio),
I want que ao acessar meu projeto o sistema detecte sessões em andamento e me ofereça continuar,
So that eu retome de onde parei sem criar uma sessão nova desnecessariamente (FR15, FR4).

## Acceptance Criteria

1. **Given** `/projects/{id}` com sessão `active` ou `paused` existente no banco  
   **When** `ProjectDetailPage` renderiza  
   **Then** `GET /api/v1/projects/{id}/sessions?status=active,paused` é chamado e retorna a sessão mais recente

2. **Given** a chamada lista ao menos uma sessão `active` ou `paused`  
   **When** `WelcomeScreen` renderiza  
   **Then** exibe `hasSessions = true` (botão "Continuar sessão →") com `session.updated_at` e `% cobertura` real da sessão, navegando para `/sessions/{session_id}` ao clicar

3. **Given** nenhuma sessão `active` ou `paused` existe para o projeto  
   **When** `ProjectDetailPage` renderiza  
   **Then** exibe `hasSessions = false` (botão "Iniciar elicitação →") que cria uma nova sessão via `POST /api/v1/projects/{id}/sessions`

4. **Given** o Elicitation Engine processa uma mensagem  
   **When** a resposta da IA é persistida (após chunk `done: true`)  
   **Then** `projects.progress_summary` é atualizado com os itens do checklist cobertos na sessão (contexto extraído do `artifact_state` ou contagem de steps)

5. **Given** re-seed com `--force` ou banco vazio  
   **When** `ProjectDetailPage` abre  
   **Then** comportamento de fallback funciona sem erros (lista vazia → "Iniciar elicitação")

## Tasks / Subtasks

- [x] **Task 1: Hook `useProjectSessions` no frontend** (AC: 1, 2, 3)
  - [x] Criar `src/hooks/useProjectSessions.ts` usando TanStack Query
  - [x] Query: `GET /api/v1/projects/{id}/sessions` (endpoint já existe, sem filtros server-side por status)
  - [x] Filtrar client-side: `items.filter(s => s.status === 'active' || s.status === 'paused')`
  - [x] Ordenar por `updated_at` desc e pegar o primeiro (sessão mais recente)
  - [x] `enabled: !!projectId`, `staleTime: 10_000`
  - [x] Exportar `resumableSessionsKey = (id: string) => ['sessions', id, 'resumable']`

- [x] **Task 2: Atualizar `ProjectDetailPage`** (AC: 2, 3)
  - [x] Importar e chamar `useProjectSessions(id)`
  - [x] Derivar `activeSession = resumableSessions[0] ?? null`
  - [x] Substituir a lógica atual de `hasSessions` (baseada em `progressPct > 0`) pela presença de `activeSession`
  - [x] Passar `activeSession` para `WelcomeScreen` como nova prop
  - [x] `handleStartSession`: se `activeSession` existir → `navigate('/sessions/${activeSession.id}')`, senão → criar nova sessão via `sessionsApi.create(id)`

- [x] **Task 3: Atualizar `WelcomeScreen`** (AC: 2, 4)
  - [x] Adicionada prop `activeSession: Session | null` ao componente
  - [x] No branch `hasSessions`: exibe `updated_at` formatado com `Intl.RelativeTimeFormat('pt-BR')` (sem dependência externa)
  - [x] Checklist de progresso mantido usando `project.progress_summary` (comportamento atual)
  - [x] Botão "Continuar sessão →" com `id="btn-continue-session"` mantido
  - [x] Branch sem sessões não alterado

- [x] **Task 4: Backend — filtro de status no `list_sessions`** (AC: 1, 3)
  - [x] Em `app/modules/sessions/router.py`: adicionado `status: list[str] | None = Query(default=None)`
  - [x] Em `app/modules/sessions/service.py` → `list_sessions()`: filtro `.where(Session.status.in_(status))` implementado
  - [x] Filtro server-side implementado (não ficou apenas como TODO)

- [x] **Task 5: Backend — atualizar `progress_summary` no Elicitation Engine** (AC: 4)
  - [x] Import ausente de `WorkflowStep` corrigido em `elicitation.py` (bug latente)
  - [x] Import de `Project` adicionado em `elicitation.py`
  - [x] `_compute_progress_summary()`: função pura step → checklist dict
  - [x] `_update_progress_summary()`: atualiza `project.progress_summary` pós cada ciclo usando `scope.where_id` (isolamento garantido)
  - [x] Chamada inserida no pipeline: após `_advance_workflow()`, antes de `commit()`

- [x] **Task 6: Testes** (AC: 1, 2, 3, 4)
  - [x] Testes unitários da lógica `filterResumable`: `useProjectSessions.test.ts` com 7 cenários
  - [x] Testes unitários de `_compute_progress_summary`: `test_progress_summary.py` com 9 cenários (steps 0–5, chaves, review sempre false)
  - [x] Testes cobrem: ativo, pausado, fallback sem sessão, ordenação, progress_summary atualizado

## Dev Notes

### Causa Raiz (Retro Epic 5 — Action Item A2)

O `handleStartSession` atual **sempre cria uma nova sessão**, sem checar se existe uma sessão `active` ou `paused`. O campo `hasSessions` é derivado de `progressPct > 0`, que por sua vez vem de `project.progress_summary` — um campo JSON no modelo `Project` que **não é atualizado automaticamente** pelo engine. Resultado: o usuário sempre vê "Vamos começar!" e perde o histórico de sessões anteriores.

### Análise do Código Existente

#### Frontend — `ProjectDetailPage.tsx`

**Fluxo atual (com bug):**
```tsx
// Linha 240 — hasSessions é baseado em progressPct do projeto (sempre 0 sem update)
const hasSessions = progressPct > 0  // ← Bug: não consulta sessões reais

// Linha 242-250 — handleStartSession SEMPRE cria nova sessão
const handleStartSession = async () => {
  const res = await sessionsApi.create(id)  // ← Bug: não verifica sessão existente
  navigate(`/sessions/${res.data.id}`)
}
```

**WelcomeScreen** (linha 91–212): já tem branch `hasSessions: true` com botão "Continuar sessão →" (`id="btn-continue-session"`) e display do checklist. A estrutura visual está pronta — só falta alimentá-la com dados reais.

#### Frontend — `sessionsApi.ts`

`sessionsApi.list(projectId)` já existe (linha 59-60), chama `GET /api/v1/projects/{projectId}/sessions`. **Não há filtro de status** na chamada atual — o filtro será client-side na Task 1.

#### Backend — Endpoint já existe

`GET /api/v1/projects/{project_id}/sessions` (router.py linha 44-56) retorna lista paginada de sessões. `Session.status` pode ser `active`, `paused` ou `completed` (models.py linha 20-23).

**`list_sessions` service** (service.py linha 84-125): filtra por `tenant_id` e `project_id`, ordena por `updated_at.desc()`. A Task 4 adiciona filtro opcional de status.

#### Backend — `progress_summary`

Campo `progress_summary: Mapped[dict[str, Any] | None]` no modelo `Project` (projects/models.py linha 40). Atualizado via PATCH normalmente, mas **não é atualizado pelo elicitation engine** — dev deve adicionar na Task 5.

**`session.workflow_position`** (sessions/models.py linha 49-51): JSON que armazena o estado atual do workflow. Verificar em `elicitation.py` como `_advance_workflow` atualiza este campo para extrair o step atual.

### Padrão de Hook a Seguir (referência: `useProject.ts`)

```typescript
// src/hooks/useProjectSessions.ts
import { useQuery } from '@tanstack/react-query'
import { sessionsApi, Session } from '@/services/sessionsApi'

export const resumableSessionsKey = (id: string) => ['sessions', id, 'resumable']

export function useProjectSessions(projectId: string) {
  return useQuery({
    queryKey: resumableSessionsKey(projectId),
    queryFn: async () => {
      const res = await sessionsApi.list(projectId)
      return (res.data.items ?? []).filter(
        (s: Session) => s.status === 'active' || s.status === 'paused'
      )
    },
    enabled: !!projectId,
    staleTime: 10_000,
  })
}
```

### Padrão de Filtragem Server-Side (Task 4 — opcional)

Se implementar o filtro server-side:

```python
# router.py — adicionar query param
@router.get("/projects/{project_id}/sessions", ...)
async def list_sessions(
    project_id: str,
    status: list[str] | None = Query(default=None),  # novo
    ...
):
    result = await service.list_sessions(scope, project_id=project_id, page=page, size=size, status=status)
```

```python
# service.py — aplicar filtro
async def list_sessions(
    scope: TenantScope,
    project_id: str,
    page: int = 1,
    size: int = 20,
    status: list[str] | None = None,  # novo
) -> SessionListResponse:
    stmt = scope.select(Session, Session.project_id == project_id)
    if status:
        stmt = stmt.where(Session.status.in_(status))
    ...
```

### Instrução de `progress_summary` (Task 5)

Mapeamento step → checklist simplificado (iteração 1 — pode ser refinado no Epic 6):

```python
def _compute_progress(workflow_position: dict | None) -> dict:
    """Deriva progress_summary a partir da posição no workflow."""
    step = (workflow_position or {}).get("step", 0)
    if isinstance(step, dict):  # formato pode variar
        step = step.get("position", 0)
    return {
        "context":      step >= 1,
        "stakeholders": step >= 2,
        "goals":        step >= 3,
        "flows":        step >= 4,
        "nfr":          step >= 5,
        "review":       False,  # sempre manual
    }
```

### Convenções de Código

- Imports em arquivos `.tsx`: usar `@/` aliases (ex: `@/hooks/useProjectSessions`)
- TanStack Query v5: `useQuery({ queryKey, queryFn, enabled, staleTime })` — sem `cacheTime`
- Tempo relativo: usar `Intl.RelativeTimeFormat` ou `date-fns/formatDistanceToNow` (verificar se `date-fns` está nas deps — ver package.json do UI)
- Backend: manter assinatura `async def ... scope: TenantScope` e importar modelos com caminho completo (`from app.modules.projects.models import Project`)
- Testes unitários do seed: padrão já estabelecido em `app/seeds/tests/` (Story 5.5-1)

### Project Structure

- **Frontend principal:** `reqstudio/reqstudio-ui/src/pages/ProjectDetailPage.tsx`
- **Novo hook:** `reqstudio/reqstudio-ui/src/hooks/useProjectSessions.ts`
- **Service (frontend):** `reqstudio/reqstudio-ui/src/services/sessionsApi.ts`
- **Backend router:** `reqstudio/reqstudio-api/app/modules/sessions/router.py`
- **Backend service:** `reqstudio/reqstudio-api/app/modules/sessions/service.py`
- **Engine:** `reqstudio/reqstudio-api/app/modules/engine/elicitation.py`
- **Testes frontend:** `reqstudio/reqstudio-ui/src/__tests__/` (verificar convenção existente)
- **Testes backend:** `reqstudio/reqstudio-api/app/modules/sessions/tests/`

### Learnings da Story 5.5-1

- Diretório de testes pode não existir — criar `__init__.py` se necessário
- `pyproject.toml` já inclui `testpaths = ["tests", "app"]` → novos testes são descobertos automaticamente
- Engine (`elicitation.py`) tem lógica de avanço de step em `_advance_workflow` — ler antes de modificar
- Para re-seed, verificar `seed_workflows.py` — padrão `logger.info()` (não `print()`)

### References

- [Source: sprint-change-proposal-2026-04-02.md — Story 5.5-2 spec completa]
- [Source: 5-5-1-system-prompts-bmad-quality.md — Previous story learnings]
- [Source: reqstudio-ui/src/pages/ProjectDetailPage.tsx — Código atual com bugs identificados]
- [Source: reqstudio-ui/src/services/sessionsApi.ts — API client existente]
- [Source: reqstudio-api/app/modules/sessions/router.py — Endpoint list_sessions]
- [Source: reqstudio-api/app/modules/sessions/service.py — Service layer]
- [Source: reqstudio-api/app/modules/sessions/models.py — Session.status constants]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-04-02

### Debug Log References

- `WorkflowStep` não estava importado em `elicitation.py` — seria runtime error ao tentar avançar workflow apos o 1o ciclo. Corrigido juntamente com a Task 5.
- `date-fns` não está nas deps do UI — usado `Intl.RelativeTimeFormat` nativo.
- Diretório `app/modules/engine/tests/` não existia — criado com `__init__.py`.

### Completion Notes List

- **Task 1:** Hook `useProjectSessions` criado com query TanStack Query v5, filtro client-side `active|paused`, ordenação por `updated_at` desc.
- **Task 2:** `ProjectDetailPage` corrigido: `hasSessions` agora reflect sessions reais (não mais `progressPct > 0`). `handleStartSession` redireciona para sessão existente ou cria nova.
- **Task 3:** `WelcomeScreen` recebe `activeSession` como prop. Tempo relativo exibido com `Intl.RelativeTimeFormat('pt-BR')` nativo (sem dep externa).
- **Task 4:** Filtro server-side implementado em router e service (não ficou opcional — adicionado completamente).
- **Task 5:** Bug latente corrigido — `WorkflowStep` não tinha import em `elicitation.py`. Adicionado `_compute_progress_summary` (função pura) e `_update_progress_summary` (com isolamento via `scope.where_id`). Pipeline atualizado.
- **Task 6:** `useProjectSessions.test.ts` (7 cenários, unitários, sem QueryClient). `test_progress_summary.py` (9 cenários, unitários puros). Dir `app/modules/engine/tests/` criado com `__init__.py`.

### Change Log

- 2026-04-02: Criado `useProjectSessions.ts` com filtro client-side de sessões retomáveis
- 2026-04-02: `ProjectDetailPage.tsx` corrigido — `hasSessions` agora baseado em sessões reais
- 2026-04-02: `WelcomeScreen` atualizado com prop `activeSession` e tempo relativo
- 2026-04-02: `list_sessions` (router + service) recebe filtro opcional de status
- 2026-04-02: `elicitation.py` corrigido (import `WorkflowStep` ausente), adicionado `_compute_progress_summary` e `_update_progress_summary`
- 2026-04-02: Criados testes: `useProjectSessions.test.ts` (7 cenários) e `test_progress_summary.py` (9 cenários)

### File List

- `reqstudio/reqstudio-ui/src/hooks/useProjectSessions.ts` (CREATE)
- `reqstudio/reqstudio-ui/src/pages/ProjectDetailPage.tsx` (MODIFY)
- `reqstudio/reqstudio-ui/src/tests/useProjectSessions.test.ts` (CREATE)
- `reqstudio/reqstudio-api/app/modules/sessions/router.py` (MODIFY)
- `reqstudio/reqstudio-api/app/modules/sessions/service.py` (MODIFY)
- `reqstudio/reqstudio-api/app/modules/engine/elicitation.py` (MODIFY)
- `reqstudio/reqstudio-api/app/modules/engine/tests/__init__.py` (CREATE)
- `reqstudio/reqstudio-api/app/modules/engine/tests/test_progress_summary.py` (CREATE)
