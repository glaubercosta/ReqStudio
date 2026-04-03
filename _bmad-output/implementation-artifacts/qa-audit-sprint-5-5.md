# QA Audit Report — Sprint 5.5 (Stories 5-5-1 a 5-5-4)
**Auditora:** Quinn (BMAD QA Engineer)  
**Data:** 2026-04-03  
**Escopo:** Auditoria de cobertura de testes das stories 5-5-1 a 5-5-4 para subsidiar os code reviews pendentes.

---

## Addendum — Fechamento Pós-CC (2026-04-03)

Após execução incremental do Correct Course:

- `QA-5-5-2-001` **Fechado**: `test_progress_summary.py` inclui teste assíncrono para `_update_progress_summary` validando chamada de DB via `scope` e atualização do `progress_summary`.
- `QA-5-5-2-002` **Fechado**: `useProjectSessions.test.ts` migrado para teste do hook real com `QueryClientProvider` e `sessionsApi.list` mockado.
- `QA-5-5-4-001` **Fechado**: `ChatInput.behavior.test.tsx` cobre comportamento base (`Enter`, `Shift+Enter`, trim, reset e disable quando vazio).
- `QA-5-5-4-002` **Fechado**: criado `SessionPage.upload.integration.test.tsx` cobrindo cadeia `SessionPage -> ChatInput -> sendMessage`.

**Evidência de execução (targeted tests):**
- `vitest run src/tests/useProjectSessions.test.ts src/tests/SessionPage.upload.integration.test.tsx`
- Resultado: `2 files passed`, `4 tests passed`.
- `vitest run src/tests/ChatInput.behavior.test.tsx src/tests/useProjectSessions.test.ts src/tests/SessionPage.upload.integration.test.tsx`
- Resultado: `3 files passed`, `8 tests passed`.

**Risco residual após CC:**
- `QA-5-5-1-001` permanece como observação de prioridade média para hardening adicional do seed `--force` (não bloqueia início de 6.1).


---

## Sumário Executivo

| Story | Status | Testes Criados | Gaps Identificados | Prioridade |
|---|---|---|---|---|
| 5-5-1 System Prompts | ✅ done | ✅ `test_seed_workflows.py` (estático + integração) | 🟡 1 gap médio | Médio |
| 5-5-2 Retomar Sessão | ✅ done | ✅ `useProjectSessions.test.ts` (3) + `test_progress_summary.py` (10) | ✅ gaps críticos fechados | Baixo |
| 5-5-3 Migration Startup | ✅ done | ✅ `test_migrations_startup.py` (7) | 🟢 Cobertura adequada | Baixo |
| 5-5-4 Upload ChatInput | ✅ done | ✅ `ChatInput.upload.test.tsx` (9) + `ChatInput.behavior.test.tsx` (4) + `SessionPage.upload.integration.test.tsx` (1) | ✅ gaps críticos fechados | Baixo |

---

## Story 5-5-1: System Prompts com Qualidade BMAD

### Testes existentes
- `app/seeds/tests/test_seed_workflows.py` — testes estáticos (sem DB) e de integração com SQLite in-memory
- Cobrem: tamanho do prompt (> 800 chars), keywords de técnicas, few-shot format, re-seed idempotente

### ⚠️ Gap Identificado — QA-5-5-1-001 [Prioridade: MÉDIO]

**Título:** Teste de integração do seed não verifica se o `Agent` antigo é deletado corretamente no `--force`

**Detalhe:** O re-seed com `--force` deleta e recria o agente. Os testes verificam que o seed funciona, mas não verificam explicitamente que registros órfãos de execuções anteriores são removidos (ex: dois agents com mesmo `name` após re-seed parcial). Esse cenário pode mascarar duplicatas silenciosas.

**Ação para code review:** Verificar no `seed_workflows.py` se a deleção usa `DELETE WHERE name = ?` antes do insert, e se os testes de integração verificam o `COUNT` de agents após `--force`.

---

## Story 5-5-2: Retomar Sessão na ProjectDetailPage

### Testes existentes
- `useProjectSessions.test.ts` — 7 testes da lógica de filtro (estáticos, sem QueryClient)
- `test_progress_summary.py` — 9 testes do `_compute_progress_summary`

### 🔴 Gap 1 — QA-5-5-2-001 [Prioridade: ALTO]

**Título:** `_update_progress_summary` não tem cobertura de testes

**Detalhe:** O arquivo `test_progress_summary.py` só testa `_compute_progress_summary` (função pura). A função `_update_progress_summary` — que efetivamente faz o `scope.db.execute` e o `commit` — não tem nenhum teste. É a função que causaria falha silenciosa em produção se o isolamento de tenant estiver errado ou se o `where_id` não encontrar o projeto.

**Ação para code review:** Confirmar se `_update_progress_summary` foi implementada e se há pelo menos 1 teste mockando `scope.db` para garantir que o update é feito com o `project_id` correto.

### 🔴 Gap 2 — QA-5-5-2-002 [Prioridade: ALTO]

**Título:** `useProjectSessions` testa lógica de filtro duplicada, não o hook real

**Detalhe:** Os testes em `useProjectSessions.test.ts` testam uma função `filterResumable` reimplementada dentro do arquivo de testes — não importam nem testam o hook real (`useProjectSessions`). Se a implementação do hook divergir da função duplicada, os testes passarão mesmo com bug.

**Ação para code review:** Verificar se o hook exporta `filterResumable` separadamente (testável isoladamente) ou se deve haver testes com `renderHook` + QueryClient mockado para fechar o gap.

---

## Story 5-5-3: Migration Automática no Startup

### Testes existentes
- `app/db/tests/test_migrations_startup.py` — 7 testes cobrindo: skip em TESTING, upgrade head, exit(1), no-exit em sucesso, revision=head, log CRITICAL, log INFO

### 🟢 Avaliação: Cobertura adequada

Todos os ACs têm cobertura direta. O uso de `importlib.reload` para isolar mudanças de `monkeypatch` é uma boa prática aplicada corretamente.

**Única observação menor:** O teste `test_skips_migrations_in_test_environment` seta tanto `setenv("TESTING", "true")` quanto `setattr(settings, "TESTING", True)` — dupla proteção necessária dado o comportamento do `pydantic-settings`. Correto, mas pode ser simplificado futuramente.

---

## Story 5-5-4: Upload de Documento no ChatInput

### Testes existentes
- `src/tests/ChatInput.upload.test.tsx` — 9 testes cobrindo todos os ACs da funcionalidade de upload

### 🔴 Gap 1 — QA-5-5-4-001 [Prioridade: ALTO]

**Título:** Comportamentos básicos do `ChatInput` sem cobertura de regressão

**Detalhe:** O componente foi reescrito (`ChatInput.tsx`) mas não havia testes pré-existentes para os comportamentos originais. Com o rewrite, os seguintes cenários ficaram sem cobertura:

- `Enter` dispara `onSend` com o texto correto
- `Shift+Enter` **não** dispara `onSend` (adiciona linha)
- Campo resetado após envio (`setValue('')`)
- Botão de envio desabilitado quando campo vazio
- `onSend` chamado com texto trimado (sem espaços nas bordas)

**Arquivo a criar:** `src/tests/ChatInput.behavior.test.tsx`

**Ação para code review:** Verificar se algum desses comportamentos foi alterado inadvertidamente no rewrite e criar a suite de regressão.

### 🟡 Gap 2 — QA-5-5-4-002 [Prioridade: MÉDIO]

**Título:** `handleUploadSuccess` em `SessionPage` não tem teste de integração a nível de componente

**Detalhe:** O `handleUploadSuccess` chama `sendMessage` com a string de confirmação. Esse fluxo (upload → mensagem automática para a IA) só foi testado via mock no nível do `ChatInput`, mas não existe teste que verifique que o `SessionPage` conecta corretamente `onUploadSuccess` ao `sendMessage`. Uma refatoração futura pode desconectar os dois silenciosamente.

**Ação para code review:** Avaliar se vale um teste de integração leve do `SessionPage` com `ChatInput` mockado para verificar o callback chain.

---

## Itens Documentados para Code Reviews

### Para o code review da 5-5-4 (imediato):
- `QA-5-5-4-001` — Criar `ChatInput.behavior.test.tsx` com regressão dos comportamentos básicos
- `QA-5-5-4-002` — Avaliar teste de integração `SessionPage ↔ ChatInput`

### Para code reviews retroativos ou próximo sprint:
- `QA-5-5-2-001` — Testar `_update_progress_summary` com mock de `scope.db`
- `QA-5-5-2-002` — Verificar se `filterResumable` é testada via hook real ou função exportada
- `QA-5-5-1-001` — Verificar deleção de orphans no re-seed `--force`

---

## Nota sobre Processo BMAD

O Claude Sonnet assumiu diretamente a implementação das stories sem ativar o skill `bmad-agent-dev` (Amelia). Do ponto de vista de QA, o impacto técnico foi limitado — a cobertura de testes está presente em todas as stories. O gap mais relevante (5-5-4-001) é estrutural, não resultado do desvio de processo.

**Recomendação:** Para a story 5-5-5 e Epic 6, seguir o ritual BMAD completo: `dev-story` → ativa Amelia → implementa conforme story file.

---

## Addendum — Hardening TESTING Env (2026-04-03)

### Mudança aplicada
- Removida flag manual `TESTING=true` de `reqstudio/.env`.
- Adicionado fallback estável no `reqstudio/docker-compose.yml` (service `api`):
  - `environment:`
  - `  TESTING: ${TESTING:-false}`

### Validação executada
1. `docker compose down` ✅
2. `docker compose up -d --build --force-recreate` ✅
3. `docker compose exec api python -c "from app.core.config import settings; print(settings.TESTING)"`  
   Resultado: `False` ✅
4. `curl.exe -i http://localhost:8082/health`  
   Resultado: `curl: (52) Empty reply from server` ⚠️
5. `curl.exe -i http://localhost:8082/docs`  
   Resultado: `curl: (52) Empty reply from server` ⚠️
6. `docker compose logs api --tail 200`  
   Resultado: startup sem `"Application startup complete"` e warning:
   `RuntimeWarning: coroutine 'run_async_migrations' was never awaited` ⚠️

### Validação de não regressão do modo debug/teste
- `docker compose run --rm -e TESTING=true api ...` com patch de `command.upgrade`:
  - `TESTING=True`
  - `upgrade_called=False` ✅ (skip migrations)
- `docker compose run --rm -e TESTING=false api ...` com patch de `command.upgrade`:
  - `TESTING=False`
  - `upgrade_called=True` ✅ (executa migrations)

### Conclusão QA
- Objetivo de hardening do env `TESTING` foi implementado com sucesso.
- Gate operacional de disponibilidade (`/health`, `/docs`, startup complete) permanece com falha no estado atual do código e requer correção específica no startup/lifespan.
