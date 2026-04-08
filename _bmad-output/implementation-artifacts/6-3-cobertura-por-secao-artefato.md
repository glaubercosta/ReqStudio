# Story 6.3: Cobertura por Seção do Artefato

Status: done

## Story

As a Ana,  
I want ver quais seções foram bem exploradas e quais precisam mais,  
so that eu saiba onde investir tempo (FR25).

## Acceptance Criteria

1. **Cálculo de cobertura por seção**
Given `artifacts/service.py`  
When `calculate_coverage(artifact_id)` for chamado  
Then retorna cobertura por seção (0.0-1.0) baseada em interações e validações.

2. **Cobertura global para UI**
Given artefato com múltiplas seções  
When endpoint de cobertura for consultado  
Then retorna `total_coverage` coerente com o estado atual do artefato.

3. **Mapeamento para estados visuais (UX-DR4 / UX-DR3)**
Given cobertura calculada  
When consumida pela UI  
Then permite mapear regras: `<30%` muted, `30-70%` âmbar, `>70%` success  
And suporta estados por seção/card: complete, active ("Ao vivo"), pending.

## Tasks / Subtasks

- [x] Implementar cálculo e atualização de cobertura por seção no módulo de artifacts (AC: 1,2)
  - [x] Revisar contrato atual de `get_artifact_coverage` e ajustar para refletir cálculo por seção de forma determinística.
  - [x] Garantir consistência entre `artifact_state.metadata.total_coverage` e retorno do endpoint de cobertura.
  - [x] Validar edge cases: artefato sem seções, cobertura mínima/máxima e conteúdo parcial.

- [x] Expandir testes backend para cobertura por seção e total (AC: 1,2)
  - [x] Adicionar cenários com coberturas heterogêneas entre seções.
  - [x] Validar limites de faixa (`<0.3`, `0.3-0.7`, `>0.7`) para suportar mapeamento visual.
  - [x] Garantir não regressão de isolamento multi-tenant no endpoint de cobertura.

- [x] Preparar integração para consumo de estados visuais no frontend (AC: 3)
  - [x] Confirmar shape de payload suficiente para `CoverageBar` e `ArtifactCard`.
  - [x] Registrar regra de mapeamento visual no artefato da story para implementação de UI (6.5/ajustes correlatos).

## Dev Notes

- Story origin: `_bmad-output/planning-artifacts/epics.md` (Story 6.3).
- Esta story inicia após fechamento formal de `6.2` e `6.2x`, reutilizando o mesmo `artifact_state` como fonte única de verdade.
- Seguir `project-context.md` para isolamento de tenant, contrato `ApiResponse` e convenções de teste.

### Project Structure Notes

- Backend alvo principal:
  - `reqstudio/reqstudio-api/app/modules/artifacts/service.py`
  - `reqstudio/reqstudio-api/app/modules/artifacts/router.py` (se necessário ajuste de contrato)
  - `reqstudio/reqstudio-api/tests/test_artifacts_coverage.py`
- Frontend: apenas preparação/contrato nesta etapa (sem alteração estrutural ampla).

### References

- `_bmad-output/planning-artifacts/epics.md` (Story 6.3 ACs)
- `project-context.md` (regras arquiteturais e testes)
- `reqstudio/reqstudio-api/app/modules/artifacts/*`

## Dev Agent Record

### Agent Model Used

gpt-5 (Codex)

### Debug Log References

- Kickoff BMAD equivalente executado: `create-story` -> `dev-story` para story `6-3`.
- Execução de validação backend:
  - `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; $env:DEBUG='false'; .venv/Scripts/python.exe -m pytest tests/test_artifacts_render.py tests/test_artifacts.py tests/test_artifacts_coverage.py tests/test_artifacts_export.py -q`
  - Resultado: `21 passed in 27.51s`.
- Code review BMAD concluído sem findings bloqueantes; aprovação para fechamento da story.

### Completion Notes List

- Cálculo de cobertura por seção consolidado em snapshot determinístico (`low|medium|high` + `pending|active|complete`).
- Endpoint de cobertura passou a recalcular `total_coverage` a partir das seções, eliminando dependência de metadado inconsistente.
- `ArtifactSectionCoverage` expandido com campos de suporte de UI: `coverage_band` e `card_state`.
- Testes de cobertura expandidos para thresholds, edge case sem seções e isolamento multi-tenant.
- Story pronta para code review.

### File List

- `_bmad-output/implementation-artifacts/6-3-cobertura-por-secao-artefato.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `reqstudio/reqstudio-api/app/modules/artifacts/service.py`
- `reqstudio/reqstudio-api/app/modules/artifacts/schemas.py`
- `reqstudio/reqstudio-api/tests/test_artifacts_coverage.py`

### Change Log

- 2026-04-07: Story criada para `6-3` e iniciada (`in-progress`) via fluxo BMAD equivalente (`create-story` + `dev-story`).
- 2026-04-07: Implementação e testes concluídos; story movida para `review`.
- 2026-04-07: `bmad-code-review` executado; story movida para `done`.
