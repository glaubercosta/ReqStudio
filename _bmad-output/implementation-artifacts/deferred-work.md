## Deferred from: code review of 5-5-1-system-prompts-bmad-quality.md (2026-04-02)

- [x] [Review][Defer] A deleção forçada de Agent poderá quebrar FK se for compartilhado no futuro [app/seeds/seed_workflows.py:200] — deferred, edge case futuro

## Deferred from: story 5-5-4-upload-documento-chatinput (2026-04-03)

- [ ] [Defer][Pós-MVP] Suporte a upload de arquivos Office (`.xls`, `.xlsx`, `.doc`, `.docx`) no ChatInput — requer: `ALLOWED_MIME_TYPES` expandido em `documents/models.py`, novos parsers em `documents/parsers.py` (dependências: `python-docx`, `openpyxl`), e atualização do `accept` no front. Decidido por Glauber: prioridade após Epic 6.

## Deferred from: code review of 5-5-4-upload-documento-chatinput.md (2026-04-03)

- F-2: `uploadError` não limpa ao abrir diálogo de arquivo e cancelar sem seleção — impacto de UX baixo, edge case improvável em uso real.
- F-5: Arquivo sem extensão (ex: `README`) gera mensagem de erro genérica sem indicar motivo — cenário improvável, aceitável no MVP.


## Deferred from: code review of 5-5-5-telemetria-baseline-tokens-custo.md (2026-04-03)

- [x] [Review][Defer] Migration Race Condition in Multi-node [app/main.py:199] — deferred, pre-existing

## Deferred from: code review of 6-0c-hardening-ux-chat-confiabilidade-sessao.md (2026-04-03)

- [x] [Review][Defer] Classes/coros hardcoded pré-existentes em componentes já existentes [reqstudio/reqstudio-ui/src/components/chat/SessionTelemetryWidget.tsx:61] — deferred, pre-existing
