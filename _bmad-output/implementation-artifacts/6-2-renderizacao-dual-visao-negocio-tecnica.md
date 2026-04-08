# Story 6.2: Renderização Dual — Visão de Negócio e Técnica

Status: done

## Story

As a Ana,  
I want ver artefato em linguagem de negócio e em formato técnico,  
so that eu e o time técnico tenhamos acesso adequado (FR20).

## Acceptance Criteria

1. **Renderização de negócio**
Given `artifacts/renderers/markdown_renderer.py`  
When `render(artifact, view="business")`  
Then gera Markdown com linguagem de negócio e prosa clara.

2. **Renderização técnica**
Given `artifacts/renderers/markdown_renderer.py`  
When `render(artifact, view="technical")`  
Then gera Markdown técnico com Given/When/Then.

3. **Endpoint de render**
Given API de artifacts  
When `GET /api/v1/artifacts/{id}/render?view=business|technical`  
Then retorna envelope `ApiResponse` com o markdown da visão solicitada.

4. **Fonte única de verdade**
Given o artifact_state JSONB  
When renderizar visões diferentes  
Then ambas usam o mesmo `artifact_state` como source of truth.

5. **Sinalização de baixa cobertura**
Given seção com cobertura baixa  
When renderizada  
Then exibe aviso: `⚠️ Pendente de aprofundamento`.

## Tasks / Subtasks

- [x] Validar endpoint de render com `view` restrito a `business|technical`.
- [x] Ajustar mensagem de baixa cobertura para aderência textual ao AC.
- [x] Atualizar testes de render para refletir o aviso canônico.
- [x] Adicionar teste de erro para `view` inválida.

## Dev Notes

- Story origin: `_bmad-output/planning-artifacts/epics.md` (Story 6.2).
- Implementação incremental sobre o renderer já existente em `app/modules/artifacts/renderers/markdown.py`.
- Mantido contrato de resposta com `ApiResponse`.

## Dev Agent Record

### Agent Model Used

gpt-5 (Codex)

### Debug Log References

- Ajuste de validação do query param `view` em `router.py`.
- Ajuste da mensagem de baixa cobertura no renderer markdown.
- Ampliação de cobertura em `tests/test_artifacts_render.py` para `view` inválida.
- `pytest tests/test_artifacts_render.py tests/test_artifacts.py tests/test_artifacts_coverage.py tests/test_artifacts_export.py -q` → `13 passed`.

### File List

- `_bmad-output/implementation-artifacts/6-2-renderizacao-dual-visao-negocio-tecnica.md`
- `reqstudio/reqstudio-api/app/modules/artifacts/router.py`
- `reqstudio/reqstudio-api/app/modules/artifacts/renderers/markdown.py`
- `reqstudio/reqstudio-api/tests/test_artifacts_render.py`

### Change Log

- 2026-04-05: Story criada em implementation artifacts e iniciada (`in-progress`).
- 2026-04-05: Implementação incremental aplicada no endpoint e renderer com cobertura de testes ampliada.
- 2026-04-05: Story movida para `review` após validação da suíte de artifacts.
- 2026-04-07: Story movida para `done` após code review e saneamento no hardening 6.2x.
