# Sprint Change Proposal — Correct Course após Retro Epic 5.5 + QA Audit

**Data:** 2026-04-03  
**Facilitador:** Bob (Scrum Master)  
**Classificação:** Moderate — Reorganização de backlog + reforço de processo

---

## 1. Issue Summary

**Trigger principal:** A retro oficial da Epic 5.5 confirmou entrega funcional e apontou dois ajustes de processo para Epic 6 (AI-1 e AI-3). O QA audit da Sprint 5.5 listou gaps de cobertura que precisavam validação de fechamento antes da execução do Epic 6.

**Evidências analisadas:**
- `_bmad-output/implementation-artifacts/epic-5-5-retro-2026-04-03.md`
- `_bmad-output/implementation-artifacts/qa-audit-sprint-5-5.md`
- Código atual de testes e hooks no backend/frontend

**Resultado da verificação técnica (estado real):**
- QA-5-5-1-001 (seed orphan/duplicata): **Fechado** (há teste dedicado + deleção por nome no seed com `--force`).
- QA-5-5-2-001 (`_update_progress_summary`): **Fechado parcialmente com cobertura mínima** (teste existe para chamada de DB/update).
- QA-5-5-2-002 (`useProjectSessions`): **Aberto** (teste ainda usa lógica duplicada em vez do hook real).
- QA-5-5-4-001 (regressão de comportamento do ChatInput): **Fechado** (`ChatInput.behavior.test.tsx` presente).
- QA-5-5-4-002 (`SessionPage` integração upload->sendMessage): **Aberto** (sem teste de integração da página).

---

## 2. Impact Analysis

### Epic Impact

- **Epic 5.5:** permanece `done` (sem reabertura do épico).
- **Epic 6:** recebe um gate explícito de qualidade/processo antes das stories funcionais 6.1–6.5.
- **Epics 7 e 8:** sem impacto direto.

### Story Impact

- Adicionar duas stories de pré-execução no Epic 6:
  - `6.0 Gate de QA — Hardening de Sessões e Upload`
  - `6.0b DoD com Checklist de Evidências e Handoff de Terminal`

### Artifact Conflict / Ajustes Necessários

- `epics.md`: incluir as stories 6.0 e 6.0b antes da 6.1.
- `sprint-status.yaml`: incluir status backlog para as novas stories do Epic 6.
- Não há conflito com PRD, arquitetura ou UX: mudança é de governança/qualidade e reforça NFRs.

### Technical Impact

- Reduz risco de regressão em retomada de sessão e upload contextual.
- Reduz risco processual de “presumir sucesso” em ambientes com Terminal Restricted Mode.

---

## 3. Recommended Approach

**Abordagem escolhida:** **Hybrid (Opção 1 + reforço de governança)**

- Base principal: **Direct Adjustment** (adicionar e executar gate de QA/DoD no início do Epic 6).
- Sem rollback e sem alteração de MVP.

**Rationale:**
- Evita iniciar Epic 6 com débito de teste conhecido em fluxos críticos.
- Formaliza AI-3 da retro como regra operacional de aceitação.
- Mantém momentum, sem replanejamento estrutural de épicos.

**Esforço estimado:** Baixo-Médio (1 a 2 ciclos curtos)  
**Risco:** Médio (se gate for ignorado), Baixo (se gate for cumprido)

---

## 4. Detailed Change Proposals

### 4.1 Epics (OLD → NEW)

**Artefato:** `_bmad-output/planning-artifacts/epics.md`

**OLD:** Epic 6 iniciava diretamente na Story 6.1.  
**NEW:** Epic 6 inicia com duas stories de preflight (6.0 e 6.0b) antes da 6.1.

**Justificativa:** garantir fechamento explícito dos gaps QA remanescentes e institucionalizar o checklist de evidências da retro 5.5.

### 4.2 Sprint Status (OLD → NEW)

**Artefato:** `_bmad-output/implementation-artifacts/sprint-status.yaml`

**OLD:** backlog do Epic 6 continha apenas `6-1` a `6-5`.  
**NEW:** backlog do Epic 6 passa a conter `6-0` e `6-0b` antes de `6-1`.

**Justificativa:** tornar o gate rastreável no fluxo oficial de execução.

### 4.3 Processo/DoD (aplicação operacional)

**OLD:** evidências de terminal/teste não eram critério obrigatório formal em todo fechamento.  
**NEW:** cada story em `review/done` deve carregar evidência de execução e handoff explícito para comandos manuais.

**Justificativa:** atender AI-3 da retro e reduzir falsos positivos de conclusão em ambiente restrito.

---

## 5. Implementation Handoff

**Escopo:** Moderate

**Responsabilidades sugeridas:**
- **Bob (SM):** manter 6.0 e 6.0b como gate obrigatório antes da 6.1.
- **Dana (QA):** validar critérios de aceite de 6.0 e 6.0b com evidência anexada.
- **Amelia (Dev):** implementar testes faltantes e atualização de checklist/template.
- **Charlie/Alice:** seguir para 6.1+ somente após gate aprovado.

**Success Criteria do Correct Course:**
1. `useProjectSessions` coberto por teste do hook real (não réplica de lógica).
2. Fluxo `SessionPage -> ChatInput -> sendMessage` coberto por teste de integração leve.
3. Evidência de comando/teste anexada por story no encerramento.
4. Epic 6 funcional só inicia após `6.0` e `6.0b` em `done`.

---

## 6. Checklist de Execução do CC (Status)

### 1) Trigger e Contexto
- [x] 1.1 Trigger identificado (retro 5.5 + QA audit)
- [x] 1.2 Problema definido
- [x] 1.3 Evidências coletadas

### 2) Epic Impact
- [x] 2.1 Epic atual avaliado
- [x] 2.2 Mudanças em nível de épico definidas
- [x] 2.3 Epics futuros revisados
- [x] 2.4 Validação de novos needs de épico/story
- [x] 2.5 Priorização ajustada (gate antes de 6.1)

### 3) Artifact Impact
- [x] 3.1 PRD sem conflito direto
- [x] 3.2 Arquitetura sem conflito direto
- [x] 3.3 UX sem conflito direto
- [x] 3.4 Artefatos secundários impactados (status/checklist de processo)

### 4) Path Forward
- [x] 4.1 Option 1 (Direct Adjustment) viável
- [N/A] 4.2 Option 2 (Rollback)
- [N/A] 4.3 Option 3 (MVP Review)
- [x] 4.4 Caminho selecionado e justificado

### 5) Proposal Components
- [x] 5.1 Issue summary
- [x] 5.2 Impact consolidado
- [x] 5.3 Abordagem recomendada
- [x] 5.4 Plano de ação alto nível
- [x] 5.5 Handoff definido

### 6) Final Review
- [x] 6.1 Revisão de completude
- [x] 6.2 Proposta consistente
- [x] 6.3 Aprovação explícita do usuário obtida
- [x] 6.4 Sprint status atualizado para refletir mudanças
- [x] 6.5 Confirmação final de papéis/timeline definida
- [x] 6.6 Gate `6.0` e `6.0b` concluído com evidência registrada

---

## Observação Operacional

Tentativa de executar gate automático de Policy Mode (`seprocess/scaffold/check-policy-mode.py`) não pôde ser concluída porque o script não existe neste workspace.

## Aprovação e Kickoff

- **Aprovação do usuário:** `yes` (2026-04-03)
- **Modo de execução aprovado:** Incremental
- **Kickoff do CC:** iniciado com normalização de status no `sprint-status.yaml` para refletir gaps QA ainda em revisão

### Progresso de Implementação (incremental)

- Gaps fechados nesta etapa:
  - `QA-5-5-2-002` (hook real `useProjectSessions`)
  - `QA-5-5-4-002` (integração `SessionPage -> ChatInput -> sendMessage`)
- Evidência de teste anexada:
  - `vitest run src/tests/useProjectSessions.test.ts src/tests/SessionPage.upload.integration.test.tsx`
  - Resultado: `2 files passed`, `4 tests passed`
- Atualização de status aplicada:
  - Epic 5.5 retornou para `done`
  - Story gate `6-0` marcada `done`
  - Story gate `6-0b` marcada `done`
  - Epic 6 movida para `in-progress`

### Decisão de Liberação

- Gate de entrada do Epic 6 concluído (`6.0` + `6.0b` = `done`).
- Epic 6 está apto para iniciar `6.1` em próximo ciclo, mantendo execução incremental.

### Hardening Operacional — TESTING env (2026-04-03)

- Concluído: remoção de `TESTING` manual do `.env` e fallback via compose (`TESTING=${TESTING:-false}` no service `api`).
- Validação de configuração: `settings.TESTING=False` no container padrão.
- Não regressão: com execução pontual `TESTING=true`, migrations são puladas; com `TESTING=false`, migrations são executadas.
- Observação: ambiente atual mantém falha de startup/saúde (`curl /health` e `/docs` com `Empty reply from server`) e ausência de `"Application startup complete"` nos logs. Este ponto ficou registrado como pendência técnica separada do hardening de env.

### Addendum II — UX Chat + Sessão + Persona BMAD (2026-04-03)

**Trigger:** primeiras impressões do teste manual pós-login, com dois pontos críticos priorizados pelo usuário:
- Upload/documento no chat com comportamento inativo
- Expiração de sessão percebida como abrupta durante uso curto (3-4 min)

**Decisão de escopo (aprovada):**
- Manter a execução dentro do Epic 6 para evitar vai-e-volta entre sprints
- Inserir dois novos gates antes da Story 6.1:
  - `6.0c Hardening de UX do Chat e Confiabilidade de Sessão`
  - `6.0d Fidelidade da Persona BMAD na Elicitação`

**Justificativa de coerência com Epic 6:**
- Não desvia do objetivo de artefatos; fortalece o fluxo de entrada da elicitação que alimenta os artefatos
- Reduz risco de retrabalho em 6.1–6.5 por problemas de UX/core loop ainda abertos
- Preserva momentum com correções de alto impacto em retenção e percepção de qualidade

**Observação de priorização:**
- `custo/tokens` tratado como ajuste de consistência de arredondamento dentro de `6.0c` (não como épico separado)
- Persona configurada para baseline "100% BMAD" no início da conversa, com progressão e sinalização de fechamento explícitas

---

**Solicitação de aprovação:** Você aprova esta Sprint Change Proposal para execução (`yes/no/revise`)?

*Gerado em 2026-04-03 — Correct Course (Bob)*
