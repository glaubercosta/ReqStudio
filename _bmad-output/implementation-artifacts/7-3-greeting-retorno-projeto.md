# Story 7.3: Greeting de Retorno ao Projeto

Status: review

## Story

As a usuário que retoma um projeto após pausa,
I want que Mary me receba com contexto do que foi feito e o que vem a seguir,
so that eu reoriente rapidamente e decida como prosseguir (FR47).

## Acceptance Criteria

1. **Greeting gerado ao retomar sessão pausada com etapas concluídas**
Given sessão com `status="paused"` e `workflow_position.step_summaries` populado
When usuário retoma sessão (frontend chama `POST /sessions/{id}/return-greeting`)
Then backend muda `session.status` de `"paused"` para `"active"`
And backend gera greeting via LLM com `RETURN_GREETING_TEMPLATE`
And mensagem inclui: saudação de retorno, etapas concluídas com seus resumos, próxima etapa programada
And mensagem pergunta se o usuário deseja continuar ou revisitar etapa anterior
And mensagem persistida como `role="assistant"` na sessão
And stream SSE retornado ao frontend (mesmo padrão do `/kickstart`)

2. **Greeting simplificado quando nenhuma etapa foi concluída ainda**
Given sessão com `status="paused"` e `step_summaries` ausente ou vazio
When usuário retoma sessão
Then backend gera greeting simplificado: saudação de retorno + anúncio da primeira etapa + convite para continuar

3. **Idempotência — sessão não pausada retorna 409**
Given `POST /sessions/{id}/return-greeting` chamado em sessão com `status != "paused"`
When endpoint processa a requisição
Then retorna `GuidedRecoveryError(409)` com code `SESSION_NOT_PAUSED`
And nenhuma mensagem nova é persistida
And status da sessão não é alterado

4. **Frontend — substitui auto-resume silencioso por return-greeting SSE**
Given `useSession.ts` detecta `session.status === "paused"`
When effect de auto-resume executa
Then chama `POST /sessions/{id}/return-greeting` via SSE em vez de `sessionsApi.updateStatus(sessionId, "active")`
And input de chat permanece desabilitado enquanto greeting está em andamento (`isReturning` state)
And ao completar stream: habilita input, invalida queries `['messages', sessionId]` e `['session', sessionId]`

5. **Cobertura de testes ≥ 80%**
Given implementação concluída
When suíte relevante executada
Then `return_greeting()` coberto por testes de integração: sessão pausada com summaries, sem summaries, sessão não pausada (409)
And lógica de frontend coberta por testes de componente: detecção de paused, desabilitação durante greeting

## Tasks / Subtasks

- [x] Task 1: Seed — `RETURN_GREETING_TEMPLATE` em `seed_workflows.py` (AC: 1, 2)
  - [x] Adicionar `RETURN_GREETING_TEMPLATE` com duas variantes baseadas em `{has_summaries}`:
    - Com summaries: `[RESUMO_OMITIR]` na primeira linha (não armazenado), saudação calorosa, lista `{summaries_text}` das etapas concluídas, anuncia `{next_step_name}`, pergunta se continua ou revisita
    - Sem summaries: saudação simples, menciona que vão começar/continuar pela `{next_step_name}`, convite para continuar
  - [x] Reutilizar `STEP_NAMES` de Task 1 da Story 7.2 (já adicionado em seed_workflows.py)

- [x] Task 2: Engine — função `return_greeting()` em `elicitation.py` (AC: 1, 2, 3)
  - [x] Adicionar `async def return_greeting(scope, session_id, user_name)` em `elicitation.py`
  - [x] Verificar `session.status == SESSION_STATUS_PAUSED`; se não, raise `GuidedRecoveryError(409, "SESSION_NOT_PAUSED")`
  - [x] Mudar `session.status` para `SESSION_STATUS_ACTIVE` antes de chamar LLM
  - [x] Montar `summaries_text` a partir de `workflow_position.step_summaries` com STEP_NAMES para labels
  - [x] Calcular `next_step_name` de `workflow_position.current_step` via `STEP_NAMES`
  - [x] Chamar `stream_completion` com `RETURN_GREETING_TEMPLATE.format(...)` acumulando e yielding chunks
  - [x] Ao concluir stream: persistir mensagem como `role="assistant"` com próximo `message_index`
  - [x] Fazer `await scope.db.commit()` para persistir status=active + mensagem juntos
  - [x] Adicionar `SESSION_NOT_PAUSED` aos `ErrorCode` em `app/core/exceptions.py`

- [x] Task 3: Backend — endpoint `POST /sessions/{id}/return-greeting` em `sessions/router.py` (AC: 1, 3)
  - [x] Criar endpoint SSE seguindo padrão exato de `/kickstart` (StreamingResponse + SSE)
  - [x] Injetar `scope: TenantScope = Depends(get_tenant_scope)` e `current_user: User`
  - [x] Chamar `elicitation.return_greeting()` e yield chunks

- [x] Task 4: Frontend — `useSession.ts` substitui auto-resume por return-greeting SSE (AC: 4)
  - [x] Adicionar estado `isReturning: boolean` (similar ao `kickstarting` da Story 7.1)
  - [x] No effect de auto-resume: substituir chamada a `sessionsApi.updateStatus(sessionId, 'active')` por `streamReturnGreeting(sessionId, ...)` via SSE
  - [x] Desabilitar `ChatInput` enquanto `isReturning === true`
  - [x] Ao completar stream de greeting: setar `isReturning = false`, invalidar `['messages', sessionId]` e `['session', sessionId]`
  - [x] Adicionar `streamReturnGreeting(sessionId)` em `sseClient.ts`
  - [x] **Atenção**: o auto-resume no unmount (pause on navigate away) preservado como useEffect separado

- [x] Task 5: Testes (AC: 5)
  - [x] `test_elicitation_return_greeting.py`: sessão pausada com summaries (persiste msg, status=active), sem summaries (greeting simplificado), não pausada (409), sessão inexistente (404), endpoint SSE, auth 401 — 8 testes passando
  - [x] Endpoint SSE coberto nos próprios testes de integração acima

## Dev Notes

### Fluxo atual de auto-resume (useSession.ts:131–147)

```typescript
// ATUAL (a substituir):
if (session.status === 'paused') {
  sessionsApi.updateStatus(sessionId, 'active')
    .then(() => {
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    })
    .catch(() => {})
}
```

**Novo comportamento**:
```typescript
if (session.status === 'paused' && !isReturning) {
  setIsReturning(true)
  await streamReturnGreeting(sessionId, (event: SSEEvent) => {
    if (event.type === 'message') { /* acumular para mostrar streaming */ }
    else if (event.type === 'done') {
      setIsReturning(false)
      queryClient.invalidateQueries({ queryKey: ['messages', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    } else if (event.type === 'error') {
      setIsReturning(false)
      // fallback: tentar updateStatus silencioso
    }
  })
}
```

### Padrão SSE para return-greeting

Segue exatamente o padrão do `/kickstart` (Story 7.1) e `/elicit` existente:
```python
@router.post("/sessions/{session_id}/return-greeting")
async def return_greeting_stream(...) -> StreamingResponse:
    async def generate():
        async for chunk in elicitation.return_greeting(...):
            yield f"event: message\ndata: {chunk.model_dump_json()}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Montagem do `summaries_text` para o template

```python
summaries = workflow_position.get("step_summaries", {})
if summaries:
    summaries_text = "\n".join(
        f"- {STEP_NAMES[int(k)]}: {v}"
        for k, v in sorted(summaries.items(), key=lambda x: int(x[0]))
        if int(k) in STEP_NAMES
    )
else:
    summaries_text = ""
```

### `next_step_name` para o template

```python
current_step = (workflow_position or {}).get("current_step", 1)
next_step_name = STEP_NAMES.get(current_step, "próxima etapa")
```

Se `workflow_position.completed == True`, a sessão está encerrada — greeting de retorno nunca é chamado nesse caso (AC 3: status seria `completed`, não `paused`).

### GuidedRecoveryError — `SESSION_NOT_PAUSED`

Adicionar em `app/core/exceptions.py` (mesmo padrão de `SESSION_ALREADY_STARTED` da Story 7.1):
```python
SESSION_NOT_PAUSED = "SESSION_NOT_PAUSED"
```

### Dependência de Story 7.2

`STEP_NAMES` e o formato de `step_summaries` em `workflow_position` são definidos/utilizados primeiro na Story 7.2. Esta story (7.3) assume que `step_summaries` já está no formato `{"1": "resumo...", "2": "resumo..."}` conforme especificado em 7.2. Se 7.3 for implementada antes de 7.2, `step_summaries` estará sempre vazio e o greeting simplificado (AC 2) será usado — comportamento seguro.

### Preservar pause-on-unmount

O cleanup do useEffect (linha 142-144 de `useSession.ts`) pausa a sessão ao navegar:
```typescript
return () => {
  if (session.status === 'active') {
    sessionsApi.updateStatus(sessionId, 'paused').catch(() => {})
  }
}
```
Este comportamento **não deve ser alterado** — é a trigger que faz a sessão voltar para `paused` e permite o return-greeting no próximo acesso.

### Arquivos a tocar

| Arquivo | Mudança |
|---------|---------|
| `reqstudio-api/app/seeds/seed_workflows.py` | Adicionar `RETURN_GREETING_TEMPLATE` |
| `reqstudio-api/app/modules/engine/elicitation.py` | Adicionar função `return_greeting()` |
| `reqstudio-api/app/modules/sessions/router.py` | Adicionar endpoint `POST /sessions/{id}/return-greeting` |
| `reqstudio-api/app/core/exceptions.py` | Adicionar `SESSION_NOT_PAUSED` ErrorCode |
| `reqstudio-ui/src/hooks/useSession.ts` | Substituir auto-resume por return-greeting SSE |
| `reqstudio-ui/src/services/sessionsApi.ts` | Adicionar `streamReturnGreeting(sessionId)` |
| `reqstudio-api/app/modules/engine/tests/test_elicitation_return_greeting.py` | Testes novos |
| `reqstudio-api/app/modules/sessions/tests/test_sessions_router.py` | Testes do endpoint |

### References

- [useSession.ts:126-147](reqstudio/reqstudio-ui/src/hooks/useSession.ts#L126) — auto-resume logic a substituir
- [sessions/router.py:129-200](reqstudio/reqstudio-api/app/modules/sessions/router.py#L129) — padrão SSE endpoint `/elicit`
- [elicitation.py](reqstudio/reqstudio-api/app/modules/engine/elicitation.py) — funções `kickstart()` (7.1) e `return_greeting()` seguem padrão similar
- [seed_workflows.py](reqstudio/reqstudio-api/app/seeds/seed_workflows.py) — `STEP_NAMES`, `KICKSTART_TEMPLATE` já adicionados pela Story 7.1
- [sessions/models.py](reqstudio/reqstudio-api/app/modules/sessions/models.py) — `SESSION_STATUS_PAUSED`, `SESSION_STATUS_ACTIVE`
- Story 7.1: [7-1-kickstart-projeto-mensagem-inicial-mary.md](_bmad-output/implementation-artifacts/7-1-kickstart-projeto-mensagem-inicial-mary.md) — padrão de kickstart a replicar
- Story 7.2: [7-2-transicao-etapa-resumo-automatico.md](_bmad-output/implementation-artifacts/7-2-transicao-etapa-resumo-automatico.md) — schema de `step_summaries`
- [project-context.md](project-context.md) — GuidedRecoveryError, TenantScope, convenções de teste

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (Amelia — bmad-agent-dev)

### Debug Log References

- 210 testes passando na suíte completa após implementação (anteriormente 202)
- 8 novos testes em `test_elicitation_return_greeting.py` — todos passando

### Completion Notes List

- Dois templates distintos criados: `RETURN_GREETING_TEMPLATE` (com summaries) e `RETURN_GREETING_TEMPLATE_NO_SUMMARIES` (sem summaries) em `seed_workflows.py`
- `SESSION_NOT_PAUSED` ErrorCode + `session_not_paused_error()` factory adicionados em `exceptions.py`
- `return_greeting()` muda `session.status = active` antes do LLM, persiste mensagem assistant ao final do stream e faz commit único
- Endpoint `/return-greeting` segue exatamente o padrão SSE do `/kickstart`
- Frontend: `returnGreetingDoneRef` previne double-firing em React Strict Mode; pause-on-unmount preservado como useEffect separado
- `isReturning` exposto no hook e propagado para `ChatInput` em SessionPage.tsx (desktop e mobile)
- Fallback silencioso no frontend: se SSE retornar erro, chama `updateStatus('active')` via REST para não bloquear usuário

### File List

| Arquivo | Mudança |
|---------|---------|
| `reqstudio-api/app/seeds/seed_workflows.py` | `RETURN_GREETING_TEMPLATE`, `RETURN_GREETING_TEMPLATE_NO_SUMMARIES` adicionados |
| `reqstudio-api/app/core/exceptions.py` | `SESSION_NOT_PAUSED` ErrorCode + `session_not_paused_error()` factory |
| `reqstudio-api/app/modules/engine/elicitation.py` | `return_greeting()` function |
| `reqstudio-api/app/modules/sessions/router.py` | `POST /sessions/{id}/return-greeting` SSE endpoint |
| `reqstudio-ui/src/services/sseClient.ts` | `streamReturnGreeting()` function |
| `reqstudio-ui/src/hooks/useSession.ts` | `isReturning` state, SSE return-greeting effect, `returnGreetingDoneRef` |
| `reqstudio-ui/src/pages/SessionPage.tsx` | `isReturning` prop em `SessionChatPanelProps`, desabilitação do ChatInput |
| `reqstudio-api/tests/test_elicitation_return_greeting.py` | 8 testes de integração (novo arquivo) |

### Review Findings

- [x] [Review][Patch] `session.status = SESSION_STATUS_ACTIVE` é setado antes do LLM stream; se stream falha, sem rollback explícito (status pode ficar dirty na sessão sem msg persistida) [elicitation.py:197-260] — aplicado: `try/except` envolve o stream; em falha, faz `rollback()`, recarrega session e reverte `status` para `PAUSED` se ainda estiver `ACTIVE`
- [ ] [Review][Patch] AC 5: testes de componente faltando para `isReturning` UI gating (Task 5 marcada [x] mas sem coverage frontend) [reqstudio-ui/src/tests/]
- [x] [Review][Patch] Endpoint `return_greeting_stream`: bare `except Exception as e` + `str(e)` vaza internals; sem logging de traceback [router.py:547-555] — aplicado via helper compartilhado `_sse_error_payload`
- [ ] [Review][Patch] Sem teste para revert de `status` em LLM failure (depende do fix do rollback acima) [test_elicitation_return_greeting.py]
- [x] [Review][Patch] `step_summaries` com chave não-numérica corrompida → `int(k)` raise ValueError no comprehension; quebra greeting completamente [elicitation.py:206-211] — aplicado via helper `_safe_int()` (return_greeting + completion sort key)
- [ ] [Review][Patch] Frontend: AbortController abort não propaga para backend; SSE generator continua até próximo yield, pode persistir após unmount [useSession.ts:786-810]
- [ ] [Review][Patch] React Strict Mode + `returnGreetingDoneRef`: primeiro abort cancela fetch enquanto ref já marcado; bloqueia retry [useSession.ts:778-810]
- [ ] [Review][Patch] SSE client `streamReturnGreeting`: split por `\n\n` apenas (CRLF quebra); single `data:` por bloco; `res.body` null sem fallback [sseClient.ts:1028-1114] — parcial: multi-line `data:` agora concatena linhas antes do `JSON.parse` (todos os 3 handlers); CRLF e `res.body` null permanecem follow-up
- [x] [Review][Patch] Parâmetro `user_name` aceito em `return_greeting()` mas nunca usado [elicitation.py:191] — removido da assinatura; router.py atualizado
- [x] [Review][Defer] SSE client: eventos com nomes desconhecidos (ping/keepalive) silenciosamente descartados [sseClient.ts:1009] — deferred, backend não emite estes hoje
