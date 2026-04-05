# Story 6.0c: Hardening de UX do Chat e Confiabilidade de Sessão

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Ana,
I want que o chat tenha fluxo contínuo e que minha sessão seja estável durante uso normal,
so that eu consiga conduzir a elicitação sem fricção operacional e sem perda de contexto.

## Acceptance Criteria

1. **Autoscroll durante streaming**
Given SessionPage ativa com mensagens da IA em streaming  
When novas mensagens chegam  
Then a rolagem acompanha automaticamente a resposta até o final do streaming, sem exigir interação manual na barra lateral.
2. **Layout resiliente para mensagens longas**
Given mensagens longas do usuário  
When renderizadas com respostas da IA  
Then não sobrepõem blocos da IA (quebra/limite de altura adequado).
3. **Timeout de sessão por inatividade total**
Given sessão autenticada em andamento  
When o usuário permanecer ativo (digitando, enviando mensagens, navegando na sessão)  
Then a sessão não pode expirar por timeout.  
And a sessão só pode expirar após **30 minutos completos de inatividade total do usuário**.
4. **Recovery de expiração real**
Given expiração real de sessão/token  
When evento ocorre  
Then UX mostra mensagem guiada com ação de recuperação (relogin/retomar), sem saída brusca.
5. **Consistência do widget de custo/tokens**
Given renders consecutivos do SessionTelemetryWidget  
When custo/tokens são exibidos  
Then valor é estável e consistente (normalização de arredondamento/precisão).
6. **Cobertura de testes de regressão**
Given implementação concluída  
When suíte de testes frontend/backend relevante executa  
Then existem testes para autoscroll, layout mensagem longa, regra de timeout em 30 min de inatividade total, sessão expirada com recovery e consistência de custo.

## Tasks / Subtasks

- [x] Task 1: Corrigir fluxo de rolagem e rendering do chat (AC: 1, 2)
  - [x] Ajustar estratégia de autoscroll em [SessionPage.tsx](/c:/Users/Glauber/codes/ReqStudio/reqstudio/reqstudio-ui/src/pages/SessionPage.tsx) para acompanhar streaming sem forçar scroll quando usuário estiver lendo histórico.
  - [x] Garantir constraints visuais em [ChatMessage.tsx](/c:/Users/Glauber/codes/ReqStudio/reqstudio/reqstudio-ui/src/components/chat/ChatMessage.tsx) para conteúdo longo (wrap/overflow/altura).
  - [x] Validar comportamento em mobile tabbed e desktop split.

- [x] Task 2: Confiabilidade de sessão e UX de recuperação (AC: 3, 4)
  - [x] Implementar regra de expiração por inatividade total de 30 min, sem expiração durante atividade contínua.
  - [x] Ajustar tratamento de erros 401/expiração em [useSession.ts](/c:/Users/Glauber/codes/ReqStudio/reqstudio/reqstudio-ui/src/hooks/useSession.ts) e [sseClient.ts](/c:/Users/Glauber/codes/ReqStudio/reqstudio/reqstudio-ui/src/services/sseClient.ts) para mensagem guiada com ação clara.
  - [x] Alinhar texto e ação com padrão Guided Recovery (relogin/retomar), sem queda silenciosa.
  - [x] Verificar backend para manutenção de semântica de erro estruturado no SSE em [router.py](/c:/Users/Glauber/codes/ReqStudio/reqstudio/reqstudio-api/app/modules/sessions/router.py).
  - [x] Validar política de timeout no backend (auth/session) para garantir convergência com o requisito de 30 min de inatividade.

- [x] Task 3: Normalização de widget de telemetria (AC: 5)
  - [x] Padronizar regra de arredondamento/exibição em [SessionTelemetryWidget.tsx](/c:/Users/Glauber/codes/ReqStudio/reqstudio/reqstudio-ui/src/components/chat/SessionTelemetryWidget.tsx).
  - [x] Garantir consistência entre valor resumido e tooltip detalhada.

- [x] Task 4: Fechar cobertura de regressão (AC: 6)
  - [x] Criar/ajustar testes em [SessionTelemetryWidget.test.tsx](/c:/Users/Glauber/codes/ReqStudio/reqstudio/reqstudio-ui/src/tests/SessionTelemetryWidget.test.tsx).
  - [x] Adicionar cenário de recuperação de sessão expirada (frontend e, se necessário, backend em [test_sse.py](/c:/Users/Glauber/codes/ReqStudio/reqstudio/reqstudio-api/tests/test_sse.py) / [test_pause_resume.py](/c:/Users/Glauber/codes/ReqStudio/reqstudio/reqstudio-api/tests/test_pause_resume.py)).
  - [x] Adicionar teste explícito para timeout somente após 30 min de inatividade total.

### Review Follow-ups (AI)

- [x] [AI-Review][High] Garantir que rolagem do container de mensagens conte como atividade do usuário para timeout de inatividade de 30 min [reqstudio/reqstudio-ui/src/hooks/useSession.ts:167] e [reqstudio/reqstudio-ui/src/pages/SessionPage.tsx:159]
- [x] [AI-Review][Medium] Separar estado/mensagem de `SESSION_EXPIRED` vs `SESSION_INACTIVITY_TIMEOUT` para evitar recovery guiado incorreto após erro real de auth [reqstudio/reqstudio-ui/src/hooks/useSession.ts:247]
- [x] [AI-Review][Medium] Adicionar teste negativo de autoscroll validando que não chama `scrollIntoView` quando usuário está lendo histórico [reqstudio/reqstudio-ui/src/tests/SessionPage.autoscroll.test.tsx:70]

### Review Findings

- [x] [Review][Patch] Auto-resume reativa sessão expirada por inatividade [reqstudio/reqstudio-ui/src/hooks/useSession.ts:113]
- [x] [Review][Patch] `visibilitychange` reseta relógio e pode burlar timeout de 30 min [reqstudio/reqstudio-ui/src/hooks/useSession.ts:140]
- [x] [Review][Patch] Falha de refresh no SSE não dispara logout global (estado auth inconsistente) [reqstudio/reqstudio-ui/src/services/sseClient.ts:64]
- [x] [Review][Patch] Mensagem otimista pode ficar fantasma em erro pré-stream [reqstudio/reqstudio-ui/src/hooks/useSession.ts:181]
- [x] [Review][Patch] Cor hardcoded adicionada no banner de erro viola regra de tokens semânticos [reqstudio/reqstudio-ui/src/pages/SessionPage.tsx:214]
- [x] [Review][Patch] Cobertura de regressão não valida timers/listeners/navegação dos CTAs de recovery [reqstudio/reqstudio-ui/src/tests/useSession.timeout.test.ts:1]
- [x] [Review][Defer] Classes/coros hardcoded pré-existentes em componentes já existentes [reqstudio/reqstudio-ui/src/components/chat/SessionTelemetryWidget.tsx:61] — deferred, pre-existing

## Dev Notes

- Story origin e ACs definidos em Epic 6 no arquivo [epics.md](/c:/Users/Glauber/codes/ReqStudio/_bmad-output/planning-artifacts/epics.md).
- Gate de entrada 6.0/6.0b já concluído no status oficial; esta story existe para corrigir fricções observadas em uso real antes de 6.1.
- Os artefatos `6-0` e `6-0b` não foram encontrados como arquivos de story individuais no diretório de implementação; usar como fonte de contexto os documentos de CC/QA listados em References.

### Technical Requirements

- Manter contrato de API envelope `{ data: ... }` e tratamento de erro estruturado.
- Não introduzir hardcoded colors fora dos tokens semânticos existentes.
- Preservar fluxo de streaming SSE via `POST /api/v1/sessions/{id}/elicit`.
- Timeout funcional exigido: expiração apenas após 30 min de inatividade total do usuário.

### Architecture Compliance

- Frontend com TanStack Query para estado de servidor; mutações com invalidação adequada.
- Erros visíveis ao usuário devem seguir padrão Guided Recovery (mensagem + ajuda + ação).
- Session reliability deve preservar status/retomada conforme Story 5.8.
- Política de timeout deve refletir regra de negócio desta story (30 min inatividade total).
- Manter separação por camadas: page/hooks/components/services.

### Library / Framework Requirements

- Stack frontend vigente no projeto:
  - `react@19.2.4`
  - `@tanstack/react-query@5.95.2`
  - `vite@8.0.1`
  - `vitest@4.1.2`
- Stack backend vigente:
  - Python `>=3.11`
  - FastAPI + SQLAlchemy 2 async (sem alterações de versão nesta story)
- Esta story é de hardening: não inclui upgrade de dependências.

### File Structure Requirements

- Escopo primário de edição esperado:
  - `reqstudio/reqstudio-ui/src/pages/SessionPage.tsx`
  - `reqstudio/reqstudio-ui/src/components/chat/ChatMessage.tsx`
  - `reqstudio/reqstudio-ui/src/components/chat/SessionTelemetryWidget.tsx`
  - `reqstudio/reqstudio-ui/src/hooks/useSession.ts`
  - `reqstudio/reqstudio-ui/src/services/sseClient.ts`
  - `reqstudio/reqstudio-api/app/modules/sessions/*` (se timeout/recovery exigir ajuste de backend)
  - `reqstudio/reqstudio-api/app/modules/auth/*` (se política de expiração estiver centralizada em auth)
  - `reqstudio/reqstudio-ui/src/tests/*` (tests relevantes)
  - `reqstudio/reqstudio-api/tests/*` (somente se necessário para erro/recovery SSE)
- Evitar expansão de escopo sem necessidade funcional direta.

### Testing Requirements

- Frontend:
  - Cobrir autoscroll em streaming.
  - Cobrir layout de mensagem longa sem sobreposição.
  - Cobrir regra de não expirar durante atividade contínua.
  - Cobrir expiração apenas após 30 min de inatividade total.
  - Cobrir recovery de sessão expirada (mensagem + ação esperada).
  - Cobrir consistência de arredondamento no widget de custo.
- Backend (se alterado):
  - Cobrir emissão de erro SSE de expiração/indisponibilidade com formato esperado.
- Evidências de execução devem seguir rito de handoff terminal da 6.0b.

### Previous Story Intelligence

- Do QA Audit pós-CC:
  - Cadeia `SessionPage -> ChatInput -> sendMessage` já ganhou teste de integração base e não é ponto crítico desta story após validação manual.
  - `ChatInput.behavior` já protege regressão de Enter/Shift+Enter/trim.
- Do Correct Course:
  - Objetivo explícito desta story é remover fricção operacional antes de iniciar 6.1+ para reduzir retrabalho em artefatos.

### Git Intelligence Summary

- Commit recente `03ab2f7` indica fechamento de Epic 5.5 + hardening operacional.
- Commits anteriores reforçam que SessionPage/ChatInput e suíte de testes já receberam ajustes rápidos; risco atual é regressão por refinamentos incrementais.

### Latest Tech Information

- Não há necessidade de pesquisa externa para upgrade nesta story.
- Diretriz: usar APIs já adotadas no código atual (React 19, Query v5, Vitest 4) e consolidar consistência comportamental.

### Project Context Reference

- Regras mandatórias de `project-context.md` aplicáveis:
  - No hardcoded colors de Tailwind fora tokens semânticos.
  - TanStack Query para estado de servidor.
  - GuidedRecoveryError para erros visíveis.
  - Scope lock: manter lista planejada de arquivos e validar `git status` no fechamento.

### References

- [epics.md](/c:/Users/Glauber/codes/ReqStudio/_bmad-output/planning-artifacts/epics.md) (Epic 6, Story 6.0c)
- [prd.md](/c:/Users/Glauber/codes/ReqStudio/_bmad-output/planning-artifacts/prd.md) (FR15, FR20-FR25, NFR14, NFR15)
- [architecture.md](/c:/Users/Glauber/codes/ReqStudio/_bmad-output/planning-artifacts/architecture.md) (SSE, Guided Recovery, patterns de frontend)
- [ux-design-specification.md](/c:/Users/Glauber/codes/ReqStudio/_bmad-output/planning-artifacts/ux-design-specification.md) (progresso visível, anti-fricção, recuperação)
- [project-context.md](/c:/Users/Glauber/codes/ReqStudio/project-context.md) (regras mandatórias de implementação)
- [qa-audit-sprint-5-5.md](/c:/Users/Glauber/codes/ReqStudio/_bmad-output/implementation-artifacts/qa-audit-sprint-5-5.md) (gaps e fechamento pós-CC)
- [sprint-change-proposal-2026-04-03.md](/c:/Users/Glauber/codes/ReqStudio/_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-03.md) (inclusão de 6.0c/6.0d)
- [cc-execution-plan-2026-04-03.prompt.md](/c:/Users/Glauber/codes/ReqStudio/_bmad-output/implementation-artifacts/cc-execution-plan-2026-04-03.prompt.md) (critérios de saída do CC)

## Story Completion Status

- Story file criado com contexto completo para implementação.
- Status final definido para `done`.
- Completion note: follow-ups do review resolvidos, comportamento validado no browser e suíte focada aprovada.

## Dev Agent Record

### Agent Model Used

gpt-5 (Codex)

### Debug Log References

- `npm run test -- src/tests/useSession.timeout.test.ts src/tests/SessionPage.session-expired.test.tsx src/tests/SessionPage.autoscroll.test.tsx src/tests/ChatMessage.layout.test.tsx src/tests/SessionTelemetryWidget.test.tsx src/tests/SessionPage.upload.integration.test.tsx`

### Completion Notes List

- Implementado timeout de inatividade no frontend: expiração apenas após 30 min de inatividade total.
- Melhorado recovery de sessão expirada no `SessionPage` com ações explícitas (`Fazer login` / `Voltar aos projetos`).
- SSE client agora tenta refresh de token em 401 e reexecuta a chamada uma vez antes de falhar.
- Autoscroll do chat ajustado para não forçar leitura de histórico quando usuário não está no final da lista.
- Renderização de mensagens longas fortalecida com constraints de largura/altura e quebra de conteúdo.
- Widget de telemetria normalizado para reduzir oscilação de precisão.
- Cobertura de regressão ampliada para timers/listeners de inatividade, CTAs de recovery, autoscroll em streaming e layout de mensagem longa.
- Testes focados da story executados e aprovados (`6 files passed`, `17 tests passed`).
- Follow-ups do code review resolvidos: scroll do container conta como atividade, recovery preserva `SESSION_EXPIRED` e autoscroll não força leitura de histórico.
- Testes focados rerodados e aprovados após a retomada (`6 files passed`, `19 tests passed`).
- Auto-scroll da `SessionPage` agora usa o container visível da conversa e abre a sessão já posicionada na última mensagem, evitando cair na primeira interação.

### File List

- `_bmad-output/implementation-artifacts/6-0c-hardening-ux-chat-confiabilidade-sessao.md`
- `reqstudio/reqstudio-ui/src/hooks/useSession.ts`
- `reqstudio/reqstudio-ui/src/pages/SessionPage.tsx`
- `reqstudio/reqstudio-ui/src/services/sseClient.ts`
- `reqstudio/reqstudio-ui/src/services/apiClient.ts`
- `reqstudio/reqstudio-ui/src/components/chat/ChatMessage.tsx`
- `reqstudio/reqstudio-ui/src/components/chat/SessionTelemetryWidget.tsx`
- `reqstudio/reqstudio-ui/src/tests/useSession.timeout.test.ts`
- `reqstudio/reqstudio-ui/src/tests/SessionPage.session-expired.test.tsx`
- `reqstudio/reqstudio-ui/src/tests/SessionPage.autoscroll.test.tsx`
- `reqstudio/reqstudio-ui/src/tests/ChatMessage.layout.test.tsx`

### Change Log

- 2026-04-04: Fechado hardening de regressão do 6.0c com cobertura explícita para timeout de 30 min, recovery guiado, autoscroll em streaming, layout de mensagens longas e consistência do widget de telemetria.
- 2026-04-04: Code review adicionou follow-ups pendentes com severidade e referências de arquivo/linha para correção pelo Dev.
- 2026-04-04: Follow-ups do review foram resolvidos e validados com a suíte focada do `6-0c`.
- 2026-04-04: Correção adicional de browser valida o auto-scroll no container visível e o carregamento da sessão já no fim da conversa.
- 2026-04-04: Story encerrada em `done` após validação no browser e confirmação da suíte focada.

## Senior Developer Review (AI)

- Reviewer: Codex (GPT-5)
- Date: 2026-04-04
- Outcome: Approved after follow-up fixes

### Summary

- Total findings: 3
- High: 1
- Medium: 2
- Low: 0

### Action Items

- [x] [High] Timeout de inatividade deve considerar atividade de rolagem no container do chat (não apenas `window`) para cumprir AC3.
- [x] [Medium] Fluxo de erro não deve sobrescrever causa real de `SESSION_EXPIRED` com mensagem de inatividade de 30 minutos.
- [x] [Medium] Cobertura de autoscroll precisa cenário negativo (“não forçar scroll quando lendo histórico”).

### Final Validation

- Browser validation completed against the live UI: auto-scroll opens on the latest conversation state and no longer snaps to the first interaction.
- Focused frontend suite passed after the last adjustment.
