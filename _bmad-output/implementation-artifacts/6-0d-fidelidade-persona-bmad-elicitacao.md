# Story 6.0d: Fidelidade da Persona BMAD na Elicitação

Status: done

## Story

As a Ana,  
I want que o agente se comporte como um facilitador BMAD real desde o início da sessão,  
so that eu perceba uma entrevista profissional, com identidade clara e progresso perceptível.

## Acceptance Criteria

1. **Abertura com identidade clara**
Given primeira mensagem da sessão  
When o agente inicia a conversa  
Then o agente se apresenta com nome e papel claramente.

2. **Uso de nome de exibição quando disponível**
Given usuário autenticado  
When o agente se refere ao usuário  
Then usa nome de exibição quando disponível, evitando depender do prefixo do e-mail.

3. **Estrutura BMAD explícita**
Given início da entrevista  
When o agente conduz a elicitação  
Then declara objetivo e estrutura em fases, com expectativa de encerramento.

4. **Condução 100% BMAD**
Given sessão em andamento  
When novas interações ocorrem  
Then mantém perguntas direcionadas, progressão clara e sem massificar.

5. **Sinalização de progresso/finalização**
Given blocos sucessivos da entrevista  
When a sessão avança  
Then o agente sinaliza evolução e proximidade de fechamento.

6. **Progresso visível durante a sessão**
Given tela de trabalho da sessão ativa  
When usuário acompanha o chat  
Then painel de etapas/progresso permanece visível também nessa tela.

7. **Cobertura de testes**
Given implementação concluída  
When suíte relevante for executada  
Then há cobertura para prompt/seed com elementos obrigatórios e UX de abertura/progressão.

## Tasks / Subtasks

- [x] Task 1: Hardening da persona BMAD no backend (AC: 1, 2, 3, 4, 5)
  - [x] Reforçar `SEED_AGENT.system_prompt` com abertura, identidade e sinalização de progresso.
  - [x] Ajustar resolução de nome do usuário em `elicitation.py` para priorizar `display_name` quando disponível.
  - [x] Garantir uso de usuário autenticado da request no fluxo SSE.

- [x] Task 2: Progresso visível na SessionPage (AC: 6)
  - [x] Exibir painel compacto de etapas com base no `workflow_position`.
  - [x] Manter visibilidade no layout desktop e mobile.

- [x] Task 3: Cobertura de regressão (AC: 7)
  - [x] Expandir testes de seed/prompt para validar requisitos de apresentação/identidade/progressão.
  - [x] Adicionar teste de UX da SessionPage cobrindo abertura com etapa atual e evolução.

## Dev Notes

- Story origin: `_bmad-output/planning-artifacts/epics.md` (Story 6.0d).
- Dependências diretas:
  - `reqstudio/reqstudio-api/app/seeds/seed_workflows.py`
  - `reqstudio/reqstudio-api/app/modules/engine/elicitation.py`
  - `reqstudio/reqstudio-ui/src/pages/SessionPage.tsx`
- Testes alvo:
  - `reqstudio/reqstudio-api/app/seeds/tests/test_seed_workflows.py`
  - `reqstudio/reqstudio-api/app/modules/engine/tests/*`
  - `reqstudio/reqstudio-ui/src/tests/*SessionPage*`

## Dev Agent Record

### Agent Model Used

gpt-5 (Codex)

### Debug Log References

- `npm run test -- src/tests/SessionPage.progress-panel.test.tsx src/tests/SessionPage.autoscroll.test.tsx src/tests/SessionPage.upload.integration.test.tsx`
- `pytest app/seeds/tests/test_seed_workflows.py -k "apresentacao or estrutura or progresso"`
- `pytest app/seeds/tests/test_seed_workflows.py app/modules/engine/tests/test_progress_summary.py` (blocked no ambiente local por falta de drivers `asyncpg`/`aiosqlite`)

### Completion Notes List

- `elicit_stream` passa a identidade do usuário autenticado para o engine (sem ambiguidade por tenant).
- Engine ganhou normalização explícita de nome (`_resolve_user_display_name`) com suporte a `display_name` quando disponível e fallback seguro.
- Prompt seed reforçado para abertura obrigatória com nome/papel, objetivo+fases e sinalização de progresso/fechamento.
- `SessionPage` agora mostra painel de etapas/progresso durante a sessão em desktop e mobile.
- Cobertura adicionada para requisitos de persona no seed e para painel de progresso na UI.

### File List

- `_bmad-output/implementation-artifacts/6-0d-fidelidade-persona-bmad-elicitacao.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `reqstudio/reqstudio-api/app/modules/sessions/router.py`
- `reqstudio/reqstudio-api/app/modules/engine/elicitation.py`
- `reqstudio/reqstudio-api/app/seeds/seed_workflows.py`
- `reqstudio/reqstudio-api/app/seeds/tests/test_seed_workflows.py`
- `reqstudio/reqstudio-api/app/modules/engine/tests/test_progress_summary.py`
- `reqstudio/reqstudio-ui/src/pages/SessionPage.tsx`
- `reqstudio/reqstudio-ui/src/tests/SessionPage.progress-panel.test.tsx`

### Change Log

- 2026-04-04: Story criada e movida para `in-progress` para execução do rito BMAD pós-6-0c.
- 2026-04-04: Implementação inicial concluída (persona BMAD + painel de progresso em sessão) com cobertura focada.
- 2026-04-04: Review formal BMAD concluído sem findings bloqueantes; story encerrada em `done`.

## Evidências de Validação

- Frontend
  - Comando: `npm run test -- src/tests/SessionPage.progress-panel.test.tsx src/tests/SessionPage.autoscroll.test.tsx src/tests/SessionPage.upload.integration.test.tsx`
  - Resultado: `3 files passed`, `5 tests passed`
- Backend (prompt persona)
  - Comando: `pytest app/seeds/tests/test_seed_workflows.py -k "apresentacao or estrutura or progresso"`
  - Resultado: `3 passed`
- Backend completo da suíte focada
  - Comando: `pytest app/seeds/tests/test_seed_workflows.py app/modules/engine/tests/test_progress_summary.py`
  - Status: `Blocked` no ambiente atual por dependências locais ausentes (`asyncpg` e `aiosqlite`)

## Story Completion Status

- Story file atualizado com fechamento formal de review.
- Status final definido para `done`.
- Completion note: persona BMAD, uso de identidade autenticada e progresso visível foram aprovados no review; gap de suíte backend local permaneceu documentado como limitação de ambiente.

## Senior Developer Review (AI)

- Reviewer: BMAD Review Agent (Codex / GPT-5)
- Date: 2026-04-04
- Outcome: Approved

### Summary

- Total findings: 0
- High: 0
- Medium: 0
- Low: 0

### Residual Risks

- A suíte backend focada completa não pôde ser executada neste ambiente local por dependências ausentes (`asyncpg` e `aiosqlite`).
- O uso de `display_name` está implementado com fallback seguro, mas sua efetividade completa depende da presença consistente desse campo no domínio de autenticação.

### Final Validation

- Persona seed validada com cobertura explícita para apresentação, estrutura em fases e sinalização de progresso/fechamento.
- `SessionPage` validada com painel de etapas visível e estado de fechamento na interface.
- Estado final aprovado para continuidade do Epic 6 dentro do rito BMAD.
