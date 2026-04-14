# Story 6.5: Tela de Visualização e Exportação de Artefatos

Status: done

## Story

As a Ana,  
I want tela dedicada para revisar e exportar artefato completo,  
so that eu verifique resultado final e baixe no formato certo.

## Acceptance Criteria

1. **Tela dedicada de artefato**
Given rota `/artifacts/{id}`  
When acessada em desktop  
Then exibe documento completo com scroll, toggle Negócio/Técnico, CoverageBar e citation badges.

2. **Experiência mobile Artifact Feed**
Given rota `/artifacts/{id}`  
When acessada em mobile  
Then exibe feed vertical com cards por seção (UX-DR10/UX-DR3), preservando leitura e badges.

3. **Exportação e histórico**
Given tela de artefato  
When usuário aciona exportação  
Then oferece MD negócio, MD técnico e JSON  
And exibe histórico de versões com data, razão e autor.

## Tasks / Subtasks

- [x] Implementar página de visualização de artefato no frontend (AC: 1,2,3)
  - [x] Criar rota protegida `/artifacts/:id`.
  - [x] Integrar consumo de APIs de artefato (`get`, `render`, `coverage`, `versions`, `export`).
  - [x] Renderizar desktop com documento completo e controles de visão/exportação.
  - [x] Renderizar mobile em formato feed por seção com indicadores visuais.

- [x] Cobrir comportamento crítico com testes frontend (AC: 1,3)
  - [x] Validar integração de serviço para consumo e exportação.
  - [x] Validar contrato básico de rota com suíte de App.

- [x] Preparar para code review BMAD (AC: 1,2,3)
  - [x] Registrar evidências de execução de testes.
  - [x] Consolidar notas de implementação no artefato da story.

- [x] Hotfix de jornada pós-elicitação (alinhamento PM BMAD)
  - [x] Ajustar SessionPage para preview legível de negócio (sem JSON cru por padrão).
  - [x] Incluir CTA direto `Abrir artefato` com navegação 1 clique para `/artifacts/:id`.
  - [x] Implementar descoberta de artefato: prioriza artefato da sessão, fallback para último do projeto.
  - [x] Evoluir SessionPage para modo unificado com alternância `Negócio/Técnico` e exportação inline.
  - [x] Adicionar modos de layout desktop (`Somente chat`, `Dividir tela`, `Somente artefato`).

## Dev Notes

- Story origin: `_bmad-output/planning-artifacts/epics.md` (Story 6.5).
- Dependências diretas: stories 6.2, 6.3 e 6.4 concluídas no backend.
- Rota e componentes devem seguir o design system já usado no frontend (`ProjectDetailPage`/`SessionPage`).

### Project Structure Notes

- Frontend alvo principal:
  - `reqstudio/reqstudio-ui/src/App.tsx`
  - `reqstudio/reqstudio-ui/src/pages/ArtifactPage.tsx`
  - `reqstudio/reqstudio-ui/src/services/artifactsApi.ts`
  - `reqstudio/reqstudio-ui/src/tests/*` (testes da story)

## Dev Agent Record

### Agent Model Used

gpt-5 (Codex)

### Debug Log References

- Kickoff BMAD equivalente executado: `create-story` -> `dev-story` para story `6-5`.
- Validação frontend:
  - `npm test -- src/test/artifactsApi.test.ts src/test/projectsApi.test.ts`
  - Resultado: `14 passed`.
  - `npm test -- src/tests/ArtifactPage.test.tsx`
  - Resultado: `3 passed`.
  - `npm test -- src/tests/App.test.tsx`
  - Resultado: `1 passed`.
  - `npm test -- src/tests/ArtifactPage.test.tsx src/tests/App.test.tsx`
  - Resultado: `4 passed`.
  - `npm run build`
  - Resultado: build/type-check concluídos com sucesso.
- Validação hotfix de jornada (SessionPage):
  - `npm run test -- src/tests/SessionPage.progress-panel.test.tsx src/tests/SessionPage.autoscroll.test.tsx src/tests/SessionPage.upload.integration.test.tsx src/tests/SessionPage.session-expired.test.tsx`
  - Resultado: `8 passed`.
- Validação 6.5b (UX unificada + render markdown):
  - `npm run test -- src/tests/SessionPage.progress-panel.test.tsx src/tests/SessionPage.autoscroll.test.tsx src/tests/SessionPage.upload.integration.test.tsx src/tests/SessionPage.session-expired.test.tsx src/tests/ArtifactPage.test.tsx`
  - Resultado: `11 passed`.
  - `npm run build`
  - Resultado: build/type-check concluídos com sucesso.
- `bmad-code-review` (papel BMAD QA/DEV) executado sem findings bloqueantes.
- Revalidação pós-fix de UX de exportação executada no review:
  - feedback de erro com `role="alert"` implementado e testado.

### Completion Notes List

- Página `/artifacts/:id` implementada com toggle de visão, cobertura global, documento completo (desktop) e feed por seção (mobile).
- Exportação disponível para MD negócio, MD técnico e JSON com download de arquivo.
- Feedback de erro em exportação implementado na UI para evitar falha silenciosa.
- Histórico de versões exibido na lateral com data, razão e autor.
- Navegação a partir do detalhe do projeto para abrir artefatos existentes.
- Hotfix de jornada aplicado na SessionPage com CTA direto para artefato e preview legível.
- Sessão passou a suportar fluxo unificado: leitura legível de artefato (Markdown renderizado), alternância negócio/técnico e exportação no mesmo contexto do chat.
- Story finalizada após validação manual de jornada no fluxo de sessão.

### File List

- `_bmad-output/implementation-artifacts/6-5-tela-visualizacao-exportacao-artefatos.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `reqstudio/reqstudio-ui/src/services/artifactsApi.ts`
- `reqstudio/reqstudio-ui/src/pages/ArtifactPage.tsx`
- `reqstudio/reqstudio-ui/src/pages/ProjectDetailPage.tsx`
- `reqstudio/reqstudio-ui/src/App.tsx`
- `reqstudio/reqstudio-ui/src/test/artifactsApi.test.ts`
- `reqstudio/reqstudio-ui/src/tests/ArtifactPage.test.tsx`
- `reqstudio/reqstudio-ui/src/pages/SessionPage.tsx`
- `reqstudio/reqstudio-ui/package.json`
- `reqstudio/reqstudio-ui/package-lock.json`

### Change Log

- 2026-04-08: Story criada e iniciada (`in-progress`) via fluxo BMAD equivalente.
- 2026-04-08: Implementação concluída, validações executadas e story movida para `review`.
- 2026-04-08: Ajuste pós-review aplicado (feedback de erro de exportação) com teste de regressão de UX.
- 2026-04-08: Reaberta para hotfix de jornada (análise PM BMAD); SessionPage ajustada com acesso direto ao artefato.
- 2026-04-08: Execução `dev-story` 6.5b com UX unificada na SessionPage (render markdown + alternância de visões + exportação inline).
- 2026-04-08: Aceite manual do produto registrado; story movida para `done`.
