# Story 6.4: Exportação de Artefatos em Markdown e JSON

Status: done

## Story

As a Ana,  
I want exportar artefato em Markdown e JSON,  
so that eu leve o resultado para reuniões e pipelines (FR22, FR23).

## Acceptance Criteria

1. **Exportação Markdown com visão**
Given `GET /api/v1/artifacts/{id}/export?format=markdown&view=business|technical`  
When solicitado  
Then retorna arquivo `.md` para download com metadados de exportação.

2. **Exportação JSON canônica**
Given `GET /api/v1/artifacts/{id}/export?format=json`  
When solicitado  
Then retorna `.json` com `artifact_state` completo, sem envelope, compatível para prompt/pipeline.

3. **Contrato de performance e interoperabilidade**
Given artefatos de maior volume  
When exportação for executada  
Then o endpoint mantém comportamento estável para uso em Notion/Jira e integrações futuras (NFR20), com base de performance monitorável para evolução ao alvo NFR3.

## Tasks / Subtasks

- [x] Consolidar contrato de export backend (AC: 1,2)
  - [x] Validar parâmetros aceitos (`format`, `view`) e respostas de erro para inputs inválidos.
  - [x] Garantir consistência de headers (`Content-Type`, `Content-Disposition`) para download em browser.
  - [x] Confirmar conteúdo do markdown exportado com metadados de versão/visão/data.

- [x] Endurecer cobertura de testes de exportação (AC: 1,2)
  - [x] Cobrir cenários `business` e `technical` no markdown.
  - [x] Cobrir `json` sem envelope `ApiResponse`.
  - [x] Cobrir invalidação de parâmetros e regressões de contrato.

- [x] Registrar baseline de performance para evolução da 6.4 (AC: 3)
  - [x] Definir cenário de medição inicial de exportação para artefatos maiores.
  - [x] Documentar limites observados e próximos ajustes necessários para NFR3.

## Dev Notes

- Story origin: `_bmad-output/planning-artifacts/epics.md` (Story 6.4).
- Parte do contrato já foi construída em 6.2/6.2x; foco desta story é consolidar exportação como capability de produto.
- Manter isolamento multi-tenant e padrões de resposta conforme `project-context.md`.

### Project Structure Notes

- Backend alvo principal:
  - `reqstudio/reqstudio-api/app/modules/artifacts/router.py`
  - `reqstudio/reqstudio-api/app/modules/artifacts/service.py`
  - `reqstudio/reqstudio-api/tests/test_artifacts_export.py`

### References

- `_bmad-output/planning-artifacts/epics.md` (Story 6.4 ACs)
- `project-context.md`
- `reqstudio/reqstudio-api/app/modules/artifacts/*`

## Dev Agent Record

### Agent Model Used

gpt-5 (Codex)

### Debug Log References

- Kickoff BMAD equivalente executado: `create-story` -> `dev-story` para story `6-4`.
- Execução de validação backend:
  - `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; $env:DEBUG='false'; .venv/Scripts/python.exe -m pytest tests/test_artifacts_render.py tests/test_artifacts.py tests/test_artifacts_coverage.py tests/test_artifacts_export.py -q`
  - Resultado: `26 passed in 25.18s`.
- Baseline NFR3 (cenário sintético equivalente a 50 páginas):
  - `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; $env:DEBUG='false'; .venv/Scripts/python.exe -m pytest tests/test_artifacts_export.py::test_export_markdown_nfr3_baseline_50_pages_equivalent -q`
  - Resultado: `1 passed in 1.34s` com verificação de `X-Export-Duration-Ms <= 5000`.
- `bmad-code-review` executado com aprovação para `review`; observações tratadas:
  - sanitização de filename de exportação,
  - teste explícito de isolamento multi-tenant,
  - metadados de export alinhados com AC (`Project`, `Version`, `Coverage`).

### Completion Notes List

- Endpoint de exportação validado para `format=markdown|json` e `view=business|technical` com rejeição de parâmetros inválidos (`422`).
- Contrato de download endurecido com `Content-Type`, `Content-Disposition` e telemetria `X-Export-Duration-Ms` para baseline monitorável.
- Metadados do `.md` alinhados à epic com `Project`, `Artifact`, `Version`, `Coverage`, `View` e `Export Date`.
- Testes de exportação ampliados para visão técnica/negócio, invalidação de `view`/`format`, JSON sem envelope, filename sanitizado e isolamento multi-tenant.
- Baseline mínima de performance documentada para NFR3 com cenário equivalente a 50 páginas; exportação dentro do limite de 5s.
- Story concluída e movida para `done`.

### File List

- `_bmad-output/implementation-artifacts/6-4-exportacao-artefatos-markdown-json.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `reqstudio/reqstudio-api/app/modules/artifacts/router.py`
- `reqstudio/reqstudio-api/app/modules/artifacts/service.py`
- `reqstudio/reqstudio-api/tests/test_artifacts_export.py`

### Change Log

- 2026-04-07: Story criada e iniciada (`in-progress`) via fluxo BMAD equivalente.
- 2026-04-07: Contrato de export consolidado e testes reforçados; iniciada baseline de performance via header `X-Export-Duration-Ms`.
- 2026-04-07: `bmad-code-review` executado, observações incorporadas e story movida para `review`.
- 2026-04-07: Baseline NFR3 registrada e validada; story movida para `done`.
