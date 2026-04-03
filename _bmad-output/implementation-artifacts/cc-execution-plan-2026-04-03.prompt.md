## Correct Course Execution Plan (Refinado)

Objetivo: corrigir rota do Epic 5.5 com o menor risco possivel, garantindo coerencia entre status, QA e inicio do Epic 6.

### Fase A - Contencao e Verdade de Status
1. Normalizar status de sprint para refletir QA real (sem story com gap critico em `done`).
2. Registrar aprovacao formal do CC e kickoff incremental.
3. Congelar escopo: sem iniciar 6.1+ antes de 6.0 e 6.0b em `done`.

### Fase B - Fechamento de Gaps Criticos
4. Fechar QA-5-5-2-002: testar hook real `useProjectSessions` (sem logica duplicada no teste).
5. Fechar QA-5-5-4-002: teste de integracao leve `SessionPage -> ChatInput -> sendMessage`.
6. Revalidar QA-5-5-4-001 contra suite atual e manter cobertura de comportamento base do ChatInput.

### Fase C - Gate de Epic 6
7. Executar story 6-0 (hardening QA) com evidencia de execucao anexada.
8. Executar story 6-0b (DoD evidencias + handoff terminal).
9. Somente apos 7 e 8: liberar 6.1 como `in-progress`.

### Arquivos de controle
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/qa-audit-sprint-5-5.md`
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-03.md`
- `_bmad-output/planning-artifacts/epics.md`
- `project-context.md`

### Criterios de saida do CC
- Nenhum gap QA alto aberto para stories 5.5 em `done`.
- Stories 6-0 e 6-0b em `done` com evidencia.
- Epic 6 liberado para 6.1 sem pendencias estruturais.

### Estado atual da execucao
- Aprovacao formal: obtida.
- Modo: incremental.
- Implementacao iniciada: normalizacao de status e checklist do CC atualizados.
- Fase B concluida: gaps QA-5-5-2-002 e QA-5-5-4-002 fechados com evidencia de teste.
- Fase C (gate) concluida: stories 6-0 e 6-0b em `done`.
- Proximo passo recomendado: iniciar 6.1 mantendo handoff com evidencia por story.