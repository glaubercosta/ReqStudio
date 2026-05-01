## Deferred from: sessão QQ quick-dev 2026-04-14 (decisão PM)

- [ ] [PM][Feature] Apresentação do agente e objetivos no início da sessão de elicitação — requer elicitação de requisitos antes de implementar.
- [ ] [PM][Feature] Tela de acompanhamento de status do projeto — nova rota/feature, requer elicitação de requisitos antes de implementar.

## Deferred from: code review of 5-5-1-system-prompts-bmad-quality.md (2026-04-02)

- [x] [Review][Defer] A deleção forçada de Agent poderá quebrar FK se for compartilhado no futuro [app/seeds/seed_workflows.py:200] — deferred, edge case futuro

## Deferred from: story 5-5-4-upload-documento-chatinput (2026-04-03)

- [ ] [Defer][Pós-MVP] Suporte a upload de arquivos Office (`.xls`, `.xlsx`, `.doc`, `.docx`) no ChatInput — requer: `ALLOWED_MIME_TYPES` expandido em `documents/models.py`, novos parsers em `documents/parsers.py` (dependências: `python-docx`, `openpyxl`), e atualização do `accept` no front. Decidido por Glauber: prioridade após Epic 6.

## Deferred from: code review of 5-5-4-upload-documento-chatinput.md (2026-04-03)

- [x] F-2: `uploadError` não limpa ao abrir diálogo de arquivo e cancelar sem seleção — corrigido: `setUploadError(null)` no early return de `handleFileChange`.
- [x] F-5: Arquivo sem extensão (ex: `README`) gera mensagem de erro genérica sem indicar motivo — corrigido: mensagens distintas para extensão inválida vs. tamanho excedido em `validateUploadFile`.


## Deferred from: code review of 5-5-5-telemetria-baseline-tokens-custo.md (2026-04-03)

- [x] [Review][Defer] Migration Race Condition in Multi-node [app/main.py:199] — deferred, pre-existing

## Deferred from: code review of 6-0c-hardening-ux-chat-confiabilidade-sessao.md (2026-04-03)

- [x] [Review][Defer] Classes/coros hardcoded pré-existentes em componentes já existentes [reqstudio/reqstudio-ui/src/components/chat/SessionTelemetryWidget.tsx:61] — deferred, pre-existing

## Deferred from: code review of Epic 7 stories 7.1/7.2/7.3 (2026-04-19)

- [ ] [Review][Patch-deferred] Race condition `kickstart`: dois requests concorrentes passam check `_next_message_index == 0` e gravam `message_index=0` duplicado — requer SELECT FOR UPDATE no Session ou unique constraint em (session_id, message_index) [elicitation.py:122-168] — adiado por exigir migration
- [ ] [Review][Patch-deferred] Frontend kickstart: AbortController não propaga para backend; SSE generator continua até próximo yield, pode persistir após unmount [useSession.ts:706-759, 786-810] — adiado por exigir integração `request.is_disconnected()` no FastAPI generator (mudança arquitetural)
- [x] [Review][Patch-deferred] React Strict Mode + ref pattern (`kickstartDoneRef`/`returnGreetingDoneRef`) — fechado em 2026-05-01: ref agora só é setado no handler de `done`; abort/erro deixa ref como `false`, permitindo re-fire na segunda mount do Strict Mode
- [x] [Review][Patch-deferred] AC 6 (7.1) e AC 5 (7.3): testes de componente para `isKickstarting`/`isReturning` UI gating — fechado em 2026-05-01 via `src/test/useSession.test.tsx`
- [x] [Review][Patch-deferred] Teste explícito de revert de `status` para `paused` em LLM failure no return_greeting — fechado em 2026-05-01: `test_return_greeting_llm_failure_reverts_status_to_paused`
- [x] [Review][Patch-deferred] SSE client: split por `\n\n` apenas (CRLF quebra) e `res.body` null sem fallback — fechado em 2026-05-01: helper `parseSseStream` usa `\r?\n\r?\n` / `\r?\n`; body null emite `NO_RESPONSE_BODY` error event
- [ ] [Review][Defer] Pause-on-unmount stale closure em `session.status` pode causar PATCH redundante [useSession.ts:811-824] — edge case de baixo impacto
- [ ] [Review][Defer] ChatInput disabled durante kickstart sem botão de cancelar; usuário sem saída em LLM hang [SessionPage.tsx:308-318] — melhoria UX
- [ ] [Review][Defer] Engine importa de `app.seeds.seed_workflows` (6 imports separados após ruff): cheiro arquitetural, mover templates para módulo `prompts` próprio [elicitation.py:75-96] — refatoração não-bloqueante
- [ ] [Review][Defer] Persona "Mary" hard-coded em 3 locais (`_load_agent_system_prompt` fallback + `_SEED_AGENT`); rename de agente quebraria silenciosamente — DRY pequeno
- [ ] [Review][Defer] `status_code=409` em `GuidedRecoveryError` é metadata morto para rotas SSE (sempre retornam 200 com event:error); clarificar contrato [exceptions.py:28-29] — contrato API
- [ ] [Review][Defer] SSE client: eventos com nomes desconhecidos (ping/keepalive) silenciosamente descartados [sseClient.ts:1009] — backend não emite estes hoje
- [ ] [Review][Defer] COMPLETION_TEMPLATE — LLM instruído a sintetizar 5 etapas mas recebe summaries 1..N-1; etapa N sem transcript no prompt [elicitation.py:440-460] — requer reavaliação com PM antes de decidir abordagem
