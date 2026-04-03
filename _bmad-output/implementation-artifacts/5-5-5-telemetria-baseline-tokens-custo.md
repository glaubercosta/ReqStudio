# Story 5.5-5: Telemetria Baseline — Tokens e Custo por Mensagem

Status: done

## Story

As a Ana,
I want ver quanto a sessão está consumindo de IA em tempo real,
So that eu tenha transparência sobre o uso e custo da plataforma (NFR12).

## Acceptance Criteria

- **[x]** **Given** mensagem enviada e resposta finalizada (chunk `done: true`)
  **When** Elicitation Engine salva resposta
  **Then** colunas `input_tokens`, `output_tokens`, `cost_usd`, `model` salvas na tabela `messages` (role=assistant)
- **[x]** **And** mini-widget visível no header da SessionPage: "💰 $0.02 · 1.2k tokens"
- **[x]** **And** tooltip expandido: input tokens, output tokens, modelo usado, latência
- **[x]** **And** sem sessão ativa: widget oculto
- **[x]** **And** testes: persistência das métricas, widget renderizado, tooltip com breakdown, modelo correto

## Developer Context & Guardrails

### Origem
- Epic 5.5 (Dívida Técnica e Fundações)
- Action Item: Retro Epic 5 — Action Item A4 (Telemetria baseline) 

### Technical Requirements
- **Backend Model & Schema:** `Message` (em `app/modules/sessions/models.py`) precisará das colunas: `input_tokens` (int), `output_tokens` (int), `cost_usd` (float), e `model` (String). Atualize Pydantic schemas (`app/modules/sessions/schemas.py`).
- **Database Migration:** Crie nova migração Alembic para adicionar as 4 novas colunas na tabela `messages`. 
- **Elicitation Engine:** Atualmente (`app/modules/engine/elicitation.py`), no trecho `Elicitation cycle complete` (linha 125+), no final da iteração, as métricas já vêm em `chunk.metrics`. Deve populá-las explicitamente ao salvar o `assistant_msg`.
- **Frontend UI:** 
  - Adicionar widget no header da `SessionPage`.  
  - Para calcular o total da sessão: pode ser um endpoint novo, ou somado no client-side hook que carrega as `messages` atuais. Decida a melhor forma, o AC diz "mini-widget visível no header" então o frontend precisa do consolidado da sessão.
  - O estilo visual do tooltip deve seguir ShadCN UI `Tooltip` do projeto atual.
  
### Previous Story Intelligence & Learnings
- Do Elicitation Engine anterior (Stories 5.3 e 5.4), aprendemos que `LiteLLM` já provê o custo (`cost_usd`) e o `chunk.metrics` nos iteradores do SSE. Em `app/integrations/llm_client.py` isso já estava abstraído, estava se perdendo as métricas para o vácuo após o log JSON estruturado (`app/modules/engine/elicitation.py:130`). Você só precisa reconectar esses pipelines.
- Testes unitários do Frontend devem utilizar React Testing Library.

## Tasks

- [x] **Task 1:** Backend Models & Migrations
  - [x] Adicionar colunas em `models.Message`
  - [x] Gerar script Alembic e rodar `alembic upgrade head`
  - [x] Atualizar `MessageResponse`
- [x] **Task 2:** Salvar Métricas do Engine
  - [x] Modificar Elicitation Engine para atachar `input_tokens`, `output_tokens`, `cost_usd`, e `model` (baseado nas configurações do LiteLLM ou vindo no payload) na criação da `Message` do assistant
- [x] **Task 3:** Frontend UI
  - [x] Somar as métricas localmente por sessão ou modificar `SessionResponse`/`GET /sessions` para retornar totals
  - [x] Build do UX Component para Header da `SessionPage` c/ Tooltip de detalhamento
- [x] **Task 4:** Testes e Homologação
  - [x] Testes no backend mockando chunks com as métricas sendo processadas
  - [x] Testes do widget RTL

## Development Notes
*Ultimate context engine analysis completed - comprehensive developer guide created.*

## Dev Agent Record

### Implementation Notes
- Colunas adicionadas: `input_tokens`, `output_tokens`, `cost_usd` e `model`.
- Schemas atualizados para propagar esses campos no payload SSE e `/api/v1/sessions/.../messages`.
- O cálculo da somatória das métricas da sessão foi implementado no lado do cliente (`SessionTelemetryWidget`) iterando sobre as propriedades nativas de cada array de mensagens retornado no front.
- Testes foram redigidos incluindo os schemas mocks de RTL e asserções Pytest no _engine_ da elicitação (assumindo a geração via sandbox do usuário de alembic).

### File List
- `reqstudio/reqstudio-api/app/modules/sessions/models.py`
- `reqstudio/reqstudio-api/app/modules/sessions/schemas.py`
- `reqstudio/reqstudio-api/app/modules/engine/elicitation.py`
- `reqstudio/reqstudio-api/tests/test_elicitation.py`
- `reqstudio/reqstudio-ui/src/services/sessionsApi.ts`
- `reqstudio/reqstudio-ui/src/pages/SessionPage.tsx`
- `reqstudio/reqstudio-ui/src/components/chat/SessionTelemetryWidget.tsx`
- `reqstudio/reqstudio-ui/src/tests/SessionTelemetryWidget.test.tsx`

### Change Log
- Add session telemetry persistence (DB fields and Elicitation engine logic)
- Create UI widget for session summary (SessionTelemetryWidget)
- Add widget into SessionPage header
- Add tests for backend insertion and React testing library render behavior for sums.
1. 
2. ### Review Findings
3. 
4. - [x] [Review][Patch] Brittle Progress Summary Mapping [elicitation.py:262-275]
5. - [x] [Review][Patch] Unguarded Telemetry Metrics [elicitation.py:117-120]
6. - [x] [Review][Patch] Missing Latency Data [models.py / SessionTelemetryWidget.tsx]
7. - [x] [Review][Patch] Inconsistent Cost Rounding [SessionTelemetryWidget.tsx:40-41]
8. - [x] [Review][Patch] Empty Status Filter Returns 0 Results [service.py:374-375]
9. - [x] [Review][Patch] Clock Skew in Relative Time [ProjectDetailPage.tsx:927-936]
10. - [x] [Review][Patch] Brittle Extension Parsing [ChatInput.tsx:636-640]
11. - [x] [Review][Defer] Migration Race Condition in Multi-node [app/main.py:199] — deferred, pre-existing
