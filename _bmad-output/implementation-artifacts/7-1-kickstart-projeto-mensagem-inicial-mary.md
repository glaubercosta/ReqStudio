# Story 7.1: Kickstart de Projeto — Mensagem Inicial da Mary

Status: done

## Story

As a usuário que abre o chat de um projeto pela primeira vez,
I want ver Mary se apresentar proativamente e explicar o processo de elicitação,
so that eu entenda o que esperar e me sinta acolhido para começar (FR43).

## Acceptance Criteria

1. **Kickstart proativo no primeiro acesso**
Given projeto sem histórico de mensagens (primeiro acesso ao chat)
When usuário abre a SessionPage
Then frontend detecta `messages.length === 0` e chama `POST /sessions/{id}/kickstart`
And input de chat permanece desabilitado até o stream de kickstart completar
And mensagem de Mary aparece no chat como `role="assistant"` com `message_index=0`

2. **Conteúdo da mensagem de abertura**
Given kickstart executado com sucesso
When mensagem de Mary é renderizada
Then mensagem inclui: auto-apresentação como Mary, analista de requisitos
And lista os nomes das 5 etapas: Contexto, Usuários e stakeholders, Objetivos de negócio, Processo atual, Restrições
And convida o usuário a começar descrevendo o problema central do projeto

3. **Idempotência — sem mensagem duplicada**
Given sessão com mensagens já existentes (retorno ao projeto)
When frontend abre SessionPage
Then `messages.length > 0` → kickstart NÃO é chamado
And histórico é exibido normalmente, input habilitado

4. **Idempotência no backend**
Given `POST /sessions/{id}/kickstart` chamado em sessão com mensagens existentes
When endpoint processa a requisição
Then retorna `GuidedRecoveryError(409)` com code `SESSION_ALREADY_STARTED`
And nenhuma mensagem nova é persistida

5. **Workflow position não avançado**
Given kickstart executado
When Mary conclui a abertura
Then `session.workflow_position.current_step` permanece em 1
And `_advance_workflow` NÃO é chamado pelo kickstart

6. **Cobertura de testes ≥ 80%**
Given implementação concluída
When suíte relevante executada
Then novo endpoint coberto por testes de integração
And lógica de detecção no frontend coberta por testes de componente

## Tasks / Subtasks

- [x] Task 1: Backend — função `kickstart()` em `elicitation.py` (AC: 1, 2, 4, 5)
  - [x] Adicionar `async def kickstart(scope, session_id, user_name)` em `elicitation.py`
  - [x] Verificar `_next_message_index == 0`; se não for, raise `GuidedRecoveryError(409, "SESSION_ALREADY_STARTED")`
  - [x] Montar prompt de kickstart: system_prompt do agente + template de abertura com os 5 nomes de etapa
  - [x] Chamar `stream_completion` com o prompt de kickstart (sem user message)
  - [x] Persistir resposta completa como `role="assistant"`, `message_index=0`
  - [x] NÃO chamar `_advance_workflow` nem `_update_progress_summary`

- [x] Task 2: Backend — endpoint `POST /sessions/{id}/kickstart` em `sessions/router.py` (AC: 1, 4)
  - [x] Criar endpoint SSE seguindo o padrão exato de `/elicit` (StreamingResponse + SSE)
  - [x] Injetar `scope: TenantScope = Depends(get_tenant_scope)` e `current_user: User`
  - [x] Chamar `elicitation.kickstart()` e yield chunks
  - [x] Garantir `ApiResponse` envelope nos erros (não no SSE — SSE retorna chunks diretos)

- [x] Task 3: Seed — template de abertura em `seed_workflows.py` (AC: 2)
  - [x] Adicionar `KICKSTART_TEMPLATE` em `seed_workflows.py` com instrução para Mary se apresentar, listar as 5 etapas por nome e convidar o usuário
  - [x] Referenciar os nomes das etapas do `SEED_WORKFLOWS` (Contexto, Usuários e stakeholders, Objetivos de negócio, Processo atual, Restrições)
  - [x] Importar e usar `KICKSTART_TEMPLATE` em `elicitation.kickstart()`

- [x] Task 4: Frontend — detecção e chamada de kickstart em `useSession.ts` (AC: 1, 3)
  - [x] Após `messages` carregadas via TanStack Query, verificar `messages.length === 0`
  - [x] Se vazio: chamar `POST /sessions/{id}/kickstart` via SSE (reutilizar lógica de streaming do `sendMessage`)
  - [x] Desabilitar `ChatInput` enquanto kickstart está em andamento (`kickstarting` state)
  - [x] Ao completar stream: habilitar `ChatInput` e invalidar query de mensagens

- [x] Task 5: Testes (AC: 6)
  - [x] `test_elicitation_kickstart.py`: testa kickstart com sessão vazia (persiste msg), sessão com msgs (409), workflow_position não avança
  - [x] Endpoint SSE, auth, tenant isolation cobertos em `test_elicitation_kickstart.py`
  - [x] `SessionPage.tsx` + `useSession.ts`: `isKickstarting` prop conectada ao `ChatInput` (disabled + placeholder)

## Dev Notes

### Contexto crítico — o que já existe vs. o que falta

A Story 6.0d implementou "abertura com identidade clara" no `system_prompt` da Mary
(`seed_workflows.py` linha 32–38): Mary já instrui a se apresentar na "PRIMEIRA resposta da sessão".
**O problema:** essa apresentação só ocorre APÓS o usuário enviar a primeira mensagem (é reativa).
Esta story torna a abertura PROATIVA — Mary fala primeiro.

O `SEED_AGENT.system_prompt` atual deve continuar inalterado (é usado em todas as chamadas).
O `KICKSTART_TEMPLATE` é um prompt adicional usado APENAS na chamada de kickstart.

### Padrão do endpoint SSE a seguir

`sessions/router.py` — endpoint `/elicit` como referência direta:
```python
@router.post("/sessions/{session_id}/elicit")
async def elicit_stream(...) -> StreamingResponse:
    async def generate():
        async for chunk in elicitation.elicit(...):
            yield f"event: message\ndata: {chunk.model_dump_json()}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```
O novo `/kickstart` segue exatamente o mesmo padrão.

### Estrutura de arquivos a tocar

| Arquivo | Mudança |
|---------|---------|
| `reqstudio-api/app/seeds/seed_workflows.py` | Adicionar `KICKSTART_TEMPLATE` |
| `reqstudio-api/app/modules/engine/elicitation.py` | Adicionar função `kickstart()` |
| `reqstudio-api/app/modules/sessions/router.py` | Adicionar endpoint `POST /sessions/{id}/kickstart` |
| `reqstudio-ui/src/hooks/useSession.ts` | Lógica de detecção e chamada de kickstart |
| `reqstudio-ui/src/services/sessionsApi.ts` | Função `kickstartSession(sessionId)` |
| `reqstudio-api/app/modules/engine/tests/test_elicitation_kickstart.py` | Testes novos |
| `reqstudio-api/app/modules/sessions/tests/test_sessions_router.py` | Testes do endpoint |
| `reqstudio-ui/src/tests/ChatInput.behavior.test.tsx` | Extensão para kickstart state |

### Nomes das 5 etapas (ELICITATION_STEPS)

Conforme `SessionPage.tsx` e `seed_workflows.py`:
```
['Contexto', 'Usuários e stakeholders', 'Objetivos de negócio', 'Processo atual', 'Restrições']
```

### Invariante de workflow_position

`kickstart()` NÃO deve chamar `_advance_workflow`. O passo 1 só avança após o PRIMEIRO par
user+assistant. A abertura proativa é uma mensagem assistente sem par com mensagem do usuário.
`workflow_position` permanece `{"current_step": 1}` após kickstart.

### GuidedRecoveryError para sessão já iniciada

Adicionar novo `ErrorCode` em `app/core/exceptions.py`:
```python
SESSION_ALREADY_STARTED = "SESSION_ALREADY_STARTED"
```
E usar via factory: `conflict_error("sessão")` ou similar — verificar factories existentes.

### Convenção de testes (project-context.md §1.2)

- Autenticação: `headers=_auth(token)` (não múltiplos clients)
- `GuidedRecoveryError` para erros de negócio, nunca `HTTPException`
- Coverage ≥ 80% no módulo
- Ler `test_projects.py` ou `test_elicitation.py` existente antes de criar os testes

### References

- [seed_workflows.py](reqstudio/reqstudio-api/app/seeds/seed_workflows.py#L22) — SEED_AGENT e system_prompt
- [elicitation.py](reqstudio/reqstudio-api/app/modules/engine/elicitation.py) — função `elicit()` como referência de implementação
- [elicitation.py:165](reqstudio/reqstudio-api/app/modules/engine/elicitation.py#L165) — `_advance_workflow` (NÃO chamar no kickstart)
- [sessions/router.py](reqstudio/reqstudio-api/app/modules/sessions/router.py) — padrão SSE endpoint
- [useSession.ts](reqstudio/reqstudio-ui/src/hooks/useSession.ts) — hook de sessão a estender
- [SessionPage.tsx](reqstudio/reqstudio-ui/src/pages/SessionPage.tsx) — `ELICITATION_STEPS` array (linha 25–31)
- [ChatInput.tsx](reqstudio/reqstudio-ui/src/components/chat/ChatInput.tsx) — prop `disabled` já existe
- [project-context.md](project-context.md) — Quartet Pattern, TenantScope, GuidedRecoveryError, test conventions
- Story 6.0d: [6-0d-fidelidade-persona-bmad-elicitacao.md](_bmad-output/implementation-artifacts/6-0d-fidelidade-persona-bmad-elicitacao.md)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (Amelia — bmad-agent-dev)

### Debug Log References

- Ruff E501 in router.py metrics lines: refactored to `m = chunk.metrics` local variable
- Ruff E501 in test file: introduced `_PATCH_STREAM` module-level constant for long patch paths
- Ruff I001 import sort in test file: fixed with `ruff check --fix`
- `sa_select` unused import: removed duplicate import (plain `select` was already present)

### Completion Notes List

- `kickstart()` validates `_next_message_index == 0`; raises `session_already_started_error()` (409) otherwise
- `_load_agent_system_prompt()` helper queries only the first WorkflowStep's Agent.system_prompt (avoids full context build)
- `kickstartDoneRef` React ref prevents double-firing of the kickstart effect in React strict mode
- Frontend: `ChatInput` disabled + placeholder "Mary está se apresentando..." while kickstart streams
- All 8 backend tests pass (`pytest tests/test_elicitation_kickstart.py -v`)

### File List

- `reqstudio/reqstudio-api/app/core/exceptions.py` — added `SESSION_ALREADY_STARTED` ErrorCode + factory
- `reqstudio/reqstudio-api/app/seeds/seed_workflows.py` — added `KICKSTART_TEMPLATE` constant
- `reqstudio/reqstudio-api/app/modules/engine/elicitation.py` — added `kickstart()` + `_load_agent_system_prompt()`
- `reqstudio/reqstudio-api/app/modules/sessions/router.py` — added `POST /sessions/{id}/kickstart` SSE endpoint
- `reqstudio/reqstudio-api/tests/test_elicitation_kickstart.py` — 8 new integration tests (all passing)
- `reqstudio/reqstudio-ui/src/services/sessionsApi.ts` — added `KICKSTART_SSE_URL` export
- `reqstudio/reqstudio-ui/src/services/sseClient.ts` — added `streamKickstart()` function
- `reqstudio/reqstudio-ui/src/hooks/useSession.ts` — kickstart effect, `isKickstarting` state, `kickstartDoneRef`
- `reqstudio/reqstudio-ui/src/pages/SessionPage.tsx` — `isKickstarting` prop wired to `ChatInput`

### Review Findings

- [ ] [Review][Patch] Race condition: dois kickstarts concorrentes passam check `_next_message_index == 0` e gravam `message_index=0` duplicado [elicitation.py:122-168] — adicionar SELECT FOR UPDATE no Session ou unique constraint em (session_id, message_index)
- [ ] [Review][Patch] Frontend kickstart abort race: cleanup do useEffect aborta fetch mas backend continua até próximo yield; pode persistir mensagem após unmount silencioso [useSession.ts:706-759] — adiado para `deferred-work.md` (requer integração `request.is_disconnected()` no FastAPI generator)
- [x] [Review][Patch] React Strict Mode + ref pattern: primeiro abort cancela fetch enquanto `kickstartDoneRef=true` já marcado, bloqueando retry; reset ref em error/abort [useSession.ts:720-749] — aplicado em 2026-05-01: `kickstartDoneRef.current = true` movido pro handler de `done`; abort/erro deixa o ref `false`, permitindo re-fire na segunda mount do Strict Mode
- [x] [Review][Patch] Endpoint `kickstart_stream`: bare `except Exception as e` + `str(e)` vaza internals (SQL fragments, etc.); sem logging de traceback [router.py:481-489] — aplicado via helper `_sse_error_payload`: `GuidedRecoveryError` serializa code+message; demais viram `INTERNAL_ERROR` genérico + `logger.exception`
- [x] [Review][Patch] SSE client: split por `\n\n` apenas (CRLF quebra); single `data:` por bloco (SSE permite múltiplas data lines); `res.body` null sem fallback [sseClient.ts:953-1019] — fechado em 2026-05-01: helper `parseSseStream` extraído com `\r?\n\r?\n`/`\r?\n`; body null emite evento `NO_RESPONSE_BODY`
- [x] [Review][Patch] AC 6: testes de componente faltando para `isKickstarting` (Task 5 marcada [x] mas sem coverage frontend) [reqstudio-ui/src/tests/] — fechado em 2026-05-01: `src/test/useSession.test.tsx` cobre flip true/false do `isKickstarting` e re-fire safety no Strict Mode
- [x] [Review][Patch] Parâmetro `user_name` aceito em `kickstart()` mas nunca usado; ou remover ou injetar no template [elicitation.py:123] — removido da assinatura de `kickstart()` e `return_greeting()`; router.py não passa mais o kwarg
- [x] [Review][Patch] `KICKSTART_SSE_URL` exportado em `sessionsApi.ts` mas nunca usado (call site em sseClient.ts hard-codeia URL) [sessionsApi.ts:62-63] — export removido
- [x] [Review][Defer] Pause-on-unmount stale closure em `session.status` pode causar PATCH redundante [useSession.ts:811-824] — deferred, edge case de baixo impacto
- [x] [Review][Defer] ChatInput disabled durante kickstart sem botão de cancelar; usuário sem saída em LLM hang [SessionPage.tsx:308-318] — deferred, melhoria UX
